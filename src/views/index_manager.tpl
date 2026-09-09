%include("header", title=" / Index & Metadata")
<div id="index-box" class="settings-card" onmousemove="updateGlow(event, this)">
    <div class="card-glow"></div>

    <!-- Header Section with Live Status Pill -->
    <div class="settings-header" style="justify-content: space-between; align-items: flex-start;">
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div class="brand-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                </svg>
            </div>
            <div>
                <h2 class="settings-title">Index Management</h2>
                <p class="settings-helper">Monitor database health, trigger re-indexing jobs, and configure sub-microsecond metadata extraction</p>
            </div>
        </div>
        % job_mode = job.get('mode') if defined('job') and isinstance(job, dict) else None
        % is_running = status == 'running'
        % has_index = exists if defined('exists') and exists is not None else True
        % if is_running:
            % if job_mode == 'full' or not has_index:
                % pill_cls = 'is-creating'
                % pill_txt = 'Creating Index'
            % else:
                % pill_cls = 'is-updating is-running'
                % pill_txt = 'Updating Index'
            % end
        % elif not has_index:
            % pill_cls = 'is-no-index'
            % pill_txt = 'No index'
        % else:
            % pill_cls = 'is-idle'
            % pill_txt = 'Index Ready'
        % end
        <div id="index-status-pill" class="index-status-pill {{pill_cls}}">
            <span class="status-dot-pulse"></span>
            <span id="index-status-text">{{pill_txt}}</span>
        </div>
    </div>

    <!-- Section 1: Database Metrics & Control Operations -->
    <div class="settings-section">
        <div class="settings-section-title">
            <div style="display: inline-flex; align-items: center; gap: 8px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                </svg>
                <span>Metrics</span>
            </div>
            <div class="section-title-actions" style="margin-left: auto; display: inline-flex; align-items: center; gap: 8px;">
                % has_index = exists if defined('exists') and exists is not None else True
                % is_running = status == 'running'
                % btn_label = 'Create Index' if not has_index else 'Update Index'
                <button type="button" class="btn btn-primary btn-sm" id="btn-index-action" onclick="triggerIndexAction()" {{'disabled' if is_running else ''}}>
                    <span id="btn-index-icon">
                        % if not has_index:
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        % else:
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="23 4 23 10 17 10"></polyline>
                            <polyline points="1 20 1 14 7 14"></polyline>
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                        </svg>
                        % end
                    </span>
                    <span id="btn-index-text">{{btn_label}}</span>
                </button>
                <button type="button" class="btn btn-danger-ghost btn-sm" id="btn-purge-index" onclick="confirmPurgeIndex()" {{'disabled' if is_running or not has_index else ''}}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        <line x1="10" y1="11" x2="10" y2="17"></line>
                        <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                    <span>Purge Index</span>
                </button>
            </div>
        </div>

        <!-- Metric Cards Grid -->
        <div class="stats-grid">
            <div class="stat-card" onmousemove="updateGlow(event, this)">
                <div class="card-glow"></div>
                <div class="stat-card-top">
                    <div class="stat-card-icon icon-cyan">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                    </div>
                    <div class="stat-card-label">Index Files</div>
                </div>
                <div class="stat-card-value" id="stat-doc-count">{{doc_count}}</div>
                <div class="stat-card-sub">Indexed entries in database</div>
            </div>

            <div class="stat-card" onmousemove="updateGlow(event, this)">
                <div class="card-glow"></div>
                <div class="stat-card-top">
                    <div class="stat-card-icon icon-emerald">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                    </div>
                    <div class="stat-card-label">Last Sync</div>
                </div>
                <div class="stat-card-value stat-small" id="stat-last-indexed">{{last_indexed}}</div>
                <div class="stat-card-sub">Timestamp of last index write</div>
            </div>

            <div class="stat-card" onmousemove="updateGlow(event, this)">
                <div class="card-glow"></div>
                <div class="stat-card-top">
                    <div class="stat-card-icon icon-purple">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                        </svg>
                    </div>
                    <div class="stat-card-label">Index Size</div>
                </div>
                <div class="stat-card-value" id="stat-db-size">{{size_human}}</div>
                <div class="stat-card-sub" id="stat-db-bytes">{{size_bytes}} bytes on disk</div>
            </div>

            <div class="stat-card" onmousemove="updateGlow(event, this)">
                <div class="card-glow"></div>
                <div class="stat-card-top">
                    <div class="stat-card-icon icon-amber">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </div>
                    <div class="stat-card-label">Data Size</div>
                </div>
                <div class="stat-card-value" id="stat-data-size">{{data_size_human}}</div>
                <div class="stat-card-sub" id="stat-data-bytes">{{data_size_bytes}} bytes in /data</div>
            </div>
        </div>



        <!-- Terminal Window Console Viewer -->
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-title">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
                    <span>recollindex.log</span>
                </div>
                <div class="terminal-actions">
                    <button type="button" class="terminal-btn" onclick="clearConsole()">Clear</button>
                    <button type="button" class="terminal-btn" onclick="copyConsoleLogs()">Copy</button>
                </div>
            </div>
            <pre class="terminal-body" id="console-output">{{'\n'.join(logs) if logs else 'Indexer console idle. Click "Run Incremental Index" or "Full Re-index" above to monitor live stdout logs.'}}</pre>
        </div>
    </div>

    <!-- Section 2: Metadata Extraction Rules Engine -->
    <div class="settings-section">
        <div class="settings-section-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="4 7 4 4 20 4 20 7"></polyline>
                <line x1="9" y1="20" x2="15" y2="20"></line>
                <line x1="12" y1="4" x2="12" y2="20"></line>
            </svg>
            <span>Metadata Extraction</span>
            <button type="button" class="btn btn-primary btn-sm" style="margin-left: auto;" onclick="openAddRuleModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>New Extraction Rule</span>
            </button>
        </div>

        <p class="settings-helper" style="margin-bottom: 1.25rem;">
            Rules are evaluated by the compiled <strong>Rust metadata extractor</strong> during indexing at sub-microsecond speeds. Extracted fields are automatically registered in Recoll's <code>fields</code> and <code>recoll.conf</code>, enabling direct queries like <code>project:Apollo</code> and rich badges on search cards.
        </p>

        <!-- Rules Grid Container -->
        <div id="rules-grid" class="rules-grid">
            <!-- Dynamically populated by JS -->
        </div>

        <!-- Interactive Test Lab Sandbox -->
        <div class="sandbox-panel">
            <div class="sandbox-header">
                <div class="sandbox-title-wrap">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #a78bfa;">
                        <path d="M10 2v7.31L4.62 19.3A2 2 0 0 0 6.37 22h11.26a2 2 0 0 0 1.75-2.7L14 9.31V2"></path>
                        <line x1="8" y1="2" x2="16" y2="2"></line>
                    </svg>
                    <h3 class="sandbox-title">Sandbox Rule Evaluation</h3>
                </div>
            </div>
            <p class="settings-helper" style="margin-bottom: 0.5rem;">
                Test candidate rules in memory against sample paths to verify field extraction before triggering an index run.
            </p>

            <!-- Quick Preset Chips -->
            <div class="sandbox-presets">
                <span class="sandbox-preset-label">Sample Presets:</span>
                <button type="button" class="preset-chip" onclick="loadSamplePath('/data/projects/Apollo/2026/Contract_Agreement.pdf')">
                    Project File
                </button>
                <button type="button" class="preset-chip" onclick="loadSamplePath('/data/invoices/INV_2026_0042_AcmeCorp.pdf')">
                    Invoice Document
                </button>
                <button type="button" class="preset-chip" onclick="loadSamplePath('/data/departments/finance/audit_report.docx')">
                    Department File
                </button>
            </div>

            <!-- Path Input Row -->
            <div class="sandbox-input-row">
                <input type="text" id="test-sample-path" class="form-control" placeholder="e.g. /data/projects/Apollo/2026/Contract_Agreement.pdf" value="/data/projects/Apollo/2026/Contract_Agreement.pdf" onkeydown="if(event.key==='Enter') runLiveTest()">
                <button type="button" class="btn btn-primary" onclick="runLiveTest()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                    <span>Evaluate</span>
                </button>
            </div>

            <!-- Results Card -->
            <div id="sandbox-results-card" class="sandbox-results-card" style="display: none;">
                <div class="sandbox-results-top">
                    <span class="sandbox-results-title">Extracted Document Fields</span>
                    <button type="button" class="terminal-btn" onclick="toggleRawView()">Toggle Raw JSON</button>
                </div>
                <div id="sandbox-chips-wrap" class="sandbox-chips-wrap"></div>
                <pre id="sandbox-raw-view" class="terminal-body" style="display: none; background: rgba(0,0,0,0.5); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px;"></pre>
            </div>
        </div>

        <!-- Save Actions Bar -->
        <div class="settings-actions" style="margin-top: 1.75rem;">
            <button type="button" class="btn btn-primary" onclick="saveAllRules()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
                <span>Save Config</span>
            </button>
            <span id="save-status-msg" class="status-msg"></span>
        </div>
    </div>
