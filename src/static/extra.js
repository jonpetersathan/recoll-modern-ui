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

    // Initialize Global Themed Dialogs & Footer Index Status
    initAppDialogs();
    initFooterIndexStatus();

    // Initialize Advanced Search Panel, Settings Form Manager, Files Download, Custom Selects, & Datepicker
    initAdvancedSearch();
    initSettingsFormManager();
    initFilesDownload();
    initCustomSelects();
    initCustomDatepicker();
    initMainQueryEditor();
    initIndexConfig();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRecollApp);
} else {
    initRecollApp();
}

/**
 * Themed Application Confirmation & Alert Dialogs
 */
let _appDialogResolve = null;

function initAppDialogs() {
    const overlay = document.getElementById('app-dialog-overlay');
    if (!overlay) return;

    const btnConfirm = document.getElementById('btn-confirm-app-dialog');
    const btnCancel = document.getElementById('btn-cancel-app-dialog');
    const btnClose = document.getElementById('btn-close-app-dialog');

    function closeDialog(result) {
        overlay.style.display = 'none';
        if (_appDialogResolve) {
            const resolve = _appDialogResolve;
            _appDialogResolve = null;
            resolve(result);
        }
    }

    if (btnConfirm) {
        btnConfirm.onclick = () => closeDialog(true);
    }
    if (btnCancel) {
        btnCancel.onclick = () => closeDialog(false);
    }
    if (btnClose) {
        btnClose.onclick = () => closeDialog(false);
    }

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            closeDialog(false);
        }
    };

    document.addEventListener('keydown', (e) => {
        if (overlay.style.display === 'flex') {
            if (e.key === 'Escape') {
                e.preventDefault();
                closeDialog(false);
            } else if (e.key === 'Enter' && !['TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                closeDialog(true);
            }
        }
    });
}

window.showConfirmModal = function(options = {}) {
    const overlay = document.getElementById('app-dialog-overlay');
    if (!overlay) {
        return Promise.resolve(confirm(options.message || 'Are you sure?'));
    }

    const titleEl = document.getElementById('app-dialog-title');
    const messageEl = document.getElementById('app-dialog-message');
    const iconEl = document.getElementById('app-dialog-icon');
    const btnConfirm = document.getElementById('btn-confirm-app-dialog');
    const btnCancel = document.getElementById('btn-cancel-app-dialog');

    if (titleEl) titleEl.textContent = options.title || 'Confirm Action';
    if (messageEl) messageEl.textContent = options.message || '';
    if (btnCancel) {
        btnCancel.style.display = 'inline-flex';
        btnCancel.textContent = options.cancelText || 'Cancel';
    }
    if (btnConfirm) {
        btnConfirm.textContent = options.confirmText || 'Confirm';
        btnConfirm.className = options.isDanger ? 'btn btn-danger' : 'btn btn-primary';
    }

    if (iconEl) {
        if (options.isDanger) {
            iconEl.innerHTML = '<svg class="dialog-icon-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
        } else {
            iconEl.innerHTML = '<svg class="dialog-icon-info" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
        }
    }

    overlay.style.display = 'flex';
    if (btnConfirm) btnConfirm.focus();

    return new Promise((resolve) => {
        _appDialogResolve = resolve;
    });
};

window.showAlertModal = function(options = {}) {
    const overlay = document.getElementById('app-dialog-overlay');
    const opts = typeof options === 'string' ? { message: options } : options;

    if (!overlay) {
        alert(opts.message || '');
        return Promise.resolve();
    }

    const titleEl = document.getElementById('app-dialog-title');
    const messageEl = document.getElementById('app-dialog-message');
    const iconEl = document.getElementById('app-dialog-icon');
    const btnConfirm = document.getElementById('btn-confirm-app-dialog');
    const btnCancel = document.getElementById('btn-cancel-app-dialog');

    if (titleEl) titleEl.textContent = opts.title || 'Notice';
    if (messageEl) messageEl.textContent = opts.message || '';
    if (btnCancel) btnCancel.style.display = 'none';
    if (btnConfirm) {
        btnConfirm.textContent = opts.okText || 'OK';
        btnConfirm.className = (opts.type === 'danger' || opts.type === 'error') ? 'btn btn-danger' : 'btn btn-primary';
    }

    if (iconEl) {
        if (opts.type === 'danger' || opts.type === 'error') {
            iconEl.innerHTML = '<svg class="dialog-icon-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
        } else if (opts.type === 'warning') {
            iconEl.innerHTML = '<svg class="dialog-icon-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
        } else if (opts.type === 'success') {
            iconEl.innerHTML = '<svg class="dialog-icon-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        } else {
            iconEl.innerHTML = '<svg class="dialog-icon-info" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
        }
    }

    overlay.style.display = 'flex';
    if (btnConfirm) btnConfirm.focus();

    return new Promise((resolve) => {
        _appDialogResolve = resolve;
    });
};

/**
 * Global Real-Time Footer Index Status
 */
window.updateFooterIndexBadge = function(statusInfo) {
    const badge = document.getElementById('footer-index-badge');
    if (!badge || !statusInfo) return;

    badge.classList.remove('status-ready', 'status-indexing', 'status-updating', 'status-creating', 'status-empty', 'status-error', 'status-no-index');

    const job = statusInfo.job || {};
    const status = statusInfo.status || job.status || 'idle';
    const isRunning = status === 'running';
    const exists = statusInfo.exists !== false && statusInfo.exists !== 0 && statusInfo.exists != null;

    if (isRunning) {
        if (job.mode === 'full' || !exists) {
            badge.textContent = 'Creating Index';
            badge.title = 'Full search index creation in progress';
            badge.classList.add('status-creating');
        } else {
            badge.textContent = 'Updating Index';
            badge.title = 'Incremental search index update in progress';
            badge.classList.add('status-indexing', 'status-updating');
        }
    } else if (!exists) {
        badge.textContent = 'No index';
        badge.title = 'No search index found. Indexing required.';
        badge.classList.add('status-error', 'status-no-index');
    } else {
        badge.textContent = 'Index Ready';
        const docCount = Number(statusInfo.doc_count) || 0;
        const countStr = docCount.toLocaleString();
        const lastSync = statusInfo.last_indexed ? ` | Last sync: ${statusInfo.last_indexed}` : '';
        badge.title = `Search index ready (${countStr} documents${lastSync})`;
        badge.classList.add('status-ready');
    }
};

