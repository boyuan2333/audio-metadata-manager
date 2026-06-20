from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_TEMPLATE = ROOT / "web" / "templates" / "library.html"
APP_JS = ROOT / "web" / "static" / "app.js"
SETTINGS_TEMPLATE = ROOT / "web" / "templates" / "settings.html"
BASE_TEMPLATE = ROOT / "web" / "templates" / "base.html"


def test_library_template_uses_shared_library_init_only():
    html = LIBRARY_TEMPLATE.read_text(encoding="utf-8")

    assert "/api/files" not in html
    assert "window.libraryInit" in html
    assert "libraryInit();" in html
    assert "data.files || data || []" not in html
    assert "f.filename || f.name" not in html


def test_app_js_contains_search_pagination_and_audio_error_contract():
    js = APP_JS.read_text(encoding="utf-8")

    assert "/api/search" in js
    assert "limit" in js
    assert "offset" in js
    assert "文件不可预览" in js


def test_app_js_reads_current_search_result_shape():
    js = APP_JS.read_text(encoding="utf-8")

    assert "data.results || []" in js
    assert "f.file_name" in js
    assert "f.metadata || {}" in js
    assert "meta.bpm" in js
    assert "meta.tags" in js


def test_settings_template_uses_shared_settings_init_and_editable_controls():
    html = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    assert "window.settingsInit();" in html
    assert "id=\"settings-language\"" in html
    assert "id=\"sample-dir-input\"" in html
    assert "id=\"btn-create-library\"" in html
    assert "library-path-input" not in html
    assert "Copy Library" not in html
    assert "data-i18n=\"settings.sampleDirectory\"" in html
    assert "data-i18n=\"settings.createLibrary\"" in html
    assert "Loading..." not in html


def test_app_js_supports_settings_api_and_language_preference():
    js = APP_JS.read_text(encoding="utf-8")

    assert "_fetchJSON('/api/settings')" in js
    assert "fetch('/api/settings'" in js
    assert "fetch('/api/settings/create-library'" in js
    assert "localStorage.setItem('amm.language'" in js
    assert "document.documentElement.lang" in js
    assert "const I18N" in js
    assert "settings.createLibrary" in js


def test_base_template_marks_global_navigation_for_language_switching():
    html = BASE_TEMPLATE.read_text(encoding="utf-8")

    assert 'data-i18n="nav.library"' in html
    assert 'data-i18n="nav.settings"' in html
    assert 'data-i18n-placeholder="search.placeholder"' in html
