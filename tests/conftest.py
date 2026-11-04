import sys
import os
import pytest
from PySide6.QtWidgets import QApplication

# Ensure src is in sys.path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


@pytest.fixture(scope="session")
def qapp():
    """Ensure a QApplication exists for Qt widgets, signals, and event loops."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