function initFooterIndexStatus() {
    const badge = document.getElementById('footer-index-badge');
    if (!badge) return;

    let pollTimer = null;

    async function checkStatus() {
        try {
            const resp = await fetch('/api/index/status');
            if (!resp.ok) return;
            const data = await resp.json();
            window.updateFooterIndexBadge(data);

            if (data.status === 'running') {
                if (!pollTimer) {
                    pollTimer = setInterval(checkStatus, 3000);
                }
            } else if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
        } catch (err) {
            // Non-blocking network status check
        }
    }

    checkStatus();
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
        window.showAlertModal({
            title: 'OpenSearch Provider',
            message: 'OpenSearch plugins can be added automatically from your browser address bar.',
            type: 'info'
        });
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
window.safeStorageGet = safeStorageGet;

function safeStorageSet(type, key, val) {
    try {
        if (window[type]) window[type].setItem(key, val);
    } catch (_) {}
}
window.safeStorageSet = safeStorageSet;

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

    const rawForms = getStoredForms();
    let forms = rawForms.filter(f => f.enabled !== false);
    if (forms.length === 0 && rawForms.length > 0) {
        forms = [rawForms[0]];
    }
    const formSelector = document.getElementById('active-form-selector');
    const fieldsContainer = document.getElementById('advanced-fields-container');
    const previewEl = document.getElementById('advanced-query-preview');
    const searchForm = document.getElementById('search-form');
    const mainQueryInput = document.querySelector('input[name="query"]');
    let userEditedMainQuery = false;

    if (mainQueryInput) {
        mainQueryInput.addEventListener('input', () => {
            userEditedMainQuery = true;
        });
        mainQueryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const isPanelOpen = panel && panel.style.display !== 'none';
                if (isPanelOpen) {
                    userEditedMainQuery = true;
                }
            }
        });
    }

    // Toggle panel visibility
    function setPanelVisibility(show) {
        panel.style.display = show ? 'block' : 'none';
        toggleBtn.classList.toggle('active', show);
        toggleBtn.setAttribute('aria-expanded', show ? 'true' : 'false');
        safeStorageSet('sessionStorage', 'recoll_adv_open', show ? '1' : '0');
        if (show) {
            userEditedMainQuery = false;
        }
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
            if (field.enabled === false) {
                return;
            }
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
                userEditedMainQuery = false;
                saveActiveFormValues();
                updateCompiledQuery();
            });
            input.addEventListener('change', () => {
                userEditedMainQuery = false;
                saveActiveFormValues();
                updateCompiledQuery();
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    userEditedMainQuery = false;
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
        userEditedMainQuery = false;
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
            const isPanelOpen = panel && panel.style.display !== 'none';
            const isEditingMain = userEditedMainQuery || (document.activeElement === mainQueryInput);

            if (isPanelOpen && isEditingMain) {
                // User manually edited the search field and pressed search/enter:
                // Do not overwrite mainQueryInput with advanced form query, collapse advanced search, and persist
                setPanelVisibility(false);
                safeStorageSet('sessionStorage', 'recoll_adv_open', '0');
            } else if (isPanelOpen) {
                saveActiveFormValues();
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
        // Populate options in formSelector to match active enabled forms
        formSelector.innerHTML = '';
        forms.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.id === 'default'
                ? 'Advanced (Default / Read-Only)'
                : (f.readonly ? `${f.name} (Default / Read-Only)` : f.name);
            formSelector.appendChild(opt);
        });

        // Restore last selected form
        const savedFormId = safeStorageGet('localStorage', 'recoll_active_form_id');
        if (savedFormId && forms.some(f => f.id === savedFormId)) {
            formSelector.value = savedFormId;
            renderActiveForm(savedFormId);
        } else if (forms.length > 0) {
            renderActiveForm(forms[0].id);
        }

        formSelector.addEventListener('change', () => {
            userEditedMainQuery = false;
            saveActiveFormValues();
            const formId = formSelector.value;
            safeStorageSet('localStorage', 'recoll_active_form_id', formId);
            renderActiveForm(formId);
        });
    }

    const resetBtn = document.getElementById('btn-reset-query') || document.querySelector('a[title="Reset Search Query"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            userEditedMainQuery = false;
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
        if (field.enabled === false) return;
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
                const textPrefixes = [
                    'filename:', 'fn:', 'containerfilename:', 'cfn:',
                    'title:', 'subject:', 'caption:',
                    'author:', 'from:', 'creator:',
                    'recipient:', 'to:',
                    'abstract:', 'summary:', 'description:',
                    'keyword:', 'keywords:', 'tag:', 'tags:',
                    'annotation:', 'annot:', 'pa:',
                    'dir:'
                ];
                if (val.includes(' ') && !val.startsWith('"') && !val.endsWith('"') &&
                    (textPrefixes.some(pfx => fmt.startsWith(pfx)))) {
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
    { value: 'application/vnd.ms-outlook', desc: 'Outlook Message / Store (*.msg, *.pst)' },
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
    { value: 'msg', desc: 'Outlook Message (*.msg)' },
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
    // MIME / File Type filters
    { prefix: 'mime:', placeholder: 'type', desc: 'MIME type filter', hasSub: true, insertPrefix: 'mime:', aliases: ['mimetype', 'mtype', 'contenttype'] },
    { prefix: 'filetype:', placeholder: 'type', desc: 'File type filter (alias for mime:)', hasSub: true, insertPrefix: 'mime:', aliases: ['mimetype', 'mtype', 'contenttype'] },

    // File Extensions
    { prefix: 'ext:', placeholder: 'extension', desc: 'File extension filter (alias: fileextension:)', hasSub: true, insertPrefix: 'ext:', aliases: ['fileextension'] },

    // Path & Filename
    { prefix: 'dir:', placeholder: 'path', desc: 'Restrict search to folder path', insertPrefix: 'dir:' },
    { prefix: 'filename:', placeholder: 'pattern', desc: 'Filename match with optional wildcards (alias: fn:)', insertPrefix: 'filename:', aliases: ['fn'] },
    { prefix: 'containerfilename:', placeholder: 'pattern', desc: 'Container / archive inner file name (alias: cfn:)', insertPrefix: 'containerfilename:', aliases: ['cfn'] },

    // Title / Subject / Caption
    { prefix: 'title:', placeholder: 'text', desc: 'Document title metadata field search', insertPrefix: 'title:' },
    { prefix: 'subject:', placeholder: 'text', desc: 'Email subject / document title search', insertPrefix: 'subject:' },
    { prefix: 'caption:', placeholder: 'text', desc: 'Document title / caption search (alias)', insertPrefix: 'caption:' },

    // Author / Sender / Creator
    { prefix: 'author:', placeholder: 'name', desc: 'Author / creator metadata search', insertPrefix: 'author:' },
    { prefix: 'from:', placeholder: 'name/email', desc: 'Email sender / author search', insertPrefix: 'from:' },
    { prefix: 'creator:', placeholder: 'name', desc: 'Document creator / author search (alias)', insertPrefix: 'creator:' },

    // Recipient
    { prefix: 'recipient:', placeholder: 'email/name', desc: 'Email recipient search (To/Cc)', insertPrefix: 'recipient:' },
    { prefix: 'to:', placeholder: 'email/name', desc: 'Email recipient search alias', insertPrefix: 'to:' },

    // Keywords & Tags
    { prefix: 'tag:', placeholder: 'keyword', desc: 'Document category or tag keyword', insertPrefix: 'tag:', aliases: ['tags'] },
    { prefix: 'keyword:', placeholder: 'word', desc: 'Document keyword search', insertPrefix: 'keyword:', aliases: ['keywords'] },

    // Abstract / Summary / Description
    { prefix: 'abstract:', placeholder: 'text', desc: 'Document abstract / summary search', insertPrefix: 'abstract:' },
    { prefix: 'summary:', placeholder: 'text', desc: 'Document summary search (alias for abstract:)', insertPrefix: 'summary:' },
    { prefix: 'description:', placeholder: 'text', desc: 'Document description search (alias for abstract:)', insertPrefix: 'description:' },

    // Annotation
    { prefix: 'annotation:', placeholder: 'text', desc: 'PDF annotation / comment search', insertPrefix: 'annotation:' },
    { prefix: 'annot:', placeholder: 'text', desc: 'PDF annotation search (alias for annotation:)', insertPrefix: 'annot:' },

    // Size & Date
    { prefix: 'size:', placeholder: 'comparison', desc: 'File size threshold', hasSub: true, insertPrefix: 'size:' },
    { prefix: 'date:', placeholder: 'range', desc: 'Date range filter (YYYY-MM-DD/YYYY-MM-DD)', insertPrefix: 'date:' },

    // Boolean Operators
    { prefix: 'AND', placeholder: '', desc: 'Boolean AND operator', insertPrefix: 'AND ', isBool: true },
    { prefix: 'OR', placeholder: '', desc: 'Boolean OR operator', insertPrefix: 'OR ', isBool: true },
    { prefix: 'NOT', placeholder: '', desc: 'Boolean NOT operator', insertPrefix: 'NOT ', isBool: true },
    { prefix: 'XOR', placeholder: '', desc: 'Boolean XOR operator', insertPrefix: 'XOR ', isBool: true },

    // Modifiers & Punctuation
    { prefix: '-', placeholder: 'term', desc: 'Negation prefix to exclude term', insertPrefix: '-', isOp: true },
    { prefix: '+', placeholder: 'term', desc: 'Inclusion prefix to require term', insertPrefix: '+', isOp: true },
    { prefix: '(', placeholder: 'clause', suffix: ')', desc: 'Parenthesize sub-conditions', insertPrefix: '(', isOp: true },
    { prefix: '"', placeholder: 'phrase', suffix: '"', desc: 'Exact phrase search', insertPrefix: '""', isOp: true },
    { prefix: 'pN', placeholder: 'N', desc: 'Proximity slack operator (within N words)', insertPrefix: 'pN', isOp: true }
];

// Text Input field specific patterns (using {value} as user input placeholder)
const TEXT_SNIPPET_PATTERNS = [
    { prefix: '{value}', placeholder: '', desc: 'Match all entered words (AND)', insertPrefix: '{value}' },
    { prefix: '*{value}*', placeholder: '', desc: 'Wildcard partial match with user input', insertPrefix: '*{value}*' },
    { prefix: '"{value}"', placeholder: '', desc: 'Match terms in exact order', insertPrefix: '"{value}"' },
    { prefix: '"{value}"pN', placeholder: '', desc: 'Match terms within N words (proximity)', insertPrefix: '"{value}"pN' },

    // Filename & Containers
    { prefix: 'filename:{value}', placeholder: '', desc: 'Filename exact match with user input', insertPrefix: 'filename:{value}', aliases: ['fn'] },
    { prefix: 'filename:*{value}*', placeholder: '', desc: 'Filename wildcard / partial search with user input', insertPrefix: 'filename:*{value}*', aliases: ['fn'] },
    { prefix: 'containerfilename:{value}', placeholder: '', desc: 'Container / archive inner file name match', insertPrefix: 'containerfilename:{value}', aliases: ['cfn'] },
    { prefix: 'containerfilename:*{value}*', placeholder: '', desc: 'Container / archive inner file name wildcard search', insertPrefix: 'containerfilename:*{value}*', aliases: ['cfn'] },

    // Title / Subject / Caption
    { prefix: 'title:{value}', placeholder: '', desc: 'Document title metadata search with user input', insertPrefix: 'title:{value}' },
    { prefix: 'title:*{value}*', placeholder: '', desc: 'Document title wildcard / partial search with user input', insertPrefix: 'title:*{value}*' },
    { prefix: 'subject:{value}', placeholder: '', desc: 'Email subject search with user input', insertPrefix: 'subject:{value}' },
    { prefix: 'subject:*{value}*', placeholder: '', desc: 'Email subject wildcard / partial search with user input', insertPrefix: 'subject:*{value}*' },
    { prefix: 'caption:{value}', placeholder: '', desc: 'Document caption search with user input', insertPrefix: 'caption:{value}' },
    { prefix: 'caption:*{value}*', placeholder: '', desc: 'Document caption wildcard / partial search with user input', insertPrefix: 'caption:*{value}*' },

    // Author / Sender / Recipient / Creator
    { prefix: 'author:{value}', placeholder: '', desc: 'Author / creator search with user input', insertPrefix: 'author:{value}' },
    { prefix: 'author:*{value}*', placeholder: '', desc: 'Author / creator wildcard / partial search with user input', insertPrefix: 'author:*{value}*' },
    { prefix: 'from:{value}', placeholder: '', desc: 'Email sender search with user input', insertPrefix: 'from:{value}' },
    { prefix: 'from:*{value}*', placeholder: '', desc: 'Email sender wildcard / partial search with user input', insertPrefix: 'from:*{value}*' },
    { prefix: 'creator:{value}', placeholder: '', desc: 'Document creator search with user input', insertPrefix: 'creator:{value}' },
    { prefix: 'creator:*{value}*', placeholder: '', desc: 'Document creator wildcard / partial search with user input', insertPrefix: 'creator:*{value}*' },
    { prefix: 'recipient:{value}', placeholder: '', desc: 'Email recipient search with user input', insertPrefix: 'recipient:{value}' },
    { prefix: 'recipient:*{value}*', placeholder: '', desc: 'Email recipient wildcard / partial search with user input', insertPrefix: 'recipient:*{value}*' },
    { prefix: 'to:{value}', placeholder: '', desc: 'Email recipient search with user input', insertPrefix: 'to:{value}' },
    { prefix: 'to:*{value}*', placeholder: '', desc: 'Email recipient wildcard / partial search with user input', insertPrefix: 'to:*{value}*' },

    // Folder Scope
    { prefix: 'dir:"{value}"', placeholder: '', desc: 'Directory Scope with user input', insertPrefix: 'dir:"{value}"' },
    { prefix: 'dir:*{value}*', placeholder: '', desc: 'Directory Scope wildcard search with user input', insertPrefix: 'dir:*{value}*' },

    // Extension / Format / MIME
    { prefix: 'ext:{value}', placeholder: '', desc: 'File extension match with user input', insertPrefix: 'ext:{value}', aliases: ['fileextension'] },
    { prefix: 'ext:*{value}*', placeholder: '', desc: 'File extension wildcard match with user input', insertPrefix: 'ext:*{value}*', aliases: ['fileextension'] },
    { prefix: 'mime:{value}', placeholder: '', desc: 'MIME type filter with user input', insertPrefix: 'mime:{value}', aliases: ['mimetype', 'mtype', 'contenttype'] },
    { prefix: 'mime:*{value}*', placeholder: '', desc: 'MIME type wildcard filter with user input', insertPrefix: 'mime:*{value}*', aliases: ['mimetype', 'mtype', 'contenttype'] },
    { prefix: 'filetype:{value}', placeholder: '', desc: 'File format filter with user input', insertPrefix: 'filetype:{value}' },
    { prefix: 'filetype:*{value}*', placeholder: '', desc: 'File format wildcard filter with user input', insertPrefix: 'filetype:*{value}*' },

    // Tags & Keywords
    { prefix: 'tag:{value}', placeholder: '', desc: 'Document tag search with user input', insertPrefix: 'tag:{value}', aliases: ['tags'] },
    { prefix: 'tag:*{value}*', placeholder: '', desc: 'Document tag wildcard search with user input', insertPrefix: 'tag:*{value}', aliases: ['tags'] },
    { prefix: 'keyword:{value}', placeholder: '', desc: 'Document keyword search with user input', insertPrefix: 'keyword:{value}', aliases: ['keywords'] },
    { prefix: 'keyword:*{value}*', placeholder: '', desc: 'Document keyword wildcard search with user input', insertPrefix: 'keyword:*{value}*', aliases: ['keywords'] },

    // Abstract, Summary, Description
    { prefix: 'abstract:{value}', placeholder: '', desc: 'Document abstract search with user input', insertPrefix: 'abstract:{value}' },
    { prefix: 'abstract:*{value}*', placeholder: '', desc: 'Document abstract wildcard search with user input', insertPrefix: 'abstract:*{value}*' },
    { prefix: 'summary:{value}', placeholder: '', desc: 'Document summary search with user input', insertPrefix: 'summary:{value}' },
    { prefix: 'summary:*{value}*', placeholder: '', desc: 'Document summary wildcard search with user input', insertPrefix: 'summary:*{value}*' },
    { prefix: 'description:{value}', placeholder: '', desc: 'Document description search with user input', insertPrefix: 'description:{value}' },
    { prefix: 'description:*{value}*', placeholder: '', desc: 'Document description wildcard search with user input', insertPrefix: 'description:*{value}*' },

    // Annotations
    { prefix: 'annotation:{value}', placeholder: '', desc: 'PDF annotation search with user input', insertPrefix: 'annotation:{value}', aliases: ['annot', 'pa', 'pdfannot'] },
    { prefix: 'annotation:*{value}*', placeholder: '', desc: 'PDF annotation wildcard search with user input', insertPrefix: 'annotation:*{value}*', aliases: ['annot', 'pa', 'pdfannot'] },

    // Size & Date
    { prefix: 'size>{value}', placeholder: '', desc: 'Minimum file size threshold with user input', insertPrefix: 'size>{value}' },
    { prefix: 'size<{value}', placeholder: '', desc: 'Maximum file size threshold with user input', insertPrefix: 'size<{value}' },
    { prefix: 'date:{value}', placeholder: '', desc: 'Date range filter with user input', insertPrefix: 'date:{value}' },

    // Inclusions & Exclusions
    { prefix: '-{value}', placeholder: '', desc: 'Exclusion / NOT operator with user input', insertPrefix: '-{value}' },
    { prefix: '-*{value}*', placeholder: '', desc: 'Wildcard exclusion operator with user input', insertPrefix: '-*{value}*' },
    { prefix: '+{value}', placeholder: '', desc: 'Mandatory / inclusion operator with user input', insertPrefix: '+{value}' },
    { prefix: '+*{value}*', placeholder: '', desc: 'Wildcard mandatory operator with user input', insertPrefix: '+*{value}*' }
];

function highlightQuerySyntax(raw) {
    if (!raw) return '';
    const escaped = raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 1: {value} placeholder
    // 2: proximity parameter pN with placeholder N: \bp[Nn]\b
    // 3: boolean operators: AND, OR, NOT, XOR
    // 4: keywords: all canonical fields & aliases, or any custom field name preceding a colon (or size with </>/colons)
    // 5: operators: * , / : ( ) " - + ? &gt; &lt; or p\d+
    // 6: literal strings / words
    const tokenRegex = /(\{value\})|(\bp[Nn]\b)|(\b(?:AND|OR|NOT|XOR)\b)|(\bsize(?=[:<>]|&gt;|&lt;)|(?:\b(?:filename|fn|containerfilename|cfn|title|subject|caption|author|creator|from|recipient|to|mime|mimetype|contenttype|mtype|filetype|ext|fileextension|dir|date|keyword|keywords|tag|tags|abstract|summary|description|annotation|annot|pa|pdfannot|[a-zA-Z_][a-zA-Z0-9_-]*)(?=:)))|([*:,/()"\-+?]|&gt;|&lt;|\bp\d+\b)|([^\s*:,/()"\-+?&{}]+)/g;

    return escaped.replace(tokenRegex, (match, valPh, proxN, boolOp, kw, op, word) => {
        if (valPh) {
            return `<span class="tok-val">${valPh}</span>`;
        } else if (proxN) {
            return `<span class="tok-op">p</span><span class="param-placeholder">${proxN.slice(1)}</span>`;
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

function scoreKeywordItem(item, q, contextType = 'general') {
    if (!q) return 0;
    const rawPrefix = item.prefix.toLowerCase();
    const prefixClean = rawPrefix.replace(/[:(]/g, '');
    const full = (item.prefix + (item.placeholder || '') + (item.suffix || '')).toLowerCase();
    const desc = (item.desc || '').toLowerCase();
    const cleanQ = q.replace(/[:(]/g, '').trim();

    // Prioritize {value} and *{value}* patterns in text context (form field query format editor)
    if (contextType === 'text') {
        if (cleanQ && (rawPrefix.startsWith(cleanQ + ':{value}') || rawPrefix === cleanQ + ':{value}')) {
            return 0.01;
        }
        if (cleanQ && (rawPrefix.startsWith(cleanQ + ':*{value}*') || rawPrefix === cleanQ + ':*{value}*')) {
            return 0.02;
        }
        if (cleanQ === 'value') {
            if (rawPrefix === '{value}') return 0.01;
            if (rawPrefix === '*{value}*') return 0.02;
        }
    }

    // Tier 0: exact keyword match (e.g. 'or' === 'or', 'and' === 'and', 'mime' === 'mime')
    if (rawPrefix === 'pn' && (/^p\d+$/i.test(q) || q === 'p' || q === 'pn')) {
        return 0.1;
    }
    if (prefixClean === q || rawPrefix === q || rawPrefix === q + ':') {
        return (contextType === 'text' && !rawPrefix.includes('{value}')) ? 0.3 : 0;
    }

    // Tier 0.5: exact alias match (e.g. 'fn' -> 'filename:', 'cfn' -> 'containerfilename:', 'fileextension' -> 'ext:', 'mimetype' -> 'mime:')
    if (item.aliases && Array.isArray(item.aliases)) {
        for (const a of item.aliases) {
            const alias = a.toLowerCase();
            if (alias === cleanQ || alias === q || (alias + ':') === q) {
                if (contextType === 'text' && rawPrefix.includes('{value}')) {
                    return rawPrefix.includes('*{value}*') ? 0.06 : 0.05;
                }
                return 1;
            }
        }
    }

    // Tier 1: keyword starts with query (e.g. 'fil' -> 'filename', 'or' -> 'order')
    if (prefixClean.startsWith(q) || rawPrefix.startsWith(q) || (cleanQ && prefixClean.startsWith(cleanQ))) {
        return 10 + (prefixClean.length - q.length);
    }

    // Tier 1.5: alias starts with query (e.g. 'fileext' -> 'fileextension' -> 'ext:')
    if (item.aliases && Array.isArray(item.aliases)) {
        for (const a of item.aliases) {
            const alias = a.toLowerCase();
            if ((cleanQ && alias.startsWith(cleanQ)) || alias.startsWith(q)) {
                return 15 + (alias.length - cleanQ.length);
            }
        }
    }

    // Tier 2: full snippet starts with query (e.g. '{val' -> '{value}')
    if (full.startsWith(q) || (cleanQ && full.startsWith(cleanQ))) {
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

        // 1. Secondary: mime: or filetype: or aliases
        const mimePrefixes = ['mime:', 'filetype:', 'mimetype:', 'mtype:', 'contenttype:'];
        const matchedMime = mimePrefixes.find(p => tokenLower.startsWith(p));
        if (matchedMime) {
            const query = tokenBeforeCursor.slice(matchedMime.length).toLowerCase();
            const scored = MIME_TYPES_LIST.map((m, idx) => ({
                item: m,
                idx,
                score: scoreSecondaryItem(m.value, m.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: m }) => ({
                badgeHtml: `<span class="tok-kw">${escapeHtml(matchedMime.replace(':', ''))}</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(m.value)}</span>`,
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

        // 2. Secondary: ext: or fileextension:
        const extPrefixes = ['ext:', 'fileextension:'];
        const matchedExt = extPrefixes.find(p => tokenLower.startsWith(p));
        if (matchedExt) {
            const query = tokenBeforeCursor.slice(matchedExt.length).toLowerCase();
            const scored = EXTENSIONS_LIST.map((e, idx) => ({
                item: e,
                idx,
                score: scoreSecondaryItem(e.value, e.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: e }) => ({
                badgeHtml: `<span class="tok-kw">${escapeHtml(matchedExt.replace(':', ''))}</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(e.value)}</span>`,
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

        // 3. Secondary: size: or size< or size>
        const sizePrefixes = ['size:', 'size<', 'size>'];
        const matchedSize = sizePrefixes.find(p => tokenLower.startsWith(p));
        if (matchedSize) {
            const query = tokenBeforeCursor.slice(matchedSize.length).toLowerCase();
            const scored = SIZE_LIST.map((s, idx) => ({
                item: s,
                idx,
                score: scoreSecondaryItem(s.value, s.desc, query)
            })).filter(x => x.score < Infinity);
            scored.sort((a, b) => a.score - b.score || a.idx - b.idx);

            const matches = scored.map(({ item: s }) => {
                let insVal = `size${s.value.startsWith('<') || s.value.startsWith('>') ? s.value : (':' + s.value)}`;
                if (matchedSize === 'size<' || matchedSize === 'size>') {
                    const cleanVal = s.value.replace(/^[<>]/, '');
                    insVal = `${matchedSize}${cleanVal}`;
                }
                return {
                    badgeHtml: `<span class="tok-kw">size</span><span class="tok-op">:</span><span class="tok-val">${escapeHtml(s.value)}</span>`,
                    snippetText: `size:${s.value}`,
                    desc: s.desc,
                    insertValue: insVal,
                    hasSub: false
                };
            });
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
            baseList = TEXT_SNIPPET_PATTERNS.concat(TOP_LEVEL_KEYWORDS);
        } else {
            baseList = TOP_LEVEL_KEYWORDS;
        }

        const query = tokenBeforeCursor.toLowerCase();
        const scored = baseList.map((item, idx) => ({
            item,
            idx,
            score: scoreKeywordItem(item, query, contextType)
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
            } else if (item.prefix === '"') {
                const ph = item.placeholder || 'phrase';
                badgeHtml = `<span class="tok-op">"</span><span class="param-placeholder">${escapeHtml(ph)}</span><span class="tok-op">"</span>`;
                snippetClass = 'snippet-op';
            } else if (item.prefix === '-' || item.prefix === '+') {
                const ph = item.placeholder || 'term';
                badgeHtml = `<span class="tok-op">${escapeHtml(item.prefix)}</span><span class="param-placeholder">${escapeHtml(ph)}</span>`;
                snippetClass = 'snippet-op';
            } else if (item.prefix === 'pN' || (item.prefix.startsWith('p') && /^\bp[0-9N]+\b$/i.test(item.prefix))) {
                if (item.prefix.toLowerCase() === 'pn' || item.placeholder === 'N') {
                    badgeHtml = `<span class="tok-op">p</span><span class="param-placeholder">N</span>`;
                } else {
                    badgeHtml = `<span class="tok-op">${escapeHtml(item.prefix)}</span>`;
                }
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
                snippetText: (item.prefix === 'pN' ? 'pN' : (item.prefix + (item.placeholder || '') + (item.suffix || ''))),
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
        const newCursorPos = (replacement === '""' || replacement === '()')
            ? ctx.tokenStart + 1
            : ctx.tokenStart + replacement.length;
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
            const isFormEnabled = form.enabled !== false;
            card.className = `form-manage-card ${isFormEnabled ? '' : 'is-disabled'}`;
            card.id = `form-card-${form.id}`;

            const isReadOnly = !!form.readonly;
            const badgeHtml = isReadOnly
                ? '<span class="badge-pill badge-readonly">Default / Read-Only</span>'
                : '<span class="badge-pill badge-custom">Custom</span>';

            let fieldChips = '';
            (form.fields || []).slice(0, 5).forEach(f => {
                const isFieldEnabled = f.enabled !== false;
                fieldChips += `<span class="field-chip ${isFieldEnabled ? '' : 'is-disabled'}" style="${isFieldEnabled ? '' : 'opacity: 0.5; text-decoration: line-through;'}">${escapeHtml(f.label)} (${escapeHtml(f.type)})</span>`;
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
                    <div class="form-card-identity">
                        ${badgeHtml}
                        <h4 class="form-card-title" title="${escapeHtml(form.name)}">${escapeHtml(form.name)}</h4>
                    </div>
                    <label class="glass-switch" title="Toggle form active state">
                        <input type="checkbox" class="form-enabled-toggle" ${isFormEnabled ? 'checked' : ''} data-form-id="${escapeHtml(form.id)}">
                        <span class="glass-slider"></span>
                    </label>
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

        // Toggle handlers for full forms
        listContainer.querySelectorAll('.form-enabled-toggle').forEach(toggle => {
            toggle.addEventListener('change', async () => {
                const formId = toggle.dataset.formId;
                const isEnabled = toggle.checked;
                const card = document.getElementById(`form-card-${formId}`);
                if (card) {
                    card.classList.toggle('is-disabled', !isEnabled);
                }
                const targetForm = forms.find(f => f.id === formId);
                if (targetForm) {
                    targetForm.enabled = isEnabled;
                }
                try {
                    const resp = await fetch('/api/forms/toggle', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: formId, enabled: isEnabled })
                    });
                    const res = await resp.json();
                    if (!resp.ok || !res.success) {
                        throw new Error(res.error || 'Failed to toggle form state');
                    }
                    const dataTag = document.getElementById('recoll-search-forms-data');
                    if (dataTag) dataTag.textContent = JSON.stringify(forms);
                } catch (err) {
                    console.error('Error toggling form state:', err);
                    window.showAlertModal({
                        title: 'Form Toggle Failed',
                        message: `Failed to toggle form: ${err.message}`,
                        type: 'danger'
                    });
                    toggle.checked = !isEnabled;
                    if (card) {
                        card.classList.toggle('is-disabled', isEnabled);
                    }
                    if (targetForm) {
                        targetForm.enabled = !isEnabled;
                    }
                }
            });
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
        const isEnabled = fieldData.enabled !== false;
        card.className = `builder-field-card ${isEnabled ? '' : 'is-disabled'}`;

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
                <div class="builder-field-header-left">
                    <label class="glass-switch" title="Toggle field enabled state">
                        <input type="checkbox" class="field-enabled-toggle" ${isEnabled ? 'checked' : ''}>
                        <span class="glass-slider"></span>
                    </label>
                    <span class="builder-field-num">Field Config</span>
                </div>
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

        // Enabled toggle handler
        const toggle = card.querySelector('.field-enabled-toggle');
        if (toggle) {
            toggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    card.classList.remove('is-disabled');
                } else {
                    card.classList.add('is-disabled');
                }
            });
        }

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
                window.showAlertModal({
                    title: 'Validation Error',
                    message: 'Please provide a form name.',
                    type: 'warning'
                });
                builderFormName.focus();
                return;
            }

            const fieldCards = builderFieldsContainer.querySelectorAll('.builder-field-card');
            if (fieldCards.length === 0) {
                window.showAlertModal({
                    title: 'Validation Error',
                    message: 'Please add at least one field to the search form.',
                    type: 'warning'
                });
                return;
            }

            const fields = [];
            for (const card of fieldCards) {
                const fId = card.querySelector('.field-id-input').value.trim();
                let fLabel = card.querySelector('.field-label-input').value.trim();
                const fType = card.querySelector('.field-type-select').value;
                const toggleInput = card.querySelector('.field-enabled-toggle');
                const isFieldEnabled = toggleInput ? toggleInput.checked : true;
                if (!fLabel && (fType === 'static_query' || fType === 'static')) {
                    fLabel = 'Static Query';
                } else if (!fLabel) {
                    window.showAlertModal({
                        title: 'Validation Error',
                        message: 'Every field must have a label.',
                        type: 'warning'
                    });
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
                    enabled: isFieldEnabled,
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
                window.showAlertModal({
                    title: 'Error Saving Form',
                    message: `Failed to save form: ${err.message}`,
                    type: 'danger'
                });
            } finally {
                btnSaveForm.disabled = false;
                btnSaveForm.textContent = 'Save Search Form';
            }
        });
    }

    async function deleteForm(form) {
        const confirmed = await window.showConfirmModal({
            title: 'Delete Search Form',
            message: `Are you sure you want to delete the custom form "${form.name}"? This action cannot be undone.`,
            confirmText: 'Delete Form',
            isDanger: true
        });
        if (!confirmed) {
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
            window.showAlertModal({
                title: 'Error Deleting Form',
                message: `Failed to delete form: ${err.message}`,
                type: 'danger'
            });
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

/* ==========================================================================
   Global Toast Notification Utility
   ========================================================================== */

window.showToast = function(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;

    let iconSvg = '';
    if (type === 'success') {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    } else if (type === 'error') {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    } else if (type === 'warning') {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
    } else {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    }

    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-content">${escapeHtml(message)}</div>
        <button type="button" class="toast-close" title="Dismiss">&times;</button>
    `;

    container.appendChild(toast);
    void toast.offsetWidth; // Trigger CSS reflow
    toast.classList.add('toast-visible');

    const closeToast = () => {
        toast.classList.remove('toast-visible');
        toast.classList.add('toast-hiding');
        setTimeout(() => { toast.remove(); }, 350);
    };

    toast.querySelector('.toast-close').addEventListener('click', closeToast);
    if (duration > 0) {
        setTimeout(closeToast, duration);
    }
};

/* ==========================================================================
   Milestone 1: Index Configuration (recoll.conf) Manager
   ========================================================================== */

var currentConfigData = {
    skippedNames: [],
    indexallfilenames: true,
    noaspell: false,
    indexstemmingpositions: true,
    thrQSlices: "1",
    idxthreads: 2,
    idxflushmb: 50,
    idxabsml: 250,
    pdfocrmode: 'off'
};
var originalConfigData = null;
var isConfigDirty = false;

window.isIndexConfigDirty = function() {
    return isConfigDirty;
};

function initIndexConfig() {
    const card = document.getElementById('index-config-card');
    if (!card) return;

    if (!currentConfigData) {
        currentConfigData = {
            skippedNames: [],
            indexallfilenames: true,
            noaspell: false,
            indexstemmingpositions: true,
            thrQSlices: "1",
            idxthreads: 2,
            idxflushmb: 50,
            idxabsml: 250,
            pdfocrmode: 'off'
        };
    }

    // Enter key handler for adding new pattern
    const patternInput = document.getElementById('input-new-pattern');
    if (patternInput) {
        patternInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddSkippedName();
            }
        });
    }

    // If server rendered initial config in template, populate immediately
    if (window.INITIAL_INDEX_CONFIG && typeof window.INITIAL_INDEX_CONFIG === 'object') {
        const initData = window.INITIAL_INDEX_CONFIG;
        currentConfigData = {
            skippedNames: Array.isArray(initData.skippedNames) ? [...initData.skippedNames] : [],
            indexallfilenames: Boolean(initData.indexallfilenames),
            noaspell: Boolean(initData.noaspell),
            indexstemmingpositions: Boolean(initData.indexstemmingpositions),
            thrQSlices: initData.thrQSlices != null ? String(initData.thrQSlices) : "1",
            idxthreads: initData.idxthreads != null ? initData.idxthreads : 2,
            idxflushmb: initData.idxflushmb != null ? initData.idxflushmb : 50,
            idxabsml: initData.idxabsml != null ? initData.idxabsml : 250,
            pdfocrmode: initData.pdfocrmode || 'off'
        };
        originalConfigData = JSON.parse(JSON.stringify(currentConfigData));
        renderConfigFields();
    }

    // Always fetch latest configuration from backend
    loadIndexConfig();
}

async function loadIndexConfig(isReset = false) {
    const statusEl = document.getElementById('config-save-status');
    if (statusEl) {
        statusEl.textContent = 'Loading recoll.conf...';
        statusEl.className = 'status-msg';
    }

    try {
        const res = await fetch('/api/index/config');
        const data = await res.json();
        if (data.success && data.config) {
            currentConfigData = {
                skippedNames: Array.isArray(data.config.skippedNames) ? [...data.config.skippedNames] : [],
                indexallfilenames: Boolean(data.config.indexallfilenames),
                noaspell: Boolean(data.config.noaspell),
                indexstemmingpositions: Boolean(data.config.indexstemmingpositions),
                thrQSlices: data.config.thrQSlices != null ? String(data.config.thrQSlices) : "1",
                idxthreads: data.config.idxthreads != null ? data.config.idxthreads : 2,
                idxflushmb: data.config.idxflushmb != null ? data.config.idxflushmb : 50,
                idxabsml: data.config.idxabsml != null ? data.config.idxabsml : 250,
                pdfocrmode: data.config.pdfocrmode || 'off'
            };
            originalConfigData = JSON.parse(JSON.stringify(currentConfigData));
            isConfigDirty = false;
            updateConfigBadge();

            renderConfigFields();

            if (statusEl) {
                statusEl.textContent = isReset ? 'Configuration reloaded.' : '';
                statusEl.className = 'status-msg status-msg-success';
                if (isReset) {
                    showToast('Configuration reloaded from disk', 'info', 2500);
                    setTimeout(() => { statusEl.textContent = ''; }, 3000);
                }
            }
        } else {
            throw new Error(data.error || 'Failed to load configuration');
        }
    } catch (err) {
        console.error('Failed to load index configuration:', err);
        if (statusEl) {
            statusEl.textContent = 'Error loading configuration: ' + err.message;
            statusEl.className = 'status-msg status-msg-error';
        }
        showToast('Failed to load index configuration: ' + err.message, 'error');
    }
}

function renderConfigFields() {
    renderSkippedNamesChips();

    const elAllNames = document.getElementById('conf-indexallfilenames');
    if (elAllNames) elAllNames.checked = currentConfigData.indexallfilenames;

    const elNoAspell = document.getElementById('conf-noaspell');
    if (elNoAspell) elNoAspell.checked = currentConfigData.noaspell;

    const elStemPos = document.getElementById('conf-indexstemmingpositions');
    if (elStemPos) elStemPos.checked = currentConfigData.indexstemmingpositions;

    const elPdfOcr = document.getElementById('conf-pdfocrmode');
    if (elPdfOcr) {
        elPdfOcr.value = currentConfigData.pdfocrmode;
        // Re-sync custom select wrapper if active
        const wrapper = elPdfOcr.closest('.custom-select-wrapper');
        if (wrapper) {
            const label = wrapper.querySelector('.custom-select-label');
            const selectedOption = elPdfOcr.options[elPdfOcr.selectedIndex];
            if (label && selectedOption) label.textContent = selectedOption.textContent;
        }
    }

    const elThreads = document.getElementById('conf-idxthreads');
    if (elThreads) elThreads.value = currentConfigData.idxthreads;

    const elSlices = document.getElementById('conf-thrQSlices');
    if (elSlices) elSlices.value = currentConfigData.thrQSlices;

    const elFlush = document.getElementById('conf-idxflushmb');
    if (elFlush) elFlush.value = currentConfigData.idxflushmb;

    const elAbsml = document.getElementById('conf-idxabsml');
    if (elAbsml) elAbsml.value = currentConfigData.idxabsml;
}

function renderSkippedNamesChips() {
    const container = document.getElementById('skipped-names-chip-list');
    const countEl = document.getElementById('skipped-names-count');
    if (!container) return;

    if (countEl) {
        countEl.textContent = `${currentConfigData.skippedNames.length} pattern${currentConfigData.skippedNames.length === 1 ? '' : 's'}`;
    }

    if (currentConfigData.skippedNames.length === 0) {
        container.innerHTML = `
            <div style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; padding: 6px 0;">
                No skipped patterns configured. All supported files will be indexed.
            </div>`;
        return;
    }

    container.innerHTML = '';
    currentConfigData.skippedNames.forEach((pattern, index) => {
        const chip = document.createElement('div');
        chip.className = 'config-chip';
        chip.dataset.index = index;
        chip.dataset.pattern = pattern;

        const textSpan = document.createElement('span');
        textSpan.className = 'chip-text';
        textSpan.textContent = pattern;
        textSpan.title = 'Click to edit pattern';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'chip-remove-btn';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = `Remove "${pattern}"`;

        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeSkippedName(index);
        });

        textSpan.addEventListener('click', () => {
            enableChipInlineEdit(chip, textSpan, index);
        });

        chip.appendChild(textSpan);
        chip.appendChild(removeBtn);
        container.appendChild(chip);
    });
}

function enableChipInlineEdit(chip, textSpan, index) {
    if (chip.classList.contains('is-editing')) return;
    chip.classList.add('is-editing');

    const currentVal = currentConfigData.skippedNames[index];
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'chip-edit-input';
    input.value = currentVal;
    input.spellcheck = false;

    chip.replaceChild(input, textSpan);
    input.focus();
    input.select();

    let finished = false;
    function commitEdit() {
        if (finished) return;
        finished = true;

        const newVal = input.value.trim();
        if (!newVal || newVal === currentVal) {
            chip.classList.remove('is-editing');
            chip.replaceChild(textSpan, input);
            return;
        }

        // Check for duplicate with other entries (exact string equality)
        const duplicateIndex = currentConfigData.skippedNames.findIndex((p, i) => i !== index && p === newVal);
        if (duplicateIndex !== -1) {
            showPatternFeedback(`Pattern "${newVal}" already exists in skippedNames list`, true);
            highlightDuplicateChip(duplicateIndex);
            showToast(`Duplicate pattern "${newVal}" rejected`, 'warning');
            chip.classList.remove('is-editing');
            chip.replaceChild(textSpan, input);
            return;
        }

        currentConfigData.skippedNames[index] = newVal;
        markConfigDirty();
        renderSkippedNamesChips();
        showToast(`Pattern updated to "${newVal}"`, 'info', 2000);
    }

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            commitEdit();
        } else if (e.key === 'Escape') {
            finished = true;
            chip.classList.remove('is-editing');
            chip.replaceChild(textSpan, input);
        }
    });
    input.addEventListener('blur', commitEdit);
}

function removeSkippedName(index) {
    const removed = currentConfigData.skippedNames.splice(index, 1)[0];
    markConfigDirty();
    renderSkippedNamesChips();
    showToast(`Removed pattern "${removed}"`, 'info', 2000);
}

function handleAddSkippedName() {
    const input = document.getElementById('input-new-pattern');
    if (!input) return;
    const raw = input.value.trim();
    if (!raw) return;

    // Support space-separated or comma-separated tokens
    const tokens = raw.split(/[\s,]+/).filter(Boolean);
    let addedCount = 0;
    let duplicateTokens = [];

    tokens.forEach(token => {
        const exists = currentConfigData.skippedNames.some(p => p === token);
        if (exists) {
            duplicateTokens.push(token);
        } else {
            currentConfigData.skippedNames.push(token);
            addedCount++;
        }
    });

    if (duplicateTokens.length > 0) {
        const firstDup = duplicateTokens[0];
        showPatternFeedback(`Pattern "${firstDup}" is already in the skipped names list!`, true);
        const dupIdx = currentConfigData.skippedNames.findIndex(p => p === firstDup);
        if (dupIdx !== -1) highlightDuplicateChip(dupIdx);
        showToast(`Duplicate pattern "${firstDup}" rejected`, 'warning');
    } else {
        clearPatternFeedback();
    }

    if (addedCount > 0) {
        input.value = '';
        markConfigDirty();
        renderSkippedNamesChips();
        const container = document.getElementById('skipped-names-chip-list');
        if (container) container.scrollTop = container.scrollHeight;
        showToast(`Added ${addedCount} pattern${addedCount > 1 ? 's' : ''}`, 'success', 2000);
    }
}

function highlightDuplicateChip(index) {
    const container = document.getElementById('skipped-names-chip-list');
    if (!container) return;
    const chip = container.querySelector(`.config-chip[data-index="${index}"]`);
    if (chip) {
        chip.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        chip.classList.remove('chip-duplicate-highlight');
        void chip.offsetWidth;
        chip.classList.add('chip-duplicate-highlight');
        setTimeout(() => { chip.classList.remove('chip-duplicate-highlight'); }, 1400);
    }
}

function sortSkippedNames() {
    currentConfigData.skippedNames.sort((a, b) => a.localeCompare(b));
    markConfigDirty();
    renderSkippedNamesChips();
    showToast('Patterns sorted alphabetically', 'info', 2000);
}

function showPatternFeedback(msg, isError = false) {
    const alertEl = document.getElementById('pattern-feedback-msg');
    const textEl = document.getElementById('pattern-feedback-text');
    if (alertEl && textEl) {
        textEl.textContent = msg;
        alertEl.className = 'pattern-feedback-msg' + (isError ? ' is-error' : '');
        alertEl.style.display = 'flex';
        setTimeout(clearPatternFeedback, 4500);
    }
}

function clearPatternFeedback() {
    const alertEl = document.getElementById('pattern-feedback-msg');
    if (alertEl) alertEl.style.display = 'none';
}

function markConfigDirty() {
    isConfigDirty = true;
    updateConfigBadge();
}

function updateConfigBadge() {
    const badge = document.getElementById('config-status-badge');
    const text = document.getElementById('config-status-text');
    if (!badge || !text) return;

    if (isConfigDirty) {
        badge.className = 'config-status-badge is-dirty';
        text.textContent = 'Unsaved Changes';
    } else {
        badge.className = 'config-status-badge';
        text.textContent = 'Active Configuration';
    }
}

async function saveIndexConfig() {
    const btnSave = document.getElementById('btn-save-index-config');
    const btnIcon = document.getElementById('btn-save-config-icon');
    const btnText = document.getElementById('btn-save-config-text');
    const statusEl = document.getElementById('config-save-status');

    const elAllNames = document.getElementById('conf-indexallfilenames');
    const elNoAspell = document.getElementById('conf-noaspell');
    const elStemPos = document.getElementById('conf-indexstemmingpositions');
    const elPdfOcr = document.getElementById('conf-pdfocrmode');
    const elThreads = document.getElementById('conf-idxthreads');
    const elSlices = document.getElementById('conf-thrQSlices');
    const elFlush = document.getElementById('conf-idxflushmb');
    const elAbsml = document.getElementById('conf-idxabsml');

    const idxthreadsVal = parseInt(elThreads ? elThreads.value : '2', 10);
    const thrQSlicesVal = parseInt(elSlices ? elSlices.value : '1', 10);
    const idxflushmbVal = parseInt(elFlush ? elFlush.value : '50', 10);
    const idxabsmlVal = parseInt(elAbsml ? elAbsml.value : '250', 10);

    // Validation
    if (isNaN(idxthreadsVal) || idxthreadsVal < 0) {
        showToast('Indexer Threads must be a non-negative number', 'error');
        if (elThreads) elThreads.focus();
        return;
    }
    if (isNaN(thrQSlicesVal) || thrQSlicesVal < 1) {
        showToast('Thread Queue Slices must be at least 1', 'error');
        if (elSlices) elSlices.focus();
        return;
    }
    if (isNaN(idxflushmbVal) || idxflushmbVal < 1) {
        showToast('Index Flush Threshold must be at least 1 MB', 'error');
        if (elFlush) elFlush.focus();
        return;
    }
    if (isNaN(idxabsmlVal) || idxabsmlVal < 0) {
        showToast('Max Abstract Length must be a non-negative number', 'error');
        if (elAbsml) elAbsml.focus();
        return;
    }

    const payload = {
        skippedNames: currentConfigData.skippedNames,
        indexallfilenames: elAllNames ? elAllNames.checked : true,
        noaspell: elNoAspell ? elNoAspell.checked : false,
        indexstemmingpositions: elStemPos ? elStemPos.checked : true,
        pdfocrmode: elPdfOcr ? elPdfOcr.value : 'off',
        idxthreads: idxthreadsVal,
        thrQSlices: String(thrQSlicesVal),
        idxflushmb: idxflushmbVal,
        idxabsml: idxabsmlVal
    };

    // UI Loading state
    if (btnSave) btnSave.disabled = true;
    if (btnIcon) {
        btnIcon.innerHTML = `<svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>`;
    }
    if (btnText) btnText.textContent = 'Saving Configuration...';
    if (statusEl) {
        statusEl.textContent = 'Writing updates to recoll.conf...';
        statusEl.className = 'status-msg';
    }

    try {
        const res = await fetch('/api/index/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            currentConfigData = {
                skippedNames: data.config.skippedNames || payload.skippedNames,
                indexallfilenames: Boolean(data.config.indexallfilenames),
                noaspell: Boolean(data.config.noaspell),
                indexstemmingpositions: Boolean(data.config.indexstemmingpositions),
                thrQSlices: data.config.thrQSlices != null ? String(data.config.thrQSlices) : String(payload.thrQSlices),
                idxthreads: data.config.idxthreads != null ? data.config.idxthreads : payload.idxthreads,
                idxflushmb: data.config.idxflushmb != null ? data.config.idxflushmb : payload.idxflushmb,
                idxabsml: data.config.idxabsml != null ? data.config.idxabsml : payload.idxabsml,
                pdfocrmode: data.config.pdfocrmode || payload.pdfocrmode
            };
            originalConfigData = JSON.parse(JSON.stringify(currentConfigData));
            isConfigDirty = false;
            updateConfigBadge();

            if (statusEl) {
                statusEl.textContent = 'recoll.conf configuration saved successfully!';
                statusEl.className = 'status-msg status-msg-success';
                setTimeout(() => { statusEl.textContent = ''; }, 4500);
            }
            showToast('Index configuration saved successfully!', 'success', 3500);
        } else {
            throw new Error(data.error || 'Unknown server error');
        }
    } catch (err) {
        console.error('Failed to save index configuration:', err);
        if (statusEl) {
            statusEl.textContent = 'Error saving config: ' + err.message;
            statusEl.className = 'status-msg status-msg-error';
        }
        showToast('Failed to save config: ' + err.message, 'error');
    } finally {
        if (btnSave) btnSave.disabled = false;
        if (btnIcon) {
            btnIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`;
        }
        if (btnText) btnText.textContent = 'Save Index Configuration';
    }
}

// Bind globally for inline onclick handlers
window.initIndexConfig = initIndexConfig;
window.loadIndexConfig = loadIndexConfig;
window.renderConfigFields = renderConfigFields;
window.renderSkippedNamesChips = renderSkippedNamesChips;
window.removeSkippedName = removeSkippedName;
window.handleAddSkippedName = handleAddSkippedName;
window.highlightDuplicateChip = highlightDuplicateChip;
window.sortSkippedNames = sortSkippedNames;
window.showPatternFeedback = showPatternFeedback;
window.clearPatternFeedback = clearPatternFeedback;
window.markConfigDirty = markConfigDirty;
window.updateConfigBadge = updateConfigBadge;
window.saveIndexConfig = saveIndexConfig;



