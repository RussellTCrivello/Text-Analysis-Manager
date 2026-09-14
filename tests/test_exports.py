"""Export, print, and localization regression tests."""
import json
import xml.etree.ElementTree as ET

import pytest


def test_json_xml_and_json_lines_preserve_unicode(tmp_path):
    from utils.json_xml_export import export_to_json, export_to_json_lines, export_to_xml

    rows = [{"title": "عنوان عربي", "body": "Special <&> text"}]
    json_path = tmp_path / "records.json"
    xml_path = tmp_path / "records.xml"
    lines_path = tmp_path / "records.jsonl"

    assert export_to_json(rows, str(json_path))
    assert export_to_xml(rows, str(xml_path))
    assert export_to_json_lines(rows, str(lines_path))
    assert json.loads(json_path.read_text(encoding="utf-8"))["records"] == rows
    assert ET.parse(xml_path).getroot().find("record/body").text == "Special <&> text"
    assert json.loads(lines_path.read_text(encoding="utf-8"))["title"] == "عنوان عربي"


def test_office_exports_and_print_html_escape(tmp_path, monkeypatch):
    pytest.importorskip("PyQt5.QtWidgets", exc_type=ImportError)
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from translations.translations import TranslationManager
    from utils.excel_export import export_to_excel
    from utils.print_utils import PrintSettings, generate_print_html
    from utils.word_export import export_to_word

    # Keep this test isolated from the user's persistent document counter.
    monkeypatch.setattr(PrintSettings, "save_settings", lambda self: None)
    translator = TranslationManager(app)
    translator.current_language = "en"
    rows = [{"title": "A <script>alert(1)</script>", "body": "عربي & text"}]
    columns = [("title", "Title", 50), ("body", "Body", 50)]

    assert export_to_excel(rows, columns, str(tmp_path / "records.xlsx"), translator)
    assert export_to_word(rows, columns, str(tmp_path / "records.docx"), translator)
    html = generate_print_html(rows, ["title", "body"], {}, "<Report>", translator)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert 'dir="ltr"' in html
    assert app is not None
