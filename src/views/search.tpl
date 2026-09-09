%import re
<div id="searchbox" class="search-card" onmousemove="updateGlow(event, this)">
    <div class="card-glow"></div>
    <form action="results" method="get" id="search-form">
        <div class="query-row">
            <div class="query-input-wrap">
                <svg class="query-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input tabindex="0" type="search" name="query" class="query-input" value="{{query['query']}}" placeholder="Search documents, text content or metadata..." autofocus autocomplete="off">
            </div>
            <div class="button-row">
                <button type="submit" class="btn btn-primary" title="Execute Search">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <span>Search</span>
                </button>
                <a href="./" id="btn-reset-query" tabindex="-1" class="btn btn-secondary" title="Reset Search Query">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M23 4v6h-6"></path>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    <span>Reset</span>
                </a>
                <button type="button" id="btn-toggle-advanced" class="btn btn-secondary" title="Advanced Search Forms" aria-expanded="false" onclick="window.toggleAdvancedSearch(event)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                    </svg>
                    <span>Advanced</span>
                </button>
            </div>
        </div>

        <!-- Advanced Search Interactive Panel -->
        <div id="advanced-search-panel" class="advanced-search-panel" style="display: none;">
            <div class="advanced-panel-header">
                <div class="form-preset-group">
                    <label for="active-form-selector" class="advanced-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        <span>Form Preset:</span>
                    </label>
                    <select id="active-form-selector" class="form-control form-preset-select">
                        %for f in forms:
                        %if f.get('enabled', True):
                        %if f.get('id') == 'default':
                        <option value="{{f['id']}}">Advanced (Default / Read-Only)</option>
                        %elif f.get('readonly'):
                        <option value="{{f['id']}}">{{f['name']}} (Default / Read-Only)</option>
                        %else:
                        <option value="{{f['id']}}">{{f['name']}}</option>
                        %end
                        %end
                        %end
                    </select>
                </div>
                <a href="settings#custom-forms-section" id="btn-manage-forms" class="btn btn-secondary btn-sm btn-manage-forms" title="Manage and create custom forms in settings">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                    <span>Manage Forms</span>
                </a>
            </div>

            <!-- Dynamic Form Fields Container -->
            <div id="advanced-fields-container" class="advanced-fields-grid">
                <!-- Injected dynamically by client JS based on selected form -->
            </div>

            <!-- Query Preview Bar -->
            <div class="advanced-bottom-bar">
                <div class="query-preview-wrap">
                    <span class="query-preview-label">Compiled Query:</span>
                    <code id="advanced-query-preview" class="query-preview-code">&lt;empty&gt;</code>
                </div>
            </div>
        </div>

        <div class="filters-grid">
            <div class="filter-group">
                <label for="folders" class="filter-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <span>Folder Scope</span>
                </label>
                <select id="folders" name="dir" class="form-control" multiple>
                %folder_list = [d for d in dirs if d != '<all>']
                %active_dirs = query.get('dirs') if 'dirs' in query else ([query['dir']] if isinstance(query.get('dir'), str) else query.get('dir', ['<all>']))
                %norm_active = [x[len('/data/'):] if str(x).startswith('/data/') else (x[len('data/'):] if str(x).startswith('data/') else str(x)) for x in active_dirs]
                %for d in (['<all>'] if '<all>' in dirs else []) + sorted(folder_list, key=str.lower):
                    %space = "&nbsp;" * (4 * d.count('/'))
                    %if d in norm_active or (d == '<all>' and ('<all>' in norm_active or not norm_active)):
                    %selected = "selected"
                    %else:
                    %selected = ""
                    %end
                    <option {{selected}} value="{{d}}">{{!space}}{{re.sub('.+/','', d)}}</option>
                %end
                </select>
            </div>

            <div class="filter-group">
                <label class="filter-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <span>Date Range</span>
                    <span class="gray">YYYY[-MM][-DD]</span>
                </label>
                <div class="date-range">
                    <input name="after" value="{{query['after']}}" class="form-control" placeholder="From" autocomplete="off">
                    <span class="date-sep">&mdash;</span>
                    <input name="before" value="{{query['before']}}" class="form-control" placeholder="To" autocomplete="off">
                </div>
            </div>

            <div class="filter-group">
                <label class="filter-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="4" y1="6" x2="20" y2="6"></line>
                        <line x1="4" y1="12" x2="14" y2="12"></line>
                        <line x1="4" y1="18" x2="8" y2="18"></line>
                    </svg>
                    <span>Sort &amp; Order</span>
                </label>
                <div class="sort-controls">
                    <select name="sort" class="form-control">
                    %for s in sorts:
                        %if query['sort'] == s[0]:
                            <option selected value="{{s[0]}}">{{s[1]}}</option>
                        %else:
                            <option value="{{s[0]}}">{{s[1]}}</option>
                        %end
                    %end
                    </select>
                    <select name="ascending" class="form-control">
                        %if int(query['ascending']) == 1:
                            <option value="0">Descending</option>
                            <option value="1" selected>Ascending</option>
                        %else:
                            <option value="0" selected>Descending</option>
                            <option value="1">Ascending</option>
                        %end
                    </select>
                </div>
            </div>
        </div>
        <input type="hidden" name="page" value="1" />
    </form>
    <script id="recoll-search-forms-data" type="application/json">{{!forms_json}}</script>
</div>
