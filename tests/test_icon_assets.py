"""Regression tests for the graphical icon system."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest


ICON_DIR = Path(__file__).parents[1] / "icons" / "images"


def test_all_svg_assets_are_well_formed():
    assets = sorted(ICON_DIR.glob("*.svg"))
    assert assets
    for asset in assets:
        ET.parse(asset)


def test_all_action_icons_load_as_qicons():
    """Exercise the same loader used by buttons and menus when Qt is usable."""
    pytest.importorskip("PyQt5.QtWidgets", exc_type=ImportError)
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from icons.icon_manager import get_icon

    for asset in ICON_DIR.glob("*.svg"):
        assert not get_icon(asset.stem, 20).isNull(), asset.name

    # Keep the reference alive for the duration of the QIcon assertions.
    assert app is not None
