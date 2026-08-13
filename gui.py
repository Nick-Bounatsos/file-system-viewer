import os
import sys
import traceback
import webbrowser
from typing import Callable, Optional

from PyQt5 import QtCore, QtGui, QtWidgets


APP_NAME = "File System Viewer"


LIGHT_STYLE_SHEET = """
QMainWindow,
QWidget#CentralWidget {
    background: #f4f6f8;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #20242a;
}

QMenuBar {
    background: #ffffff;
    border-bottom: 1px solid #dfe3e8;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 5px;
}

QMenuBar::item:selected {
    background: #eef2f6;
}

QMenu {
    background: #ffffff;
    border: 1px solid #dfe3e8;
    padding: 5px;
}

QMenu::item {
    padding: 7px 28px 7px 10px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: #eaf2ff;
}

QFrame#InfoCard,
QFrame#SearchPanel,
QFrame#FilterPanel {
    background: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 10px;
}

QLabel#AppTitle {
    font-size: 20pt;
    font-weight: 700;
    color: #16191d;
}

QLabel#LocationLabel {
    color: #667085;
    font-size: 9.5pt;
}

QLabel#CardTitle {
    color: #667085;
    font-size: 8.5pt;
    font-weight: 600;
}

QLabel#CardValue {
    color: #16191d;
    font-size: 14pt;
    font-weight: 700;
}

QLineEdit {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #cfd6de;
    border-radius: 7px;
    padding: 8px 10px;
    selection-background-color: #3478f6;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #3478f6;
}

QComboBox {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #cfd6de;
    border-radius: 7px;
    padding: 7px 9px;
    min-height: 18px;
}

QComboBox:hover,
QComboBox:focus {
    border-color: #3478f6;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #cfd6de;
    selection-background-color: #eaf2ff;
}

QPushButton {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #cfd6de;
    border-radius: 7px;
    padding: 7px 12px;
    min-height: 18px;
}

QPushButton:hover {
    background: #f5f7fa;
    border-color: #aeb8c4;
}

QPushButton:pressed {
    background: #e9edf2;
}

QPushButton#PrimaryButton {
    background: #3478f6;
    color: #ffffff;
    border: 1px solid #3478f6;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background: #2f6fdf;
}

QPushButton#ThemeButton {
    min-width: 110px;
    font-weight: 600;
}

QTableView {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #dfe3e8;
    border-radius: 10px;
    gridline-color: #edf0f3;
    alternate-background-color: #fafbfc;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}

QTableView::item {
    padding: 7px;
    border-bottom: 1px solid #f0f2f5;
}

QHeaderView::section {
    background: #f8fafc;
    color: #475467;
    border: none;
    border-bottom: 1px solid #dfe3e8;
    padding: 9px 8px;
    font-weight: 600;
}

QScrollBar:vertical {
    background: #f1f3f5;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #c7cdd4;
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

QScrollBar:horizontal {
    background: #f1f3f5;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #c7cdd4;
    min-width: 30px;
    border-radius: 6px;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QProgressBar {
    background: #e9edf2;
    border: none;
    border-radius: 4px;
    max-height: 8px;
}

QProgressBar::chunk {
    background: #3478f6;
    border-radius: 4px;
}

QStatusBar {
    background: #ffffff;
    color: #475467;
    border-top: 1px solid #dfe3e8;
}

QToolTip {
    background: #ffffff;
    color: #20242a;
    border: 1px solid #cfd6de;
}
"""


DARK_STYLE_SHEET = """
QMainWindow,
QWidget#CentralWidget {
    background: #111827;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #e5e7eb;
}

QMenuBar {
    background: #161d2a;
    color: #e5e7eb;
    border-bottom: 1px solid #2b3545;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 5px;
}

QMenuBar::item:selected {
    background: #263244;
}

QMenu {
    background: #182130;
    color: #e5e7eb;
    border: 1px solid #334155;
    padding: 5px;
}

QMenu::item {
    padding: 7px 28px 7px 10px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: #263d61;
}

QMenu::separator {
    height: 1px;
    background: #334155;
    margin: 5px 8px;
}

QFrame#InfoCard,
QFrame#SearchPanel,
QFrame#FilterPanel {
    background: #182130;
    border: 1px solid #2b3545;
    border-radius: 10px;
}

QLabel#AppTitle {
    font-size: 20pt;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#LocationLabel {
    color: #9ca3af;
    font-size: 9.5pt;
}

QLabel#CardTitle {
    color: #9ca3af;
    font-size: 8.5pt;
    font-weight: 600;
}

QLabel#CardValue {
    color: #f8fafc;
    font-size: 14pt;
    font-weight: 700;
}

QLineEdit {
    background: #111827;
    color: #f3f4f6;
    border: 1px solid #3a4658;
    border-radius: 7px;
    padding: 8px 10px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #60a5fa;
}

QComboBox {
    background: #111827;
    color: #f3f4f6;
    border: 1px solid #3a4658;
    border-radius: 7px;
    padding: 7px 9px;
    min-height: 18px;
}

QComboBox:hover,
QComboBox:focus {
    border-color: #60a5fa;
}

QComboBox:disabled {
    background: #161d2a;
    color: #6b7280;
}

QComboBox QAbstractItemView {
    background: #182130;
    color: #e5e7eb;
    border: 1px solid #334155;
    selection-background-color: #263d61;
}

QLineEdit:disabled {
    background: #161d2a;
    color: #6b7280;
}

QPushButton {
    background: #202b3b;
    color: #e5e7eb;
    border: 1px solid #3a4658;
    border-radius: 7px;
    padding: 7px 12px;
    min-height: 18px;
}

QPushButton:hover {
    background: #29364a;
    border-color: #526177;
}

QPushButton:pressed {
    background: #182130;
}

QPushButton:disabled {
    background: #182130;
    color: #6b7280;
    border-color: #2b3545;
}

QPushButton#PrimaryButton {
    background: #3b82f6;
    color: #ffffff;
    border: 1px solid #3b82f6;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background: #2563eb;
}

QPushButton#ThemeButton {
    min-width: 110px;
    font-weight: 600;
}

QTableView {
    background: #161d2a;
    color: #e5e7eb;
    border: 1px solid #2b3545;
    border-radius: 10px;
    gridline-color: #263244;
    alternate-background-color: #192334;
    selection-background-color: #1e4f8f;
    selection-color: #ffffff;
}

QTableView:disabled {
    color: #7c8798;
}

QTableView::item {
    padding: 7px;
    border-bottom: 1px solid #222d3d;
}

QHeaderView::section {
    background: #202b3b;
    color: #cbd5e1;
    border: none;
    border-bottom: 1px solid #334155;
    padding: 9px 8px;
    font-weight: 600;
}

QScrollBar:vertical {
    background: #111827;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #3d4a5d;
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #526177;
}

QScrollBar:horizontal {
    background: #111827;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #3d4a5d;
    min-width: 30px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background: #526177;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QProgressBar {
    background: #273244;
    border: none;
    border-radius: 4px;
    max-height: 8px;
}

QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 4px;
}

QStatusBar {
    background: #161d2a;
    color: #9ca3af;
    border-top: 1px solid #2b3545;
}

QToolTip {
    background: #202b3b;
    color: #f3f4f6;
    border: 1px solid #465469;
}

QMessageBox {
    background: #182130;
}
"""


