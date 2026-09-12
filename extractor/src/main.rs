use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RulesConfig {
    #[serde(default)]
    pub rules: Vec<MetadataRule>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelimiterMapping {
    pub index: usize,
    pub field: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum RuleType {
    #[serde(rename = "depth")]
    Depth {
        #[serde(default)]
        depth: i32,
        field: String,
    },
    #[serde(rename = "delimiter")]
    Delimiter {
        delimiter: String,
        #[serde(default = "default_delimiter_target")]
        target: String, // "filename" or "path"
        mappings: Vec<DelimiterMapping>,
    },
    #[serde(rename = "regex")]
    Regex {
        pattern: String,
    },
}

fn default_delimiter_target() -> String {
    "filename".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetadataRule {
    pub id: String,
    #[serde(default)]
    pub name: String,
    #[serde(default = "default_enabled")]
    pub enabled: bool,
    #[serde(default)]
    pub path_filter: String,
    #[serde(flatten)]
    pub rule_type: RuleType,
}

fn default_enabled() -> bool {
    true
}

/// Simple, efficient path glob pattern matcher (supports *, **, and literal segments)
pub fn matches_glob(pattern: &str, path_str: &str) -> bool {
    let pattern = pattern.trim();
    if pattern.is_empty() || pattern == "*" || pattern == "**" {
        return true;
    }

    // Exact match
    if pattern == path_str {
        return true;
    }

    // Suffix match like *.pdf or **/*.pdf
    if let Some(suffix) = pattern.strip_prefix("**/*.") {
        return path_str.ends_with(&format!(".{}", suffix));
    }
    if let Some(suffix) = pattern.strip_prefix("*.") {
        return path_str.ends_with(&format!(".{}", suffix));
    }

    // Prefix match like /data/projects/**
    if let Some(prefix) = pattern.strip_suffix("/**") {
        return path_str.starts_with(prefix);
    }
    if let Some(prefix) = pattern.strip_suffix("/*") {
        return path_str.starts_with(prefix);
    }

    // Wildcard substring match
    if pattern.starts_with('*') && pattern.ends_with('*') && pattern.len() > 2 {
        let substr = &pattern[1..pattern.len() - 1];
        return path_str.contains(substr);
    }

    // Fallback: convert glob to basic regex
    let mut regex_str = String::from("^");
    let mut chars = pattern.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '*' => {
                if chars.peek() == Some(&'*') {
                    chars.next();
                    if chars.peek() == Some(&'/') {
                        chars.next();
                        regex_str.push_str("(?:.*/)?");
                    } else {
                        regex_str.push_str(".*");
                    }
                } else {
                    regex_str.push_str("[^/]*");
                }
            }
            '?' => regex_str.push_str("[^/]"),
            '.' | '(' | ')' | '+' | '|' | '^' | '$' | '@' | '%' | '{' | '}' | '[' | ']' => {
                regex_str.push('\\');
                regex_str.push(c);
            }
            _ => regex_str.push(c),
        }
    }
    regex_str.push('$');

    Regex::new(&regex_str).map(|re| re.is_match(path_str)).unwrap_or(false)
}

/// Sanitize field names to alphanumeric + underscores for Recoll compatibility, preserving dmtime@ directives
fn sanitize_field_name(name: &str) -> String {
    let trimmed = name.trim();
    let lower = trimmed.to_lowercase();
    if lower.starts_with("dmtime@") {
        let suffix: String = trimmed[7..]
            .chars()
            .filter(|c| c.is_ascii_alphanumeric() || *c == '_')
            .collect();
        return format!("dmtime@{}", suffix);
    }
    trimmed
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() || c == '_' { c } else { '_' })
        .collect::<String>()
        .to_lowercase()
}

/// Normalize value by stripping newlines/carriage returns
fn sanitize_field_value(val: &str) -> String {
    val.replace('\n', " ").replace('\r', " ").trim().to_string()
}

fn days_from_civil(y: i64, m: u32, d: u32) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = (y - era * 400) as u32;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146097 + doe as i64 - 719468
}

