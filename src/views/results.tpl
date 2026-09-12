%view_mode = get('view_mode', 'detail')
%include('header', title=": " + query['query'] + " (" + str(nres) + ")")
%include('search', query=query, dirs=dirs, sorts=sorts, config=config, forms=forms, forms_json=forms_json)
<div id="status" class="status-bar">
    <div id="found" class="status-found">
        <span class="pulse-dot"></span>
        <span>Found <strong class="highlight-count">{{nres}}</strong> results for <strong class="query-term">{{qs}}</strong></span>
        <span class="time-badge">{{"%.3f" % time.total_seconds()}}s</span>
    </div>
    %if len(res) > 0:
    <div class="results-actions-bar">
        <div class="selection-controls">
            <span id="selected-counter" class="selected-counter-badge" style="display: none;">
                <span id="selected-count">0</span> selected
                <button type="button" id="btn-clear-selection" class="btn-clear-sel" title="Clear all selections">&times;</button>
            </span>
        </div>

        %if not config.get('rclc_nojsoncsv', False):
        <div id="downloads" class="download-chips">
            <a href="./json?{{query_string}}&page=0" id="btn-download-json" class="chip-btn" title="Download Results as JSON">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>JSON</span>
            </a>
            <a href="./csv?{{query_string}}&page=0" id="btn-download-csv" class="chip-btn" title="Download Results as CSV">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>CSV</span>
            </a>
            <button type="button" id="btn-download-files" class="chip-btn" title="Download matching files" data-total-count="{{nres}}" data-query-string="{{query_string}}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    <polyline points="12 11 12 17 9 14"></polyline>
                    <polyline points="12 17 15 14"></polyline>
                </svg>
                <span>FILES</span>
            </button>
        </div>
        %end
    </div>
    %end
</div>

<div class="results-nav-bar">
    <div class="nav-bar-left"></div>
    <div class="nav-bar-center">
        %include('pages', query=query, config=config, nres=nres, view_mode=view_mode)
    </div>
    <div class="nav-bar-right">
        %if len(res) > 0:
        <label class="details-toggle-label" for="toggle-show-details" title="Toggle Detailed / Simple Search Results View">
            <span class="details-toggle-text">Show Details</span>
            <span class="glass-switch">
                <input type="checkbox" id="toggle-show-details" class="toggle-switch-input" {{ 'checked' if view_mode != 'simple' else '' }}>
                <span class="glass-slider"></span>
            </span>
        </label>
        %end
    </div>
</div>

<script>
(function() {
    try {
        var params = new URLSearchParams(window.location.search);
        var urlView = params.get('view');
        var m = urlView || localStorage.getItem('recoll_search_view_mode');
        if (!m && document.cookie) {
            var match = document.cookie.match(/(?:^|;\s*)recoll_search_view_mode=([^;]+)/);
            if (match) m = match[1];
        }
        if (m === 'simple') {
            var r = document.getElementById('results');
            if (r) r.classList.add('view-simple');
            var t = document.getElementById('toggle-show-details');
            if (t) t.checked = false;
        } else if (m === 'detail') {
            var r = document.getElementById('results');
            if (r) r.classList.remove('view-simple');
            var t = document.getElementById('toggle-show-details');
            if (t) t.checked = true;
        }
    } catch(e) {}
})();
</script>

<div id="results" class="results-container {{ 'view-simple' if view_mode == 'simple' else '' }}">
%for i in range(0, len(res)):
    %include('result', d=res[i], i=i, query=query, config=config, query_string=query_string)
%end
</div>

<!-- Modal Dialog for Zipping Files with Animated Progress Bar -->
<div id="archive-modal" class="modal-backdrop" style="display: none;">
    <div class="modal-dialog archive-modal-dialog">
        <div class="modal-header">
            <div class="modal-title-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    <polyline points="12 11 12 17 9 14"></polyline>
                    <polyline points="12 17 15 14"></polyline>
                </svg>
                <h3 id="archive-modal-title">Zipping Files</h3>
            </div>
            <button type="button" class="modal-close-btn" id="btn-close-archive-modal" aria-label="Close dialog">&times;</button>
        </div>
        <div class="modal-body">
            <div class="archive-status-wrap">
                <span id="archive-status-text" class="archive-status-text">Preparing files for archive...</span>
                <span id="archive-percent-text" class="archive-percent-text">0%</span>
            </div>
            <div class="archive-progress-track">
                <div id="archive-progress-bar" class="archive-progress-bar" style="width: 0%;"></div>
            </div>
            <p id="archive-file-detail" class="archive-file-detail"></p>
        </div>
        <div class="modal-footer">
            <button type="button" id="btn-cancel-archive" class="btn btn-secondary btn-sm">Cancel</button>
        </div>
    </div>
</div>

%include('pages', query=query, config=config, nres=nres, view_mode=view_mode)
%include('footer')
