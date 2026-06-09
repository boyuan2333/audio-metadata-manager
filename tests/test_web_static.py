from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_TEMPLATE = ROOT / "web" / "templates" / "library.html"
APP_JS = ROOT / "web" / "static" / "app.js"


def test_library_template_uses_shared_library_init_only():
    html = LIBRARY_TEMPLATE.read_text(encoding="utf-8")

    assert "/api/files" not in html
    assert "window.libraryInit" in html
    assert "libraryInit();" in html


def test_app_js_contains_search_pagination_and_audio_error_contract():
    js = APP_JS.read_text(encoding="utf-8")

    assert "/api/search" in js
    assert "limit" in js
    assert "offset" in js
    assert "文件不可预览" in js


def test_app_js_reads_current_search_result_shape():
    js = APP_JS.read_text(encoding="utf-8")

    assert "f.file_name" in js
    assert "f.metadata || {}" in js
    assert "meta.bpm" in js
    assert "meta.tags" in js
