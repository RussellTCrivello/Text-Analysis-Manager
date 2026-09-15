"""Reusable table interaction primitives for the research workspace.

The application has several intentionally different table surfaces (records,
previews, backups, and report output). This module standardizes the mechanics
without forcing the same actions or selection model onto each dataset.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


def configure_table(table: QTableWidget, *, multi_select: bool = False,
                    stretch_last: bool = True, row_height: int = 38):
    """Apply accessible, dense, keyboard-friendly defaults to a table."""
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(
        QAbstractItemView.ExtendedSelection if multi_select
        else QAbstractItemView.SingleSelection
    )
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setFocusPolicy(Qt.StrongFocus)
    table.setTextElideMode(Qt.ElideRight)
    table.setWordWrap(False)
    table.setAlternatingRowColors(True)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.verticalHeader().setMinimumSectionSize(row_height)

    header = table.horizontalHeader()
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(False)
    header.setStretchLastSection(stretch_last)
    header.setMinimumSectionSize(72)
    table.setAccessibleName(table.objectName() or "Data table")
    return table


def set_item_with_tooltip(table: QTableWidget, row: int, column: int,
                          value, *, alignment=None):
    """Insert a display value while keeping its full text recoverable."""
    text = "" if value is None else str(value)
    item = QTableWidgetItem(text)
    item.setToolTip(text)
    item.setTextAlignment(alignment or (Qt.AlignLeft | Qt.AlignVCenter))
    table.setItem(row, column, item)
    return item