def resource_path(*parts: str) -> str:
    """Return a resource path that works both from source and PyInstaller."""
    base_dir = getattr(
        sys,
        "_MEIPASS",
        os.path.dirname(os.path.abspath(__file__)),
    )
    return os.path.join(base_dir, *parts)


class InfoCard(QtWidgets.QFrame):
    """Small reusable card used for metadata summaries."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("InfoCard")
        self.setMinimumHeight(82)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(3)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("CardTitle")

        self.value_label = QtWidgets.QLabel(value)
        self.value_label.setObjectName("CardValue")
        self.value_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class FileTableModel(QtCore.QAbstractTableModel):
    """Lightweight model for efficiently displaying file data."""

    HEADERS = ("Size", "Path")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows = []

    def set_data_frame(self, data_frame) -> None:
        self.beginResetModel()

        if data_frame is None or data_frame.empty:
            self._rows = []
        else:
            self._rows = list(
                data_frame[
                    ["size", "path"]
                ].itertuples(
                    index=False,
                    name=None,
                )
            )

        self.endResetModel()

    def rowCount(
        self,
        parent=QtCore.QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0

        return len(self._rows)

    def columnCount(
        self,
        parent=QtCore.QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0

        return 2

    def data(
        self,
        index,
        role=QtCore.Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= len(self._rows):
            return None

        if role == QtCore.Qt.DisplayRole:
            return str(
                self._rows[row][column]
            )

        if (
            role == QtCore.Qt.TextAlignmentRole
            and column == 0
        ):
            return int(
                QtCore.Qt.AlignRight
                | QtCore.Qt.AlignVCenter
            )

        if (
            role == QtCore.Qt.ToolTipRole
            and column == 1
        ):
            return str(
                self._rows[row][1]
            )

        return None

    def headerData(
        self,
        section,
        orientation,
        role=QtCore.Qt.DisplayRole,
    ):
        if role != QtCore.Qt.DisplayRole:
            return None

        if (
            orientation == QtCore.Qt.Horizontal
            and 0 <= section < 2
        ):
            return self.HEADERS[section]

        return None

    def path_at(
        self,
        row: int,
    ) -> Optional[str]:
        if 0 <= row < len(self._rows):
            return str(
                self._rows[row][1]
            )

        return None


class TaskThread(QtCore.QThread):
    """Run blocking Python work without freezing the Qt event loop."""

    result = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        function: Callable,
        *args,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.function = function
        self.args = args

    def run(self) -> None:
        try:
            result = self.function(
                *self.args
            )

        except Exception:
            self.error.emit(
                traceback.format_exc()
            )

        else:
            self.result.emit(result)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(
        self,
        app: object,
        database: object,
    ) -> None:
        """Build the interface, connect events and load saved data."""
        super().__init__()

        self.app_name = APP_NAME
        self.database = database
        self.limit: Optional[int] = 1000
        self.current_page = 1
        self.worker_thread: Optional[
            TaskThread
        ] = None

        self._busy = False
        self.dark_mode = True

        app.setApplicationName(
            self.app_name
        )

        app.setStyle("Fusion")

        self.setup_interface()
        self.setup_menus()
        self.apply_theme()

        if self.database.load_data():
            self.print_data()
            self.print_metadata()

        else:
            self.print_data()
            self.print_metadata()

            self.show_status(
                "Ready — no saved database loaded."
            )

        # Maximized, rather than borderless fullscreen:
        # window controls and Windows taskbar remain available.
        self.setWindowState(
            self.windowState()
            | QtCore.Qt.WindowMaximized
        )

    def setup_interface(self) -> None:
        """Create the main window and all visible widgets."""

        self.setWindowTitle(
            self.app_name
        )

        self.setMinimumSize(
            900,
            600,
        )

        self.resize(
            1180,
            760,
        )

        icon_path = resource_path(
            "Images",
            "database.png",
        )

        if os.path.exists(icon_path):
            self.setWindowIcon(
                QtGui.QIcon(icon_path)
            )

        central_widget = QtWidgets.QWidget(
            self
        )

        central_widget.setObjectName(
            "CentralWidget"
        )

        self.setCentralWidget(
            central_widget
        )

        outer_layout = QtWidgets.QVBoxLayout(
            central_widget
        )

        outer_layout.setContentsMargins(
            20,
            18,
            20,
            14,
        )

        outer_layout.setSpacing(14)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(12)

        header_text_layout = QtWidgets.QVBoxLayout()
        header_text_layout.setSpacing(2)

        self.title_label = QtWidgets.QLabel(
            self.app_name
        )

        self.title_label.setObjectName(
            "AppTitle"
        )

        self.location_label = QtWidgets.QLabel(
            "No directory loaded"
        )

        self.location_label.setObjectName(
            "LocationLabel"
        )

        self.location_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )

        header_text_layout.addWidget(
            self.title_label
        )

        header_text_layout.addWidget(
            self.location_label
        )

        self.theme_button = QtWidgets.QPushButton(
            "Dark mode"
        )

        self.theme_button.setObjectName(
            "ThemeButton"
        )

        self.theme_button.setToolTip(
            "Switch between light and dark theme "
            "(Ctrl+Shift+D)"
        )

        self.theme_button.clicked.connect(
            self.toggle_theme
        )

        header_layout.addLayout(
            header_text_layout,
            1,
        )

        header_layout.addWidget(
            self.theme_button,
            0,
            QtCore.Qt.AlignTop,
        )

        outer_layout.addLayout(
            header_layout
        )

        # Metadata cards
        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(10)

        self.date_card = InfoCard(
            "SCAN DATE"
        )

        self.files_card = InfoCard(
            "FOLDERS / FILES"
        )
        self.files_card.value_label.setWordWrap(True)
        self.files_card.value_label.setStyleSheet(
            "font-size: 11.5pt;"
        )

        self.size_card = InfoCard(
            "TOTAL SIZE"
        )

        self.time_card = InfoCard(
            "TIMINGS"
        )
        self.time_card.setMinimumHeight(104)
        self.time_card.value_label.setWordWrap(True)
        self.time_card.value_label.setStyleSheet(
            "font-size: 10.5pt;"
        )

        for card in (
            self.date_card,
            self.files_card,
            self.size_card,
            self.time_card,
        ):
            cards_layout.addWidget(
                card,
                1,
            )

        outer_layout.addLayout(
            cards_layout
        )

        # Search panel
        search_panel = QtWidgets.QFrame()
        search_panel.setObjectName(
            "SearchPanel"
        )

        search_layout = QtWidgets.QHBoxLayout(
            search_panel
        )

        search_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        search_layout.setSpacing(8)

        self.search_bar = QtWidgets.QLineEdit()

        self.search_bar.setClearButtonEnabled(
            False
        )

        self.search_bar.setPlaceholderText(
            "Search paths — e.g. "
            "ext:pdf,xlsx && >10mb, "
            "%invoice%, !temp"
        )

        self.search_bar.setToolTip(
            "Search syntax:\n"
            "text        contains text\n"
            "%text%      case-insensitive contains\n"
            "^text       starts with\n"
            "text$       ends with\n"
            "!text       exclude text\n"
            "ext:pdf,xlsx exact file extension(s)\n"
            ">10mb       larger than 10 MB\n"
            "<500kb      smaller than 500 KB\n"
            "Use ' && ' to combine filters."
        )

        self.search_bar.returnPressed.connect(
            self.search_data
        )

        self.search_button = QtWidgets.QPushButton(
            "Search"
        )

        self.search_button.setObjectName(
            "PrimaryButton"
        )

        self.search_button.clicked.connect(
            self.search_data
        )

        self.clear_search_button = QtWidgets.QPushButton(
            "Clear"
        )

        self.clear_search_button.clicked.connect(
            self.clear_search
        )

        self.filter_toggle_button = QtWidgets.QPushButton(
            "Filters ▾"
        )

        self.filter_toggle_button.setToolTip(
            "Show or hide the visual filter builder."
        )

        self.filter_toggle_button.clicked.connect(
            self.toggle_filter_panel
        )

        self.result_summary = QtWidgets.QLabel(
            ""
        )

        self.result_summary.setMinimumWidth(
            180
        )

        self.result_summary.setAlignment(
            QtCore.Qt.AlignRight
            | QtCore.Qt.AlignVCenter
        )

        search_layout.addWidget(
            self.search_bar,
            1,
        )

        search_layout.addWidget(
            self.search_button
        )

        search_layout.addWidget(
            self.clear_search_button
        )

        search_layout.addWidget(
            self.filter_toggle_button
        )

        search_layout.addWidget(
            self.result_summary
        )

        outer_layout.addWidget(
            search_panel
        )

        # Visual filter builder. It compiles controls into the same advanced
        # query syntax used by the search bar, keeping a single search engine.
        self.filter_panel = QtWidgets.QFrame()
        self.filter_panel.setObjectName(
            "FilterPanel"
        )
        self.filter_panel.hide()

        filter_layout = QtWidgets.QGridLayout(
            self.filter_panel
        )
        filter_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )
        filter_layout.setHorizontalSpacing(8)
        filter_layout.setVerticalSpacing(8)

        self.filter_text_input = QtWidgets.QLineEdit()
        self.filter_text_input.setPlaceholderText(
            "Text in path"
        )

        self.filter_mode_combo = QtWidgets.QComboBox()
        self.filter_mode_combo.addItems(
            [
                "Contains",
                "Contains (case-insensitive)",
                "Starts with",
                "Ends with",
                "Excludes",
            ]
        )

        self.filter_extension_input = QtWidgets.QLineEdit()
        self.filter_extension_input.setPlaceholderText(
            "Extensions: pdf, xlsx"
        )
        self.filter_extension_input.setToolTip(
            "Comma-separated extensions. Dots are optional."
        )

        self.filter_min_size_input = QtWidgets.QLineEdit()
        self.filter_min_size_input.setPlaceholderText(
            "Minimum size"
        )

        self.filter_min_unit_combo = QtWidgets.QComboBox()
        self.filter_min_unit_combo.addItems(
            [
                "Bytes",
                "KB",
                "MB",
                "GB",
                "TB",
            ]
        )
        self.filter_min_unit_combo.setCurrentText(
            "MB"
        )

        self.filter_max_size_input = QtWidgets.QLineEdit()
        self.filter_max_size_input.setPlaceholderText(
            "Maximum size"
        )

        self.filter_max_unit_combo = QtWidgets.QComboBox()
        self.filter_max_unit_combo.addItems(
            [
                "Bytes",
                "KB",
                "MB",
                "GB",
                "TB",
            ]
        )
        self.filter_max_unit_combo.setCurrentText(
            "MB"
        )

        self.apply_filters_button = QtWidgets.QPushButton(
            "Apply Filters"
        )
        self.apply_filters_button.setObjectName(
            "PrimaryButton"
        )
        self.apply_filters_button.clicked.connect(
            self.apply_filter_builder
        )

        self.reset_filters_button = QtWidgets.QPushButton(
            "Reset"
        )
        self.reset_filters_button.clicked.connect(
            self.reset_filter_builder
        )

        filter_layout.addWidget(
            QtWidgets.QLabel("Text"),
            0,
            0,
        )
        filter_layout.addWidget(
            self.filter_text_input,
            0,
            1,
        )
        filter_layout.addWidget(
            self.filter_mode_combo,
            0,
            2,
        )
        filter_layout.addWidget(
            QtWidgets.QLabel("Extension"),
            0,
            3,
        )
        filter_layout.addWidget(
            self.filter_extension_input,
            0,
            4,
        )

        filter_layout.addWidget(
            QtWidgets.QLabel("Size"),
            1,
            0,
        )
        filter_layout.addWidget(
            self.filter_min_size_input,
            1,
            1,
        )
        filter_layout.addWidget(
            self.filter_min_unit_combo,
            1,
            2,
        )
        filter_layout.addWidget(
            self.filter_max_size_input,
            1,
            3,
        )
        filter_layout.addWidget(
            self.filter_max_unit_combo,
            1,
            4,
        )
        filter_layout.addWidget(
            self.apply_filters_button,
            0,
            5,
        )
        filter_layout.addWidget(
            self.reset_filters_button,
            1,
            5,
        )

        filter_layout.setColumnStretch(1, 2)
        filter_layout.setColumnStretch(4, 1)

        self.filter_text_input.returnPressed.connect(
            self.apply_filter_builder
        )
        self.filter_extension_input.returnPressed.connect(
            self.apply_filter_builder
        )
        self.filter_min_size_input.returnPressed.connect(
            self.apply_filter_builder
        )
        self.filter_max_size_input.returnPressed.connect(
            self.apply_filter_builder
        )

        outer_layout.addWidget(
            self.filter_panel
        )

        # File table
        self.table_model = FileTableModel(
            self
        )

        self.table = QtWidgets.QTableView()

        self.table.setModel(
            self.table_model
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )

        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(False)

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.verticalHeader().setDefaultSectionSize(
            34
        )

        self.table.doubleClicked.connect(
            self.open_parent_directory
        )

        header = self.table.horizontalHeader()

        header.setSectionsClickable(
            True
        )

        header.setHighlightSections(
            False
        )

        header.setSortIndicatorShown(
            True
        )

        header.setSortIndicator(
            -1,
            QtCore.Qt.AscendingOrder,
        )

        header.sectionClicked.connect(
            self.sort_from_header
        )

        header.setSectionResizeMode(
            0,
            QtWidgets.QHeaderView.Fixed,
        )

        header.resizeSection(
            0,
            135,
        )

        header.setSectionResizeMode(
            1,
            QtWidgets.QHeaderView.Stretch,
        )

        outer_layout.addWidget(
            self.table,
            1,
        )

        # Pagination controls. ``Visible Rows`` is now the page size.
        pagination_layout = QtWidgets.QHBoxLayout()
        pagination_layout.setSpacing(8)

        self.first_page_button = QtWidgets.QPushButton("First")
        self.previous_page_button = QtWidgets.QPushButton("Previous")
        self.page_label = QtWidgets.QLabel("Page 1 of 1")
        self.page_label.setAlignment(QtCore.Qt.AlignCenter)
        self.page_label.setMinimumWidth(130)
        self.page_range_label = QtWidgets.QLabel("0 files")
        self.page_range_label.setAlignment(
            QtCore.Qt.AlignCenter
        )
        self.next_page_button = QtWidgets.QPushButton("Next")
        self.last_page_button = QtWidgets.QPushButton("Last")

        self.first_page_button.clicked.connect(
            self.go_to_first_page
        )
        self.previous_page_button.clicked.connect(
            self.go_to_previous_page
        )
        self.next_page_button.clicked.connect(
            self.go_to_next_page
        )
        self.last_page_button.clicked.connect(
            self.go_to_last_page
        )

        pagination_layout.addStretch(1)
        pagination_layout.addWidget(self.first_page_button)
        pagination_layout.addWidget(self.previous_page_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addWidget(self.last_page_button)
        pagination_layout.addSpacing(10)
        pagination_layout.addWidget(self.page_range_label)
        pagination_layout.addStretch(1)

        outer_layout.addLayout(
            pagination_layout
        )

        # Status bar
        self.status_message = QtWidgets.QLabel(
            "Ready"
        )

        self.statusBar().addWidget(
            self.status_message,
            1,
        )

        self.progress_bar = QtWidgets.QProgressBar()

        self.progress_bar.setRange(
            0,
            0,
        )

        self.progress_bar.setFixedWidth(
            150
        )

        self.progress_bar.hide()

        self.statusBar().addPermanentWidget(
            self.progress_bar
        )

        QtWidgets.QShortcut(
            QtGui.QKeySequence(
                "Ctrl+F"
            ),
            self,
            self.focus_search,
        )

        QtWidgets.QShortcut(
            QtGui.QKeySequence(
                "Escape"
            ),
            self,
            self.clear_search,
        )

        QtWidgets.QShortcut(
            QtGui.QKeySequence(
                "Ctrl+Shift+D"
            ),
            self,
            self.toggle_theme,
        )

    def setup_menus(self) -> None:
        """Create menus and actions."""

        menubar = self.menuBar()

        file_menu = menubar.addMenu(
            "File"
        )

        view_menu = menubar.addMenu(
            "View"
        )

        help_menu = menubar.addMenu(
            "Help"
        )

        self.action_gather = QtWidgets.QAction(
            "Gather Data…",
            self,
        )

        self.action_gather.setShortcut(
            "Ctrl+G"
        )

        self.action_gather.triggered.connect(
            self.gather_data
        )

        self.action_update = QtWidgets.QAction(
            "Update Data",
            self,
        )

        self.action_update.setShortcut(
            "Ctrl+U"
        )

        self.action_update.triggered.connect(
            self.update_data
        )

        self.action_plot = QtWidgets.QAction(
            "Plot Size Distribution",
            self,
        )

        self.action_plot.triggered.connect(
            self.plot_data
        )

        self.action_plot_file_types = QtWidgets.QAction(
            "Plot File Types by Size",
            self,
        )

        self.action_plot_file_types.triggered.connect(
            self.plot_file_types_by_size
        )

        export_menu = file_menu.addMenu(
            "Export As"
        )

        export_options = (
            (
                "CSV Snapshot (Backup)",
                "snapshot",
            ),
            (
                "Excel File",
                "excel",
            ),
            (
                "HTML Table",
                "html",
            ),
            (
                "CSV File",
                "csv",
            ),
            (
                "JSON File",
                "json",
            ),
            (
                "Text File",
                "text",
            ),
        )

        self.export_actions = []

        for label, kind in export_options:

            action = QtWidgets.QAction(
                label,
                self,
            )

            action.triggered.connect(
                lambda checked=False,
                export_kind=kind:
                self.export_data(
                    export_kind
                )
            )

            export_menu.addAction(
                action
            )

            self.export_actions.append(
                action
            )

        self.action_import = QtWidgets.QAction(
            "Import CSV Snapshot…",
            self,
        )

        self.action_import.setShortcut(
            "Ctrl+I"
        )

        self.action_import.triggered.connect(
            self.import_data
        )

        self.action_exit = QtWidgets.QAction(
            "Exit",
            self,
        )

        self.action_exit.setShortcut(
            "Ctrl+Q"
        )

        self.action_exit.triggered.connect(
            self.close
        )

        file_menu.addAction(
            self.action_gather
        )

        file_menu.addAction(
            self.action_update
        )

        file_menu.addSeparator()

        file_menu.addAction(
            self.action_plot
        )
        file_menu.addAction(
            self.action_plot_file_types
        )

        file_menu.addSeparator()

        file_menu.addMenu(
            export_menu
        )

        file_menu.addAction(
            self.action_import
        )

        file_menu.addSeparator()

        file_menu.addAction(
            self.action_exit
        )

        self.limit_menu = view_menu.addMenu(
            "Rows per Page"
        )

        for value in (
            250,
            500,
            1000,
            2000,
        ):

            action = QtWidgets.QAction(
                f"{value:,}",
                self,
            )

            action.triggered.connect(
                lambda checked=False,
                new_limit=value:
                self.set_limit(
                    new_limit
                )
            )

            self.limit_menu.addAction(
                action
            )

        self.limit_menu.addSeparator()

        unlimited_action = QtWidgets.QAction(
            "All rows",
            self,
        )

        unlimited_action.triggered.connect(
            lambda:
            self.set_limit(
                None
            )
        )

        self.limit_menu.addAction(
            unlimited_action
        )

        self.update_limit_menu_title()

        view_menu.addSeparator()

        self.action_theme = QtWidgets.QAction(
            "Dark mode",
            self,
        )

        self.action_theme.setShortcut(
            "Ctrl+Shift+D"
        )

        self.action_theme.triggered.connect(
            self.toggle_theme
        )

        view_menu.addAction(
            self.action_theme
        )

        action_github = QtWidgets.QAction(
            "Visit GitHub",
            self,
        )

        action_github.triggered.connect(
            lambda:
            self.visit(
                "GitHub"
            )
        )

        action_manual = QtWidgets.QAction(
            "Manual",
            self,
        )

        action_manual.triggered.connect(
            lambda:
            self.visit(
                "Manual"
            )
        )

        help_menu.addAction(
            action_manual
        )

        help_menu.addAction(
            action_github
        )

    def apply_theme(self) -> None:
        """Apply the active theme and update theme controls."""

        if self.dark_mode:

            self.setStyleSheet(
                DARK_STYLE_SHEET
            )

            self.theme_button.setText(
                "Light mode"
            )

            self.action_theme.setText(
                "Light mode"
            )

        else:

            self.setStyleSheet(
                LIGHT_STYLE_SHEET
            )

            self.theme_button.setText(
                "Dark mode"
            )

            self.action_theme.setText(
                "Dark mode"
            )

        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )

        self.update()

    def toggle_theme(self) -> None:
        """Switch between light and dark themes."""

        self.dark_mode = (
            not self.dark_mode
        )

        self.apply_theme()

    def gather_data(self) -> None:
        """Choose a directory and scan it in a background thread."""

        if self._busy:
            return

        dirpath = (
            QtWidgets.QFileDialog
            .getExistingDirectory(
                self,
                "Select Directory",
            )
        )

        if not dirpath:
            return

        dirpath = os.path.normpath(
            dirpath
        )

        self.start_background_task(
            self.database.gather_data,
            dirpath,
            message=(
                f"Scanning {dirpath}…"
            ),
            on_success=(
                self._scan_finished
            ),
        )

    def update_data(self) -> None:
        """Rescan the currently loaded directory."""

        if self._busy:
            return

        location = (
            self.database
            .metadata
            .get(
                "location",
                "",
            )
        )

        if (
            not location
            or not os.path.isdir(
                location
            )
        ):

            self.show_warning(
                "Update Data",
                "There is no valid "
                "directory to update. "
                "Gather data first.",
            )

            return

        self.start_background_task(
            self.database.gather_data,
            location,
            message=(
                f"Updating {location}…"
            ),
            on_success=(
                self._scan_finished
            ),
        )

    def _scan_finished(
        self,
        _result=None,
    ) -> None:

        self.current_page = 1
        self.print_data()
        self.print_metadata()

        self.show_status(
            "Scan complete — "
            f"{self.database.metadata['total_files']:,} "
            "files."
        )

    def toggle_filter_panel(self) -> None:
        """Show or hide the visual filter builder."""
        visible = not self.filter_panel.isVisible()
        self.filter_panel.setVisible(
            visible
        )
        self.filter_toggle_button.setText(
            "Filters ▴"
            if visible
            else "Filters ▾"
        )

    @staticmethod
    def _builder_size_token(
        value: str,
        unit: str,
    ) -> Optional[str]:
        """Convert a visual size input to advanced-search size syntax."""
        value = value.strip()
        if not value:
            return None

        try:
            numeric_value = float(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid size value: {value}"
            ) from exc

        if numeric_value < 0:
            raise ValueError(
                "File size filters cannot be negative."
            )

        unit_map = {
            "Bytes": "b",
            "KB": "kb",
            "MB": "mb",
            "GB": "gb",
            "TB": "tb",
        }

        normalized_number = (
            str(int(numeric_value))
            if numeric_value.is_integer()
            else str(numeric_value)
        )

        return (
            f"{normalized_number}"
            f"{unit_map[unit]}"
        )

    def apply_filter_builder(self) -> None:
        """Compile visual filters into the existing advanced query syntax."""
        if self._busy:
            return

        tokens = []
        text_value = self.filter_text_input.text().strip()

        if text_value:
            mode = self.filter_mode_combo.currentText()
            text_tokens = {
                "Contains": text_value,
                "Contains (case-insensitive)": f"%{text_value}%",
                "Starts with": f"^{text_value}",
                "Ends with": f"{text_value}$",
                "Excludes": f"!{text_value}",
            }
            tokens.append(
                text_tokens[mode]
            )

        extensions = [
            extension.strip().lstrip(".")
            for extension in self.filter_extension_input.text().split(",")
            if extension.strip()
        ]
        if extensions:
            tokens.append(
                "ext:" + ",".join(extensions)
            )

        try:
            minimum = self._builder_size_token(
                self.filter_min_size_input.text(),
                self.filter_min_unit_combo.currentText(),
            )
            maximum = self._builder_size_token(
                self.filter_max_size_input.text(),
                self.filter_max_unit_combo.currentText(),
            )
        except ValueError as exc:
            self.show_warning(
                "Filters",
                str(exc),
            )
            return

        if minimum:
            tokens.append(
                f">={minimum}"
            )

        if maximum:
            tokens.append(
                f"<={maximum}"
            )

        if minimum and maximum:
            minimum_bytes = self.database.parse_bytes(
                minimum
            )
            maximum_bytes = self.database.parse_bytes(
                maximum
            )
            if (
                minimum_bytes is not None
                and maximum_bytes is not None
                and minimum_bytes > maximum_bytes
            ):
                self.show_warning(
                    "Filters",
                    "Minimum size cannot be larger than maximum size.",
                )
                return

        self.search_bar.setText(
            " && ".join(tokens)
        )
        self.search_data()

    def _clear_filter_builder_fields(self) -> None:
        """Reset visual filter controls without triggering a search."""
        self.filter_text_input.clear()
        self.filter_mode_combo.setCurrentIndex(0)
        self.filter_extension_input.clear()
        self.filter_min_size_input.clear()
        self.filter_min_unit_combo.setCurrentText(
            "MB"
        )
        self.filter_max_size_input.clear()
        self.filter_max_unit_combo.setCurrentText(
            "MB"
        )

    def reset_filter_builder(self) -> None:
        """Clear visual and advanced filters and restore all rows."""
        if self._busy:
            return

        self._clear_filter_builder_fields()
        self.search_bar.clear()
        self.database.search(
            ""
        )
        self.current_page = 1
        self.print_data()

    def search_data(self) -> None:
        """Apply the current search query and refresh the table."""

        if self._busy:
            return

        try:
            self.database.search(
                self.search_bar
                .text()
                .strip()
            )

        except Exception as exc:

            self.show_error(
                "Search Error",
                str(exc),
            )

            return

        self.current_page = 1
        self.print_data()

    def clear_search(self) -> None:

        if self._busy:
            return

        if (
            not self.search_bar.text()
            and not self.database.is_sliced()
        ):
            return

        self.search_bar.clear()
        self._clear_filter_builder_fields()

        self.database.search(
            ""
        )

        self.current_page = 1
        self.print_data()

        self.search_bar.setFocus()

    def focus_search(self) -> None:

        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def sort_from_header(
        self,
        section: int,
    ) -> None:

        if section == 0:
            self.sort_by(
                "size"
            )

        elif section == 1:
            self.sort_by(
                "name"
            )

    def sort_by(
        self,
        attr: str,
    ) -> None:
        """Sort using the database layer, then refresh the view."""

        if self._busy:
            return

        self.database.sort_by(
            attr
        )

        self.current_page = 1
        self.print_data()
        self.update_sort_indicator()

    def update_sort_indicator(
        self,
    ) -> None:

        sort_kind = (
            self.database.sorted
        )

        header = (
            self.table
            .horizontalHeader()
        )

        if not sort_kind:

            header.setSortIndicator(
                -1,
                QtCore.Qt.AscendingOrder,
            )

            return

        section = (
            0
            if sort_kind.startswith(
                "size"
            )
            else 1
        )

        order = (
            QtCore.Qt.AscendingOrder
            if sort_kind.endswith(
                "asc"
            )
            else
            QtCore.Qt.DescendingOrder
        )

        header.setSortIndicator(
            section,
            order,
        )

    def open_parent_directory(
        self,
        index: QtCore.QModelIndex,
    ) -> None:
        """Open the selected file's parent directory."""

        row = index.row()

        stored_path = (
            self.table_model
            .path_at(
                row
            )
        )

        if not stored_path:
            return

        location = (
            self.database
            .metadata
            .get(
                "location",
                "",
            )
        )

        if stored_path.startswith(
            "~"
        ):

            filepath = stored_path.replace(
                "~",
                location,
                1,
            )

        else:
            filepath = stored_path

        filepath = os.path.normpath(
            filepath
        )

        parent_directory = os.path.dirname(
            filepath
        )

        if not os.path.isdir(
            parent_directory
        ):

            self.show_warning(
                "Directory Not Found",
                "The parent directory "
                "no longer exists:\n\n"
                f"{parent_directory}",
            )

            return

        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(
                parent_directory
            )
        )

    def set_limit(
        self,
        new_limit: Optional[int],
    ) -> None:

        if new_limit == self.limit:
            return

        self.limit = new_limit
        self.current_page = 1

        self.update_limit_menu_title()
        self.print_data()

    def update_limit_menu_title(
        self,
    ) -> None:

        if self.limit is None:
            self.limit_menu.setTitle(
                "Rows per Page: All"
            )
        else:
            self.limit_menu.setTitle(
                "Rows per Page: "
                f"{self.limit:,}"
            )

    def _page_count(self, total_results: int) -> int:
        """Return the number of pages for the current result set."""
        if self.limit is None or total_results <= 0:
            return 1

        return max(
            1,
            (total_results + self.limit - 1) // self.limit,
        )

    def go_to_first_page(self) -> None:
        if self._busy or self.current_page == 1:
            return
        self.current_page = 1
        self.print_data()

    def go_to_previous_page(self) -> None:
        if self._busy or self.current_page <= 1:
            return
        self.current_page -= 1
        self.print_data()

    def go_to_next_page(self) -> None:
        if self._busy:
            return
        total_results = self.database.get_data()[0].shape[0]
        total_pages = self._page_count(total_results)
        if self.current_page >= total_pages:
            return
        self.current_page += 1
        self.print_data()

    def go_to_last_page(self) -> None:
        if self._busy:
            return
        total_results = self.database.get_data()[0].shape[0]
        total_pages = self._page_count(total_results)
        if self.current_page == total_pages:
            return
        self.current_page = total_pages
        self.print_data()

    def _update_pagination_controls(
        self,
        total_results: int,
        start_index: int,
        end_index: int,
    ) -> None:
        """Refresh page labels and navigation button availability."""
        total_pages = self._page_count(total_results)
        self.current_page = min(
            max(1, self.current_page),
            total_pages,
        )

        self.page_label.setText(
            f"Page {self.current_page:,} of {total_pages:,}"
        )

        if total_results:
            self.page_range_label.setText(
                f"{start_index + 1:,}–{end_index:,} of "
                f"{total_results:,}"
            )
        else:
            self.page_range_label.setText(
                "0 files"
            )

        can_go_back = self.current_page > 1 and not self._busy
        can_go_forward = (
            self.current_page < total_pages
            and not self._busy
        )
        self.first_page_button.setEnabled(can_go_back)
        self.previous_page_button.setEnabled(can_go_back)
        self.next_page_button.setEnabled(can_go_forward)
        self.last_page_button.setEnabled(can_go_forward)

    def print_data(self) -> None:
        """Refresh the table using the current result page."""
        data, matches_size = self.database.get_data()
        total_results = data.shape[0]
        total_pages = self._page_count(total_results)
        self.current_page = min(
            max(1, self.current_page),
            total_pages,
        )

        if self.limit is None:
            start_index = 0
            end_index = total_results
            visible_data = data
        else:
            start_index = (
                self.current_page - 1
            ) * self.limit
            end_index = min(
                start_index + self.limit,
                total_results,
            )
            visible_data = data.iloc[
                start_index:end_index
            ]

        self.table_model.set_data_frame(
            visible_data
        )
        self.update_sort_indicator()
        self._update_pagination_controls(
            total_results,
            start_index,
            end_index,
        )

        if self.database.is_sliced():
            self.result_summary.setText(
                f"{total_results:,} results "
                f"• {matches_size}"
            )
        else:
            self.result_summary.setText(
                f"{total_results:,} files "
                f"• {matches_size}"
            )

        if total_results and self.limit is not None:
            result_kind = (
                "matching files"
                if self.database.is_sliced()
                else "files"
            )
            self.show_status(
                f"Showing {start_index + 1:,}–{end_index:,} "
                f"of {total_results:,} {result_kind}."
            )
        elif not self._busy:
            self.show_status(
                f"Showing {total_results:,} files."
            )

    def print_metadata(self) -> None:
        """Refresh location, metadata cards and timing breakdown."""
        (
            location,
            date,
            _process_time,
            total_folders,
            total_files,
            total_size,
        ) = self.database.get_printable_metadata()

        self.location_label.setText(
            location
            or "No directory loaded"
        )
        self.setWindowTitle(
            (
                f"{self.app_name} — {location}"
                if location
                else self.app_name
            )
        )
        self.date_card.set_value(
            date or "—"
        )
        folders_text = (
            f"{total_folders:,} folders"
            if total_folders is not None
            else "— folders"
        )
        self.files_card.set_value(
            f"{folders_text}\n{total_files:,} files"
        )
        self.size_card.set_value(
            total_size
        )

        try:
            timings = self.database.get_timing_details()
        except AttributeError:
            timings = {
                "scan": "—",
                "processing": "—",
                "database": "—",
                "total": _process_time or "—",
            }

        timing_text = (
            f"Scan {timings['scan']}  •  "
            f"Process {timings['processing']}\n"
            f"DB save {timings['database']}  •  "
            f"Total {timings['total']}"
        )
        self.time_card.set_value(
            timing_text
        )
        self.time_card.setToolTip(
            "Filesystem scan: " + timings["scan"] + "\n"
            "DataFrame/formatting: " + timings["processing"] + "\n"
            "MongoDB snapshot save: " + timings["database"] + "\n"
            "Total operation: " + timings["total"]
        )

    def plot_data(self) -> None:
        """Plot the size distribution for the current filtered results."""
        if self.database.matches.empty:
            self.show_warning(
                "Plot",
                "There are no matching files to plot.",
            )
            return

        try:
            self.database.plot_data(
                dark_mode=self.dark_mode
            )
        except Exception as exc:
            self.show_error(
                "Plot Error",
                str(exc),
            )

    def plot_file_types_by_size(self) -> None:
        """Plot file types by total size for the current filtered results."""
        if self.database.matches.empty:
            self.show_warning(
                "Plot",
                "There are no matching files to plot.",
            )
            return

        try:
            self.database.plot_file_types_by_size(
                dark_mode=self.dark_mode
            )
        except Exception as exc:
            self.show_error(
                "Plot Error",
                str(exc),
            )

    def _select_export_path(
        self,
        kind: str,
    ) -> Optional[str]:
        """Ask the user where an export should be saved."""
        try:
            default_path = self.database.get_default_export_path(kind)
        except (AttributeError, ValueError) as exc:
            self.show_error(
                "Export",
                str(exc),
            )
            return None

        dialog_filters = {
            "snapshot": "File System Viewer Snapshot (*.csv)",
            "excel": "Excel Workbook (*.xlsx)",
            "csv": "CSV File (*.csv)",
            "json": "JSON File (*.json)",
            "html": "HTML File (*.html)",
            "text": "Text File (*.txt)",
        }

        file_filter = dialog_filters.get(kind)
        if file_filter is None:
            self.show_error(
                "Export",
                f"Unknown export type: {kind}",
            )
            return None

        os.makedirs(
            os.path.dirname(default_path),
            exist_ok=True,
        )

        selected_path, _ = (
            QtWidgets.QFileDialog
            .getSaveFileName(
                self,
                "Export As",
                default_path,
                file_filter,
            )
        )

        if not selected_path:
            return None

        return os.path.normpath(selected_path)

    def export_data(
        self,
        kind: str,
    ) -> None:

        if self._busy:
            return

        if self.database.data.empty:
            self.show_warning(
                "Export",
                "There is no data "
                "to export yet.",
            )
            return

        export_path = self._select_export_path(kind)

        if not export_path:
            self.show_status(
                "Export cancelled."
            )
            return

        self.start_background_task(
            self.database.export_as,
            kind,
            export_path,
            message=(
                f"Exporting {kind}…"
            ),
            on_success=(
                lambda result:
                self._export_finished(
                    kind,
                    result,
                )
            ),
        )

    def _export_finished(
        self,
        kind: str,
        result,
    ) -> None:

        if result:
            final_path = os.path.normpath(
                str(result)
            )

            self.show_status(
                "Export saved to: "
                f"{final_path}"
            )

        else:
            self.show_warning(
                "Export",
                f"The {kind} export "
                "did not complete successfully. "
                "Check the terminal output "
                "for details.",
            )

    def import_data(self) -> None:

        if self._busy:
            return

        default_directory = (
            self.database.get_exports_directory()
        )
        os.makedirs(
            default_directory,
            exist_ok=True,
        )

        filepath, _ = (
            QtWidgets.QFileDialog
            .getOpenFileName(
                self,
                "Import CSV Snapshot",
                default_directory,
                (
                    "File System Viewer Snapshot (*.csv);;"
                    "CSV Files (*.csv)"
                ),
            )
        )

        if not filepath:
            return

        self.start_background_task(
            self.database.import_data,
            os.path.normpath(
                filepath
            ),
            message=(
                "Importing CSV snapshot…"
            ),
            on_success=(
                self._import_finished
            ),
        )

    def _import_finished(
        self,
        result,
    ) -> None:
        """Handle CSV validation separately from MongoDB persistence."""
        if not isinstance(result, dict):
            result = {
                "success": bool(result),
                "persisted": bool(result),
                "error": "Unknown snapshot import error.",
            }

        if result.get("success"):
            self.current_page = 1
            self.print_data()
            self.print_metadata()
            self.search_bar.clear()
            self._clear_filter_builder_fields()

            if result.get("persisted"):
                self.show_status(
                    "CSV snapshot imported and saved successfully."
                )
            else:
                self.show_warning(
                    "Import Completed — Database Save Failed",
                    result.get("error")
                    or (
                        "The snapshot was imported successfully, but "
                        "could not be saved to MongoDB."
                    ),
                )
            return

        self.show_warning(
            "CSV Snapshot Import",
            result.get("error")
            or "The selected snapshot could not be imported.",
        )

    def start_background_task(
        self,
        function: Callable,
        *args,
        message: str,
        on_success: Optional[
            Callable
        ] = None,
    ) -> None:
        """Run blocking work in a QThread and keep the GUI responsive."""

        if self._busy:
            return

        self.set_busy(
            True,
            message,
        )

        self.worker_thread = TaskThread(
            function,
            *args,
            parent=self,
        )

        if on_success is not None:

            self.worker_thread.result.connect(
                on_success
            )

        self.worker_thread.error.connect(
            self._background_task_failed
        )

        self.worker_thread.finished.connect(
            self._background_task_finished
        )

        self.worker_thread.start()

    def _background_task_failed(
        self,
        details: str,
    ) -> None:

        print(details)

        self.show_error(
            "Operation Failed",
            "The operation failed. "
            "The full traceback was "
            "printed to the terminal.",
        )

    def _background_task_finished(
        self,
    ) -> None:

        self.set_busy(
            False
        )

        thread = self.worker_thread
        self.worker_thread = None

        if thread is not None:
            thread.deleteLater()

    def set_busy(
        self,
        busy: bool,
        message: str = "",
    ) -> None:

        self._busy = busy

        self.search_bar.setEnabled(
            not busy
        )

        self.search_button.setEnabled(
            not busy
        )

        self.clear_search_button.setEnabled(
            not busy
        )

        self.filter_toggle_button.setEnabled(
            not busy
        )
        self.filter_text_input.setEnabled(
            not busy
        )
        self.filter_mode_combo.setEnabled(
            not busy
        )
        self.filter_extension_input.setEnabled(
            not busy
        )
        self.filter_min_size_input.setEnabled(
            not busy
        )
        self.filter_min_unit_combo.setEnabled(
            not busy
        )
        self.filter_max_size_input.setEnabled(
            not busy
        )
        self.filter_max_unit_combo.setEnabled(
            not busy
        )
        self.apply_filters_button.setEnabled(
            not busy
        )
        self.reset_filters_button.setEnabled(
            not busy
        )

        self.theme_button.setEnabled(
            not busy
        )

        self.table.setEnabled(
            not busy
        )

        # Page controls are also refreshed by print_data(); while a worker is
        # active they must remain disabled regardless of page position.
        if busy:
            for button in (
                self.first_page_button,
                self.previous_page_button,
                self.next_page_button,
                self.last_page_button,
            ):
                button.setEnabled(False)
        else:
            data = self.database.get_data()[0]
            total_pages = self._page_count(data.shape[0])
            self.first_page_button.setEnabled(
                self.current_page > 1
            )
            self.previous_page_button.setEnabled(
                self.current_page > 1
            )
            self.next_page_button.setEnabled(
                self.current_page < total_pages
            )
            self.last_page_button.setEnabled(
                self.current_page < total_pages
            )

        for action in (
            self.action_gather,
            self.action_update,
            self.action_plot,
            self.action_plot_file_types,
            self.action_import,
            self.action_theme,
            *self.export_actions,
        ):
            action.setEnabled(
                not busy
            )

        if busy:

            self.progress_bar.show()

            self.show_status(
                message
                or "Working…"
            )

            QtWidgets.QApplication.setOverrideCursor(
                QtCore.Qt.WaitCursor
            )

        else:

            self.progress_bar.hide()

            if (
                QtWidgets.QApplication
                .overrideCursor()
                is not None
            ):

                QtWidgets.QApplication.restoreOverrideCursor()

    def show_status(
        self,
        message: str,
    ) -> None:

        self.status_message.setText(
            message
        )

    def show_warning(
        self,
        title: str,
        message: str,
    ) -> None:

        QtWidgets.QMessageBox.warning(
            self,
            title,
            message,
        )

    def show_error(
        self,
        title: str,
        message: str,
    ) -> None:

        QtWidgets.QMessageBox.critical(
            self,
            title,
            message,
        )

    def visit(
        self,
        target: str,
    ) -> None:

        if target == "GitHub":

            webbrowser.open(
                "https://github.com/"
                "Nick-Bounatsos/"
                "file-system-viewer"
            )

            return

        if target == "Manual":

            manual_path = resource_path(
                "Manual",
                "manual.html",
            )

            if not os.path.exists(
                manual_path
            ):

                self.show_warning(
                    "Manual",
                    "Manual file not found:"
                    "\n\n"
                    f"{manual_path}",
                )

                return

            QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(
                    manual_path
                )
            )

    def closeEvent(
        self,
        event: QtGui.QCloseEvent,
    ) -> None:

        if (
            self._busy
            and self.worker_thread
            is not None
        ):

            self.show_warning(
                "Operation in Progress",
                "A scan, import or export "
                "is still running. "
                "Close the application after "
                "the operation finishes.",
            )

            event.ignore()
            return

        event.accept()
