%import sys
%from urllib.parse import urlencode
%import math

%q = dict(query)
%def page_href(page):
	%q['page'] = page
	%return './results?%s' % urlencode(q)
%end
%if nres > 0:
	%npages = int(math.ceil(nres/float(config['perpage'])))
	%if npages > 1:
		<div class="pagination-wrapper">
			<nav class="tab-navigation">
				<a title="First Page" class="tab-btn" href="{{page_href(1)}}">&laquo;</a>
				<a title="Previous Page" class="tab-btn" href="{{page_href(max(1, query['page']-1))}}">&lsaquo;</a>
				%offset = ((query['page']) // 10) * 10
				%for p in range(max(1, offset), min(offset + 10, npages + 1)):
					%if p == query['page']:
						<span class="tab-btn active">{{p}}</span>
					%else:
						<a href="{{page_href(p)}}" class="tab-btn">{{p}}</a>
					%end
				%end
				<a title="Next Page" class="tab-btn" href="{{page_href(min(npages, query['page']+1))}}">&rsaquo;</a>
				<a title="Last Page" class="tab-btn" href="{{page_href(npages)}}">&raquo;</a>
			</nav>
		</div>
	%end
%end