fn date_to_utc_epoch(y: i64, m: u32, d: u32) -> Option<i64> {
    if y <= 0 || m < 1 || m > 12 || d < 1 || d > 31 {
        return None;
    }
    let days_in_month = match m {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            let is_leap = (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
            if is_leap { 29 } else { 28 }
        }
        _ => return None,
    };
    if d > days_in_month {
        return None;
    }
    let days = days_from_civil(y, m, d);
    Some(days * 86400)
}

fn parse_month_str(s: &str) -> Option<u32> {
    let trimmed = s.trim();
    if let Ok(m) = trimmed.parse::<u32>() {
        if (1..=12).contains(&m) {
            return Some(m);
        }
        return None;
    }
    match trimmed.to_lowercase().as_str() {
        "jan" | "january" => Some(1),
        "feb" | "february" => Some(2),
        "mar" | "march" => Some(3),
        "apr" | "april" => Some(4),
        "may" => Some(5),
        "jun" | "june" => Some(6),
        "jul" | "july" => Some(7),
        "aug" | "august" => Some(8),
        "sep" | "sept" | "september" => Some(9),
        "oct" | "october" => Some(10),
        "nov" | "november" => Some(11),
        "dec" | "december" => Some(12),
        _ => None,
    }
}

fn parse_day_str(s: &str) -> Option<u32> {
    if let Ok(d) = s.trim().parse::<u32>() {
        if (1..=31).contains(&d) {
            return Some(d);
        }
    }
    None
}

fn parse_year_str(s: &str) -> Option<i64> {
    if let Ok(mut y) = s.trim().parse::<i64>() {
        if y < 100 && y >= 0 {
            y += if y < 70 { 2000 } else { 1900 };
        }
        if y > 0 {
            return Some(y);
        }
    }
    None
}

fn parse_formatted_date(val: &str, fmt: &str) -> Option<i64> {
    let trimmed = val.trim();
    if trimmed.is_empty() {
        return None;
    }

    let parts: Vec<&str> = trimmed
        .split(|c: char| c == '-' || c == '/' || c == '.' || c == '_' || c.is_whitespace())
        .filter(|s| !s.is_empty())
        .collect();

    if parts.len() == 3 {
        match fmt {
            "yyyymmdd" => {
                let y = parse_year_str(parts[0])?;
                let m = parse_month_str(parts[1])?;
                let d = parse_day_str(parts[2])?;
                return date_to_utc_epoch(y, m, d);
            }
            "ddmmyyyy" => {
                let d = parse_day_str(parts[0])?;
                let m = parse_month_str(parts[1])?;
                let y = parse_year_str(parts[2])?;
                return date_to_utc_epoch(y, m, d);
            }
            "mmddyyyy" => {
                let m = parse_month_str(parts[0])?;
                let d = parse_day_str(parts[1])?;
                let y = parse_year_str(parts[2])?;
                return date_to_utc_epoch(y, m, d);
            }
            _ => {}
        }
    }

    let digits: String = trimmed.chars().filter(|c| c.is_ascii_digit()).collect();
    if digits.len() == 8 {
        match fmt {
            "yyyymmdd" => {
                let y = digits[0..4].parse::<i64>().ok()?;
                let m = digits[4..6].parse::<u32>().ok()?;
                let d = digits[6..8].parse::<u32>().ok()?;
                return date_to_utc_epoch(y, m, d);
            }
            "ddmmyyyy" => {
                let d = digits[0..2].parse::<u32>().ok()?;
                let m = digits[2..4].parse::<u32>().ok()?;
                let y = digits[4..8].parse::<i64>().ok()?;
                return date_to_utc_epoch(y, m, d);
            }
            "mmddyyyy" => {
                let m = digits[0..2].parse::<u32>().ok()?;
                let d = digits[2..4].parse::<u32>().ok()?;
                let y = digits[4..8].parse::<i64>().ok()?;
                return date_to_utc_epoch(y, m, d);
            }
            _ => {}
        }
    }

    None
}

