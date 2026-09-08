"""
Custom search form schema management, persistence in forms.json, and validation.
"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional
from recollweb.constants import DEFAULT_SEARCH_FORM, SAMPLE_CUSTOM_FORM, TEMP_DIR
from recollweb.logging import logger


class SearchFormsManager:
    """
    Manages search form presets, persistence in forms.json, and schema validation.
    """

    FORMS_FILENAME = "forms.json"
    LEGACY_FORMS_FILENAME = "custom_search_forms.json"

    @classmethod
    def get_forms_path(cls, conf_dir: Optional[str] = None) -> str:
        """
        Resolve absolute path to forms.json inside the Recoll configuration directory.
        """
        from recollweb.config import get_config_dir
        base_dir = conf_dir or get_config_dir()
        try:
            os.makedirs(base_dir, exist_ok=True)
            return os.path.join(base_dir, cls.FORMS_FILENAME)
        except OSError:
            return os.path.join(TEMP_DIR, cls.FORMS_FILENAME)

    @classmethod
    def get_forms(cls, conf_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load all search forms from forms.json.
        Migrates legacy custom_search_forms.json if forms.json does not exist.
        Ensures the default advanced search form is present with readonly=True.
        Initializes the sample custom form if only the default form exists.
        """
        path = cls.get_forms_path(conf_dir)
        forms: List[Dict[str, Any]] = []

        if not os.path.isfile(path):
            legacy_path = os.path.join(os.path.dirname(path), cls.LEGACY_FORMS_FILENAME)
            if os.path.isfile(legacy_path):
                try:
                    with open(legacy_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                except Exception as exc:
                    logger.warning("Could not migrate legacy forms file %s: %s", legacy_path, exc)

        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'forms' in data:
                        forms = data['forms']
                    elif isinstance(data, list):
                        forms = data
            except Exception as exc:
                logger.error("Failed to load forms from %s: %s", path, exc)

        has_default = False
        sanitized_forms: List[Dict[str, Any]] = []

        for form in forms:
            if not isinstance(form, dict):
                continue
            if form.get('id') == 'default':
                form_copy = dict(DEFAULT_SEARCH_FORM)
                if 'enabled' in form:
                    form_copy['enabled'] = bool(form['enabled'])
                else:
                    form_copy['enabled'] = True
                sanitized_forms.insert(0, form_copy)
                has_default = True
            else:
                form['readonly'] = False
                if 'enabled' in form:
                    form['enabled'] = bool(form['enabled'])
                else:
                    form['enabled'] = True
                sanitized_forms.append(form)

        if not has_default:
            default_copy = dict(DEFAULT_SEARCH_FORM)
            default_copy['enabled'] = True
            sanitized_forms.insert(0, default_copy)

        # Provide sample classification form out-of-the-box if no custom forms exist
        if len(sanitized_forms) == 1:
            sanitized_forms.append(dict(SAMPLE_CUSTOM_FORM))
            cls.save_forms(conf_dir, sanitized_forms)

        return sanitized_forms

    @classmethod
    def save_forms(cls, conf_dir: Optional[str], forms: List[Dict[str, Any]]) -> bool:
        """
        Persist list of forms atomically into forms.json.
        """
        path = cls.get_forms_path(conf_dir)
        try:
            clean_forms: List[Dict[str, Any]] = []
            default_form = dict(DEFAULT_SEARCH_FORM)
            for f in forms:
                if isinstance(f, dict) and f.get('id') == 'default':
                    if 'enabled' in f:
                        default_form['enabled'] = bool(f['enabled'])
                    break
            clean_forms.append(default_form)
            for form in forms:
                if not isinstance(form, dict) or form.get('id') == 'default':
                    continue
                form_copy = dict(form)
                form_copy['readonly'] = False
                if 'enabled' in form:
                    form_copy['enabled'] = bool(form['enabled'])
                clean_forms.append(form_copy)

            temp_path = f"{path}.tmp.{uuid.uuid4().hex}"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump({'forms': clean_forms}, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)
            return True
        except Exception as exc:
            logger.error("Failed to save forms to %s: %s", path, exc)
            return False

    @classmethod
    def toggle_form(cls, conf_dir: Optional[str], form_id: str, enabled: bool) -> Dict[str, Any]:
        """
        Toggle active state of a search form (default or custom) and persist to forms.json.
        """
        forms = cls.get_forms(conf_dir)
        target = None
        for f in forms:
            if f.get('id') == form_id:
                f['enabled'] = enabled
                target = f
                break
        if not target:
            raise ValueError(f"Form with ID '{form_id}' not found.")
        if not cls.save_forms(conf_dir, forms):
            raise IOError("Failed to persist forms to disk.")
        return target

    @classmethod
    def save_custom_form(cls, conf_dir: Optional[str], form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate, create or update a custom search form, persisting changes to disk.
        Raises ValueError on invalid form payloads or attempting to edit default form.
        """
        if not isinstance(form_data, dict):
            raise ValueError("Invalid form payload")
        form_id = str(form_data.get('id', '')).strip()
        if form_id == 'default':
            raise ValueError("The default search form is read-only and cannot be modified.")

        form_name = str(form_data.get('name', '')).strip()
        if not form_name:
            raise ValueError("Form name is required.")

        fields = form_data.get('fields', [])
        if not isinstance(fields, list) or len(fields) == 0:
            raise ValueError("A form must have at least one field.")

        clean_fields = []
        for f in fields:
            if not isinstance(f, dict):
                continue
            fid = str(f.get('id', '')).strip() or f"f_{uuid.uuid4().hex[:8]}"
            flabel = str(f.get('label', '')).strip() or "Unnamed Field"
            ftype = str(f.get('type', 'text')).strip()
            clean_field: Dict[str, Any] = {
                'id': fid,
                'label': flabel,
                'type': ftype,
                'helper': str(f.get('helper', '')).strip(),
                'placeholder': str(f.get('placeholder', '')).strip(),
                'enabled': bool(f.get('enabled', True)) if 'enabled' in f else True,
            }
            if ftype == 'select':
                raw_options = f.get('options', [])
                clean_options = []
                for opt in raw_options:
                    if isinstance(opt, dict):
                        clean_options.append({
                            'label': str(opt.get('label', '')).strip(),
                            'query': str(opt.get('query', '')).strip(),
                        })
                clean_field['options'] = clean_options
            elif ftype in ('toggle', 'checkbox'):
                clean_field['type'] = 'toggle'
                clean_field['query'] = str(f.get('query', '')).strip()
            elif ftype in ('static_query', 'static') or ftype.lower().replace(' ', '_').replace('-', '_') in ('static_query', 'static'):
                clean_field['type'] = ftype if ftype in ('static_query', 'static') else 'static_query'
                clean_field['query'] = str(f.get('query', '')).strip()
            else:
                clean_field['type'] = 'text'
                clean_field['query_format'] = str(f.get('query_format', '{value}')).strip()
                if clean_field['query_format'] == 'proximity':
                    try:
                        clean_field['slack'] = int(f.get('slack', 4))
                    except Exception:
                        clean_field['slack'] = 4
            clean_fields.append(clean_field)

        if not clean_fields:
            raise ValueError("Form must have valid fields.")

        if not form_id:
            form_id = f"custom_{uuid.uuid4().hex[:8]}"

        new_form: Dict[str, Any] = {
            'id': form_id,
            'name': form_name,
            'description': str(form_data.get('description', '')).strip(),
            'readonly': False,
            'fields': clean_fields,
            'enabled': bool(form_data.get('enabled', True)) if 'enabled' in form_data else True,
        }

        existing_forms = cls.get_forms(conf_dir)
        updated = False
        for idx, f in enumerate(existing_forms):
            if f.get('id') == form_id:
                existing_forms[idx] = new_form
                updated = True
                break

        if not updated:
            existing_forms.append(new_form)

        if not cls.save_forms(conf_dir, existing_forms):
            raise IOError("Failed to persist custom search forms to disk.")

        return new_form

    @classmethod
    def delete_custom_form(cls, conf_dir: Optional[str], form_id: str) -> bool:
        """
        Delete custom search form by ID.
        Raises ValueError if attempting to delete default form or non-existent form.
        """
        if form_id == 'default':
            raise ValueError("The default search form is read-only and cannot be deleted.")

        existing_forms = cls.get_forms(conf_dir)
        filtered = [f for f in existing_forms if f.get('id') != form_id]

        if len(filtered) == len(existing_forms):
            raise ValueError(f"Form '{form_id}' not found.")

        if not cls.save_forms(conf_dir, filtered):
            raise IOError("Failed to update custom search forms on disk.")
        return True
