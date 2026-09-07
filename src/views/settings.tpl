%include("header", title=" / Settings")
<div id="settings-box" class="settings-card" onmousemove="updateGlow(event, this)">
    <div class="card-glow"></div>
    <div class="settings-header">
        <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
        </div>
        <div>
            <h2 class="settings-title">Search Engine Preferences</h2>
            <p class="settings-helper">Customize indexing parameters, display options, and mount paths</p>
        </div>
    </div>

    <form action="set" method="get">
        <!-- Search & Query Behavior -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Search &amp; Query Behavior</span>
            </div>
            <div class="settings-grid">
                <div class="settings-field">
                    <label class="settings-label">Find Similar (Stemming)</label>
                    <span class="settings-helper">1 (enabled) or 0 (disabled), expands words e.g. "run" to "running"</span>
                    <input name="stem" class="form-control" value="{{stem}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Collapse Duplicate Results</label>
                    <span class="settings-helper">1 or 0, only show one result for identical content</span>
                    <input name="collapsedups" class="form-control" value="{{collapsedups}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Maximum Total Results</label>
                    <span class="settings-helper">0 for unlimited, or specify hard cap</span>
                    <input name="maxresults" class="form-control" value="{{maxresults}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Results Per Page</label>
                    <span class="settings-helper">Number of results per page (0 for single page)</span>
                    <input name="perpage" class="form-control" value="{{perpage}}">
                </div>
            </div>
        </div>

        <!-- Snippets & Formatting -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <span>Snippets &amp; Display</span>
            </div>
            <div class="settings-grid">
                <div class="settings-field">
                    <label class="settings-label">Context Words</label>
                    <span class="settings-helper">Number of surrounding words in snippet</span>
                    <input name="context" class="form-control" value="{{context}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Context Characters</label>
                    <span class="settings-helper">Maximum characters displayed in snippet</span>
                    <input name="maxchars" class="form-control" value="{{maxchars}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Date Format String</label>
                    <span class="settings-helper">Standard strftime format (e.g. %c or %Y-%m-%d %H:%M)</span>
                    <input name="timefmt" class="form-control" value="{{timefmt}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Folder Dropdown Depth</label>
                    <span class="settings-helper">Hierarchy levels shown in folder selector</span>
                    <input name="dirdepth" class="form-control" value="{{dirdepth}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Default Title Click Action</label>
                    <span class="settings-helper">Action triggered when clicking document title</span>
                    <select name="title_link" class="form-control">
                        <option value="download" {{'selected' if title_link == 'download' else ''}}>Download</option>
                        <option value="preview" {{'selected' if title_link == 'preview' else ''}}>Preview</option>
                        <option value="open" {{'selected' if title_link == 'open' else ''}}>Open</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Mounts & Locations -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                <span>Directory Mounts &amp; Remote URLs</span>
            </div>
            <div class="settings-grid">
                %for d in dirs:
                <div class="settings-field">
                    <label class="settings-label">{{d}}</label>
                    <span class="settings-helper">Remote URL or mount rewrite</span>
                    <input name="mount_{{d}}" class="form-control" value="{{mounts.get(d, '')}}">
                </div>
                %end
            </div>
        </div>

        <!-- Export & Integrations -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>Export &amp; Browser Integration</span>
            </div>
            <div class="settings-grid">
                <div class="settings-field">
                    <label class="settings-label">CSV Fields</label>
                    <span class="settings-helper">Available fields: {{fields}}</span>
                    <input name="csvfields" class="form-control" value="{{csvfields}}">
                </div>
                <div class="settings-field">
                    <label class="settings-label">Browser Search Plugin</label>
                    <span class="settings-helper">Register Recoll into browser search bar</span>
                    <a href="#" class="btn btn-secondary" style="margin-top: 4px; display: inline-flex;" onClick="addOpenSearch();return false">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        <span>Add OpenSearch Provider</span>
                    </a>
                </div>
            </div>
        </div>

        <div class="settings-actions">
            <button type="submit" class="btn btn-primary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
                <span>Save Preferences</span>
            </button>
            <a href="./" class="btn btn-secondary">
                <span>Cancel</span>
            </a>
        </div>
    </form>
</div>
%include("footer")
