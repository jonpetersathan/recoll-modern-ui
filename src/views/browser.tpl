%include("header", title=" / Browser", active_tab="browser")
<div id="browser-box" class="settings-card browser-card" onmousemove="updateGlow(event, this)">
    <div class="card-glow"></div>

    <!-- Header Section -->
    <div class="settings-header" style="justify-content: space-between; align-items: flex-start;">
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div class="brand-icon browser-brand-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
            </div>
            <div>
                <h2 class="settings-title">File &amp; Folder Browser</h2>
                <p class="settings-helper">Read-only directory navigation and secure document download</p>
            </div>
        </div>
        <div class="browser-header-badges">
            <div class="security-badge status-readonly" title="Read-only mode active: file modifications are disabled">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <span>Read-Only Mode</span>
            </div>
        </div>
    </div>

    % if defined('warning') and warning:
    <div class="browser-alert browser-alert-warning">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span>{{warning}}</span>
    </div>
    % end

    <!-- Browser Navigation Toolbar -->
    <div class="browser-toolbar">
        <nav class="browser-breadcrumbs" id="browser-breadcrumbs" aria-label="Directory Breadcrumbs">
            % for idx, crumb in enumerate(breadcrumbs):
                % is_last = (idx == len(breadcrumbs) - 1)
                % if idx > 0:
                    <span class="browser-crumb-separator" aria-hidden="true">/</span>
                % end
                % if is_last:
                    <span class="browser-crumb current" aria-current="page" data-path="{{crumb['path']}}">
                        % if idx == 0:
                            <svg class="crumb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
                        % end
                        <span>{{crumb['name']}}</span>
                    </span>
                % else:
                    <a href="browser?path={{crumb['path']}}" class="browser-crumb" data-path="{{crumb['path']}}">
                        % if idx == 0:
                            <svg class="crumb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
                        % end
                        <span>{{crumb['name']}}</span>
                    </a>
                % end
            % end
        </nav>

        <div class="browser-actions">
            % parent_path = breadcrumbs[-2]['path'] if len(breadcrumbs) > 1 else ''
            <button type="button" class="btn btn-secondary btn-sm browser-nav-btn" id="btn-browser-up" title="Navigate up to parent directory" {{'disabled' if len(breadcrumbs) <= 1 else ''}} data-parent="{{parent_path}}">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 19V5M5 12l7-7 7 7"></path>
                </svg>
                <span>Up</span>
            </button>
            <button type="button" class="btn btn-secondary btn-sm browser-nav-btn" id="btn-browser-refresh" title="Refresh folder contents">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <polyline points="1 20 1 14 7 14"></polyline>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                <span>Refresh</span>
            </button>
            <div class="browser-filter-wrap">
                <svg class="browser-filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input type="text" id="browser-filter-input" class="browser-filter-input" placeholder="Filter current folder..." autocomplete="off" spellcheck="false">
                <button type="button" id="btn-browser-clear-filter" class="browser-filter-clear" title="Clear filter" style="display: none;">&times;</button>
            </div>
        </div>
    </div>

    <!-- Stats Bar -->
    <div class="browser-stats-bar">
        <div class="browser-stats-counts" id="browser-items-count">
            <strong>{{total_entries}}</strong> item{{'s' if total_entries != 1 else ''}}
            <span class="stats-divider">&bull;</span>
            <span>{{total_dirs}} folder{{'s' if total_dirs != 1 else ''}}</span>
            <span class="stats-divider">&bull;</span>
            <span>{{total_files}} file{{'s' if total_files != 1 else ''}}</span>
        </div>
        <div class="browser-path-chip" id="browser-current-path-display" title="Canonical System Path">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="browser-path-text">{{current_path}}</span>
        </div>
    </div>

    <!-- Browser Table Container -->
    <div class="browser-table-container">
        <table class="browser-table" id="browser-table" aria-label="Directory Contents">
            <thead>
                <tr>
                    <th class="col-icon" scope="col" aria-label="Type">Type</th>
                    <th class="col-name" scope="col" data-sort="name">Name</th>
                    <th class="col-mimetype" scope="col" data-sort="mimetype">MIME Type</th>
                    <th class="col-size" scope="col" data-sort="size">Size</th>
                    <th class="col-mtime" scope="col" data-sort="mtime">Modified Date</th>
                    <th class="col-action" scope="col" aria-label="Actions">Action</th>
                </tr>
            </thead>
            <tbody id="browser-tbody">
                % for entry in entries:
                <tr class="browser-row {{'is-directory' if entry['is_dir'] else 'is-file'}}" data-name="{{entry['name']}}" data-path="{{entry['path']}}" data-is-dir="{{'true' if entry['is_dir'] else 'false'}}">
                    <td class="col-icon">
                        % if entry['is_dir']:
                            <div class="browser-item-icon folder-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                                </svg>
                            </div>
                        % else:
                            % mt = entry['mimetype']
                            % if 'pdf' in mt:
                                <div class="browser-item-icon file-icon icon-pdf">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="9" y1="15" x2="15" y2="15"></line></svg>
                                </div>
                            % elif 'image' in mt:
                                <div class="browser-item-icon file-icon icon-image">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                                </div>
                            % elif 'word' in mt or 'document' in mt:
                                <div class="browser-item-icon file-icon icon-doc">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                </div>
                            % elif 'excel' in mt or 'sheet' in mt or 'csv' in mt:
                                <div class="browser-item-icon file-icon icon-sheet">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><line x1="12" y1="9" x2="12" y2="21"></line></svg>
                                </div>
                            % elif 'presentation' in mt or 'powerpoint' in mt:
                                <div class="browser-item-icon file-icon icon-presentation">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                                </div>
                            % elif 'zip' in mt or 'tar' in mt or 'gzip' in mt or 'compressed' in mt:
                                <div class="browser-item-icon file-icon icon-archive">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>
                                </div>
                            % else:
                                <div class="browser-item-icon file-icon icon-generic">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                </div>
                            % end
                        % end
                    </td>
                    <td class="col-name">
                        % if entry['is_dir']:
                            <a href="browser?path={{entry['path']}}" class="browser-entry-link dir-link" data-path="{{entry['path']}}">
                                <span class="entry-name-text">{{entry['name']}}</span>
                            </a>
                        % else:
                            <a href="/api/browser/download?path={{entry['path']}}" class="browser-entry-link file-link" data-path="{{entry['path']}}" title="Download {{entry['name']}}">
                                <span class="entry-name-text">{{entry['name']}}</span>
                            </a>
                        % end
                    </td>
                    <td class="col-mimetype">
                        <span class="mimetype-tag {{'tag-dir' if entry['is_dir'] else ''}}" title="{{entry['mimetype']}}">
                            {{entry['mimetype_label']}}
                        </span>
                    </td>
                    <td class="col-size">
                        <span class="size-text font-mono">{{entry['size_human']}}</span>
                    </td>
                    <td class="col-mtime">
                        <span class="mtime-text font-mono">{{entry['mtime_human']}}</span>
                    </td>
                    <td class="col-action">
                        % if entry['is_dir']:
                            <a href="browser?path={{entry['path']}}" class="btn btn-secondary btn-xs btn-open-folder" data-path="{{entry['path']}}" title="Open Folder">
                                <span>Open</span>
                                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                            </a>
                        % else:
                            <a href="/api/browser/download?path={{entry['path']}}" class="btn btn-secondary btn-xs btn-download-file" title="Download File">
                                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                                <span>Download</span>
                            </a>
                        % end
                    </td>
                </tr>
                % end
            </tbody>
        </table>

        <!-- Empty Folder State -->
        <div id="browser-empty" class="browser-empty-state" style="{{'display: none;' if entries else ''}}">
            <div class="empty-state-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    <line x1="8" y1="13" x2="16" y2="13"></line>
                </svg>
            </div>
            <h4 class="empty-state-title">This folder is empty</h4>
            <p class="empty-state-desc">There are no files or subdirectories located in this directory.</p>
        </div>

        <!-- Filter No Results State -->
        <div id="browser-no-filter-results" class="browser-empty-state" style="display: none;">
            <div class="empty-state-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    <line x1="8" y1="11" x2="14" y2="11"></line>
                </svg>
            </div>
            <h4 class="empty-state-title">No matching items found</h4>
            <p class="empty-state-desc">Try clearing or adjusting your filename filter.</p>
        </div>

        <!-- Inaccessible Directory State -->
        <div id="browser-error" class="browser-error-state" style="display: none;">
            <div class="error-state-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
            </div>
            <h4 class="error-state-title">Directory Inaccessible</h4>
            <p id="browser-error-text" class="error-state-desc">Unable to load the requested directory.</p>
            <button type="button" class="btn btn-primary btn-sm" id="btn-browser-root">
                <span>Return to Root</span>
            </button>
        </div>
    </div>
</div>

<!-- Initial Data Injection for Client-Side Script -->
<script id="browser-initial-data" type="application/json">{{!initial_data_json}}</script>

%include("footer")