fn process_date_directives(results: &mut BTreeMap<String, String>) {
    let mut keys_to_delete = Vec::new();
    let mut extracted_timestamp: Option<i64> = None;

    for (k, v) in results.iter() {
        let lower = k.to_lowercase();
        if lower == "dmtime@yyyymmdd" || lower == "dmtime_yyyymmdd" {
            keys_to_delete.push(k.clone());
            if let Some(ts) = parse_formatted_date(v, "yyyymmdd") {
                extracted_timestamp = Some(ts);
            }
        } else if lower == "dmtime@ddmmyyyy" || lower == "dmtime_ddmmyyyy" {
            keys_to_delete.push(k.clone());
            if let Some(ts) = parse_formatted_date(v, "ddmmyyyy") {
                extracted_timestamp = Some(ts);
            }
        } else if lower == "dmtime@mmddyyyy" || lower == "dmtime_mmddyyyy" {
            keys_to_delete.push(k.clone());
            if let Some(ts) = parse_formatted_date(v, "mmddyyyy") {
                extracted_timestamp = Some(ts);
            }
        }
    }

    let mut year_val: Option<String> = None;
    let mut month_val: Option<String> = None;
    let mut day_val: Option<String> = None;

    for (k, v) in results.iter() {
        let lower = k.to_lowercase();
        if lower == "dmtime@year" || lower == "dmtime_year" {
            keys_to_delete.push(k.clone());
            year_val = Some(v.clone());
        } else if lower == "dmtime@month" || lower == "dmtime_month" {
            keys_to_delete.push(k.clone());
            month_val = Some(v.clone());
        } else if lower == "dmtime@day" || lower == "dmtime_day" {
            keys_to_delete.push(k.clone());
            day_val = Some(v.clone());
        }
    }

    if extracted_timestamp.is_none() {
        if let Some(ref y_str) = year_val {
            if let Some(y) = parse_year_str(y_str) {
                let m = month_val.as_deref().and_then(parse_month_str).unwrap_or(1);
                let d = day_val.as_deref().and_then(parse_day_str).unwrap_or(1);
                if let Some(ts) = date_to_utc_epoch(y, m, d) {
                    extracted_timestamp = Some(ts);
                }
            }
        }
    }

    for k in results.keys() {
        if k.to_lowercase().starts_with("dmtime@") {
            keys_to_delete.push(k.clone());
        }
    }

    for k in keys_to_delete {
        results.remove(&k);
    }

    if let Some(ts) = extracted_timestamp {
        results.insert("dmtime".to_string(), ts.to_string());
    }
}

