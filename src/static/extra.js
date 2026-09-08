/**
 * Recoll Modern UI - Interactive Client Scripts
 * Vanilla JavaScript (Zero External Dependencies)
 */

function initRecollApp() {
    // Form submission loading fade
    const searchForms = document.querySelectorAll('form');
    const fadeOverlay = document.getElementById('fade');

    searchForms.forEach(form => {
        form.addEventListener('submit', () => {
            if (typeof window.closeAllQueryDropdowns === 'function') {
                window.closeAllQueryDropdowns();
            }
            const inputs = form.querySelectorAll('input');
            inputs.forEach(input => input.blur());
            if (fadeOverlay) {
                fadeOverlay.style.display = 'block';
                fadeOverlay.style.opacity = '1';
            }
        });
    });

    // Keyboard navigation shortcuts
    document.addEventListener('keydown', (e) => {
        // Press '/' to focus search box when not typing in an input
        if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            const queryInput = document.querySelector('input[name="query"]');
            if (queryInput) {
                queryInput.focus();
                queryInput.select();
            }
        }
        // Press 'Escape' to close open datepickers, open dropdowns, open modals, or blur active inputs
        if (e.key === 'Escape') {
            const openQueryDropdowns = document.querySelectorAll('.query-autocomplete-dropdown');
            if (openQueryDropdowns.length > 0) {
                openQueryDropdowns.forEach(d => d.remove());
                return;
            }

            const openDatepickers = document.querySelectorAll('.custom-datepicker-popover.is-open');
            if (openDatepickers.length > 0) {
                openDatepickers.forEach(p => p.classList.remove('is-open', 'drop-up'));
                return;
            }

            const openDropdowns = document.querySelectorAll('.custom-select-wrapper.is-open');
            if (openDropdowns.length > 0) {
                openDropdowns.forEach(w => {
                    w.classList.remove('is-open', 'drop-up');
                    const trg = w.querySelector('.custom-select-trigger');
                    if (trg) {
                        trg.setAttribute('aria-expanded', 'false');
                        trg.focus();
                    }
                });
                return;
            }

            const openModals = document.querySelectorAll('.modal-backdrop');
            openModals.forEach(m => {
                if (m.style.display !== 'none') m.style.display = 'none';
            });
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
                document.activeElement.blur();
            }
        }
    });

    // Initialize Advanced Search Panel, Settings Form Manager, Files Download, Custom Selects, & Datepicker
    initAdvancedSearch();
    initSettingsFormManager();
    initFilesDownload();
    initCustomSelects();
    initCustomDatepicker();
    initMainQueryEditor();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRecollApp);
} else {
    initRecollApp();
}

/**
 * Interactive Mouse-Tracking Radial Card Glow
 * @param {MouseEvent} event
 * @param {HTMLElement} card
 */
function updateGlow(event, card) {
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    card.style.setProperty('--x', `${x}px`);
    card.style.setProperty('--y', `${y}px`);
}

/**
 * Add OpenSearch Provider to Browser
 */
function addOpenSearch() {
    if (window.external && 'AddSearchProvider' in window.external) {
        const url = window.location.origin + '/osd.xml';
        window.external.AddSearchProvider(url);
    } else {
        alert('OpenSearch plugins can be added automatically from your browser address bar.');
    }
}

// ============================================================================
// Advanced Search Component
// ============================================================================

function escapeHtml(str) {
    if (!str && str !== 0) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function safeStorageGet(type, key) {
    try {
        return window[type] ? window[type].getItem(key) : null;
    } catch (_) {
        return null;
    }
}

function safeStorageSet(type, key, val) {
    try {
        if (window[type]) window[type].setItem(key, val);
    } catch (_) {}
}

window.closeAllQueryDropdowns = function() {
    document.querySelectorAll('.query-editor-wrap').forEach(w => {
        if (typeof w._closeQueryDropdown === 'function') {
            w._closeQueryDropdown();
        }
    });
    document.querySelectorAll('.query-autocomplete-dropdown').forEach(d => {
        if (d.parentNode) d.parentNode.removeChild(d);
    });
    document.querySelectorAll('.has-active-dropdown').forEach(el => {
        el.classList.remove('has-active-dropdown');
    });
};

let _lastAdvToggleTime = 0;
window.toggleAdvancedSearch = function(e) {
    if (e) {
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();
    }
    if (typeof window.closeAllQueryDropdowns === 'function') {
        window.closeAllQueryDropdowns();
    }
    const now = Date.now();
    if (now - _lastAdvToggleTime < 250) {
        return;
    }
    _lastAdvToggleTime = now;

    const panel = document.getElementById('advanced-search-panel');
    const toggleBtn = document.getElementById('btn-toggle-advanced');
    if (!panel) return;

    const isCurrentlyOpen = panel.style.display !== 'none';
    const show = !isCurrentlyOpen;
    panel.style.display = show ? 'block' : 'none';
    if (toggleBtn) {
        toggleBtn.classList.toggle('active', show);
        toggleBtn.setAttribute('aria-expanded', show ? 'true' : 'false');
    }
    safeStorageSet('sessionStorage', 'recoll_adv_open', show ? '1' : '0');
};

function getStoredForms() {
    const dataTag = document.getElementById('recoll-search-forms-data');
    if (dataTag && dataTag.textContent) {
        try {
            return JSON.parse(dataTag.textContent);
        } catch (e) {
            console.error('Failed to parse recoll-search-forms-data JSON:', e);
        }
    }
    return [];
}

function initAdvancedSearch() {
    const toggleBtn = document.getElementById('btn-toggle-advanced');
    const panel = document.getElementById('advanced-search-panel');
    if (!toggleBtn || !panel) return;

    const forms = getStoredForms();
    const formSelector = document.getElementById('active-form-selector');
    const fieldsContainer = document.getElementById('advanced-fields-container');
    const previewEl = document.getElementById('advanced-query-preview');
    const searchForm = document.getElementById('search-form');
    const mainQueryInput = document.querySelector('input[name="query"]');

    // Toggle panel visibility
    function setPanelVisibility(show) {
        panel.style.display = show ? 'block' : 'none';
        toggleBtn.classList.toggle('active', show);
        toggleBtn.setAttribute('aria-expanded', show ? 'true' : 'false');
        safeStorageSet('sessionStorage', 'recoll_adv_open', show ? '1' : '0');
    }

    if (!toggleBtn.hasAttribute('onclick')) {
        toggleBtn.addEventListener('click', window.toggleAdvancedSearch);
    }

    if (safeStorageGet('sessionStorage', 'recoll_adv_open') === '1') {
        setPanelVisibility(true);
    }

    let activeForm = forms[0] || null;

    function saveActiveFormValues() {
        if (!activeForm || !fieldsContainer) return;
        const values = {};
        const inputs = fieldsContainer.querySelectorAll('.advanced-field-input');
        inputs.forEach(input => {
            const fId = input.dataset.fieldId;
            if (!fId) return;
            if (input.type === 'checkbox') {
                values[fId] = input.checked;
            } else {
                values[fId] = input.value;
            }
        });
        safeStorageSet('localStorage', `recoll_adv_values_${activeForm.id}`, JSON.stringify(values));
    }

    function loadActiveFormValues(formId) {
        if (!formId) return {};
        const raw = safeStorageGet('localStorage', `recoll_adv_values_${formId}`);
        if (!raw) return {};
        try {
            return JSON.parse(raw) || {};
        } catch (_) {
            return {};
        }
    }

    function renderActiveForm(formId) {
        activeForm = forms.find(f => f.id === formId) || forms[0];
        if (!activeForm) return;

        const savedValues = loadActiveFormValues(activeForm.id);
        fieldsContainer.innerHTML = '';

        (activeForm.fields || []).forEach(field => {
            const ftype = String(field.type || 'text').trim().toLowerCase().replace(/[\s-]/g, '_');
            if (ftype === 'static_query' || ftype === 'static') {
                return;
            }

            const card = document.createElement('div');
            card.className = 'advanced-field-card';

            const fieldId = `adv-${field.id}`;
            const labelHtml = `<label for="${fieldId}"><span>${escapeHtml(field.label)}</span></label>`;
            const helperHtml = field.helper ? `<span class="field-helper">${escapeHtml(field.helper)}</span>` : '';

            if (field.type === 'select') {
                let optionsHtml = '';
                const savedVal = savedValues[field.id] !== undefined ? savedValues[field.id] : '';
                (field.options || []).forEach(opt => {
                    const isSelected = String(opt.query || '') === String(savedVal);
                    optionsHtml += `<option value="${escapeHtml(opt.query || '')}" ${isSelected ? 'selected' : ''}>${escapeHtml(opt.label)}</option>`;
                });
                card.innerHTML = `
                    ${labelHtml}
                    <select id="${fieldId}" data-field-id="${escapeHtml(field.id)}" class="form-control advanced-field-input">
                        ${optionsHtml}
                    </select>
                    ${helperHtml}
                `;
            } else if (field.type === 'toggle' || field.type === 'checkbox') {
                const isChecked = !!savedValues[field.id];
                card.className = 'advanced-field-card advanced-field-toggle-card';
                card.innerHTML = `
                    <div class="advanced-field-toggle-row">
                        <label class="advanced-field-toggle" for="${fieldId}">
                            <div class="toggle-switch-wrapper">
                                <input type="checkbox" role="switch" id="${fieldId}" data-field-id="${escapeHtml(field.id)}" class="advanced-field-input toggle-switch-input" data-query="${escapeHtml(field.query || '')}" ${isChecked ? 'checked' : ''}>
                                <span class="toggle-switch-slider"></span>
                            </div>
                            <span class="toggle-switch-label">${escapeHtml(field.label)}</span>
                        </label>
                        ${helperHtml}
                    </div>
                `;
            } else {
                const savedVal = savedValues[field.id] !== undefined ? savedValues[field.id] : '';
                card.innerHTML = `
                    ${labelHtml}
                    <input type="text" id="${fieldId}" data-field-id="${escapeHtml(field.id)}" class="form-control advanced-field-input" placeholder="${escapeHtml(field.placeholder || '')}" value="${escapeHtml(savedVal)}" autocomplete="off">
                    ${helperHtml}
                `;
            }

            fieldsContainer.appendChild(card);
        });

        const hasVisibleFields = fieldsContainer.children.length > 0;
        if (!hasVisibleFields) {
            panel.classList.add('has-no-user-fields');
            fieldsContainer.style.display = 'none';
        } else {
            panel.classList.remove('has-no-user-fields');
            fieldsContainer.style.display = '';
        }

        // Attach change and Enter listeners
        const inputs = fieldsContainer.querySelectorAll('.advanced-field-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                saveActiveFormValues();
                updateCompiledQuery();
            });
            input.addEventListener('change', () => {
                saveActiveFormValues();
                updateCompiledQuery();
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    executeFormSearch();
                }
            });
        });

        updateCompiledQuery();
        initCustomSelects(fieldsContainer);
    }

    function updateCompiledQuery() {
        if (!activeForm || !fieldsContainer) return '';
        const compiled = compileQueryFromForm(activeForm, fieldsContainer);
        if (previewEl) {
            previewEl.innerHTML = compiled ? highlightQuerySyntax(compiled) : '&lt;empty&gt;';
        }
        return compiled;
    }

    function executeFormSearch() {
        if (typeof window.closeAllQueryDropdowns === 'function') {
            window.closeAllQueryDropdowns();
        }
        saveActiveFormValues();
        const query = updateCompiledQuery();
        if (mainQueryInput && query) {
            mainQueryInput.value = query;
            if (typeof mainQueryInput._updateHighlight === 'function') {
                mainQueryInput._updateHighlight();
            }
        }
        safeStorageSet('sessionStorage', 'recoll_adv_open', '1');
        if (searchForm) {
            searchForm.submit();
        }
    }

    if (searchForm) {
        searchForm.addEventListener('submit', () => {
            saveActiveFormValues();
            const isPanelOpen = panel && panel.style.display !== 'none';
            if (isPanelOpen) {
                const query = updateCompiledQuery();
                if (mainQueryInput && query) {
                    mainQueryInput.value = query;
                    if (typeof mainQueryInput._updateHighlight === 'function') {
                        mainQueryInput._updateHighlight();
                    }
                }
                safeStorageSet('sessionStorage', 'recoll_adv_open', '1');
            }
            if (typeof window.closeAllQueryDropdowns === 'function') {
                window.closeAllQueryDropdowns();
            }
        });
    }

    if (formSelector) {
        // Restore last selected form
        const savedFormId = safeStorageGet('localStorage', 'recoll_active_form_id');
        if (savedFormId && forms.some(f => f.id === savedFormId)) {
            formSelector.value = savedFormId;
            renderActiveForm(savedFormId);
        } else if (forms.length > 0) {
            renderActiveForm(forms[0].id);
        }

        formSelector.addEventListener('change', () => {
            saveActiveFormValues();
            const formId = formSelector.value;
            safeStorageSet('localStorage', 'recoll_active_form_id', formId);
            renderActiveForm(formId);
        });
    }

    const resetBtn = document.getElementById('btn-reset-query') || document.querySelector('a[title="Reset Search Query"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            // Collapse advanced search panel and return UI to simple search
            safeStorageSet('sessionStorage', 'recoll_adv_open', '0');
            setPanelVisibility(false);

            // Clear stored form values
            forms.forEach(f => {
                safeStorageSet('localStorage', `recoll_adv_values_${f.id}`, '{}');
            });

            // Reset preset selector to default
            safeStorageSet('localStorage', 'recoll_active_form_id', 'default');
            if (formSelector) {
                formSelector.value = 'default';
            }

            // Clear all field inputs
            if (fieldsContainer) {
                const inputs = fieldsContainer.querySelectorAll('.advanced-field-input');
                inputs.forEach(input => {
                    if (input.type === 'checkbox') input.checked = false;
                    else input.value = '';
                });
            }

            // Clear main query input and preview
            if (mainQueryInput) {
                mainQueryInput.value = '';
                mainQueryInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            renderActiveForm('default');
            updateCompiledQuery();
        });
    }
}

