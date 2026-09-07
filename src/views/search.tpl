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
                <input tabindex="0" type="search" name="query" class="query-input" value="{{query['query']}}" placeholder="Search documents, text content, metadata, or keywords..." autofocus autocomplete="off">
            </div>
            <div class="button-row">
                <button type="submit" class="btn btn-primary" title="Execute Search">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <span>Search</span>
                </button>
                <a href="./" tabindex="-1" class="btn btn-secondary" title="Reset Search Query">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M23 4v6h-6"></path>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    <span>Reset</span>
                </a>
                %if not config.get('rclc_nosettings', False):
                <a href="settings" tabindex="-1" class="btn btn-secondary" title="Settings &amp; Preferences">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                    <span>Settings</span>
                </a>
                %end
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
                <select id="folders" name="dir" class="form-control">
                %for d in sorted(dirs, key=str.lower):
                    %space = "&nbsp;" * (4 * d.count('/'))
                    %if d in query['dir']:
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
</div>
