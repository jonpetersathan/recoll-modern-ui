%include('header', title=": " + query['query'] + " (" + str(nres) + ")")
%include('search', query=query, dirs=dirs, sorts=sorts, config=config)
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
    </div>
    %end
</div>

%include('pages', query=query, config=config, nres=nres)

<div id="results" class="results-container">
%for i in range(0, len(res)):
    %include('result', d=res[i], i=i, query=query, config=config, query_string=query_string)
%end
</div>

%include('pages', query=query, config=config, nres=nres)
%include('footer')