/// Evaluates all enabled rules against a given file path string.
pub fn evaluate_rules(config: &RulesConfig, file_path: &str) -> BTreeMap<String, String> {
    let mut results: BTreeMap<String, String> = BTreeMap::new();
    let normalized_path = file_path.replace('\\', "/");
    let path = Path::new(&normalized_path);

    // Extract segments: omit empty components
    let segments: Vec<&str> = normalized_path
        .split('/')
        .filter(|s| !s.is_empty())
        .collect();

    let filename = path
        .file_name()
        .and_then(|f| f.to_str())
        .unwrap_or("");

    // Filename without extension
    let stem = path
        .file_stem()
        .and_then(|f| f.to_str())
        .unwrap_or(filename);

    for rule in &config.rules {
        if !rule.enabled {
            continue;
        }

        // Check path filter / glob
        if !rule.path_filter.is_empty() && !matches_glob(&rule.path_filter, &normalized_path) {
            continue;
        }

        match &rule.rule_type {
            RuleType::Depth { depth, field } => {
                if segments.is_empty() || field.trim().is_empty() {
                    continue;
                }
                let target_index = if *depth < 0 {
                    let rev = segments.len() as i32 + *depth;
                    if rev >= 0 { Some(rev as usize) } else { None }
                } else if (*depth as usize) < segments.len() {
                    Some(*depth as usize)
                } else {
                    None
                };

                if let Some(idx) = target_index {
                    let val = segments[idx];
                    let clean_field = sanitize_field_name(field);
                    let clean_val = sanitize_field_value(val);
                    if !clean_field.is_empty() && !clean_val.is_empty() {
                        results.insert(clean_field, clean_val);
                    }
                }
            }
            RuleType::Delimiter { delimiter, target, mappings } => {
                if delimiter.is_empty() || mappings.is_empty() {
                    continue;
                }

                let target_str = match target.as_str() {
                    "path" => normalized_path.as_str(),
                    "stem" => stem,
                    _ => filename,
                };

                let tokens: Vec<&str> = target_str.split(delimiter.as_str()).collect();

                for m in mappings {
                    if m.index < tokens.len() {
                        let clean_field = sanitize_field_name(&m.field);
                        let clean_val = sanitize_field_value(tokens[m.index]);
                        if !clean_field.is_empty() && !clean_val.is_empty() {
                            results.insert(clean_field, clean_val);
                        }
                    }
                }
            }
            RuleType::Regex { pattern } => {
                if pattern.trim().is_empty() {
                    continue;
                }
                if let Ok(re) = Regex::new(pattern) {
                    if let Some(caps) = re.captures(&normalized_path) {
                        for name in re.capture_names().flatten() {
                            if let Some(m) = caps.name(name) {
                                let clean_field = sanitize_field_name(name);
                                let clean_val = sanitize_field_value(m.as_str());
                                if !clean_field.is_empty() && !clean_val.is_empty() {
                                    results.insert(clean_field, clean_val);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    process_date_directives(&mut results);
    results
}

fn resolve_config_path(override_path: Option<&str>) -> Option<PathBuf> {
    if let Some(p) = override_path {
        let pb = PathBuf::from(p);
        if pb.is_file() {
            return Some(pb);
        }
    }

    if let Ok(conf_dir) = env::var("RECOLL_CONFDIR") {
        let p = Path::new(&conf_dir).join("metadata_rules.json");
        if p.is_file() {
            return Some(p);
        }
    }

    if let Ok(home) = env::var("HOME") {
        let p = Path::new(&home).join(".recoll").join("metadata_rules.json");
        if p.is_file() {
            return Some(p);
        }
    }

    let default_p = PathBuf::from("/root/.recoll/metadata_rules.json");
    if default_p.is_file() {
        return Some(default_p);
    }

    None
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut config_override: Option<&str> = None;
    let mut test_mode = false;
    let mut target_file: Option<&str> = None;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--config" | "-c" => {
                if i + 1 < args.len() {
                    config_override = Some(&args[i + 1]);
                    i += 1;
                }
            }
            "--test" | "-t" => {
                test_mode = true;
            }
            "--version" | "-v" => {
                println!("recoll-metadata-extractor v{}", env!("CARGO_PKG_VERSION"));
                return;
            }
            "--help" | "-h" => {
                eprintln!("Usage: recoll-metadata-extractor [OPTIONS] <FILE_PATH>");
                eprintln!("Extracts metadata from file paths based on metadata_rules.json");
                eprintln!("\nOptions:");
                eprintln!("  -c, --config <PATH>   Path to metadata_rules.json");
                eprintln!("  -t, --test            Output extracted metadata as JSON");
                eprintln!("  -v, --version         Print version");
                eprintln!("  -h, --help            Print help");
                return;
            }
            other => {
                if !other.starts_with('-') && target_file.is_none() {
                    target_file = Some(other);
                }
            }
        }
        i += 1;
    }

    let target_path = match target_file {
        Some(p) => p,
        None => {
            if test_mode {
                println!("{{}}");
            }
            return;
        }
    };

    let config_path = resolve_config_path(config_override);
    let rules_config = match config_path {
        Some(p) => match fs::read_to_string(&p) {
            Ok(content) => serde_json::from_str::<RulesConfig>(&content).unwrap_or_else(|_| RulesConfig { rules: Vec::new() }),
            Err(_) => RulesConfig { rules: Vec::new() },
        },
        None => RulesConfig { rules: Vec::new() },
    };

    let metadata = evaluate_rules(&rules_config, target_path);

    if test_mode {
        let json_str = serde_json::to_string_pretty(&metadata).unwrap_or_else(|_| "{}".to_string());
        println!("{}", json_str);
    } else {
        // Output in Recoll's rclmulti format: field = value per line
        for (field, value) in metadata {
            println!("{} = {}", field, value);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_glob_matching() {
        assert!(matches_glob("*.pdf", "/data/documents/report.pdf"));
        assert!(matches_glob("**/*.pdf", "/data/documents/report.pdf"));
        assert!(matches_glob("/data/projects/**", "/data/projects/alpha/doc.txt"));
        assert!(!matches_glob("/data/invoices/**", "/data/projects/alpha/doc.txt"));
    }

    #[test]
    fn test_depth_rule() {
        let config = RulesConfig {
            rules: vec![
                MetadataRule {
                    id: "r1".into(),
                    name: "Department".into(),
                    enabled: true,
                    path_filter: "".into(),
                    rule_type: RuleType::Depth {
                        depth: 2, // /data/departments/finance/doc.pdf -> 0:data, 1:departments, 2:finance
                        field: "department".into(),
                    },
                },
                MetadataRule {
                    id: "r2".into(),
                    name: "ParentDir".into(),
                    enabled: true,
                    path_filter: "".into(),
                    rule_type: RuleType::Depth {
                        depth: -2, // parent folder
                        field: "folder".into(),
                    },
                },
            ],
        };

        let res = evaluate_rules(&config, "/data/departments/finance/invoices/doc.pdf");
        assert_eq!(res.get("department"), Some(&"finance".to_string()));
        assert_eq!(res.get("folder"), Some(&"invoices".to_string()));
    }

    #[test]
    fn test_delimiter_rule() {
        let config = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_delim".into(),
                name: "Invoice Delimiter".into(),
                enabled: true,
                path_filter: "*.pdf".into(),
                rule_type: RuleType::Delimiter {
                    delimiter: "_".into(),
                    target: "stem".into(),
                    mappings: vec![
                        DelimiterMapping { index: 0, field: "doctype".into() },
                        DelimiterMapping { index: 1, field: "year".into() },
                        DelimiterMapping { index: 2, field: "doc_id".into() },
                    ],
                },
            }],
        };

        let res = evaluate_rules(&config, "/data/invoices/INV_2024_0042.pdf");
        assert_eq!(res.get("doctype"), Some(&"INV".to_string()));
        assert_eq!(res.get("year"), Some(&"2024".to_string()));
        assert_eq!(res.get("doc_id"), Some(&"0042".to_string()));
    }

    #[test]
    fn test_regex_rule() {
        let config = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_regex".into(),
                name: "Project Regex".into(),
                enabled: true,
                path_filter: "".into(),
                rule_type: RuleType::Regex {
                    pattern: r".*/projects/(?P<project>[^/]+)/(?P<year>\d{4})/(?P<client>[^_]+)_(?P<title>[^.]+)\.pdf".into(),
                },
            }],
        };

        let res = evaluate_rules(&config, "/data/projects/Phoenix/2026/AcmeCorp_Contract.pdf");
        assert_eq!(res.get("project"), Some(&"Phoenix".to_string()));
        assert_eq!(res.get("year"), Some(&"2026".to_string()));
        assert_eq!(res.get("client"), Some(&"AcmeCorp".to_string()));
        assert_eq!(res.get("title"), Some(&"Contract".to_string()));
    }

    #[test]
    fn test_date_directives_yyyymmdd() {
        let config = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_date".into(),
                name: "Date YYYYMMDD".into(),
                enabled: true,
                path_filter: "".into(),
                rule_type: RuleType::Delimiter {
                    delimiter: "_".into(),
                    target: "stem".into(),
                    mappings: vec![
                        DelimiterMapping { index: 0, field: "doctype".into() },
                        DelimiterMapping { index: 1, field: "dmtime@YYYYMMDD".into() },
                        DelimiterMapping { index: 2, field: "title".into() },
                    ],
                },
            }],
        };
        let res = evaluate_rules(&config, "/data/invoices/INV_20230514_AnnualReport.pdf");
        assert_eq!(res.get("doctype"), Some(&"INV".to_string()));
        assert_eq!(res.get("title"), Some(&"AnnualReport".to_string()));
        assert_eq!(res.get("dmtime"), Some(&"1684022400".to_string()));
        assert!(!res.contains_key("dmtime@YYYYMMDD"));
    }

    #[test]
    fn test_date_directives_ddmmyyyy_and_mmddyyyy() {
        let config_dd = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_dd".into(),
                name: "Date DDMMYYYY".into(),
                enabled: true,
                path_filter: "".into(),
                rule_type: RuleType::Delimiter {
                    delimiter: "_".into(),
                    target: "stem".into(),
                    mappings: vec![DelimiterMapping { index: 0, field: "dmtime@DDMMYYYY".into() }],
                },
            }],
        };
        let res_dd = evaluate_rules(&config_dd, "/data/invoices/14052023_file.pdf");
        assert_eq!(res_dd.get("dmtime"), Some(&"1684022400".to_string()));
        assert!(!res_dd.contains_key("dmtime@DDMMYYYY"));

        let config_mm = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_mm".into(),
                name: "Date MMDDYYYY".into(),
                enabled: true,
                path_filter: "".into(),
                rule_type: RuleType::Delimiter {
                    delimiter: "_".into(),
                    target: "stem".into(),
                    mappings: vec![DelimiterMapping { index: 0, field: "dmtime@MMDDYYYY".into() }],
                },
            }],
        };
        let res_mm = evaluate_rules(&config_mm, "/data/invoices/05142023_file.pdf");
        assert_eq!(res_mm.get("dmtime"), Some(&"1684022400".to_string()));
        assert!(!res_mm.contains_key("dmtime@MMDDYYYY"));
    }

    #[test]
    fn test_date_directives_split_month() {
        for m_str in ["2", "02", "Feb", "February", "february", "FEBRUARY"] {
            let config = RulesConfig {
                rules: vec![MetadataRule {
                    id: "r_split".into(),
                    name: "Split Date".into(),
                    enabled: true,
                    path_filter: "".into(),
                    rule_type: RuleType::Delimiter {
                        delimiter: "_".into(),
                        target: "stem".into(),
                        mappings: vec![
                            DelimiterMapping { index: 0, field: "dmtime@year".into() },
                            DelimiterMapping { index: 1, field: "dmtime@month".into() },
                            DelimiterMapping { index: 2, field: "dmtime@day".into() },
                        ],
                    },
                }],
            };
            let path = format!("/data/docs/2023_{}_14.pdf", m_str);
            let res = evaluate_rules(&config, &path);
            assert_eq!(res.get("dmtime"), Some(&"1676332800".to_string()), "Failed for {}", m_str);
            assert!(!res.contains_key("dmtime@year"));
            assert!(!res.contains_key("dmtime@month"));
            assert!(!res.contains_key("dmtime@day"));
        }
    }

    #[test]
    fn test_date_directives_missing_day_defaults_to_one() {
        let config = RulesConfig {
            rules: vec![MetadataRule {
                id: "r_no_day".into(),
                name: "No Day".into(),
                enabled: true,
                path_filter: "".into(),
                rule_type: RuleType::Delimiter {
                    delimiter: "_".into(),
                    target: "stem".into(),
                    mappings: vec![
                        DelimiterMapping { index: 0, field: "dmtime@year".into() },
                        DelimiterMapping { index: 1, field: "dmtime@month".into() },
                    ],
                },
            }],
        };
        let res = evaluate_rules(&config, "/data/docs/2023_02.pdf");
        assert_eq!(res.get("dmtime"), Some(&"1675209600".to_string()));
    }
}

