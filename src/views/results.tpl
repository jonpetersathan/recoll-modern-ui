%include('header', title=": " + query['query'] + " (" + str(nres) + ")")
%include('search', query=query, dirs=dirs, sorts=sorts, config=config, forms=forms, forms_json=forms_json)
<div id="status" class="status-bar">
    <div id="found" class="status-found">
        <span class="pulse-dot"></span>
        <span>Found <strong class="highlight-count">{{nres}}</strong> results for <strong class="query-term">{{qs}}</strong></span>
        <span class="time-badge">{{"%.3f" % time.total_seconds()}}s</span>
    </div>
    %if len(res) > 0 and not config.get('rclc_nojsoncsv', False):
    <div id="downloads" class="download-chips">
        <a href="./json?{{query_string}}&page=0" class="chip-btn" title="Download Results as JSON">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>JSON</span>
        </a>
        <a href="./csv?{{query_string}}&page=0" class="chip-btn" title="Download Results as CSV">
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

%include('pages', query=query, config=config, nres=nres)

<div id="results" class="results-container">
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

%include('pages', query=query, config=config, nres=nres)
%include('footer')