</div>

<!-- ==========================================================================
     Section: Dedicated Index Configuration (recoll.conf) Card
     ========================================================================== -->
<div id="index-config-card" class="settings-card" onmousemove="updateGlow(event, this)" style="margin-top: 2rem;">
    <div class="card-glow"></div>

    <!-- Header Section with Live Status Badge -->
    <div class="settings-header" style="justify-content: space-between; align-items: flex-start;">
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div class="brand-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="4" y1="21" x2="4" y2="14"></line>
                    <line x1="4" y1="10" x2="4" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12" y2="3"></line>
                    <line x1="20" y1="21" x2="20" y2="16"></line>
                    <line x1="20" y1="12" x2="20" y2="3"></line>
                    <line x1="1" y1="14" x2="7" y2="14"></line>
                    <line x1="9" y1="8" x2="15" y2="8"></line>
                    <line x1="17" y1="16" x2="23" y2="16"></line>
                </svg>
            </div>
            <div>
                <h2 class="settings-title">Index Configuration (<code class="recoll-conf-code">recoll.conf</code>)</h2>
                <p class="settings-helper">Customize file exclusion rules, crawler thread allocation, OCR triggers, and Xapian database cache sizes</p>
            </div>
        </div>
        <div class="config-status-badge" id="config-status-badge">
            <span class="status-dot-pulse"></span>
            <span id="config-status-text">Active Configuration</span>
        </div>
    </div>

    <!-- Parameter 1: skippedNames (Interactive Chip / Tag List) -->
    <div class="settings-section">
        <div class="settings-section-title">
            <div style="display: inline-flex; align-items: center; gap: 8px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    <line x1="9" y1="14" x2="15" y2="14"></line>
                </svg>
                <span>Excluded Filename Patterns (<code class="field-code">skippedNames</code>)</span>
            </div>
            <div class="section-title-actions" style="margin-left: auto;">
                <span class="chip-count-badge" id="skipped-names-count">0 patterns</span>
            </div>
        </div>
        <p class="settings-helper" style="margin-bottom: 0.75rem;">
            Files and directories matching these wildcard patterns (e.g. <code>*.vmdk</code>, <code>.DS_Store</code>) are completely skipped during indexing. Click any tag to edit inline, click <strong>&times;</strong> to remove, or add new patterns below. Duplicate patterns are automatically rejected.
        </p>

        <!-- Interactive Chips List -->
        <div class="chip-tag-container" id="skipped-names-chip-list">
            <!-- Dynamically populated chips -->
        </div>

        <!-- Add Pattern Toolbar -->
        <div class="chip-add-toolbar">
            <div class="chip-input-wrap">
                <input type="text" id="input-new-pattern" class="form-control chip-add-input" placeholder="Enter pattern (e.g. *.iso, .git, ~*)... Press Enter to add" autocomplete="off" spellcheck="false">
            </div>
            <button type="button" class="btn btn-primary btn-sm" id="btn-add-pattern" onclick="handleAddSkippedName()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>Add Pattern</span>
            </button>
            <button type="button" class="btn btn-secondary btn-sm" id="btn-sort-patterns" onclick="sortSkippedNames()" title="Sort alphabetically">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="7 15 12 20 17 15"></polyline>
                    <polyline points="7 9 12 4 17 9"></polyline>
                </svg>
                <span>Sort A-Z</span>
            </button>
        </div>

        <!-- Inline Duplicate Prevention / Validation Feedback -->
        <div id="pattern-feedback-msg" class="pattern-feedback-msg" style="display: none;">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span id="pattern-feedback-text"></span>
        </div>
    </div>

    <!-- Parameters 2, 3, 4, 5: Indexing Directives & PDF OCR -->
    <div class="settings-section">
        <div class="settings-section-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            <span>Indexing Directives &amp; OCR Engine</span>
        </div>

        <div class="config-toggles-grid">
            <!-- Toggle 1: indexallfilenames -->
            <div class="config-toggle-card">
                <div class="toggle-text-wrap">
                    <label class="toggle-card-label" for="conf-indexallfilenames">Index All Filenames</label>
                    <span class="settings-helper"><code>indexallfilenames</code>: Index file names even for unextractable or unsupported file types</span>
                </div>
                <label class="toggle-switch-wrapper">
                    <input type="checkbox" id="conf-indexallfilenames" name="indexallfilenames" class="toggle-switch-input" onchange="markConfigDirty()">
                    <span class="toggle-switch-slider"></span>
                </label>
            </div>

            <!-- Toggle 2: noaspell -->
            <div class="config-toggle-card">
                <div class="toggle-text-wrap">
                    <label class="toggle-card-label" for="conf-noaspell">Disable Aspell Spelling</label>
                    <span class="settings-helper"><code>noaspell</code>: Skip aspell dictionary generation to reduce indexing time and memory</span>
                </div>
                <label class="toggle-switch-wrapper">
                    <input type="checkbox" id="conf-noaspell" name="noaspell" class="toggle-switch-input" onchange="markConfigDirty()">
                    <span class="toggle-switch-slider"></span>
                </label>
            </div>

            <!-- Toggle 3: indexstemmingpositions -->
            <div class="config-toggle-card">
                <div class="toggle-text-wrap">
                    <label class="toggle-card-label" for="conf-indexstemmingpositions">Index Stemming Positions</label>
                    <span class="settings-helper"><code>indexstemmingpositions</code>: Store word positions for stemmed forms to accelerate phrase searches</span>
                </div>
                <label class="toggle-switch-wrapper">
                    <input type="checkbox" id="conf-indexstemmingpositions" name="indexstemmingpositions" class="toggle-switch-input" onchange="markConfigDirty()">
                    <span class="toggle-switch-slider"></span>
                </label>
            </div>
        </div>

        <!-- Select Dropdown: pdfocrmode -->
        <div class="config-field-row" style="margin-top: 1rem;">
            <div class="settings-field" style="max-width: 480px;">
                <label class="settings-label" for="conf-pdfocrmode">PDF OCR Mode (<code>pdfocrmode</code>)</label>
                <span class="settings-helper">Select Optical Character Recognition execution policy for PDF documents</span>
                <select id="conf-pdfocrmode" name="pdfocrmode" class="form-control" onchange="markConfigDirty()">
                    <option value="off">off &mdash; Never run OCR on PDFs</option>
                    <option value="auto">auto &mdash; Run OCR only when PDF has no selectable text</option>
                    <option value="always">always &mdash; Force OCR on all PDF pages</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Parameters 6, 7, 8, 9: Threads & Performance Tuning -->
    <div class="settings-section">
        <div class="settings-section-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                <line x1="6" y1="6" x2="6.01" y2="6"></line>
                <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            <span>Performance &amp; Memory Allocation</span>
        </div>

        <div class="settings-grid">
            <!-- Numeric 1: idxthreads -->
            <div class="settings-field">
                <label class="settings-label" for="conf-idxthreads">Indexer Threads (<code>idxthreads</code>)</label>
                <span class="settings-helper">Worker thread count for document reading and processing (0 or 1 for single-threaded)</span>
                <input type="number" id="conf-idxthreads" name="idxthreads" class="form-control" min="0" max="64" step="1" placeholder="e.g. 2" oninput="markConfigDirty()">
            </div>

            <!-- Numeric 2: thrQSlices -->
            <div class="settings-field">
                <label class="settings-label" for="conf-thrQSlices">Thread Queue Slices (<code>thrQSlices</code>)</label>
                <span class="settings-helper">Queue depth multiplier for multithreaded indexing pipelines</span>
                <input type="number" id="conf-thrQSlices" name="thrQSlices" class="form-control" min="1" max="10" step="1" placeholder="e.g. 1" oninput="markConfigDirty()">
            </div>

            <!-- Numeric 3: idxflushmb -->
            <div class="settings-field">
                <label class="settings-label" for="conf-idxflushmb">Index Flush Threshold (<code>idxflushmb</code>)</label>
                <span class="settings-helper">Megabytes of memory before flushing document updates to Xapian disk storage</span>
                <div class="input-unit-wrap">
                    <input type="number" id="conf-idxflushmb" name="idxflushmb" class="form-control" min="10" max="4096" step="10" placeholder="e.g. 50" oninput="markConfigDirty()">
                    <span class="input-unit-label">MB</span>
                </div>
            </div>

            <!-- Numeric 4: idxabsml -->
            <div class="settings-field">
                <label class="settings-label" for="conf-idxabsml">Max Abstract Length (<code>idxabsml</code>)</label>
                <span class="settings-helper">Maximum character length for synthetic abstract excerpt generation</span>
                <div class="input-unit-wrap">
                    <input type="number" id="conf-idxabsml" name="idxabsml" class="form-control" min="50" max="10000" step="25" placeholder="e.g. 250" oninput="markConfigDirty()">
                    <span class="input-unit-label">chars</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Save Actions Bar with Loading & Feedback -->
    <div class="settings-actions" style="margin-top: 1.75rem;">
        <button type="button" class="btn btn-primary" id="btn-save-index-config" onclick="saveIndexConfig()">
            <span id="btn-save-config-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
            </span>
            <span id="btn-save-config-text">Save Index Configuration</span>
        </button>

        <button type="button" class="btn btn-secondary" id="btn-reset-index-config" onclick="loadIndexConfig(true)" title="Discard uncommitted edits and reload from disk">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            <span>Reload Config</span>
        </button>

        <span id="config-save-status" class="status-msg"></span>
    </div>
