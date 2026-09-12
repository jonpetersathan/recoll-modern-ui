#!/usr/bin/env python3
"""
CLI wrapper for metadata extraction matching the Rust extractor binary interface.
Can be run directly or used as a fallback if the compiled Rust binary is unavailable.
"""

import json
import os
import sys

# Ensure script dir is not shadowing standard library (e.g. logging)
_script_dir = os.path.dirname(os.path.abspath(__file__))
while _script_dir in sys.path:
    sys.path.remove(_script_dir)
_parent_dir = os.path.abspath(os.path.join(_script_dir, ".."))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from recollweb.metadata import evaluate_rules_in_memory


def resolve_config_path(override_path: str = None) -> str:
    if override_path and os.path.isfile(override_path):
        return override_path

    conf_dir = os.environ.get("RECOLL_CONFDIR")
    if conf_dir:
        p = os.path.join(conf_dir, "metadata_rules.json")
        if os.path.isfile(p):
            return p

    home = os.environ.get("HOME")
    if home:
        p = os.path.join(home, ".recoll", "metadata_rules.json")
        if os.path.isfile(p):
            return p

    default_p = "/root/.recoll/metadata_rules.json"
    if os.path.isfile(default_p):
        return default_p

    return ""


def main():
    args = sys.argv[1:]
    config_override = None
    test_mode = False
    target_file = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--config", "-c"):
            if i + 1 < len(args):
                config_override = args[i + 1]
                i += 1
        elif arg in ("--test", "-t"):
            test_mode = True
        elif arg in ("--version", "-v"):
            print("recoll-metadata-extractor v0.9.5")
            sys.exit(0)
        elif arg in ("--help", "-h"):
            print("Usage: recoll-metadata-extractor [OPTIONS] <FILE_PATH>")
            print("Extracts metadata from file paths based on metadata_rules.json")
            sys.exit(0)
        elif not arg.startswith('-') and target_file is None:
            target_file = arg
        i += 1

    if not target_file:
        if test_mode:
            print("{}")
        sys.exit(0)

    cfg_path = resolve_config_path(config_override)
    rules_data = {"rules": []}
    if cfg_path and os.path.isfile(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
        except Exception:
            pass

    metadata = evaluate_rules_in_memory(rules_data.get("rules", []), target_file)

    if test_mode:
        print(json.dumps(metadata, indent=2))
    else:
        # Output in Recoll's rclmulti format: field = value
        for k, v in sorted(metadata.items()):
            print(f"{k} = {v}")


if __name__ == "__main__":
    main()
