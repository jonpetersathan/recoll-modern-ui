%include("header", title=" / Settings")
% is_admin_val = get('is_admin', False) if defined('is_admin') else (config.get('is_admin', False) if defined('config') else False)
% st_map = field_status if defined('field_status') else {}
% from recollweb.constants import DEFAULT_CONFIG

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

    <form action="set" method="post" id="settings-form">
        <input type="hidden" name="forms_json" id="settings-forms-json" value="">
        <!-- Search & Query Behavior -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Search &amp; Query Behavior</span>
            </div>
            <div class="settings-grid">
                <!-- stem -->
                % st = st_map.get('stem', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 1)
                % cur_val = get('stem', glob_val)
                <div class="settings-field" data-setting-key="stem">
                    <label class="settings-label">Find Similar (Stemming)</label>
                    <span class="settings-helper">1 (enabled) or 0 (disabled), expands words e.g. "run" to "running"</span>
                    <div class="setting-input-group">
                        <input name="stem" id="setting-stem" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_stem" id="scope-stem" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-stem" data-key="stem" onclick="window.toggleAdminScope('stem')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-stem" data-key="stem" onclick="window.restoreDefaultSetting('stem')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- collapsedups -->
                % st = st_map.get('collapsedups', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 0)
                % cur_val = get('collapsedups', glob_val)
                <div class="settings-field" data-setting-key="collapsedups">
                    <label class="settings-label">Collapse Duplicate Results</label>
                    <span class="settings-helper">1 or 0, only show one result for identical content</span>
                    <div class="setting-input-group">
                        <input name="collapsedups" id="setting-collapsedups" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_collapsedups" id="scope-collapsedups" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-collapsedups" data-key="collapsedups" onclick="window.toggleAdminScope('collapsedups')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-collapsedups" data-key="collapsedups" onclick="window.restoreDefaultSetting('collapsedups')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- maxresults -->
                % st = st_map.get('maxresults', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 0)
                % cur_val = get('maxresults', glob_val)
                <div class="settings-field" data-setting-key="maxresults">
                    <label class="settings-label">Maximum Total Results</label>
                    <span class="settings-helper">0 for unlimited, or specify hard cap</span>
                    <div class="setting-input-group">
                        <input name="maxresults" id="setting-maxresults" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_maxresults" id="scope-maxresults" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-maxresults" data-key="maxresults" onclick="window.toggleAdminScope('maxresults')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-maxresults" data-key="maxresults" onclick="window.restoreDefaultSetting('maxresults')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- perpage -->
                % st = st_map.get('perpage', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 25)
                % cur_val = get('perpage', glob_val)
                <div class="settings-field" data-setting-key="perpage">
                    <label class="settings-label">Results Per Page</label>
                    <span class="settings-helper">Number of results per page (0 for single page)</span>
                    <div class="setting-input-group">
                        <input name="perpage" id="setting-perpage" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_perpage" id="scope-perpage" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-perpage" data-key="perpage" onclick="window.toggleAdminScope('perpage')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-perpage" data-key="perpage" onclick="window.restoreDefaultSetting('perpage')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
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
                <!-- context -->
                % st = st_map.get('context', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 30)
                % cur_val = get('context', glob_val)
                <div class="settings-field" data-setting-key="context">
                    <label class="settings-label">Context Words</label>
                    <span class="settings-helper">Number of surrounding words in snippet</span>
                    <div class="setting-input-group">
                        <input name="context" id="setting-context" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_context" id="scope-context" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-context" data-key="context" onclick="window.toggleAdminScope('context')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-context" data-key="context" onclick="window.restoreDefaultSetting('context')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- maxchars -->
                % st = st_map.get('maxchars', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 500)
                % cur_val = get('maxchars', glob_val)
                <div class="settings-field" data-setting-key="maxchars">
                    <label class="settings-label">Context Characters</label>
                    <span class="settings-helper">Maximum characters displayed in snippet</span>
                    <div class="setting-input-group">
                        <input name="maxchars" id="setting-maxchars" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_maxchars" id="scope-maxchars" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-maxchars" data-key="maxchars" onclick="window.toggleAdminScope('maxchars')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-maxchars" data-key="maxchars" onclick="window.restoreDefaultSetting('maxchars')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- timefmt -->
                % st = st_map.get('timefmt', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', '%c')
                % cur_val = get('timefmt', glob_val)
                <div class="settings-field" data-setting-key="timefmt">
                    <label class="settings-label">Date Format String</label>
                    <span class="settings-helper">Standard strftime format (e.g. %c or %Y-%m-%d %H:%M)</span>
                    <div class="setting-input-group">
                        <input name="timefmt" id="setting-timefmt" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_timefmt" id="scope-timefmt" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-timefmt" data-key="timefmt" onclick="window.toggleAdminScope('timefmt')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-timefmt" data-key="timefmt" onclick="window.restoreDefaultSetting('timefmt')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- dirdepth -->
                % st = st_map.get('dirdepth', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 2)
                % cur_val = get('dirdepth', glob_val)
                <div class="settings-field" data-setting-key="dirdepth">
                    <label class="settings-label">Folder Dropdown Depth</label>
                    <span class="settings-helper">Hierarchy levels shown in folder selector</span>
                    <div class="setting-input-group">
                        <input name="dirdepth" id="setting-dirdepth" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_dirdepth" id="scope-dirdepth" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-dirdepth" data-key="dirdepth" onclick="window.toggleAdminScope('dirdepth')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-dirdepth" data-key="dirdepth" onclick="window.restoreDefaultSetting('dirdepth')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>

                <!-- title_link -->
                % st = st_map.get('title_link', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', 'download')
                % cur_val = get('title_link', glob_val)
                <div class="settings-field" data-setting-key="title_link">
                    <label class="settings-label">Default Title Click Action</label>
                    <span class="settings-helper">Action triggered when clicking document title</span>
                    <div class="setting-input-group">
                        <select name="title_link" id="setting-title_link" class="form-control" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                            <option value="download" {{'selected' if cur_val == 'download' else ''}}>Download</option>
                            <option value="preview" {{'selected' if cur_val == 'preview' else ''}}>Preview</option>
                            <option value="open" {{'selected' if cur_val == 'open' else ''}}>Open</option>
                        </select>
                        <input type="hidden" name="scope_title_link" id="scope-title_link" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-title_link" data-key="title_link" onclick="window.toggleAdminScope('title_link')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-title_link" data-key="title_link" onclick="window.restoreDefaultSetting('title_link')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>
            </div>
        </div>

        %if dirs:
        <!-- Mounts & Locations -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                <span>Directory Mounts &amp; Remote URLs</span>
            </div>
            <div class="settings-grid">
                %for d in dirs:
                % mk = f"mount_{d}"
                % st = st_map.get(mk, {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', '')
                % cur_val = mounts.get(d, glob_val)
                <div class="settings-field" data-setting-key="{{mk}}">
                    <label class="settings-label">{{d}}</label>
                    <span class="settings-helper">Remote URL or mount rewrite</span>
                    <div class="setting-input-group">
                        <input name="{{mk}}" id="setting-{{mk}}" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_{{mk}}" id="scope-{{mk}}" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-{{mk}}" data-key="{{mk}}" onclick="window.toggleAdminScope('{{mk}}')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-{{mk}}" data-key="{{mk}}" onclick="window.restoreDefaultSetting('{{mk}}')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
                </div>
                %end
            </div>
        </div>
        %end

        <!-- Export & Integrations -->
        <div class="settings-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>Export &amp; Browser Integration</span>
            </div>
            <div class="settings-grid">
                <!-- csvfields (renamed to JSON/CSV Fields) -->
                % st = st_map.get('csvfields', {})
                % is_cust = st.get('is_custom', False)
                % glob_val = st.get('global_value', DEFAULT_CONFIG.get('csvfields', ''))
                % cur_val = get('csvfields', glob_val)
                <div class="settings-field" data-setting-key="csvfields">
                    <label class="settings-label">JSON/CSV Fields</label>
                    <span class="settings-helper">Available keywords: {{fields}}</span>
                    <div class="setting-input-group">
                        <input name="csvfields" id="setting-csvfields" class="form-control" value="{{cur_val}}" data-global-value="{{glob_val}}" data-user-value="{{cur_val}}">
                        <input type="hidden" name="scope_csvfields" id="scope-csvfields" value="user">
                        % if is_admin_val:
                        <button type="button" class="setting-action-btn scope-user" id="btn-scope-csvfields" data-key="csvfields" onclick="window.toggleAdminScope('csvfields')" title="User-Specific Setting (Click to switch to Global Default)">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                        </button>
                        % else:
                        <button type="button" class="setting-action-btn btn-restore-default" id="btn-restore-csvfields" data-key="csvfields" onclick="window.restoreDefaultSetting('csvfields')" {{'' if is_cust else 'disabled'}} title="Restore global default value">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </button>
                        % end
                    </div>
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

        <!-- Custom Search Forms Management -->
        <div class="settings-section" id="custom-forms-section">
            <div class="settings-section-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
                <span>Custom Search Forms</span>
                <button type="button" class="btn btn-primary btn-sm" id="btn-create-form" style="margin-left: auto;" onclick="window.openNewFormBuilder(event)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    <span>New Search Form</span>
                </button>
            </div>
            <p class="settings-helper" style="margin-bottom: 1.25rem;">
                Design specialized search forms with custom dropdowns (e.g. "Document Type" mapping to filenames or MIME types) and fields. Configurations are persisted in SQLite across application restarts.
            </p>

            <div id="forms-cards-list" class="forms-management-grid">
                <!-- Populated dynamically from embedded JSON / API -->
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

<!-- Interactive Form Builder Modal -->
<div id="form-builder-overlay" class="modal-backdrop" style="display: none;">
    <div class="modal-dialog">
        <div class="modal-header">
            <div class="modal-title-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
                <h3 id="modal-title">Create Custom Search Form</h3>
            </div>
            <button type="button" class="modal-close-btn" id="btn-close-modal" title="Close">&times;</button>
        </div>

        <div class="modal-body">
            <input type="hidden" id="builder-form-id" value="">

            <div class="settings-field" style="margin-bottom: 1rem;">
                <label class="settings-label" for="builder-form-name">Form Name *</label>
                <span class="settings-helper">Descriptive name displayed in the search form preset selector</span>
                <input id="builder-form-name" class="form-control" placeholder="e.g. Document Type Classifier" required>
            </div>

            <div class="settings-field" style="margin-bottom: 1rem;">
                <label class="settings-label" for="builder-form-desc">Form Description</label>
                <span class="settings-helper">Brief explanation of what this search form is optimized for</span>
                <input id="builder-form-desc" class="form-control" placeholder="e.g. Search files by pre-defined document categories and keywords">
            </div>

            <div class="settings-field" style="margin-bottom: 1.5rem;">
                <label class="settings-label" for="builder-form-scope">Form Scope / Visibility</label>
                <span class="settings-helper">User-specific forms are only visible to you; Global forms are available to all users</span>
                <select id="builder-form-scope" class="form-control">
                    <option value="user" selected>User-Specific (Only visible to me)</option>
                    <option value="global">Global (System-wide default for all users)</option>
                </select>
            </div>

            <div class="modal-section-title">
                <span>Form Fields</span>
                <button type="button" class="btn btn-secondary btn-sm" id="btn-add-field">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    <span>Add Field</span>
                </button>
            </div>

            <div id="builder-fields-container" class="builder-fields-container">
                <!-- Field configuration cards rendered by JS -->
            </div>
        </div>

        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="btn-cancel-modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="btn-save-form">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                </svg>
                <span>Save Search Form</span>
            </button>
        </div>
    </div>
</div>

<!-- View Schema Modal (for Read-Only Default Form) -->
<div id="schema-viewer-overlay" class="modal-backdrop" style="display: none;">
    <div class="modal-dialog">
        <div class="modal-header">
            <div class="modal-title-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <h3 id="schema-modal-title">Default Search Form Schema</h3>
            </div>
            <button type="button" class="modal-close-btn" id="btn-close-schema-modal" title="Close">&times;</button>
        </div>
        <div class="modal-body">
            <p class="settings-helper" style="margin-bottom: 1rem;">
                The Default search form is built into the engine and read-only. It covers all Recoll query language operators. You can create custom forms in the section above.
            </p>
            <div id="schema-fields-table"></div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="btn-close-schema">Close</button>
        </div>
    </div>
</div>

<script id="recoll-search-forms-data" type="application/json">{{!forms_json}}</script>
% if defined('settings_bundle_json'):
<script id="recoll-settings-bundle-data" type="application/json">{{!settings_bundle_json}}</script>
% end
%include("footer")
