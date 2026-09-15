"""Focused regression coverage for the reusable table workspace patterns."""
import pytest


@pytest.fixture
def qt_app():
    pytest.importorskip("PyQt5.QtWidgets", exc_type=ImportError)
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    return app


def test_adaptive_page_sequence_has_stable_edges_and_context():
    from widgets.pagination_widget import PaginationWidget

    assert PaginationWidget._build_page_sequence(1, 1) == [1]
    assert PaginationWidget._build_page_sequence(7, 4) == [1, 2, 3, 4, 5, 6, 7]
    assert PaginationWidget._build_page_sequence(20, 1) == [1, 2, 3, 4, 5, "ellipsis", 20]
    assert PaginationWidget._build_page_sequence(20, 10) == [1, "ellipsis", 9, 10, 11, "ellipsis", 20]
    assert PaginationWidget._build_page_sequence(20, 20) == [1, "ellipsis", 16, 17, 18, 19, 20]


def test_pagination_updates_range_and_clamps_after_last_page_deletion(qt_app):
    from translations.translations import TranslationManager
    from widgets.pagination_widget import PaginationWidget

    translator = TranslationManager()
    translator.current_language = "en"
    pagination = PaginationWidget(translator)
    pagination.set_total_items(101)
    assert not pagination.btn_first.isEnabled()
    assert not pagination.btn_prev.isEnabled()
    assert pagination.btn_next.isEnabled()
    assert pagination.btn_last.isEnabled()
    pagination.go_to_next()
    assert pagination.current_page == 2
    pagination.go_to_first()
    pagination.go_to_last()
    assert pagination.current_page == 3
    assert not pagination.btn_next.isEnabled()
    assert not pagination.btn_last.isEnabled()
    assert pagination.get_page_range() == (100, 101)
    assert "101" in pagination.records_label.text()

    pagination.set_total_items(100)
    assert pagination.current_page == 2
    assert pagination.get_page_range() == (50, 100)
    pagination.page_size_combo.setCurrentText("100")
    assert pagination.current_page == 1
    assert pagination.get_page_range() == (0, 100)


def test_pagination_preserves_previous_next_meaning_in_rtl(qt_app):
    from translations.translations import TranslationManager
    from widgets.pagination_widget import PaginationWidget

    translator = TranslationManager()
    translator.current_language = "en"
    pagination = PaginationWidget(translator)
    pagination.set_total_items(101)
    pagination.go_to_next()
    translator.current_language = "ar"
    pagination.refresh_translations()
    assert pagination.btn_prev.icon_name == "btn_page_next"
    assert pagination.btn_next.icon_name == "btn_page_prev"
    assert pagination.btn_prev.accessibleName() == "الصفحة السابقة"
    assert pagination.btn_next.accessibleName() == "الصفحة التالية"


def test_toolbar_prioritizes_labeled_primary_and_overflow_actions(qt_app):
    from PyQt5.QtWidgets import QToolButton
    from core.toolbar_factory import ToolbarFactory, ToolbarConfig, ButtonConfig
    from translations.translations import TranslationManager

    translator = TranslationManager()
    translator.current_language = "en"
    factory = ToolbarFactory(translator)
    calls = []
    toolbar = factory.create_toolbar(
        None,
        ToolbarConfig(
            show_date_filter=False,
            page_specific_buttons=[
                ButtonConfig("advanced_search", "btn_search", lambda: calls.append("advanced")),
            ],
        ),
        {"add": lambda: None, "edit": lambda: None, "delete": lambda: None,
         "refresh": lambda: None, "export_unified": lambda: None},
    )
    add = factory.get_button("btn_add")
    assert add is not None
    assert add.text() == "Add"
    assert add.toolTip() == "Add"
    more = toolbar.findChild(QToolButton, "toolbarMoreButton")
    assert more is not None
    assert [action.text() for action in more.menu().actions()] == ["Advanced Search"]
    more.menu().actions()[0].trigger()
    assert calls == ["advanced"]


def test_bulk_dialog_carries_selected_rows_into_its_operation_table(qt_app):
    from dialogs.bulk_operations_dialog import BulkOperationsDialog
    from translations.translations import TranslationManager

    translator = TranslationManager()
    translator.current_language = "en"
    dialog = BulkOperationsDialog(
        None,
        translator,
        "sources",
        [{"id": 1, "name": "Alpha"}, {"id": 2, "name": "Beta"}],
        [("id", "ID", 60), ("name", "Name", 120)],
        preselected_ids=[2],
    )
    checkbox = dialog.selection_table.cellWidget(1, 0)
    assert checkbox.isChecked()
    assert dialog.selected_ids == [2]
    assert dialog.selection_table.accessibleName()
    dialog.close()