function compileQueryFromForm(form, container) {
    if (!form || !container) return '';
    const clauses = [];
    const fields = form.fields || [];

    fields.forEach(field => {
        const ftype = String(field.type || 'text').trim().toLowerCase().replace(/[\s-]/g, '_');
        if (ftype === 'static_query' || ftype === 'static') {
            const q = String(field.query || '').trim();
            if (q) clauses.push(q);
            return;
        }

        const input = container.querySelector(`[data-field-id="${field.id}"]`);
        if (!input) return;

        if (field.type === 'select') {
            const val = (input.value || '').trim();
            if (val) clauses.push(val);
        } else if (field.type === 'toggle' || field.type === 'checkbox') {
            if (input.checked) {
                const q = (field.query || input.dataset.query || '').trim();
                if (q) clauses.push(q);
            }
        } else {
            const val = (input.value || '').trim();
            if (!val) return;
            const fmt = field.query_format || '{value}';

            if (fmt === '{value}') {
                clauses.push(val);
            } else if (fmt === '"{value}"') {
                clauses.push(`"${val.replace(/"/g, '')}"`);
            } else if (fmt === 'or_terms') {
                const words = val.split(/\s+/).filter(Boolean);
                if (words.length > 1) {
                    clauses.push(`(${words.join(' OR ')})`);
                } else if (words.length === 1) {
                    clauses.push(words[0]);
                }
            } else if (fmt === 'not_terms') {
                const words = val.split(/\s+/).filter(Boolean);
                if (words.length > 0) {
                    clauses.push(words.map(w => `-${w}`).join(' '));
                }
            } else if (fmt === 'proximity') {
                const slack = field.slack || 4;
                const words = val.replace(/"/g, '').trim();
                clauses.push(`"${words}"p${slack}`);
            } else if (fmt.includes('{value}')) {
                if (val.includes(' ') && !val.startsWith('"') && !val.endsWith('"') &&
                    (fmt.startsWith('filename:') || fmt.startsWith('title:') || fmt.startsWith('author:') || fmt.startsWith('dir:'))) {
                    clauses.push(fmt.replace('{value}', `"${val}"`));
                } else {
                    clauses.push(fmt.replace('{value}', val));
                }
            } else {
                clauses.push(`${fmt} ${val}`);
            }
        }
    });

    return clauses.join(' ').trim();
}

// ============================================================================
// Query Syntax Autocomplete & Real-Time Highlighting Engine
// ============================================================================

const MIME_TYPES_LIST = [
    { value: 'application/pdf', desc: 'PDF Document (*.pdf)' },
    { value: 'application/msword', desc: 'Word Document (*.doc)' },
    { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', desc: 'Word Document (*.docx)' },
    { value: 'application/vnd.ms-excel', desc: 'Excel Spreadsheet (*.xls)' },
    { value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', desc: 'Excel Spreadsheet (*.xlsx)' },
    { value: 'application/vnd.ms-powerpoint', desc: 'PowerPoint Presentation (*.ppt)' },
    { value: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', desc: 'PowerPoint (*.pptx)' },
    { value: 'application/epub+zip', desc: 'EPUB Electronic Book (*.epub)' },
    { value: 'application/zip', desc: 'ZIP Compressed Archive (*.zip)' },
    { value: 'application/x-tar', desc: 'TAR Archive (*.tar)' },
    { value: 'application/gzip', desc: 'GZIP Compressed File (*.gz)' },
    { value: 'text/html', desc: 'HTML Web Document (*.html)' },
    { value: 'text/plain', desc: 'Plain Text File (*.txt)' },
    { value: 'text/csv', desc: 'CSV Data Spreadsheet (*.csv)' },
    { value: 'text/markdown', desc: 'Markdown Document (*.md)' },
    { value: 'message/rfc822', desc: 'Email Message (*.eml, *.msg)' },
    { value: 'image/jpeg', desc: 'JPEG Image (*.jpg, *.jpeg)' },
    { value: 'image/png', desc: 'PNG Image (*.png)' },
    { value: 'image/svg+xml', desc: 'SVG Vector Graphic (*.svg)' },
    { value: 'image/*', desc: 'All Image Formats' },
    { value: 'audio/*', desc: 'All Audio Formats' },
    { value: 'video/*', desc: 'All Video Formats' }
];

const EXTENSIONS_LIST = [
    { value: 'pdf', desc: 'PDF Document (*.pdf)' },
    { value: 'docx', desc: 'Word Document (*.docx)' },
    { value: 'doc', desc: 'Legacy Word Document (*.doc)' },
    { value: 'xlsx', desc: 'Excel Spreadsheet (*.xlsx)' },
    { value: 'xls', desc: 'Legacy Excel Spreadsheet (*.xls)' },
    { value: 'pptx', desc: 'PowerPoint Presentation (*.pptx)' },
    { value: 'html', desc: 'HTML Web Document (*.html)' },
    { value: 'csv', desc: 'CSV Spreadsheet (*.csv)' },
    { value: 'txt', desc: 'Plain Text File (*.txt)' },
    { value: 'md', desc: 'Markdown File (*.md)' },
    { value: 'png', desc: 'PNG Image (*.png)' },
    { value: 'jpg', desc: 'JPEG Image (*.jpg)' },
    { value: 'zip', desc: 'ZIP Archive (*.zip)' },
    { value: 'eml', desc: 'Email Message (*.eml)' },
    { value: 'py', desc: 'Python Source Code (*.py)' },
    { value: 'json', desc: 'JSON Data File (*.json)' }
];

const SIZE_LIST = [
    { value: '<1m', desc: 'Files strictly smaller than 1 Megabyte' },
    { value: '<10m', desc: 'Files strictly smaller than 10 Megabytes' },
    { value: '<100k', desc: 'Files strictly smaller than 100 Kilobytes' },
    { value: '>1m', desc: 'Files strictly larger than 1 Megabyte' },
    { value: '>10m', desc: 'Files strictly larger than 10 Megabytes' },
    { value: '>100m', desc: 'Files strictly larger than 100 Megabytes' },
    { value: '>1g', desc: 'Files strictly larger than 1 Gigabyte' }
];

// Top-level keywords with parameter placeholder hints
const TOP_LEVEL_KEYWORDS = [
    { prefix: 'mime:', placeholder: 'type', desc: 'MIME type filter (prompts MIME types list)', hasSub: true, insertPrefix: 'mime:' },
    { prefix: 'ext:', placeholder: 'extension', desc: 'File extension filter (prompts extensions list)', hasSub: true, insertPrefix: 'ext:' },
    { prefix: 'dir:', placeholder: 'path', desc: 'Directory scope: restrict search to folder path', insertPrefix: 'dir:' },
    { prefix: 'filename:', placeholder: 'pattern', desc: 'Filename match with optional wildcards (e.g. report*.pdf)', insertPrefix: 'filename:' },
    { prefix: 'filetype:', placeholder: 'type', desc: 'File type filter (alias for MIME types / extensions)', hasSub: true, insertPrefix: 'mime:' },
    { prefix: 'title:', placeholder: 'text', desc: 'Document title metadata field search', insertPrefix: 'title:' },
    { prefix: 'author:', placeholder: 'name', desc: 'Author / creator metadata search', insertPrefix: 'author:' },
    { prefix: 'size:', placeholder: 'comparison', desc: 'File size threshold (prompts size list)', hasSub: true, insertPrefix: 'size:' },
    { prefix: 'date:', placeholder: 'range', desc: 'Date range filter (YYYY-MM-DD/YYYY-MM-DD)', insertPrefix: 'date:' },
    { prefix: 'tag:', placeholder: 'keyword', desc: 'Document category or tag keyword', insertPrefix: 'tag:' },
    { prefix: 'AND', placeholder: '', desc: 'Boolean AND operator (both conditions match)', insertPrefix: 'AND ', isBool: true },
    { prefix: 'OR', placeholder: '', desc: 'Boolean OR operator (either condition matches)', insertPrefix: 'OR ', isBool: true },
    { prefix: 'NOT', placeholder: '', desc: 'Boolean NOT operator (inverts next condition)', insertPrefix: 'NOT ', isBool: true },
    { prefix: '-', placeholder: 'term', desc: 'Negation prefix to exclude term (e.g. -temp)', insertPrefix: '-', isOp: true },
    { prefix: '(', placeholder: 'clause', suffix: ')', desc: 'Grouping clause: parenthesize sub-conditions', insertPrefix: '(', isOp: true }
];

// Text Input field specific patterns (using {value} as user input placeholder)
const TEXT_SNIPPET_PATTERNS = [
    { prefix: '{value}', placeholder: '', desc: 'Standard search: match all entered words (AND)', insertPrefix: '{value}' },
    { prefix: '"{value}"', placeholder: '', desc: 'Exact phrase search: match terms in exact order', insertPrefix: '"{value}"' },
    { prefix: 'filename:{value}', placeholder: '', desc: 'Filename exact match with user input', insertPrefix: 'filename:{value}' },
    { prefix: 'filename:*{value}*', placeholder: '', desc: 'Filename wildcard search with user input', insertPrefix: 'filename:*{value}*' },
    { prefix: 'title:{value}', placeholder: '', desc: 'Document title metadata search with user input', insertPrefix: 'title:{value}' },
    { prefix: 'author:{value}', placeholder: '', desc: 'Author / creator search with user input', insertPrefix: 'author:{value}' },
    { prefix: 'dir:"{value}"', placeholder: '', desc: 'Directory Scope with user input', insertPrefix: 'dir:"{value}"' },
    { prefix: 'ext:{value}', placeholder: '', desc: 'File extension match with user input', insertPrefix: 'ext:{value}' },
    { prefix: 'mime:{value}', placeholder: '', desc: 'MIME type filter with user input', insertPrefix: 'mime:{value}' },
    { prefix: 'size>{value}', placeholder: '', desc: 'Minimum file size threshold with user input', insertPrefix: 'size>{value}' },
    { prefix: 'size<{value}', placeholder: '', desc: 'Maximum file size threshold with user input', insertPrefix: 'size<{value}' },
    { prefix: 'date:{value}', placeholder: '', desc: 'Date range filter with user input', insertPrefix: 'date:{value}' },
    { prefix: '"{value}"p4', placeholder: '', desc: 'Proximity: match terms within 4 words', insertPrefix: '"{value}"p4' },
    { prefix: '-{value}', placeholder: '', desc: 'Exclusion / NOT operator with user input', insertPrefix: '-{value}' }
];

function highlightQuerySyntax(raw) {
    if (!raw) return '';
    const escaped = raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 1: {value} placeholder
    // 2: boolean operators: AND, OR, NOT, XOR
    // 3: keywords: filename, title, author, mime, dir, ext, size, date, keyword, recipient, tag, filetype
    // 4: operators: * , / : ( ) " - + &gt; &lt; or p\d+
    // 5: literal strings / words
    const tokenRegex = /(\{value\})|(\b(?:AND|OR|NOT|XOR)\b)|(\b(?:filename|title|author|mime|dir|ext|size|date|keyword|recipient|tag|filetype)\b)|([*:,/()"\-+]|&gt;|&lt;|\bp\d+\b)|([^\s*:,/()"\-+&{}]+)/g;

    return escaped.replace(tokenRegex, (match, valPh, boolOp, kw, op, word) => {
        if (valPh) {
            return `<span class="tok-val">${valPh}</span>`;
        } else if (boolOp) {
            return `<span class="tok-bool">${boolOp}</span>`;
        } else if (kw) {
            return `<span class="tok-kw">${kw}</span>`;
        } else if (op) {
            return `<span class="tok-op">${op}</span>`;
        } else if (word) {
            return `<span class="tok-val">${word}</span>`;
        }
        return match;
    });
}

function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function scoreKeywordItem(item, q) {
    if (!q) return 0;
    const rawPrefix = item.prefix.toLowerCase();
    const prefixClean = rawPrefix.replace(/[:(]/g, '');
    const full = (item.prefix + (item.placeholder || '') + (item.suffix || '')).toLowerCase();
    const desc = (item.desc || '').toLowerCase();

    // Tier 0: exact keyword match (e.g. 'or' === 'or', 'and' === 'and', 'mime' === 'mime')
    if (prefixClean === q || rawPrefix === q || rawPrefix === q + ':') {
        return 0;
    }
    // Tier 1: keyword starts with query (e.g. 'fil' -> 'filename', 'or' -> 'order')
    if (prefixClean.startsWith(q) || rawPrefix.startsWith(q)) {
        return 10 + (prefixClean.length - q.length);
    }
    // Tier 2: full snippet starts with query (e.g. '{val' -> '{value}')
    if (full.startsWith(q)) {
        return 30 + (full.length - q.length);
    }
    // Tier 3: word boundary in prefix or template
    const escQ = escapeRegex(q);
    const wordBoundRegex = new RegExp('\\b' + escQ, 'i');
    if (wordBoundRegex.test(item.prefix) || wordBoundRegex.test(full)) {
        return 50;
    }
    // Tier 4: substring in template/prefix
    if (item.prefix.toLowerCase().includes(q) || full.includes(q)) {
        return 70;
    }
    // Tier 5: word boundary in description
    if (wordBoundRegex.test(desc)) {
        return 100;
    }
    // Tier 6: substring in description
    if (desc.includes(q)) {
        return 150;
    }
    return Infinity;
}

function scoreSecondaryItem(val, desc, q) {
    if (!q) return 0;
    const v = val.toLowerCase();
    const d = (desc || '').toLowerCase();
    if (v === q) return 0;
    if (v.startsWith(q)) return 10 + (v.length - q.length);
    const escQ = escapeRegex(q);
    const wordBoundRegex = new RegExp('\\b' + escQ, 'i');
    if (wordBoundRegex.test(v)) return 30;
    if (v.includes(q)) return 50;
    if (wordBoundRegex.test(d)) return 100;
    if (d.includes(q)) return 150;
    return Infinity;
}

function setupQueryFieldEditor(inputEl, contextType = 'general') {
    if (!inputEl || inputEl.dataset.queryEditorInit) return;
    inputEl.dataset.queryEditorInit = 'true';

    // Wrap in .query-editor-wrap
    const wrap = document.createElement('div');
    wrap.className = 'query-editor-wrap';
    if (inputEl.classList.contains('query-input')) {
        wrap.classList.add('main-query-editor-wrap');
    }
    inputEl.parentNode.insertBefore(wrap, inputEl);
    wrap.appendChild(inputEl);
    if (inputEl.classList.contains('query-input') && wrap.parentElement) {
        const icon = wrap.parentElement.querySelector('.query-input-icon');
        if (icon) wrap.appendChild(icon);
    }

    // Backdrop for real-time syntax highlighting
    const backdrop = document.createElement('div');
    backdrop.className = 'query-highlight-backdrop';
    if (inputEl.classList.contains('query-input')) {
        backdrop.classList.add('main-query-highlight-backdrop');
    }
    backdrop.setAttribute('aria-hidden', 'true');
    wrap.insertBefore(backdrop, inputEl);

    function updateHighlight() {
        if (!inputEl.value) {
            backdrop.innerHTML = '';
        } else {
            backdrop.innerHTML = highlightQuerySyntax(inputEl.value);
        }
        backdrop.scrollLeft = inputEl.scrollLeft;
    }

    inputEl.addEventListener('input', updateHighlight);
    inputEl.addEventListener('scroll', () => { backdrop.scrollLeft = inputEl.scrollLeft; });
    inputEl.addEventListener('change', updateHighlight);
    inputEl._updateHighlight = updateHighlight;
    updateHighlight();

    // Autocomplete Suggestions Dropdown
    let dropdown = null;
    let activeIdx = -1;
    let currentMatches = [];
    let currentContext = null;

    function closeDropdown() {
        if (dropdown) {
            if (dropdown.parentNode) dropdown.parentNode.removeChild(dropdown);
            dropdown = null;
        }
        wrap.classList.remove('has-active-dropdown');
        const parentCard = wrap.closest('.builder-field-card');
        if (parentCard && !parentCard.querySelector('.query-autocomplete-dropdown')) {
            parentCard.classList.remove('has-active-dropdown');
        }
        const parentRow = wrap.closest('.options-table tr');
        if (parentRow && !parentRow.querySelector('.query-autocomplete-dropdown')) {
            parentRow.classList.remove('has-active-dropdown');
        }
        const parentQueryInputWrap = wrap.closest('.query-input-wrap');
        if (parentQueryInputWrap && !parentQueryInputWrap.querySelector('.query-autocomplete-dropdown')) {
            parentQueryInputWrap.classList.remove('has-active-dropdown');
        }
        const parentSearchCard = wrap.closest('.search-card');
        if (parentSearchCard && !parentSearchCard.querySelector('.query-autocomplete-dropdown')) {
            parentSearchCard.classList.remove('has-active-dropdown');
        }
        const parentSearchForm = wrap.closest('#search-form');
        if (parentSearchForm && !parentSearchForm.querySelector('.query-autocomplete-dropdown')) {
            parentSearchForm.classList.remove('has-active-dropdown');
        }
        activeIdx = -1;
        currentContext = null;
        currentMatches = [];
    }

    wrap._closeQueryDropdown = closeDropdown;

    function getActiveContext() {
        const val = inputEl.value;
        const pos = (typeof inputEl.selectionStart === 'number') ? inputEl.selectionStart : val.length;

        // Find token boundaries around cursor
        let start = pos;
        while (start > 0 && !/[\s()]/.test(val[start - 1])) {
            start--;
        }
        let end = pos;
        while (end < val.length && !/[\s()]/.test(val[end])) {
            end++;
        }

        const tokenBeforeCursor = val.slice(start, pos);
        const tokenLower = tokenBeforeCursor.toLowerCase();

        // 1. Secondary: mime:
        if (tokenLower.startsWith('mime:')) {
            const query = tokenBeforeCursor.slice(5).toLowerCase();
            const scored = MIME_TYPES_LIST.map((m, idx) => ({
                item: m,
                idx,
                score: scoreSecondaryItem(m.value, m.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: m }) => ({
                badgeHtml: `<span class="tok-kw">mime</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(m.value)}</span>`,
                snippetText: `mime:${m.value}`,
                desc: m.desc,
                insertValue: `mime:${m.value}`,
                hasSub: false
            }));
            return {
                mode: 'mime',
                header: `MIME TYPES`,
                matches,
                tokenStart: start,
                tokenEnd: end
            };
        }

        // 2. Secondary: ext:
        if (tokenLower.startsWith('ext:')) {
            const query = tokenBeforeCursor.slice(4).toLowerCase();
            const scored = EXTENSIONS_LIST.map((e, idx) => ({
                item: e,
                idx,
                score: scoreSecondaryItem(e.value, e.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: e }) => ({
                badgeHtml: `<span class="tok-kw">ext</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(e.value)}</span>`,
                snippetText: `ext:${e.value}`,
                desc: e.desc,
                insertValue: `ext:${e.value}`,
                hasSub: false
            }));
            return {
                mode: 'ext',
                header: `FILE EXTENSIONS`,
                matches,
                tokenStart: start,
                tokenEnd: end
            };
        }

        // 3. Secondary: size:
        if (tokenLower.startsWith('size:')) {
            const query = tokenBeforeCursor.slice(5).toLowerCase();
            const scored = SIZE_LIST.map((s, idx) => ({
                item: s,
                idx,
                score: scoreSecondaryItem(s.value, s.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: s }) => ({
                badgeHtml: `<span class="tok-kw">size</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(s.value)}</span>`,
                snippetText: `size:${s.value}`,
                desc: s.desc,
                insertValue: `size${s.value.startsWith('<') || s.value.startsWith('>') ? s.value : (':' + s.value)}`,
                hasSub: false
            }));
            return {
                mode: 'size',
                header: `FILE SIZES`,
                matches,
                tokenStart: start,
                tokenEnd: end
            };
        }

        // 4. Top-level keywords / patterns
        let baseList;
        if (contextType === 'text') {
            baseList = (val.trim() === '')
                ? TEXT_SNIPPET_PATTERNS.concat(TOP_LEVEL_KEYWORDS)
                : TOP_LEVEL_KEYWORDS.concat(TEXT_SNIPPET_PATTERNS);
        } else {
            baseList = TOP_LEVEL_KEYWORDS;
        }

        const query = tokenBeforeCursor.toLowerCase();
        const scored = baseList.map((item, idx) => ({
            item,
            idx,
            score: scoreKeywordItem(item, query)
        })).filter(x => x.score < Infinity);
        scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

        const matches = scored.map(({ item }) => {
            let badgeHtml = '';
            let snippetClass = '';
            if (item.isBool || ['AND', 'OR', 'NOT', 'XOR'].includes(item.prefix)) {
                badgeHtml = `<span class="tok-bool">${escapeHtml(item.prefix)}</span>`;
                snippetClass = 'snippet-bool';
            } else if (item.prefix === '(') {
                const ph = item.placeholder || 'clause';
                badgeHtml = `<span class="tok-op">(</span><span class="param-placeholder">${escapeHtml(ph)}</span><span class="tok-op">)</span>`;
                snippetClass = 'snippet-op';
            } else if (item.prefix === '-') {
                const ph = item.placeholder || 'term';
                badgeHtml = `<span class="tok-op">-</span><span class="param-placeholder">${escapeHtml(ph)}</span>`;
                snippetClass = 'snippet-op';
            } else if (item.placeholder) {
                const kw = item.prefix.replace(/[:(]/, '');
                const op = item.prefix.slice(kw.length);
                badgeHtml = `<span class="tok-kw">${escapeHtml(kw)}</span><span class="tok-op">${escapeHtml(op)}</span><span class="param-placeholder">${escapeHtml(item.placeholder)}</span>`;
                if (item.suffix) {
                    badgeHtml += `<span class="tok-op">${escapeHtml(item.suffix)}</span>`;
                }
            } else if (item.prefix.startsWith('{value}') || item.prefix.includes('{value}')) {
                badgeHtml = highlightQuerySyntax(item.prefix);
            } else {
                badgeHtml = `<span class="tok-kw">${escapeHtml(item.prefix)}</span>`;
            }

            return {
                badgeHtml,
                snippetClass,
                snippetText: item.prefix + (item.placeholder || '') + (item.suffix || ''),
                desc: item.desc,
                hasSub: !!item.hasSub,
                insertPrefix: item.insertPrefix,
                insertValue: item.insertPrefix || item.prefix
            };
        });

        return {
            mode: 'top',
            header: '',
            matches,
            tokenStart: start,
            tokenEnd: end
        };
    }

    function renderDropdown(ctx) {
        currentContext = ctx;
        currentMatches = (ctx && ctx.matches) ? ctx.matches : [];
        activeIdx = -1;

        if (currentMatches.length === 0) {
            closeDropdown();
            return;
        }

        if (!dropdown || !dropdown.isConnected) {
            dropdown = document.createElement('div');
            dropdown.className = 'query-autocomplete-dropdown';
            wrap.appendChild(dropdown);
        }

        wrap.classList.add('has-active-dropdown');
        const parentCard = wrap.closest('.builder-field-card');
        if (parentCard) parentCard.classList.add('has-active-dropdown');
        const parentRow = wrap.closest('.options-table tr');
        if (parentRow) parentRow.classList.add('has-active-dropdown');
        const parentQueryInputWrap = wrap.closest('.query-input-wrap');
        if (parentQueryInputWrap) parentQueryInputWrap.classList.add('has-active-dropdown');
        const parentSearchCard = wrap.closest('.search-card');
        if (parentSearchCard) parentSearchCard.classList.add('has-active-dropdown');
        const parentSearchForm = wrap.closest('#search-form');
        if (parentSearchForm) parentSearchForm.classList.add('has-active-dropdown');

        const rect = wrap.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        if (spaceBelow < 280 && rect.top > 280) {
            dropdown.classList.add('drop-up');
        } else {
            dropdown.classList.remove('drop-up');
        }

        dropdown.innerHTML = '';

        if (ctx.header) {
            const header = document.createElement('div');
            header.className = 'query-autocomplete-header';
            header.innerHTML = `<span>${ctx.header}</span>`;
            dropdown.appendChild(header);
        }

        const listContainer = document.createElement('div');
        listContainer.className = 'query-autocomplete-list';
        dropdown.appendChild(listContainer);

        currentMatches.forEach((item, idx) => {
            const row = document.createElement('div');
            row.className = `query-suggestion-item ${idx === activeIdx ? 'is-selected' : ''}`;
            row.dataset.index = idx;
            row.innerHTML = `
                <span class="query-suggestion-snippet ${item.snippetClass || ''}">${item.badgeHtml}</span>
                <span class="query-suggestion-desc">${escapeHtml(item.desc)}</span>
            `;

            row.addEventListener('mouseenter', () => {
                activeIdx = idx;
                updateSelectedRow();
            });

            row.addEventListener('mousedown', (e) => {
                e.preventDefault(); // prevent blur
                selectSuggestion(item);
            });
            listContainer.appendChild(row);
        });

        scrollActiveIntoView();
    }

    function scrollActiveIntoView() {
        if (!dropdown) return;
        const selected = dropdown.querySelector('.query-suggestion-item.is-selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest' });
        }
    }

    function filterAndShow() {
        const ctx = getActiveContext();
        if (!ctx || !ctx.matches || ctx.matches.length === 0) {
            closeDropdown();
            return;
        }
        renderDropdown(ctx);
    }

    function selectSuggestion(item) {
        const ctx = currentContext || getActiveContext();
        const val = inputEl.value;
        const before = val.slice(0, ctx.tokenStart);
        const after = val.slice(ctx.tokenEnd);

        const replacement = item.insertValue || item.insertPrefix || item.snippetText;
        const reopenSub = !!item.hasSub;

        inputEl.value = before + replacement + after;
        const newCursorPos = ctx.tokenStart + replacement.length;
        inputEl.setSelectionRange(newCursorPos, newCursorPos);

        updateHighlight();
        inputEl.dispatchEvent(new Event('input', { bubbles: true }));

        if (reopenSub) {
            // Immediately open context suggestions at the cursor
            filterAndShow();
        } else {
            closeDropdown();
        }
        inputEl.focus();
    }

    inputEl.addEventListener('focus', () => {
        updateHighlight();
    });

    inputEl.addEventListener('click', () => {
        updateHighlight();
        if (!dropdown) filterAndShow();
    });

    inputEl.addEventListener('input', () => {
        filterAndShow();
    });

    inputEl.addEventListener('keydown', (e) => {
        if (!dropdown) {
            if (e.key === 'ArrowDown' || (e.key === ' ' && e.ctrlKey)) {
                filterAndShow();
                e.preventDefault();
            }
            return;
        }

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (currentMatches.length > 0) {
                activeIdx = (activeIdx + 1) % currentMatches.length;
                updateSelectedRow();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (currentMatches.length > 0) {
                activeIdx = activeIdx <= 0 ? currentMatches.length - 1 : activeIdx - 1;
                updateSelectedRow();
            }
        } else if (e.key === 'Enter') {
            if (activeIdx >= 0 && activeIdx < currentMatches.length) {
                e.preventDefault();
                e.stopPropagation();
                selectSuggestion(currentMatches[activeIdx]);
            } else {
                closeDropdown();
            }
        } else if (e.key === 'Tab') {
            if (currentMatches.length > 0) {
                e.preventDefault();
                e.stopPropagation();
                selectSuggestion(currentMatches[activeIdx >= 0 ? activeIdx : 0]);
            }
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            closeDropdown();
        }
    });

    function updateSelectedRow() {
        if (!dropdown) return;
        dropdown.querySelectorAll('.query-suggestion-item').forEach((row, idx) => {
            row.classList.toggle('is-selected', idx === activeIdx);
        });
        scrollActiveIntoView();
    }

    document.addEventListener('click', (e) => {
        if (!wrap.contains(e.target)) {
            closeDropdown();
        }
    });

    document.addEventListener('mousedown', (e) => {
        if (!wrap.contains(e.target)) {
            closeDropdown();
        }
    });
}

function initMainQueryEditor() {
    const mainQueryInput = document.querySelector('input.query-input');
    if (mainQueryInput) {
        setupQueryFieldEditor(mainQueryInput, 'general');
    }
}

// ============================================================================
// Settings Custom Form Builder & Manager
// ============================================================================

function initSettingsFormManager() {
    const listContainer = document.getElementById('forms-cards-list');
    if (!listContainer) return;

    let forms = getStoredForms();
    const builderOverlay = document.getElementById('form-builder-overlay');
    const schemaOverlay = document.getElementById('schema-viewer-overlay');
    const btnCreate = document.getElementById('btn-create-form');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const btnCloseSchema = document.getElementById('btn-close-schema');
    const btnCloseSchemaModal = document.getElementById('btn-close-schema-modal');
    const btnAddField = document.getElementById('btn-add-field');
    const btnSaveForm = document.getElementById('btn-save-form');

    const builderFormId = document.getElementById('builder-form-id');
    const builderFormName = document.getElementById('builder-form-name');
    const builderFormDesc = document.getElementById('builder-form-desc');
    const builderFieldsContainer = document.getElementById('builder-fields-container');
    const modalTitle = document.getElementById('modal-title');

    function renderCards() {
        listContainer.innerHTML = '';
        forms.forEach(form => {
            const card = document.createElement('div');
            card.className = 'form-manage-card';

            const isReadOnly = !!form.readonly;
            const badgeHtml = isReadOnly
                ? '<span class="badge-pill badge-readonly">Default / Read-Only</span>'
                : '<span class="badge-pill badge-custom">Custom</span>';

            let fieldChips = '';
            (form.fields || []).slice(0, 5).forEach(f => {
                fieldChips += `<span class="field-chip">${escapeHtml(f.label)} (${escapeHtml(f.type)})</span>`;
            });
            if ((form.fields || []).length > 5) {
                fieldChips += `<span class="field-chip">+${form.fields.length - 5} more</span>`;
            }

            let actionsHtml = '';
            if (isReadOnly) {
                actionsHtml = `
                    <button type="button" class="btn btn-secondary btn-sm" data-action="view-schema" data-form-id="${escapeHtml(form.id)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        <span>View Schema</span>
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" data-action="duplicate" data-form-id="${escapeHtml(form.id)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        <span>Duplicate</span>
                    </button>
                `;
            } else {
                actionsHtml = `
                    <button type="button" class="btn btn-secondary btn-sm" data-action="edit" data-form-id="${escapeHtml(form.id)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        <span>Edit</span>
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" data-action="duplicate" data-form-id="${escapeHtml(form.id)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        <span>Duplicate</span>
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm btn-icon-danger" data-action="delete" data-form-id="${escapeHtml(form.id)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        <span>Delete</span>
                    </button>
                `;
            }

            card.innerHTML = `
                <div class="form-card-top">
                    <h4 class="form-card-title">${escapeHtml(form.name)}</h4>
                    ${badgeHtml}
                </div>
                <p class="form-card-desc">${escapeHtml(form.description || 'No description provided.')}</p>
                <div class="form-card-fields-preview">
                    ${fieldChips}
                </div>
                <div class="form-card-actions">
                    ${actionsHtml}
                </div>
            `;

            listContainer.appendChild(card);
        });

        // Attach action handlers
        listContainer.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.dataset.action;
                const formId = btn.dataset.formId;
                const formObj = forms.find(f => f.id === formId);
                if (!formObj) return;

                if (action === 'view-schema') {
                    showSchemaModal(formObj);
                } else if (action === 'edit') {
                    openBuilderModal(formObj, false);
                } else if (action === 'duplicate') {
                    openBuilderModal(formObj, true);
                } else if (action === 'delete') {
                    deleteForm(formObj);
                }
            });
        });
    }

    function showSchemaModal(form) {
        const titleEl = document.getElementById('schema-modal-title');
        const tableEl = document.getElementById('schema-fields-table');
        if (titleEl) titleEl.textContent = `${form.name} (Schema)`;
        if (tableEl) {
            let html = '<table class="options-table"><thead><tr><th>Field Label</th><th>Type</th><th>Operator / Format</th><th>Helper</th></tr></thead><tbody>';
            (form.fields || []).forEach(f => {
                html += `<tr>
                    <td><strong>${escapeHtml(f.label)}</strong></td>
                    <td><code>${escapeHtml(f.type)}</code></td>
                    <td><code>${escapeHtml(f.query_format || f.query || (f.options ? f.options.length + ' options' : ''))}</code></td>
                    <td><span class="schema-field-helper">${escapeHtml(f.helper || '')}</span></td>
                </tr>`;
            });
            html += '</tbody></table>';
            tableEl.innerHTML = html;
        }
        schemaOverlay.style.display = 'flex';
    }

    function updateBuilderEmptyState() {
        const existingNotice = builderFieldsContainer.querySelector('.builder-empty-state');
        const cards = builderFieldsContainer.querySelectorAll('.builder-field-card');
        if (cards.length === 0) {
            if (!existingNotice) {
                const notice = document.createElement('div');
                notice.className = 'builder-empty-state';
                notice.innerHTML = 'No fields added yet. Click &ldquo;Add Field&rdquo; above to configure fields for this search form.';
                builderFieldsContainer.appendChild(notice);
            }
        } else if (existingNotice) {
            existingNotice.remove();
        }
    }

    function openBuilderModal(formToEdit = null, isDuplicate = false) {
        builderFieldsContainer.innerHTML = '';

        if (formToEdit) {
            builderFormId.value = isDuplicate ? '' : formToEdit.id;
            builderFormName.value = isDuplicate ? `${formToEdit.name} (Copy)` : formToEdit.name;
            builderFormDesc.value = formToEdit.description || '';
            modalTitle.textContent = isDuplicate ? 'Duplicate Search Form' : `Edit Search Form: ${formToEdit.name}`;

            (formToEdit.fields || []).forEach(f => {
                addFieldCard(f);
            });
        } else {
            builderFormId.value = '';
            builderFormName.value = '';
            builderFormDesc.value = '';
            modalTitle.textContent = 'Create Custom Search Form';
        }

        updateBuilderEmptyState();
        builderOverlay.style.display = 'flex';
    }

    function addFieldCard(fieldData = {}) {
        const emptyNotice = builderFieldsContainer.querySelector('.builder-empty-state');
        if (emptyNotice) emptyNotice.remove();

        const card = document.createElement('div');
        card.className = 'builder-field-card';

        const fId = fieldData.id || `f_${Math.random().toString(36).substring(2, 9)}`;
        const fLabel = fieldData.label || '';
        const fType = fieldData.type || 'text';
        const fHelper = fieldData.helper || '';
        const fPlaceholder = fieldData.placeholder || '';
        const fFormat = fieldData.query_format || '{value}';
        const fQuery = fieldData.query || '';
        const options = fieldData.options || [
            { label: 'Option 1', query: 'filename:*000*' }
        ];

        card.innerHTML = `
            <div class="builder-field-header">
                <span class="builder-field-num">Field Config</span>
                <div class="builder-field-controls">
                    <button type="button" class="btn-icon btn-move-up" title="Move Up">&uarr;</button>
                    <button type="button" class="btn-icon btn-move-down" title="Move Down">&darr;</button>
                    <button type="button" class="btn-icon btn-icon-danger btn-del-field" title="Remove Field">&times;</button>
                </div>
            </div>
            <input type="hidden" class="field-id-input" value="${escapeHtml(fId)}">
            <div class="settings-grid" style="margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Field Label *</label>
                    <input class="form-control field-label-input" value="${escapeHtml(fLabel)}" placeholder="e.g. Document Type" required>
                </div>
                <div class="settings-field">
                    <label class="settings-label">Field Type</label>
                    <select class="form-control field-type-select">
                        <option value="text" ${fType === 'text' ? 'selected' : ''}>Text Input</option>
                        <option value="select" ${fType === 'select' ? 'selected' : ''}>Dropdown  Filter</option>
                        <option value="toggle" ${(fType === 'toggle' || fType === 'checkbox') ? 'selected' : ''}>Toggle Filter</option>
                        <option value="static_query" ${(fType === 'static_query' || fType === 'static') ? 'selected' : ''}>Static Query</option>
                    </select>
                </div>
            </div>
            <div class="settings-grid" style="margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Helper Description</label>
                    <input class="form-control field-helper-input" value="${escapeHtml(fHelper)}" placeholder="Brief user guidance">
                </div>
                <div class="settings-field field-placeholder-wrap" style="${fType === 'text' ? '' : 'display: none;'}">
                    <label class="settings-label">Placeholder Text</label>
                    <input class="form-control field-placeholder-input" value="${escapeHtml(fPlaceholder)}" placeholder="e.g. Enter term...">
                </div>
            </div>

            <!-- Text Config: Query Snippet -->
            <div class="field-text-config" style="${fType === 'text' ? '' : 'display: none;'} margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Query Snippet</label>
                    <span class="settings-helper">Use {value} as placeholder for user input, e.g. filename:*{value}* or title:{value}</span>
                    <input class="form-control form-control-query field-custom-format-input" value="${escapeHtml(fFormat)}" placeholder="e.g. {value} or filename:*{value}*" spellcheck="false" autocomplete="off">
                </div>
            </div>

            <!-- Toggle Config -->
            <div class="field-toggle-config field-checkbox-config" style="${(fType === 'toggle' || fType === 'checkbox') ? '' : 'display: none;'} margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Query Snippet When Toggled On</label>
                    <input class="form-control form-control-query field-toggle-query-input field-checkbox-query-input" value="${escapeHtml(fQuery)}" placeholder="e.g. mime:application/pdf" spellcheck="false" autocomplete="off">
                </div>
            </div>

            <!-- Static Query Config -->
            <div class="field-static-config" style="${(fType === 'static_query' || fType === 'static') ? '' : 'display: none;'} margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Static Recoll Query *</label>
                    <span class="settings-helper">This query clause is automatically added to searches using this form (not visible in the search form)</span>
                    <input class="form-control form-control-query field-static-query-input" value="${escapeHtml(fQuery)}" placeholder="e.g. dir:/archive OR mime:application/pdf" spellcheck="false" autocomplete="off">
                </div>
            </div>

            <!-- Select Options Config -->
            <div class="field-select-config" style="${fType === 'select' ? '' : 'display: none;'}">
                <div class="options-header">
                    <span class="settings-label">Dropdown Options (Label &rarr; Recoll Query)</span>
                    <button type="button" class="btn btn-secondary btn-sm btn-add-option">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                        <span>Add Option</span>
                    </button>
                </div>
                <table class="options-table">
                    <thead>
                        <tr>
                            <th style="width: 46%;">Option Label</th>
                            <th style="width: 44%;">Recoll Query Snippet</th>
                            <th style="width: 10%; text-align: center;"></th>
                        </tr>
                    </thead>
                    <tbody class="options-tbody">
                    </tbody>
                </table>
            </div>
        `;

        const typeSelect = card.querySelector('.field-type-select');
        const textConfig = card.querySelector('.field-text-config');
        const placeholderWrap = card.querySelector('.field-placeholder-wrap');
        const toggleConfig = card.querySelector('.field-toggle-config') || card.querySelector('.field-checkbox-config');
        const selectConfig = card.querySelector('.field-select-config');
        const staticConfig = card.querySelector('.field-static-config');
        const optionsTbody = card.querySelector('.options-tbody');

        function renderOptionRow(optLabel = '', optQuery = '') {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input class="form-control opt-label-input" value="${escapeHtml(optLabel)}" placeholder="e.g. Invoices" required></td>
                <td><input class="form-control form-control-query opt-query-input" value="${escapeHtml(optQuery)}" placeholder="e.g. filename:*INV*" spellcheck="false" autocomplete="off"></td>
                <td style="text-align: center;"><button type="button" class="btn-icon btn-icon-danger btn-del-opt">&times;</button></td>
            `;
            tr.querySelector('.btn-del-opt').addEventListener('click', () => tr.remove());
            optionsTbody.appendChild(tr);
            setupQueryFieldEditor(tr.querySelector('.opt-query-input'), 'general');
        }

        options.forEach(opt => {
            renderOptionRow(opt.label, opt.query);
        });

        card.querySelector('.btn-add-option').addEventListener('click', () => {
            renderOptionRow('New Option', '');
        });

        typeSelect.addEventListener('change', () => {
            const selectedType = typeSelect.value;
            const isStatic = selectedType === 'static_query' || selectedType === 'static';
            const isToggle = selectedType === 'toggle' || selectedType === 'checkbox';
            textConfig.style.display = selectedType === 'text' ? 'block' : 'none';
            placeholderWrap.style.display = selectedType === 'text' ? 'block' : 'none';
            if (toggleConfig) toggleConfig.style.display = isToggle ? 'block' : 'none';
            selectConfig.style.display = selectedType === 'select' ? 'block' : 'none';
            staticConfig.style.display = isStatic ? 'block' : 'none';
        });

        setupQueryFieldEditor(card.querySelector('.field-custom-format-input'), 'text');
        const toggleQueryInput = card.querySelector('.field-toggle-query-input') || card.querySelector('.field-checkbox-query-input');
        if (toggleQueryInput) setupQueryFieldEditor(toggleQueryInput, 'general');
        setupQueryFieldEditor(card.querySelector('.field-static-query-input'), 'general');

        // Reordering and deletion handlers
        card.querySelector('.btn-del-field').addEventListener('click', () => {
            card.remove();
            updateBuilderEmptyState();
        });
        card.querySelector('.btn-move-up').addEventListener('click', () => {
            const prev = card.previousElementSibling;
            if (prev) builderFieldsContainer.insertBefore(card, prev);
        });
        card.querySelector('.btn-move-down').addEventListener('click', () => {
            const next = card.nextElementSibling;
            if (next) builderFieldsContainer.insertBefore(next, card);
        });

        builderFieldsContainer.appendChild(card);
        initCustomSelects(card);
    }

    window.openNewFormBuilder = function(e) {
        if (e && e.preventDefault) e.preventDefault();
        openBuilderModal(null, false);
    };

    if (btnCreate) {
        btnCreate.addEventListener('click', window.openNewFormBuilder);
    }

    if (btnCloseModal) btnCloseModal.addEventListener('click', () => builderOverlay.style.display = 'none');
    if (btnCancelModal) btnCancelModal.addEventListener('click', () => builderOverlay.style.display = 'none');
    if (btnCloseSchema) btnCloseSchema.addEventListener('click', () => schemaOverlay.style.display = 'none');
    if (btnCloseSchemaModal) btnCloseSchemaModal.addEventListener('click', () => schemaOverlay.style.display = 'none');

    if (btnAddField) {
        btnAddField.addEventListener('click', () => {
            addFieldCard({
                id: `field_${Date.now()}`,
                label: 'New Field',
                type: 'text',
                query_format: '{value}'
            });
        });
    }

    if (btnSaveForm) {
        btnSaveForm.addEventListener('click', async () => {
            const name = builderFormName.value.trim();
            if (!name) {
                alert('Please provide a form name.');
                builderFormName.focus();
                return;
            }

            const fieldCards = builderFieldsContainer.querySelectorAll('.builder-field-card');
            if (fieldCards.length === 0) {
                alert('Please add at least one field to the search form.');
                return;
            }

            const fields = [];
            for (const card of fieldCards) {
                const fId = card.querySelector('.field-id-input').value.trim();
                let fLabel = card.querySelector('.field-label-input').value.trim();
                const fType = card.querySelector('.field-type-select').value;
                if (!fLabel && (fType === 'static_query' || fType === 'static')) {
                    fLabel = 'Static Query';
                } else if (!fLabel) {
                    alert('Every field must have a label.');
                    return;
                }
                const fHelper = card.querySelector('.field-helper-input').value.trim();
                const fPlaceholder = card.querySelector('.field-placeholder-input').value.trim();

                const fieldObj = {
                    id: fId,
                    label: fLabel,
                    type: fType,
                    helper: fHelper,
                    placeholder: fPlaceholder,
                };

                if (fType === 'select') {
                    const optionRows = card.querySelectorAll('.options-tbody tr');
                    const options = [];
                    optionRows.forEach(row => {
                        const optLabel = row.querySelector('.opt-label-input').value.trim();
                        const optQuery = row.querySelector('.opt-query-input').value.trim();
                        if (optLabel) {
                            options.push({ label: optLabel, query: optQuery });
                        }
                    });
                    fieldObj.options = options;
                } else if (fType === 'toggle' || fType === 'checkbox') {
                    fieldObj.type = 'toggle';
                    const qInput = card.querySelector('.field-toggle-query-input') || card.querySelector('.field-checkbox-query-input');
                    fieldObj.query = qInput ? qInput.value.trim() : '';
                } else if (fType === 'static_query' || fType === 'static') {
                    fieldObj.query = card.querySelector('.field-static-query-input').value.trim();
                } else {
                    fieldObj.query_format = card.querySelector('.field-custom-format-input').value.trim() || '{value}';
                }
                fields.push(fieldObj);
            }

            const payload = {
                id: builderFormId.value.trim() || undefined,
                name: name,
                description: builderFormDesc.value.trim(),
                fields: fields
            };

            btnSaveForm.disabled = true;
            btnSaveForm.textContent = 'Saving...';

            try {
                const response = await fetch('/api/forms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();
                if (!response.ok || !result.success) {
                    throw new Error(result.error || 'Failed to save form');
                }

                // Refresh forms list
                const getResp = await fetch('/api/forms');
                const getData = await getResp.json();
                forms = getData.forms || [];

                // Update embedded JSON
                const dataTag = document.getElementById('recoll-search-forms-data');
                if (dataTag) dataTag.textContent = JSON.stringify(forms);

                builderOverlay.style.display = 'none';
                renderCards();
            } catch (err) {
                alert(`Error saving form: ${err.message}`);
            } finally {
                btnSaveForm.disabled = false;
                btnSaveForm.textContent = 'Save Search Form';
            }
        });
    }

    async function deleteForm(form) {
        if (!confirm(`Are you sure you want to delete the custom form "${form.name}"?`)) {
            return;
        }

        try {
            const resp = await fetch('/api/forms/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: form.id })
            });
            const result = await resp.json();
            if (!resp.ok || !result.success) {
                throw new Error(result.error || 'Failed to delete form');
            }

            // Refresh forms list
            const getResp = await fetch('/api/forms');
            const getData = await getResp.json();
            forms = getData.forms || [];

            const dataTag = document.getElementById('recoll-search-forms-data');
            if (dataTag) dataTag.textContent = JSON.stringify(forms);

            renderCards();
        } catch (err) {
            alert(`Error deleting form: ${err.message}`);
        }
    }

    renderCards();
}

/**
 * Files Download Handler (Single File direct download or Zip Archive with Progress)
 */
function initFilesDownload() {
    const btnDownloadFiles = document.getElementById('btn-download-files');
    const archiveModal = document.getElementById('archive-modal');
    if (!btnDownloadFiles || !archiveModal) return;

    const btnCloseModal = document.getElementById('btn-close-archive-modal');
    const btnCancelArchive = document.getElementById('btn-cancel-archive');
    const statusText = document.getElementById('archive-status-text');
    const percentText = document.getElementById('archive-percent-text');
    const progressBar = document.getElementById('archive-progress-bar');
    const fileDetail = document.getElementById('archive-file-detail');

    let activeJobId = null;
    let pollTimer = null;

    function closeModal() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
        if (activeJobId) {
            const jobIdToCancel = activeJobId;
            activeJobId = null;
            try {
                fetch(`/api/archive/cancel/${jobIdToCancel}`, { method: 'POST' }).catch(() => {});
            } catch (e) {}
        }
        archiveModal.style.display = 'none';
    }

    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', closeModal);
    }
    if (btnCancelArchive) {
        btnCancelArchive.addEventListener('click', closeModal);
    }
    archiveModal.addEventListener('click', (e) => {
        if (e.target === archiveModal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && archiveModal.style.display !== 'none') {
            closeModal();
        }
    });

    btnDownloadFiles.addEventListener('click', async (e) => {
        e.preventDefault();
        const totalCount = parseInt(btnDownloadFiles.dataset.totalCount, 10);
        let queryString = btnDownloadFiles.dataset.queryString || '';
        if (!queryString && window.location.search) {
            queryString = window.location.search.replace(/^\?/, '');
        }

        // Single file: direct download without opening dialog or zipping
        if (totalCount === 1) {
            window.location.href = `./download/0?${queryString}`;
            return;
        }

        // Multiple files: open dialog with animated progress bar
        statusText.textContent = 'Preparing files for archive...';
        statusText.style.color = '';
        percentText.textContent = '0%';
        progressBar.style.width = '0%';
        fileDetail.textContent = '';
        archiveModal.style.display = 'flex';

        try {
            const res = await fetch(`/api/archive/start?${queryString}`);
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || 'Failed to start archive');
            }
            const data = await res.json();

            if (data.single_file) {
                closeModal();
                window.location.href = data.download_url || `./download/0?${queryString}`;
                return;
            }

            activeJobId = data.job_id;

            // Poll zipping progress
            pollTimer = setInterval(async () => {
                if (!activeJobId) {
                    clearInterval(pollTimer);
                    return;
                }
                try {
                    const statusRes = await fetch(`/api/archive/status/${activeJobId}`);
                    if (!statusRes.ok) {
                        throw new Error('Status request failed');
                    }
                    const statusData = await statusRes.json();

                    const pct = statusData.percent != null ? statusData.percent : 0;
                    progressBar.style.width = `${pct}%`;
                    percentText.textContent = `${pct}%`;

                    if (statusData.status === 'zipping') {
                        statusText.textContent = `Zipping files (${statusData.processed || 0} of ${statusData.total || 0})...`;
                        fileDetail.textContent = statusData.current_file ? `Adding: ${statusData.current_file}` : '';
                    } else if (statusData.status === 'ready') {
                        clearInterval(pollTimer);
                        pollTimer = null;
                        const dlUrl = statusData.download_url || `/api/archive/download/${activeJobId}`;
                        activeJobId = null;
                        // Close modal immediately upon completion; browser proceeds to download
                        archiveModal.style.display = 'none';
                        window.location.href = dlUrl;
                    } else if (statusData.status === 'error') {
                        clearInterval(pollTimer);
                        pollTimer = null;
                        activeJobId = null;
                        statusText.textContent = `Archive failed: ${statusData.error || 'Unknown error'}`;
                        statusText.style.color = '#ef4444';
                        fileDetail.textContent = '';
                    } else if (statusData.status === 'cancelled') {
                        clearInterval(pollTimer);
                        pollTimer = null;
                        activeJobId = null;
                        archiveModal.style.display = 'none';
                    }
                } catch (pollErr) {
                    // Ignore transient network errors during polling
                }
            }, 300);

        } catch (startErr) {
            statusText.textContent = `Error: ${startErr.message}`;
            statusText.style.color = '#ef4444';
        }
    });
}

/**
 * Custom Glassmorphic Select Component
 * Enhances native <select class="form-control"> into a luxury glassmorphic dropdown
 * with animated rotating chevron, glowing highlights, checkmarks, and keyboard navigation.
 */
function initCustomSelects(root = document) {
    let selects = [];
    if (root.matches && root.matches('select.form-control:not([data-customized])')) {
        selects = [root];
    } else if (root.querySelectorAll) {
        selects = Array.from(root.querySelectorAll('select.form-control:not([data-customized])'));
    }

    selects.forEach(select => {
        select.dataset.customized = 'true';

        // Check if already inside a wrapper
        let wrapper = select.closest('.custom-select-wrapper');
        if (!wrapper) {
            wrapper = document.createElement('div');
            wrapper.className = 'custom-select-wrapper';
            if (select.classList.contains('form-preset-select')) {
                wrapper.classList.add('form-preset-select');
            }
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(select);
        }

        // Create Trigger Button
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'custom-select-trigger';
        trigger.setAttribute('role', 'combobox');
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');

        const label = document.createElement('span');
        label.className = 'custom-select-label';

        const arrow = document.createElement('span');
        arrow.className = 'custom-select-arrow';
        arrow.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;

        trigger.appendChild(label);
        trigger.appendChild(arrow);
        wrapper.appendChild(trigger);

        // Create Menu Popover
        const menu = document.createElement('div');
        menu.className = 'custom-select-menu';
        menu.setAttribute('role', 'listbox');
        wrapper.appendChild(menu);

        let highlightedIndex = -1;
        let typeAheadBuffer = '';
        let typeAheadTimer = null;

        function renderOptions() {
            menu.innerHTML = '';
            const selectedOpt = select.options[select.selectedIndex] || select.options[0];
            if (selectedOpt) {
                label.textContent = selectedOpt.textContent.trim();
            } else {
                label.textContent = '';
            }

            Array.from(select.options).forEach((opt, idx) => {
                const optEl = document.createElement('div');
                optEl.className = 'custom-select-option';
                optEl.setAttribute('role', 'option');
                optEl.dataset.index = idx;
                optEl.dataset.value = opt.value;
                if (opt.selected) {
                    optEl.classList.add('is-selected');
                    optEl.setAttribute('aria-selected', 'true');
                }
                if (opt.disabled) {
                    optEl.classList.add('is-disabled');
                }

                const textSpan = document.createElement('span');
                textSpan.className = 'custom-select-option-text';

                // Preserve folder hierarchy indentation if non-breaking spaces are present
                if (opt.innerHTML && opt.innerHTML.includes('&nbsp;')) {
                    textSpan.innerHTML = opt.innerHTML;
                } else {
                    textSpan.textContent = opt.textContent.trim();
                }

                const checkSpan = document.createElement('span');
                checkSpan.className = 'custom-select-check';
                checkSpan.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

                optEl.appendChild(textSpan);
                optEl.appendChild(checkSpan);

                optEl.addEventListener('mouseenter', () => {
                    setHighlighted(idx);
                });

                optEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (opt.disabled) return;
                    selectOption(idx);
                });

                menu.appendChild(optEl);
            });
        }

        function openMenu() {
            // Close any other open dropdowns
            document.querySelectorAll('.custom-select-wrapper.is-open').forEach(w => {
                if (w !== wrapper) {
                    w.classList.remove('is-open', 'drop-up');
                    const trg = w.querySelector('.custom-select-trigger');
                    if (trg) trg.setAttribute('aria-expanded', 'false');
                }
            });

            // Calculate viewport position for drop-up if near bottom
            const rect = trigger.getBoundingClientRect();
            const spaceBelow = window.innerHeight - rect.bottom;
            if (spaceBelow < 260 && rect.top > 260) {
                wrapper.classList.add('drop-up');
            } else {
                wrapper.classList.remove('drop-up');
            }

            wrapper.classList.add('is-open');
            trigger.setAttribute('aria-expanded', 'true');

            highlightedIndex = select.selectedIndex >= 0 ? select.selectedIndex : 0;
            updateHighlightScroll();
        }

        function closeMenu() {
            wrapper.classList.remove('is-open', 'drop-up');
            trigger.setAttribute('aria-expanded', 'false');
            highlightedIndex = -1;
            clearHighlight();
        }

        function selectOption(index) {
            if (index < 0 || index >= select.options.length) return;
            const opt = select.options[index];
            if (opt.disabled) return;

            select.selectedIndex = index;
            label.textContent = opt.textContent.trim();

            menu.querySelectorAll('.custom-select-option').forEach((el, idx) => {
                if (idx === index) {
                    el.classList.add('is-selected');
                    el.setAttribute('aria-selected', 'true');
                } else {
                    el.classList.remove('is-selected');
                    el.removeAttribute('aria-selected');
                }
            });

            closeMenu();
            trigger.focus();

            // Dispatch events to trigger native form and search listeners
            select.dispatchEvent(new Event('change', { bubbles: true }));
            select.dispatchEvent(new Event('input', { bubbles: true }));
        }

        function setHighlighted(index) {
            highlightedIndex = index;
            const items = menu.querySelectorAll('.custom-select-option');
            items.forEach((item, idx) => {
                item.classList.toggle('is-highlighted', idx === highlightedIndex);
            });
        }

        function clearHighlight() {
            menu.querySelectorAll('.custom-select-option').forEach(item => {
                item.classList.remove('is-highlighted');
            });
        }

        function updateHighlightScroll() {
            setHighlighted(highlightedIndex);
            const items = menu.querySelectorAll('.custom-select-option');
            const highlightedItem = items[highlightedIndex];
            if (highlightedItem) {
                highlightedItem.scrollIntoView({ block: 'nearest' });
            }
        }

        // Trigger Click
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (wrapper.classList.contains('is-open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        // Keyboard Navigation
        trigger.addEventListener('keydown', (e) => {
            const isOpen = wrapper.classList.contains('is-open');
            const optionCount = select.options.length;

            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                if (isOpen) {
                    if (highlightedIndex >= 0) {
                        selectOption(highlightedIndex);
                    } else {
                        closeMenu();
                    }
                } else {
                    openMenu();
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (!isOpen) {
                    openMenu();
                } else {
                    highlightedIndex = (highlightedIndex + 1) % optionCount;
                    updateHighlightScroll();
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (!isOpen) {
                    openMenu();
                } else {
                    highlightedIndex = (highlightedIndex - 1 + optionCount) % optionCount;
                    updateHighlightScroll();
                }
            } else if (e.key === 'Home') {
                if (isOpen) {
                    e.preventDefault();
                    highlightedIndex = 0;
                    updateHighlightScroll();
                }
            } else if (e.key === 'End') {
                if (isOpen) {
                    e.preventDefault();
                    highlightedIndex = optionCount - 1;
                    updateHighlightScroll();
                }
            } else if (e.key === 'Escape') {
                if (isOpen) {
                    e.preventDefault();
                    e.stopPropagation();
                    closeMenu();
                    trigger.focus();
                }
            } else if (e.key === 'Tab') {
                if (isOpen) {
                    closeMenu();
                }
            } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
                // Type-ahead jump
                if (!isOpen) openMenu();
                clearTimeout(typeAheadTimer);
                typeAheadBuffer += e.key.toLowerCase();
                typeAheadTimer = setTimeout(() => { typeAheadBuffer = ''; }, 500);

                for (let i = 0; i < select.options.length; i++) {
                    const text = select.options[i].textContent.trim().toLowerCase();
                    if (text.startsWith(typeAheadBuffer)) {
                        highlightedIndex = i;
                        updateHighlightScroll();
                        break;
                    }
                }
            }
        });

        // Sync when native select is changed programmatically
        function syncFromNative() {
            const currentSelected = select.options[select.selectedIndex];
            if (currentSelected) {
                label.textContent = currentSelected.textContent.trim();
            }
            menu.querySelectorAll('.custom-select-option').forEach((el, idx) => {
                if (idx === select.selectedIndex) {
                    el.classList.add('is-selected');
                    el.setAttribute('aria-selected', 'true');
                } else {
                    el.classList.remove('is-selected');
                    el.removeAttribute('aria-selected');
                }
            });
        }

        select.addEventListener('change', syncFromNative);

        // Intercept programmatic value & selectedIndex setters on this select
        const proto = HTMLSelectElement.prototype;
        const valDesc = Object.getOwnPropertyDescriptor(proto, 'value');
        if (valDesc && valDesc.set) {
            Object.defineProperty(select, 'value', {
                get() {
                    return valDesc.get.call(this);
                },
                set(val) {
                    valDesc.set.call(this, val);
                    syncFromNative();
                },
                configurable: true
            });
        }

        const selIdxDesc = Object.getOwnPropertyDescriptor(proto, 'selectedIndex');
        if (selIdxDesc && selIdxDesc.set) {
            Object.defineProperty(select, 'selectedIndex', {
                get() {
                    return selIdxDesc.get.call(this);
                },
                set(idx) {
                    selIdxDesc.set.call(this, idx);
                    syncFromNative();
                },
                configurable: true
            });
        }

        // MutationObserver to update options if DOM children change
        const observer = new MutationObserver(() => {
            renderOptions();
            syncFromNative();
        });
        observer.observe(select, { childList: true, subtree: true });

        // Initial render
        renderOptions();
    });

    // Close any open custom select when clicking outside (registered once)
    if (!window._customSelectGlobalClickRegistered) {
        window._customSelectGlobalClickRegistered = true;
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.custom-select-wrapper')) {
                document.querySelectorAll('.custom-select-wrapper.is-open').forEach(w => {
                    w.classList.remove('is-open', 'drop-up');
                    const trg = w.querySelector('.custom-select-trigger');
                    if (trg) trg.setAttribute('aria-expanded', 'false');
                });
            }
        });
    }
}

/**
 * Custom Glassmorphic Datepicker Component
 * Enhances date range inputs (name="after" and name="before") with an interactive
 * calendar popover, month/year navigation, quick presets, and keyboard accessibility.
 */
function initCustomDatepicker() {
    const dateRanges = document.querySelectorAll('.date-range');
    if (!dateRanges.length) return;

    const MONTH_NAMES = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const WEEKDAY_NAMES = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

    dateRanges.forEach(rangeContainer => {
        const afterInput = rangeContainer.querySelector('input[name="after"]');
        const beforeInput = rangeContainer.querySelector('input[name="before"]');
        if (!afterInput || !beforeInput) return;

        // Prevent duplicate initialization
        if (rangeContainer.dataset.datepickerInit === 'true') return;
        rangeContainer.dataset.datepickerInit = 'true';

        // Wrap inputs in .date-input-wrapper if not already wrapped
        [afterInput, beforeInput].forEach(input => {
            if (!input.parentNode.classList.contains('date-input-wrapper')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'date-input-wrapper';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);

                const iconBtn = document.createElement('button');
                iconBtn.type = 'button';
                iconBtn.className = 'date-picker-icon-btn';
                iconBtn.title = 'Open date picker';
                iconBtn.setAttribute('aria-label', `Choose date for ${input.placeholder || 'date'}`);
                iconBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
                wrapper.appendChild(iconBtn);

                iconBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleDatepicker(input);
                });

                input.addEventListener('focus', () => {
                    openDatepicker(input);
                });
            }
        });

        // Create Shared Popover Element inside rangeContainer
        const popover = document.createElement('div');
        popover.className = 'custom-datepicker-popover';
        popover.setAttribute('role', 'dialog');
        popover.setAttribute('aria-modal', 'true');
        rangeContainer.appendChild(popover);

        let activeInput = null;
        let viewYear = new Date().getFullYear();
        let viewMonth = new Date().getMonth();
        let viewMode = 'days'; // 'days' or 'years'
        let yearGridStart = Math.floor(viewYear / 12) * 12;

        function parseInputDate(str) {
            if (!str) return null;
            const parts = str.trim().split('-');
            if (parts.length === 3) {
                const y = parseInt(parts[0], 10);
                const m = parseInt(parts[1], 10) - 1;
                const d = parseInt(parts[2], 10);
                if (!isNaN(y) && !isNaN(m) && !isNaN(d) && m >= 0 && m <= 11 && d >= 1 && d <= 31) {
                    return { year: y, month: m, day: d };
                }
            } else if (parts.length === 2) {
                const y = parseInt(parts[0], 10);
                const m = parseInt(parts[1], 10) - 1;
                if (!isNaN(y) && !isNaN(m) && m >= 0 && m <= 11) {
                    return { year: y, month: m, day: 1 };
                }
            } else if (parts.length === 1 && parts[0].length === 4) {
                const y = parseInt(parts[0], 10);
                if (!isNaN(y)) return { year: y, month: 0, day: 1 };
            }
            return null;
        }

        function formatDate(y, m, d) {
            const mm = String(m + 1).padStart(2, '0');
            const dd = String(d).padStart(2, '0');
            return `${y}-${mm}-${dd}`;
        }

        function renderCalendar() {
            popover.innerHTML = '';

            const today = new Date();
            const todayY = today.getFullYear();
            const todayM = today.getMonth();
            const todayD = today.getDate();
            const parsedCurrent = activeInput ? parseInputDate(activeInput.value) : null;

            // 1. Header
            const header = document.createElement('div');
            header.className = 'datepicker-header';

            if (viewMode === 'days') {
                // Left Navigation: Prev Year (<<) and Prev Month (<)
                const leftNav = document.createElement('div');
                leftNav.className = 'datepicker-nav-group';

                const prevYearBtn = document.createElement('button');
                prevYearBtn.type = 'button';
                prevYearBtn.className = 'datepicker-nav-btn btn-prev-year';
                prevYearBtn.title = 'Previous year';
                prevYearBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"></polyline><polyline points="18 17 13 12 18 7"></polyline></svg>`;
                prevYearBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    viewYear--;
                    renderCalendar();
                });

                const prevMonthBtn = document.createElement('button');
                prevMonthBtn.type = 'button';
                prevMonthBtn.className = 'datepicker-nav-btn btn-prev-month';
                prevMonthBtn.title = 'Previous month';
                prevMonthBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>`;
                prevMonthBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    viewMonth--;
                    if (viewMonth < 0) {
                        viewMonth = 11;
                        viewYear--;
                    }
                    renderCalendar();
                });

                leftNav.appendChild(prevYearBtn);
                leftNav.appendChild(prevMonthBtn);
                header.appendChild(leftNav);

                // Center Title: Month label + Clickable Year Button (opens year grid)
                const titleWrap = document.createElement('div');
                titleWrap.className = 'datepicker-title-wrap';

                const monthLabel = document.createElement('span');
                monthLabel.className = 'datepicker-month-label';
                monthLabel.textContent = MONTH_NAMES[viewMonth];

                const yearBtn = document.createElement('button');
                yearBtn.type = 'button';
                yearBtn.className = 'datepicker-year-btn';
                yearBtn.title = 'Click to switch year';
                yearBtn.innerHTML = `<span>${viewYear}</span><svg class="datepicker-year-chevron" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
                yearBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    yearGridStart = Math.floor(viewYear / 12) * 12;
                    viewMode = 'years';
                    renderCalendar();
                });

                titleWrap.appendChild(monthLabel);
                titleWrap.appendChild(yearBtn);
                header.appendChild(titleWrap);

                // Right Navigation: Next Month (>) and Next Year (>>)
                const rightNav = document.createElement('div');
                rightNav.className = 'datepicker-nav-group';

                const nextMonthBtn = document.createElement('button');
                nextMonthBtn.type = 'button';
                nextMonthBtn.className = 'datepicker-nav-btn btn-next-month';
                nextMonthBtn.title = 'Next month';
                nextMonthBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
                nextMonthBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    viewMonth++;
                    if (viewMonth > 11) {
                        viewMonth = 0;
                        viewYear++;
                    }
                    renderCalendar();
                });

                const nextYearBtn = document.createElement('button');
                nextYearBtn.type = 'button';
                nextYearBtn.className = 'datepicker-nav-btn btn-next-year';
                nextYearBtn.title = 'Next year';
                nextYearBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"></polyline><polyline points="6 17 11 12 6 7"></polyline></svg>`;
                nextYearBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    viewYear++;
                    renderCalendar();
                });

                rightNav.appendChild(nextMonthBtn);
                rightNav.appendChild(nextYearBtn);
                header.appendChild(rightNav);
                popover.appendChild(header);

                // 2. Weekdays
                const weekdaysRow = document.createElement('div');
                weekdaysRow.className = 'datepicker-weekdays';
                WEEKDAY_NAMES.forEach(w => {
                    const wCell = document.createElement('span');
                    wCell.className = 'datepicker-weekday';
                    wCell.textContent = w;
                    weekdaysRow.appendChild(wCell);
                });
                popover.appendChild(weekdaysRow);

                // 3. Days Grid
                const grid = document.createElement('div');
                grid.className = 'datepicker-days-grid';

                // Monday as first day of week
                const firstDayOfMonth = new Date(viewYear, viewMonth, 1).getDay();
                const startDayIndex = (firstDayOfMonth + 6) % 7;
                const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
                const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

                // Previous month days
                for (let i = startDayIndex - 1; i >= 0; i--) {
                    const dayNum = daysInPrevMonth - i;
                    const cell = document.createElement('button');
                    cell.type = 'button';
                    cell.className = 'datepicker-day-cell is-other-month';
                    cell.textContent = dayNum;
                    cell.addEventListener('click', (e) => {
                        e.stopPropagation();
                        let m = viewMonth - 1;
                        let y = viewYear;
                        if (m < 0) { m = 11; y--; }
                        selectDate(y, m, dayNum);
                    });
                    grid.appendChild(cell);
                }

                // Current month days
                for (let d = 1; d <= daysInMonth; d++) {
                    const cell = document.createElement('button');
                    cell.type = 'button';
                    cell.className = 'datepicker-day-cell';
                    cell.textContent = d;

                    if (viewYear === todayY && viewMonth === todayM && d === todayD) {
                        cell.classList.add('is-today');
                    }

                    if (parsedCurrent && parsedCurrent.year === viewYear && parsedCurrent.month === viewMonth && parsedCurrent.day === d) {
                        cell.classList.add('is-selected');
                    }

                    cell.addEventListener('click', (e) => {
                        e.stopPropagation();
                        selectDate(viewYear, viewMonth, d);
                    });

                    grid.appendChild(cell);
                }

                // Next month days
                const totalCells = startDayIndex + daysInMonth;
                const nextDaysNeeded = (totalCells > 35 ? 42 : 35) - totalCells;
                for (let n = 1; n <= nextDaysNeeded; n++) {
                    const cell = document.createElement('button');
                    cell.type = 'button';
                    cell.className = 'datepicker-day-cell is-other-month';
                    cell.textContent = n;
                    cell.addEventListener('click', (e) => {
                        e.stopPropagation();
                        let m = viewMonth + 1;
                        let y = viewYear;
                        if (m > 11) { m = 0; y++; }
                        selectDate(y, m, n);
                    });
                    grid.appendChild(cell);
                }

                popover.appendChild(grid);

            } else {
                // Year Selection Mode (12-year grid)
                const prevYearsBtn = document.createElement('button');
                prevYearsBtn.type = 'button';
                prevYearsBtn.className = 'datepicker-nav-btn';
                prevYearsBtn.title = 'Previous 12 years';
                prevYearsBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>`;
                prevYearsBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    yearGridStart -= 12;
                    renderCalendar();
                });

                const titleWrap = document.createElement('div');
                titleWrap.className = 'datepicker-title-wrap';

                const yearRangeBtn = document.createElement('button');
                yearRangeBtn.type = 'button';
                yearRangeBtn.className = 'datepicker-year-btn is-active';
                yearRangeBtn.title = 'Return to calendar days';
                yearRangeBtn.innerHTML = `<span>${yearGridStart} &ndash; ${yearGridStart + 11}</span><svg class="datepicker-year-chevron" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
                yearRangeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    viewMode = 'days';
                    renderCalendar();
                });

                titleWrap.appendChild(yearRangeBtn);

                const nextYearsBtn = document.createElement('button');
                nextYearsBtn.type = 'button';
                nextYearsBtn.className = 'datepicker-nav-btn';
                nextYearsBtn.title = 'Next 12 years';
                nextYearsBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
                nextYearsBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    yearGridStart += 12;
                    renderCalendar();
                });

                header.appendChild(prevYearsBtn);
                header.appendChild(titleWrap);
                header.appendChild(nextYearsBtn);
                popover.appendChild(header);

                // Years Grid (4 columns x 3 rows)
                const yearsGrid = document.createElement('div');
                yearsGrid.className = 'datepicker-years-grid';

                for (let y = yearGridStart; y < yearGridStart + 12; y++) {
                    const yCell = document.createElement('button');
                    yCell.type = 'button';
                    yCell.className = 'datepicker-year-cell';
                    yCell.textContent = y;

                    if (y === todayY) {
                        yCell.classList.add('is-today');
                    }
                    if (y === viewYear) {
                        yCell.classList.add('is-selected');
                    }

                    yCell.addEventListener('click', (e) => {
                        e.stopPropagation();
                        viewYear = y;
                        viewMode = 'days';
                        renderCalendar();
                    });

                    yearsGrid.appendChild(yCell);
                }

                popover.appendChild(yearsGrid);
            }

            // 4. Quick Presets Row
            const presetsRow = document.createElement('div');
            presetsRow.className = 'datepicker-presets-row';

            const presets = [
                {
                    label: 'Today',
                    apply: () => {
                        const t = new Date();
                        const str = formatDate(t.getFullYear(), t.getMonth(), t.getDate());
                        if (activeInput) {
                            activeInput.value = str;
                            activeInput.dispatchEvent(new Event('input', { bubbles: true }));
                            activeInput.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        closeDatepicker();
                    }
                },
                {
                    label: 'Past 7 Days',
                    apply: () => {
                        const now = new Date();
                        const past = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        afterInput.value = formatDate(past.getFullYear(), past.getMonth(), past.getDate());
                        beforeInput.value = formatDate(now.getFullYear(), now.getMonth(), now.getDate());
                        [afterInput, beforeInput].forEach(inp => {
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        });
                        closeDatepicker();
                    }
                },
                {
                    label: 'Past 30 Days',
                    apply: () => {
                        const now = new Date();
                        const past = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                        afterInput.value = formatDate(past.getFullYear(), past.getMonth(), past.getDate());
                        beforeInput.value = formatDate(now.getFullYear(), now.getMonth(), now.getDate());
                        [afterInput, beforeInput].forEach(inp => {
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        });
                        closeDatepicker();
                    }
                },
                {
                    label: 'This Year',
                    apply: () => {
                        const y = new Date().getFullYear();
                        afterInput.value = `${y}-01-01`;
                        beforeInput.value = `${y}-12-31`;
                        [afterInput, beforeInput].forEach(inp => {
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        });
                        closeDatepicker();
                    }
                },
                {
                    label: 'Last Year',
                    apply: () => {
                        const y = new Date().getFullYear() - 1;
                        afterInput.value = `${y}-01-01`;
                        beforeInput.value = `${y}-12-31`;
                        [afterInput, beforeInput].forEach(inp => {
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        });
                        closeDatepicker();
                    }
                }
            ];

            presets.forEach(p => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'datepicker-preset-btn';
                btn.textContent = p.label;
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    p.apply();
                });
                presetsRow.appendChild(btn);
            });
            popover.appendChild(presetsRow);

            // 5. Footer Actions (Clear, Close)
            const footer = document.createElement('div');
            footer.className = 'datepicker-footer-actions';

            const clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = 'datepicker-action-btn datepicker-btn-clear';
            clearBtn.textContent = 'Clear Field';
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (activeInput) {
                    activeInput.value = '';
                    activeInput.dispatchEvent(new Event('input', { bubbles: true }));
                    activeInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
                closeDatepicker();
            });

            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'datepicker-action-btn datepicker-btn-close';
            closeBtn.textContent = 'Close';
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDatepicker();
            });

            footer.appendChild(clearBtn);
            footer.appendChild(closeBtn);
            popover.appendChild(footer);
        }

        function selectDate(y, m, d) {
            if (!activeInput) return;
            const str = formatDate(y, m, d);
            activeInput.value = str;
            activeInput.dispatchEvent(new Event('input', { bubbles: true }));
            activeInput.dispatchEvent(new Event('change', { bubbles: true }));
            closeDatepicker();
            activeInput.focus();
        }

        function openDatepicker(input) {
            // Close any custom select dropdowns
            document.querySelectorAll('.custom-select-wrapper.is-open').forEach(w => {
                w.classList.remove('is-open', 'drop-up');
            });

            activeInput = input;
            viewMode = 'days';
            const parsed = parseInputDate(input.value);
            if (parsed) {
                viewYear = parsed.year;
                viewMonth = parsed.month;
            } else {
                const now = new Date();
                viewYear = now.getFullYear();
                viewMonth = now.getMonth();
            }

            // Position relative to input wrapper
            const inputWrapper = input.closest('.date-input-wrapper');
            const rangeRect = rangeContainer.getBoundingClientRect();
            const wrapperRect = inputWrapper ? inputWrapper.getBoundingClientRect() : rangeRect;

            const offsetLeft = wrapperRect.left - rangeRect.left;
            popover.style.left = `${Math.max(0, offsetLeft)}px`;

            if (offsetLeft + 320 > rangeRect.width) {
                popover.style.left = 'auto';
                popover.style.right = '0px';
            } else {
                popover.style.right = 'auto';
            }

            const spaceBelow = window.innerHeight - wrapperRect.bottom;
            if (spaceBelow < 340 && wrapperRect.top > 340) {
                popover.classList.add('drop-up');
            } else {
                popover.classList.remove('drop-up');
            }

            renderCalendar();
            popover.classList.add('is-open');
        }

        function closeDatepicker() {
            popover.classList.remove('is-open', 'drop-up');
            activeInput = null;
            viewMode = 'days';
        }

        function toggleDatepicker(input) {
            if (popover.classList.contains('is-open') && activeInput === input) {
                closeDatepicker();
            } else {
                openDatepicker(input);
            }
        }
    });

    // Close on click outside (registered once globally)
    if (!window._datepickerGlobalClickRegistered) {
        window._datepickerGlobalClickRegistered = true;
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.date-range') && !e.target.closest('.custom-datepicker-popover')) {
                document.querySelectorAll('.custom-datepicker-popover.is-open').forEach(p => {
                    p.classList.remove('is-open', 'drop-up');
                });
            }
        });
    }
}



