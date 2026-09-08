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
        // Press 'Escape' to blur active input or close open modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal-backdrop');
            openModals.forEach(m => {
                if (m.style.display !== 'none') m.style.display = 'none';
            });
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
                document.activeElement.blur();
            }
        }
    });

    // Initialize Advanced Search Panel & Settings Form Manager
    initAdvancedSearch();
    initSettingsFormManager();
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

let _lastAdvToggleTime = 0;
window.toggleAdvancedSearch = function(e) {
    if (e) {
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();
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
    const formDesc = document.getElementById('active-form-desc');
    const fieldsContainer = document.getElementById('advanced-fields-container');
    const previewEl = document.getElementById('advanced-query-preview');
    const clearBtn = document.getElementById('btn-clear-advanced');
    const submitBtn = document.getElementById('btn-submit-advanced');
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

        if (formDesc) {
            formDesc.textContent = activeForm.description || '';
        }

        const savedValues = loadActiveFormValues(activeForm.id);
        fieldsContainer.innerHTML = '';

        (activeForm.fields || []).forEach(field => {
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
            } else if (field.type === 'checkbox') {
                const isChecked = !!savedValues[field.id];
                card.className = 'advanced-field-card';
                card.innerHTML = `
                    <label class="advanced-field-checkbox" for="${fieldId}">
                        <input type="checkbox" id="${fieldId}" data-field-id="${escapeHtml(field.id)}" class="advanced-field-input" data-query="${escapeHtml(field.query || '')}" ${isChecked ? 'checked' : ''}>
                        <span>${escapeHtml(field.label)}</span>
                    </label>
                    ${helperHtml}
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
    }

    function updateCompiledQuery() {
        if (!activeForm || !fieldsContainer) return '';
        const compiled = compileQueryFromForm(activeForm, fieldsContainer);
        if (previewEl) {
            previewEl.textContent = compiled || '<empty>';
        }
        return compiled;
    }

    function executeFormSearch() {
        saveActiveFormValues();
        const query = updateCompiledQuery();
        if (mainQueryInput && query) {
            mainQueryInput.value = query;
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
                }
                safeStorageSet('sessionStorage', 'recoll_adv_open', '1');
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

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            const inputs = fieldsContainer.querySelectorAll('.advanced-field-input');
            inputs.forEach(input => {
                if (input.type === 'checkbox') input.checked = false;
                else input.value = '';
            });
            if (activeForm) {
                safeStorageSet('localStorage', `recoll_adv_values_${activeForm.id}`, '{}');
            }
            updateCompiledQuery();
            if (mainQueryInput) mainQueryInput.value = '';
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
            }
            renderActiveForm('default');
            updateCompiledQuery();
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            executeFormSearch();
        });
    }
}

function compileQueryFromForm(form, container) {
    if (!form || !container) return '';
    const clauses = [];
    const fields = form.fields || [];

    fields.forEach(field => {
        const input = container.querySelector(`[data-field-id="${field.id}"]`);
        if (!input) return;

        if (field.type === 'select') {
            const val = (input.value || '').trim();
            if (val) clauses.push(val);
        } else if (field.type === 'checkbox') {
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
                        <option value="checkbox" ${fType === 'checkbox' ? 'selected' : ''}>Checkbox Filter</option>
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

            <!-- Text Config: Operator Format -->
            <div class="field-text-config" style="${fType === 'text' ? '' : 'display: none;'}">
                <div class="settings-field" style="margin-top: 0.5rem;">
                    <label class="settings-label">Query Operator / Target</label>
                    <select class="form-control field-format-select">
                        <option value="{value}" ${fFormat === '{value}' ? 'selected' : ''}>Search Terms (AND) - {value}</option>
                        <option value='"{value}"' ${fFormat === '"{value}"' ? 'selected' : ''}>Exact Phrase - "{value}"</option>
                        <option value="or_terms" ${fFormat === 'or_terms' ? 'selected' : ''}>Any Words (OR) - (word1 OR word2)</option>
                        <option value="not_terms" ${fFormat === 'not_terms' ? 'selected' : ''}>Exclude Words (NOT) - -word1 -word2</option>
                        <option value="proximity" ${fFormat === 'proximity' ? 'selected' : ''}>Proximity Search - "words"p4</option>
                        <option value="title:{value}" ${fFormat === 'title:{value}' ? 'selected' : ''}>Document Title - title:{value}</option>
                        <option value="author:{value}" ${fFormat === 'author:{value}' ? 'selected' : ''}>Author / Creator - author:{value}</option>
                        <option value="filename:{value}" ${fFormat === 'filename:{value}' ? 'selected' : ''}>Filename / Wildcard - filename:{value}</option>
                        <option value='dir:"{value}"' ${fFormat === 'dir:"{value}"' ? 'selected' : ''}>Directory Scope - dir:"{value}"</option>
                        <option value="custom" ${!['{value}', '"{value}"', 'or_terms', 'not_terms', 'proximity', 'title:{value}', 'author:{value}', 'filename:{value}', 'dir:"{value}"'].includes(fFormat) ? 'selected' : ''}>Custom Pattern...</option>
                    </select>
                </div>
                <div class="settings-field field-custom-format-wrap" style="${!['{value}', '"{value}"', 'or_terms', 'not_terms', 'proximity', 'title:{value}', 'author:{value}', 'filename:{value}', 'dir:"{value}"'].includes(fFormat) ? '' : 'display: none;'} margin-top: 0.5rem;">
                    <label class="settings-label">Custom Query Pattern</label>
                    <span class="settings-helper">Use {value} as placeholder, e.g. filename:*{value}*</span>
                    <input class="form-control field-custom-format-input" value="${escapeHtml(fFormat)}">
                </div>
            </div>

            <!-- Checkbox Config -->
            <div class="field-checkbox-config" style="${fType === 'checkbox' ? '' : 'display: none;'} margin-top: 0.5rem;">
                <div class="settings-field">
                    <label class="settings-label">Query Snippet When Checked</label>
                    <input class="form-control field-checkbox-query-input" value="${escapeHtml(fQuery)}" placeholder="e.g. mime:application/pdf">
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
        const checkboxConfig = card.querySelector('.field-checkbox-config');
        const selectConfig = card.querySelector('.field-select-config');
        const formatSelect = card.querySelector('.field-format-select');
        const customFormatWrap = card.querySelector('.field-custom-format-wrap');
        const optionsTbody = card.querySelector('.options-tbody');

        function renderOptionRow(optLabel = '', optQuery = '') {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input class="form-control opt-label-input" value="${escapeHtml(optLabel)}" placeholder="e.g. Invoices" required></td>
                <td><input class="form-control opt-query-input" value="${escapeHtml(optQuery)}" placeholder="e.g. filename:*INV*"></td>
                <td style="text-align: center;"><button type="button" class="btn-icon btn-icon-danger btn-del-opt">&times;</button></td>
            `;
            tr.querySelector('.btn-del-opt').addEventListener('click', () => tr.remove());
            optionsTbody.appendChild(tr);
        }

        options.forEach(opt => {
            renderOptionRow(opt.label, opt.query);
        });

        card.querySelector('.btn-add-option').addEventListener('click', () => {
            renderOptionRow('New Option', '');
        });

        typeSelect.addEventListener('change', () => {
            const selectedType = typeSelect.value;
            textConfig.style.display = selectedType === 'text' ? 'block' : 'none';
            placeholderWrap.style.display = selectedType === 'text' ? 'block' : 'none';
            checkboxConfig.style.display = selectedType === 'checkbox' ? 'block' : 'none';
            selectConfig.style.display = selectedType === 'select' ? 'block' : 'none';
        });

        formatSelect.addEventListener('change', () => {
            customFormatWrap.style.display = formatSelect.value === 'custom' ? 'block' : 'none';
        });

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
                const fLabel = card.querySelector('.field-label-input').value.trim();
                if (!fLabel) {
                    alert('Every field must have a label.');
                    return;
                }
                const fType = card.querySelector('.field-type-select').value;
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
                } else if (fType === 'checkbox') {
                    fieldObj.query = card.querySelector('.field-checkbox-query-input').value.trim();
                } else {
                    const fmtSelect = card.querySelector('.field-format-select').value;
                    if (fmtSelect === 'custom') {
                        fieldObj.query_format = card.querySelector('.field-custom-format-input').value.trim() || '{value}';
                    } else {
                        fieldObj.query_format = fmtSelect;
                    }
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