</div>

<!-- Polished Rule Configuration Modal -->
<div id="rule-modal" class="modal-backdrop" style="display: none;">
    <div class="modal-dialog">
        <div class="modal-header">
            <div class="modal-title-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="4 7 4 4 20 4 20 7"></polyline>
                    <line x1="9" y1="20" x2="15" y2="20"></line>
                    <line x1="12" y1="4" x2="12" y2="20"></line>
                </svg>
                <h3 id="modal-rule-title">Configure Extraction Rule</h3>
            </div>
            <button type="button" class="modal-close-btn" onclick="closeRuleModal()">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Rule Type Segmented Switcher -->
            <div class="segmented-control">
                <button type="button" class="segmented-tab is-active" id="tab-regex" onclick="selectRuleType('regex')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>
                    <span>Regex Groups</span>
                </button>
                <button type="button" class="segmented-tab" id="tab-depth" onclick="selectRuleType('depth')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    <span>Directory Depth</span>
                </button>
                <button type="button" class="segmented-tab" id="tab-delimiter" onclick="selectRuleType('delimiter')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line></svg>
                    <span>Delimiter Split</span>
                </button>
            </div>

            <input type="hidden" id="modal-rule-type" value="regex">

            <div class="settings-field" style="margin-bottom: 1rem;">
                <label class="settings-label" for="modal-rule-name">Rule Name *</label>
                <span class="settings-helper">Descriptive label for identification in the rules grid</span>
                <input type="text" id="modal-rule-name" class="form-control" placeholder="e.g. Project Identifier from Path">
            </div>

            <div class="settings-field" style="margin-bottom: 1rem;">
                <label class="settings-label" for="modal-rule-glob">Path Filter (Glob Pattern)</label>
                <span class="settings-helper">Optional fast-path filter (e.g. <code>*.pdf</code> or <code>/data/projects/**</code>).</span>
                <input type="text" id="modal-rule-glob" class="form-control" placeholder="e.g. *.pdf, /data/projects/** (leave empty for all files)">
            </div>

            <!-- Regex Configuration -->
            <div id="rule-fields-regex" class="rule-type-fields">
                <div class="settings-field">
                    <label class="settings-label" for="modal-rule-pattern">Regex Pattern with Named Capture Groups *</label>
                    <span class="settings-helper">Use <code>(?P&lt;fieldname&gt;pattern)</code> syntax. Each capture group automatically creates a stored Recoll field.</span>
                    <input type="text" id="modal-rule-pattern" class="form-control" placeholder="e.g. .*/projects/(?P<project>[^/]+)/(?P<year>\d{4})/(?P<title>[^.]+)\.pdf">
                </div>
            </div>

            <!-- Depth Configuration -->
            <div id="rule-fields-depth" class="rule-type-fields" style="display: none;">
                <div class="form-row">
                    <div class="settings-field col-half">
                        <label class="settings-label" for="modal-rule-depth">Segment Depth *</label>
                        <span class="settings-helper">Index of path segment (e.g. <code>2</code> for /data/projects/Apollo). Use negative e.g. <code>-2</code> for parent folder.</span>
                        <input type="number" id="modal-rule-depth" class="form-control" value="2">
                    </div>
                    <div class="settings-field col-half">
                        <label class="settings-label" for="modal-rule-depth-field">Target Field Name *</label>
                        <span class="settings-helper">Recoll field to store (e.g. <code>project</code> or <code>department</code>).</span>
                        <input type="text" id="modal-rule-depth-field" class="form-control" placeholder="e.g. project">
                    </div>
                </div>
            </div>

            <!-- Delimiter Configuration -->
            <div id="rule-fields-delimiter" class="rule-type-fields" style="display: none;">
                <div class="form-row">
                    <div class="settings-field col-half">
                        <label class="settings-label" for="modal-rule-delimiter">Separator Character *</label>
                        <span class="settings-helper">Character to split tokens by (e.g. <code>_</code> or <code>-</code>).</span>
                        <input type="text" id="modal-rule-delimiter" class="form-control" value="_">
                    </div>
                    <div class="settings-field col-half">
                        <label class="settings-label" for="modal-rule-delim-target">Target Segment *</label>
                        <span class="settings-helper">Part of path to split.</span>
                        <select id="modal-rule-delim-target" class="form-control">
                            <option value="stem">Filename stem (without extension)</option>
                            <option value="filename">Full filename (with extension)</option>
                            <option value="path">Full absolute path</option>
                        </select>
                    </div>
                </div>
                <div class="settings-field" style="margin-top: 0.75rem;">
                    <label class="settings-label" for="modal-rule-delim-mappings">Token Mappings *</label>
                    <span class="settings-helper">Map 0-based token indices to field names: <code>0:doctype, 1:year, 2:invoice_id</code></span>
                    <input type="text" id="modal-rule-delim-mappings" class="form-control" placeholder="e.g. 0:doctype, 1:year, 2:invoice_id">
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeRuleModal()">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="saveModalRule()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Apply Rule</span>
            </button>
        </div>
    </div>
</div>

<script>
let currentRulesData = {{!rules_json}};
let initialIndexConfig = {{!index_config_json}};
if (initialIndexConfig) window.INITIAL_INDEX_CONFIG = initialIndexConfig;
let editingRuleId = null;
let statusPollInterval = null;

function safeSessionGet(key) {
    try {
        return window.sessionStorage ? window.sessionStorage.getItem(key) : null;
    } catch (_) {
        return null;
    }
}

function safeSessionSet(key, val) {
    try {
        if (window.sessionStorage) window.sessionStorage.setItem(key, val);
    } catch (_) {}
}

document.addEventListener('DOMContentLoaded', function() {
    const testSampleInput = document.getElementById('test-sample-path');
    if (testSampleInput) {
        const savedSample = safeSessionGet('recoll_sandbox_sample_path');
        if (savedSample !== null) {
            testSampleInput.value = savedSample;
        }
        testSampleInput.addEventListener('input', function() {
            safeSessionSet('recoll_sandbox_sample_path', this.value);
        });
    }

    renderRules();
    startStatusPolling();
    runLiveTest();
});

function renderRules() {
    const container = document.getElementById('rules-grid');
    if (!currentRulesData.rules || currentRulesData.rules.length === 0) {
        container.innerHTML = `
            <div class="empty-rules-state" style="grid-column: 1 / -1;">
                <svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--text-muted); margin-bottom: 0.75rem;">
                    <polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line>
                </svg>
                <h4 style="color: var(--text-primary); margin-bottom: 0.25rem;">No Metadata Rules Configured</h4>
                <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.88rem;">Create extraction rules to automatically parse custom fields from document paths and filenames.</p>
                <button type="button" class="btn btn-sm btn-primary" onclick="openAddRuleModal()">+ Create First Rule</button>
            </div>`;
        return;
    }

    let html = '';
    currentRulesData.rules.forEach((rule) => {
        const isEnabled = rule.enabled !== false;
        let mappingHtml = '';

        if (rule.type === 'depth') {
            mappingHtml = `
                <div class="mapping-row">
                    <span class="mapping-chip">Segment [${rule.depth}]</span>
                    <span class="mapping-arrow">&rarr;</span>
                    <span class="mapping-target">${escapeHtml(rule.field)}</span>
                </div>`;
        } else if (rule.type === 'delimiter') {
            const mapChips = (rule.mappings || []).map(m => 
                `<span class="mapping-chip">[${m.index}] &rarr; ${escapeHtml(m.field)}</span>`
            ).join(' ');
            mappingHtml = `
                <div class="mapping-row" style="flex-wrap: wrap;">
                    <span class="mapping-chip" title="Delimiter and target">Split by '${escapeHtml(rule.delimiter)}' (${rule.target || 'stem'})</span>
                    <span class="mapping-arrow">&rarr;</span>
                    ${mapChips}
                </div>`;
        } else if (rule.type === 'regex') {
            mappingHtml = `
                <div class="mapping-row">
                    <span class="rule-code-snippet" title="${escapeHtml(rule.pattern)}">${escapeHtml(rule.pattern)}</span>
                </div>`;
        }

        const filterBadge = rule.path_filter 
            ? `<span class="scope-pill"><svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>${escapeHtml(rule.path_filter)}</span>` 
            : '<span class="scope-pill scope-pill-all">All Documents</span>';

        html += `
        <div class="rule-glass-card ${isEnabled ? '' : 'is-disabled'}" id="rule-card-${rule.id}">
            <div class="rule-card-top">
                <div class="rule-card-identity">
                    <span class="rule-type-badge type-${rule.type}">${rule.type}</span>
                    <h4 class="rule-card-name" title="${escapeHtml(rule.name || 'Unnamed')}">${escapeHtml(rule.name || 'Unnamed Rule')}</h4>
                </div>
                <label class="glass-switch" title="Toggle rule active state">
                    <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="toggleRuleEnabled('${rule.id}', this.checked)">
                    <span class="glass-slider"></span>
                </label>
            </div>
            
            <div class="rule-card-scope">
                ${filterBadge}
            </div>

            <div class="rule-mapping-box">
                ${mappingHtml}
            </div>

            <div class="rule-card-footer">
                <button type="button" class="rule-action-btn" onclick="editRule('${rule.id}')" title="Edit rule configuration">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    <span>Edit</span>
                </button>
                <button type="button" class="rule-action-btn rule-action-danger" onclick="deleteRule('${rule.id}')" title="Delete rule">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    <span>Delete</span>
                </button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function toggleRuleEnabled(id, isEnabled) {
    const rule = currentRulesData.rules.find(r => r.id === id);
    if (rule) {
        rule.enabled = isEnabled;
        renderRules();
        runLiveTest();
    }
}

async function deleteRule(id) {
    const confirmed = await window.showConfirmModal({
        title: "Remove Extraction Rule",
        message: "Are you sure you want to remove this extraction rule? Custom fields generated by this rule will no longer be indexed.",
        confirmText: "Remove Rule",
        isDanger: true
    });
    if (confirmed) {
        currentRulesData.rules = currentRulesData.rules.filter(r => r.id !== id);
        renderRules();
        runLiveTest();
    }
}

function selectRuleType(type) {
    document.getElementById('modal-rule-type').value = type;
    document.getElementById('tab-regex').className = 'segmented-tab' + (type === 'regex' ? ' is-active' : '');
    document.getElementById('tab-depth').className = 'segmented-tab' + (type === 'depth' ? ' is-active' : '');
    document.getElementById('tab-delimiter').className = 'segmented-tab' + (type === 'delimiter' ? ' is-active' : '');

    document.getElementById('rule-fields-regex').style.display = type === 'regex' ? 'block' : 'none';
    document.getElementById('rule-fields-depth').style.display = type === 'depth' ? 'block' : 'none';
    document.getElementById('rule-fields-delimiter').style.display = type === 'delimiter' ? 'block' : 'none';
}

function openAddRuleModal() {
    editingRuleId = null;
    document.getElementById('modal-rule-title').innerText = 'Create Extraction Rule';
    document.getElementById('modal-rule-name').value = '';
    document.getElementById('modal-rule-glob').value = '';
    document.getElementById('modal-rule-pattern').value = '';
    document.getElementById('modal-rule-depth').value = '2';
    document.getElementById('modal-rule-depth-field').value = '';
    document.getElementById('modal-rule-delimiter').value = '_';
    document.getElementById('modal-rule-delim-target').value = 'stem';
    document.getElementById('modal-rule-delim-mappings').value = '0:doctype, 1:year, 2:doc_id';
    selectRuleType('regex');
    document.getElementById('rule-modal').style.display = 'flex';
}

function editRule(id) {
    const rule = currentRulesData.rules.find(r => r.id === id);
    if (!rule) return;
    editingRuleId = id;
    document.getElementById('modal-rule-title').innerText = 'Edit Extraction Rule';
    document.getElementById('modal-rule-name').value = rule.name || '';
    document.getElementById('modal-rule-glob').value = rule.path_filter || '';

    if (rule.type === 'depth') {
        document.getElementById('modal-rule-depth').value = rule.depth !== undefined ? rule.depth : 2;
        document.getElementById('modal-rule-depth-field').value = rule.field || '';
    } else if (rule.type === 'delimiter') {
        document.getElementById('modal-rule-delimiter').value = rule.delimiter || '_';
        document.getElementById('modal-rule-delim-target').value = rule.target || 'stem';
        const mapStr = (rule.mappings || []).map(m => `${m.index}:${m.field}`).join(', ');
        document.getElementById('modal-rule-delim-mappings').value = mapStr;
    } else if (rule.type === 'regex') {
        document.getElementById('modal-rule-pattern').value = rule.pattern || '';
    }

    selectRuleType(rule.type);
    document.getElementById('rule-modal').style.display = 'flex';
}

function closeRuleModal() {
    document.getElementById('rule-modal').style.display = 'none';
}

function saveModalRule() {
    const name = document.getElementById('modal-rule-name').value.trim();
    const rtype = document.getElementById('modal-rule-type').value;
    const glob = document.getElementById('modal-rule-glob').value.trim();

    const ruleObj = {
        id: editingRuleId || ('rule_' + Date.now().toString(36)),
        name: name || (rtype.toUpperCase() + ' Extraction Rule'),
        enabled: true,
        type: rtype,
        path_filter: glob
    };

    if (rtype === 'depth') {
        ruleObj.depth = parseInt(document.getElementById('modal-rule-depth').value, 10) || 0;
        ruleObj.field = document.getElementById('modal-rule-depth-field').value.trim();
        if (!ruleObj.field) {
            window.showAlertModal({
                title: 'Validation Error',
                message: 'Target field name is required.',
                type: 'warning'
            });
            return;
        }
    } else if (rtype === 'delimiter') {
        ruleObj.delimiter = document.getElementById('modal-rule-delimiter').value || '_';
        ruleObj.target = document.getElementById('modal-rule-delim-target').value;
        const mapStr = document.getElementById('modal-rule-delim-mappings').value;
        const mappings = [];
        mapStr.split(',').forEach(item => {
            const p = item.split(':');
            if (p.length === 2) {
                const idx = parseInt(p[0].trim(), 10);
                const f = p[1].trim();
                if (!isNaN(idx) && f) mappings.push({ index: idx, field: f });
            }
        });
        if (mappings.length === 0) {
            window.showAlertModal({
                title: 'Validation Error',
                message: 'At least one token mapping (e.g. 0:doctype) is required.',
                type: 'warning'
            });
            return;
        }
        ruleObj.mappings = mappings;
    } else if (rtype === 'regex') {
        ruleObj.pattern = document.getElementById('modal-rule-pattern').value.trim();
        if (!ruleObj.pattern) {
            window.showAlertModal({
                title: 'Validation Error',
                message: 'Regex pattern is required.',
                type: 'warning'
            });
            return;
        }
        if (!ruleObj.pattern.includes('(?P<')) {
            window.showAlertModal({
                title: 'Validation Error',
                message: 'Regex must include at least one named capture group e.g. (?P<project>[^/]+)',
                type: 'warning'
            });
            return;
        }
    }

    if (editingRuleId) {
        const idx = currentRulesData.rules.findIndex(r => r.id === editingRuleId);
        if (idx !== -1) currentRulesData.rules[idx] = ruleObj;
    } else {
        currentRulesData.rules.push(ruleObj);
    }

    closeRuleModal();
    renderRules();
    runLiveTest();
}

function loadSamplePath(path) {
    const input = document.getElementById('test-sample-path');
    if (input) {
        input.value = path;
        safeSessionSet('recoll_sandbox_sample_path', path);
    }
    runLiveTest();
}

function runLiveTest() {
    const input = document.getElementById('test-sample-path');
    if (!input) return;
    const samplePath = input.value.trim();
    safeSessionSet('recoll_sandbox_sample_path', input.value);
    const resultsCard = document.getElementById('sandbox-results-card');
    const chipsWrap = document.getElementById('sandbox-chips-wrap');
    const rawView = document.getElementById('sandbox-raw-view');

    if (!samplePath) {
        resultsCard.style.display = 'none';
        return;
    }

    fetch('/api/metadata/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sample_path: samplePath,
            rules: currentRulesData.rules
        })
    })
    .then(res => res.json())
    .then(data => {
        resultsCard.style.display = 'block';
        chipsWrap.innerHTML = '';
        const results = data.metadata || {};
        const keys = Object.keys(results);

        if (keys.length === 0) {
            chipsWrap.innerHTML = '<span class="empty-badge">No active rules matched this path pattern.</span>';
        } else {
            keys.forEach(k => {
                const val = results[k];
                const chip = document.createElement('div');
                chip.className = 'meta-chip';
                chip.innerHTML = `
                    <span class="meta-chip-key">${escapeHtml(k)}</span>
                    <span class="meta-chip-val">${escapeHtml(val)}</span>
                    <a href="./?query=${encodeURIComponent(k + ':' + val)}" class="meta-chip-query" title="Search for documents with ${escapeHtml(k)}:${escapeHtml(val)}">
                        Search &rarr;
                    </a>`;
                chipsWrap.appendChild(chip);
            });
        }
        rawView.innerText = JSON.stringify(results, null, 2);
    })
    .catch(err => {
        console.error('Test error:', err);
    });
}

function toggleRawView() {
    const rawView = document.getElementById('sandbox-raw-view');
    rawView.style.display = rawView.style.display === 'none' ? 'block' : 'none';
}

function saveAllRules() {
    const statusMsg = document.getElementById('save-status-msg');
    statusMsg.innerText = 'Synchronizing Recoll fields and saving rules...';
    statusMsg.className = 'status-msg';

    fetch('/api/metadata/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentRulesData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            statusMsg.innerText = 'Rules persisted and Recoll configuration synced successfully!';
            statusMsg.className = 'status-msg status-msg-success';
            setTimeout(() => { statusMsg.innerText = ''; }, 4500);
        } else {
            statusMsg.innerText = 'Error saving rules: ' + (data.error || 'Unknown error');
            statusMsg.className = 'status-msg status-msg-error';
        }
    })
    .catch(err => {
        statusMsg.innerText = 'Network error: ' + err;
        statusMsg.className = 'status-msg status-msg-error';
    });
}

function triggerIndexAction() {
    const btnAction = document.getElementById('btn-index-action');
    if (btnAction && btnAction.disabled) return;
    if (btnAction) btnAction.disabled = true;

    fetch('/api/index/reindex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full: false })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            fetchIndexStatus();
        } else {
            if (btnAction) btnAction.disabled = false;
            window.showAlertModal({
                title: "Indexing Error",
                message: "Could not start indexing: " + (data.error || "Unknown error"),
                type: "danger"
            });
        }
    })
    .catch(err => {
        if (btnAction) btnAction.disabled = false;
        window.showAlertModal({
            title: "Indexing Error",
            message: "Failed to trigger indexing: " + err,
            type: "danger"
        });
    });
}
window.triggerIndexing = function(full) { triggerIndexAction(); };

async function confirmPurgeIndex() {
    const confirmed = await window.showConfirmModal({
        title: "Purge Search Index Database",
        message: "WARNING: This will permanently purge the search database directory (xapiandb). Search results will be empty until indexing completes. Proceed?",
        confirmText: "Purge Database",
        isDanger: true
    });
    if (!confirmed) return;

    fetch('/api/index/purge', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.showAlertModal({
                title: "Database Purged",
                message: "Index database successfully purged.",
                type: "success"
            });
            fetchIndexStatus();
        } else {
            window.showAlertModal({
                title: "Purge Failed",
                message: "Purge failed: " + (data.error || "Unknown error"),
                type: "danger"
            });
        }
    })
    .catch(err => {
        window.showAlertModal({
            title: "Purge Failed",
            message: "Purge network error: " + err,
            type: "danger"
        });
    });
}

function clearConsole() {
    document.getElementById('console-output').innerText = 'Indexer console cleared.';
}

function copyConsoleLogs() {
    const text = document.getElementById('console-output').innerText;
    navigator.clipboard.writeText(text).then(() => {
        window.showAlertModal({
            title: "Logs Copied",
            message: "Console logs copied to clipboard.",
            type: "success"
        });
    });
}

function fetchIndexStatus() {
    fetch('/api/index/status')
    .then(res => res.json())
    .then(data => {
        document.getElementById('stat-doc-count').innerText = data.doc_count !== undefined ? Number(data.doc_count).toLocaleString() : '0';
        document.getElementById('stat-last-indexed').innerText = data.last_indexed || 'Never';
        document.getElementById('stat-db-size').innerText = data.size_human || '0 B';
        if (document.getElementById('stat-db-bytes')) {
            document.getElementById('stat-db-bytes').innerText = (data.size_bytes || 0).toLocaleString() + ' bytes on disk';
        }
        if (document.getElementById('stat-data-size')) {
            document.getElementById('stat-data-size').innerText = data.data_size_human || '0 B';
        }
        if (document.getElementById('stat-data-bytes')) {
            document.getElementById('stat-data-bytes').innerText = (data.data_size_bytes || 0).toLocaleString() + ' bytes in /data';
        }

        const job = data.job || {};
        const isRunning = data.status === 'running' || job.status === 'running';
        const exists = data.exists !== false && data.exists !== 0 && data.exists != null;
        const pill = document.getElementById('index-status-pill');
        const textEl = document.getElementById('index-status-text');
        if (pill && textEl) {
            if (isRunning) {
                if (job.mode === 'full' || !exists) {
                    pill.className = 'index-status-pill is-creating';
                    textEl.innerText = 'Creating Index';
                } else {
                    pill.className = 'index-status-pill is-updating is-running';
                    textEl.innerText = 'Updating Index';
                }
            } else if (!exists) {
                pill.className = 'index-status-pill is-no-index';
                textEl.innerText = 'No index';
            } else {
                pill.className = 'index-status-pill is-idle';
                textEl.innerText = 'Index Ready';
            }
        }

        const btnAction = document.getElementById('btn-index-action');
        const btnText = document.getElementById('btn-index-text');
        const btnIcon = document.getElementById('btn-index-icon');
        const btnPurge = document.getElementById('btn-purge-index');

        if (btnAction) {
            btnAction.disabled = isRunning;
            if (!exists) {
                if (btnText) btnText.innerText = 'Create Index';
                if (btnIcon) {
                    btnIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`;
                }
            } else {
                if (btnText) btnText.innerText = 'Update Index';
                if (btnIcon) {
                    btnIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`;
                }
            }
        }
        if (btnPurge) {
            btnPurge.disabled = isRunning || !exists;
        }

        if (data.logs && data.logs.length > 0) {
            const consoleOut = document.getElementById('console-output');
            consoleOut.innerText = data.logs.join('\n');
            consoleOut.scrollTop = consoleOut.scrollHeight;
        }

        if (typeof window.updateFooterIndexBadge === 'function') {
            window.updateFooterIndexBadge(data);
        }
    })
    .catch(err => console.error('Status fetch error:', err));
}

function startStatusPolling() {
    if (statusPollInterval) clearInterval(statusPollInterval);
    statusPollInterval = setInterval(fetchIndexStatus, 3000);
}
</script>

%include("footer")
