from PyQt5 import QtCore, QtGui, QtWidgets
import webbrowser
import subprocess
import sys
import os


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, database: object) -> None:
        """Setup the UI, connect to the database and add event listeners."""
        super(MainWindow, self).__init__()
        self.database = database

        self.limit = 1000

        self.setup_interface()

        # Load previous data, if they exist
        if self.database.load_data():
            self.print_data()
            self.print_metadata()


    def setup_interface(self) -> None:
        """Get the main window and setup the whole UI."""
        
        # Get system screen width and height, to enable fullscreen
        FONT = QtGui.QFont("Constantia Monospace", 10)
        self.setFont(FONT)
        
        # Window size/name customization
        self.setWindowTitle("Database")
        self.setMinimumSize(820, 480)
        self.showMaximized()


        # Application Icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("database.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(self)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)


        # Metadata display frame dimensions
        SEARCH_RESULTS_W = 250

        
        # The top frame, data and search info are displayed here
        self.dataWidget = QtWidgets.QWidget(self.centralwidget)

        self.dataLayout = QtWidgets.QHBoxLayout(self.dataWidget)
        self.dataLayout.setContentsMargins(0, 5, 0, 0)

        # Date label
        self.date_label = QtWidgets.QLabel(self.dataWidget)
        self.date_label.setText(" Date:")
       
        # Files label
        self.files_label = QtWidgets.QLabel(self.dataWidget)
        self.files_label.setText(" | Files:")
        
        # Process time label
        self.proc_time_label = QtWidgets.QLabel(self.dataWidget)
        self.proc_time_label.setText(" | Process time:")
        

        # Search results output
        self.search_info = QtWidgets.QLabel(self.dataWidget)
        self.search_info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.search_info.setMinimumWidth(SEARCH_RESULTS_W)
        self.search_info.setText("")
        
        # Search text box
        self.search_bar = QtWidgets.QLineEdit(self.dataWidget)
        
        # Search Button, Bound to <Return> (Enter)
        self.search_button = QtWidgets.QPushButton(self.dataWidget)
        self.search_button.setText("Search")
        self.search_button.setShortcut("Return")
        self.search_button.clicked.connect(self.search_data)


        self.dataLayout.addWidget(self.date_label)
        self.dataLayout.addWidget(self.files_label)
        self.dataLayout.addWidget(self.proc_time_label)
        self.dataLayout.addWidget(self.search_info)
        self.dataLayout.addWidget(self.search_bar)
        self.dataLayout.addWidget(self.search_button)


        # The bottom (2nd) frame, containing buttons that'll sort the data
        self.sortButtonsWidget = QtWidgets.QWidget(self.centralwidget)

        self.sortButtonsLayout = QtWidgets.QHBoxLayout(self.sortButtonsWidget)
        self.sortButtonsLayout.setContentsMargins(0, 0, 0, 0)

        
        # Size button width. The path button width changes accordingly
        SIZE_BTN_W = 150

        # Size Button. Will be accessed, so that the text changes depending on sorting
        self.size_button = QtWidgets.QPushButton(self.sortButtonsWidget)
        self.size_button.setFixedWidth(SIZE_BTN_W)
        self.size_button.setText("Size")
        self.size_button.clicked.connect(self.sort_by_size)
        
        # Path Button. Will be accessed, so that the text changes depending on sorting
        self.path_button = QtWidgets.QPushButton(self.sortButtonsWidget)
        self.path_button.setText("Path")
        self.path_button.clicked.connect(self.sort_by_name)

        self.sortButtonsLayout.addWidget(self.size_button)
        self.sortButtonsLayout.addWidget(self.path_button)


        # Main screen area, data will be displayed here
        self.screen = QtWidgets.QListWidget(self.centralwidget)
        self.screen.itemDoubleClicked.connect(self.open_directory)

        
        # Scrollbars
        self.scroll_bar_v = QtWidgets.QScrollBar(self.screen)
        self.scroll_bar_h = QtWidgets.QScrollBar(self.screen)

        self.scroll_bar_v.setStyleSheet("background : lightgray;")
        self.scroll_bar_h.setStyleSheet("background : lightgray;")


        self.screen.setVerticalScrollBar(self.scroll_bar_v)
        self.screen.setHorizontalScrollBar(self.scroll_bar_h)


        # Vertical Layout to tie them up
        self.verticalLayout.addWidget(self.dataWidget)
        self.verticalLayout.addWidget(self.sortButtonsWidget)
        self.verticalLayout.addWidget(self.screen)

        self.setCentralWidget(self.centralwidget)
        

        # Menu Bar
        self.menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.menubar)
        
        # Main Menu Categories
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setTitle("View")
        
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setTitle("Help")
        
        # Gather Data
        self.actionGather_Data = QtWidgets.QAction(self)
        self.actionGather_Data.setText("Gather Data")
        self.actionGather_Data.setShortcut("Ctrl+G")
        self.actionGather_Data.triggered.connect(self.gather_data)

        
        # Update Data
        self.actionUpdate_Data = QtWidgets.QAction(self)
        self.actionUpdate_Data.setText("Update Data")
        self.actionUpdate_Data.setShortcut("Ctrl+U")
        self.actionUpdate_Data.triggered.connect(self.update_data)
        
        # Plot
        self.actionPlot = QtWidgets.QAction(self)
        self.actionPlot.setText("Plot")
        self.actionPlot.setShortcut("Ctrl+P")
        self.actionPlot.triggered.connect(self.database.plot_data)
        
        # Export As, and its' subcategories
        self.menuExport_As = QtWidgets.QMenu(self)
        self.menuExport_As.setTitle("Export As...")

        self.action_txt = QtWidgets.QAction(self)
        self.action_txt.setText(".txt")
        self.action_txt.triggered.connect(lambda: self.database.export_as("text"))
        
        self.action_csv = QtWidgets.QAction(self)
        self.action_csv.setText(".csv")
        self.action_csv.triggered.connect(lambda: self.database.export_as("csv"))
        
        self.action_xlsx = QtWidgets.QAction(self)
        self.action_xlsx.setText(".xlsx")
        self.action_xlsx.triggered.connect(lambda: self.database.export_as("excel"))
        
        self.action_json = QtWidgets.QAction(self)
        self.action_json.setText(".json")
        self.action_json.triggered.connect(lambda: self.database.export_as("json"))
        
        # Import
        self.actionImport = QtWidgets.QAction(self)
        self.actionImport.setText("Import...")
        self.actionImport.setShortcut("Ctrl+I")
        self.actionImport.triggered.connect(self.import_data)
        
        # Exit
        self.actionExit = QtWidgets.QAction(self)
        self.actionExit.setText("Exit")
        self.actionExit.setShortcut("Ctrl+Q")
        self.actionExit.triggered.connect(sys.exit)
        
        # Limit
        self.menuLimit = QtWidgets.QMenu(self)
        self.menuLimit.setTitle(f"Limit: {self.limit}")

        # Change limit categories
        self.actionSetLimit_1 = QtWidgets.QAction(self)
        self.actionSetLimit_1.setText(f"Set {250}")
        self.actionSetLimit_1.triggered.connect(lambda: self.set_limit(250))

        self.actionSetLimit_2 = QtWidgets.QAction(self)
        self.actionSetLimit_2.setText(f"Set {500}")
        self.actionSetLimit_2.triggered.connect(lambda: self.set_limit(500))

        self.actionSetLimit_3 = QtWidgets.QAction(self)
        self.actionSetLimit_3.setText(f"Set {1000}")
        self.actionSetLimit_3.triggered.connect(lambda: self.set_limit(1000))

        self.actionSetLimit_4 = QtWidgets.QAction(self)
        self.actionSetLimit_4.setText(f"Set {2000}")
        self.actionSetLimit_4.triggered.connect(lambda: self.set_limit(2000))

        self.actionSetLimit_5 = QtWidgets.QAction(self)
        self.actionSetLimit_5.setText("Disable limit")
        self.actionSetLimit_5.triggered.connect(lambda: self.set_limit(-1))

        # Visit GitHub
        self.actionVisit_GitHub = QtWidgets.QAction(self)
        self.actionVisit_GitHub.setText("Visit GitHub")
        self.actionVisit_GitHub.triggered.connect(lambda: self.visit("GitHub"))
        
        # Manual
        self.actionManual = QtWidgets.QAction(self)
        self.actionManual.setText("Manual")
        self.actionManual.triggered.connect(lambda: self.visit("Manual"))
        
        # Widget packing process (Menubar)

        # Adding exporting categories to Export As
        self.menuExport_As.addAction(self.action_txt)
        self.menuExport_As.addAction(self.action_csv)
        self.menuExport_As.addAction(self.action_xlsx)
        self.menuExport_As.addAction(self.action_json)

        # Adding File categories to File
        self.menuFile.addAction(self.actionGather_Data)
        self.menuFile.addAction(self.actionUpdate_Data)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionPlot)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.menuExport_As.menuAction())
        self.menuFile.addAction(self.actionImport)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        # Adding change limit categories to Limit
        self.menuLimit.addAction(self.actionSetLimit_1)
        self.menuLimit.addAction(self.actionSetLimit_2)
        self.menuLimit.addAction(self.actionSetLimit_3)
        self.menuLimit.addAction(self.actionSetLimit_4)
        self.menuLimit.addAction(self.actionSetLimit_5)

        # Adding View categories to View
        self.menuView.addAction(self.menuLimit.menuAction())
        
        # Adding Help categories to Help
        self.menuHelp.addAction(self.actionVisit_GitHub)
        self.menuHelp.addAction(self.actionManual)
        
        # Adding the big categories to the menu bar
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())


    def gather_data(self) -> None:
        """Gather data action (menubar). Get a new dirpath, and call database gather_data method"""

        # askopendir. if it's cancelled, returns an empty string. The path returns has / as sep, regardless of os
        dirpath = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")).replace("/", os.sep)
        if dirpath:
            self.database.gather_data(dirpath)

            self.print_data()
            self.print_metadata()


    def update_data(self) -> None:
        """Update data action (menubar). Get location from metadata, and call database gather data method
        with the location as dirpath. Then print the new data."""

        location = self.database.get_metadata()[0]
        self.database.gather_data(location)

        self.print_data()
        self.print_metadata()


    def search_data(self) -> None:
        """Call database search method to search, and print the results.
        Read the key from the search bar."""

        self.database.search(self.search_bar.text())
        self.print_data()


    def sort_by_size(self) -> None:
        """Sort by size using the database method, and print the data."""
        self.database.sort_by_size()
        self.print_data()


    def sort_by_name(self) -> None:
        """Sort by name using the database method, and print the data."""
        self.database.sort_by_name()
        self.print_data()


    def open_directory(self) -> None:
        """Triggered whenever an item is double clicked.
        Check from the metadata, if the dataset is imported. If it is, do nothing.
        If it's a local file, open its' directory."""
        
        location = self.database.get_metadata()[0]
        if location.startswith("Imported"):
            return
        
        item_selected = self.screen.currentItem().text()

        # The following line ensures that double clicking will work whether the filepath is expanded or not
        _delimiter = "~" if "~" in item_selected else location
        filepath = location + item_selected.split(_delimiter)[-1]

        if os.path.exists(filepath):
            item_directory = filepath.rstrip(filepath.split(os.sep)[-1])
            
            if sys.platform.startswith("win"):
                os.startfile(item_directory)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", item_directory])
            else:
                subprocess.run(["open", item_directory])


    def set_limit(self, new_limit: int) -> None:
        """Set self.limit (Limit of rows per page)."""
        
        if new_limit == -1:
            new_limit = self.database.get_metadata()[3]

        if new_limit == self.limit:
            return
        
        self.limit = new_limit
        self.menuLimit.setTitle(f"Limit: {self.limit}")

        self.print_data()


    def print_data(self) -> None:
        """Gets the data and prints them on screen. If data is empty, prints respective message.
        Calls self.update_sort_buttons() method"""

        self.screen.clear()
        self.search_info.clear()

        data, size = self.database.get_data()

        # This boolean function determines whether search info must be displayed
        # if the matches are the same as the data, this means no search occured, so no reason to display info
        if self.database.is_sliced():
            self.search_info.setText(f"{len(data):,} files ({size})")

        if data:
            
            length = len(data)
            stop = length if length < self.limit else self.limit
            
            for i in range(stop):
                self.screen.addItem(f"{f'{data[i].size:>10}':^31}{data[i].path}")
        else:
            self.screen.addItem("No files found.")

        self.update_sort_buttons()


    def print_metadata(self) -> None:
        """Gets metadata from the database and updates the respective widgets"""

        location, date, time, total_files, total_size = self.database.get_metadata()
        self.setWindowTitle(f"Database - {location}")
        self.date_label.setText(f" Date: {date}")
        self.proc_time_label.setText(f" | Process time: {time}")
        self.files_label.setText(f" | Files: {total_files:,}")
        self.size_button.setText(f"Size ({total_size})")


    def update_sort_buttons(self) -> None:
        """Gets the self.database.sorted attr, and properly updates the buttons.
        This method is called from self.print_data().
        Whenever a change has happened, either a new search, a new sort, or gather/update,
        data is printed on screen."""
        
        sort_kind = self.database.sorted

        if not sort_kind:
            self.size_button.setText(self.size_button.text().rstrip(" ↓").rstrip(" ↑"))
            self.path_button.setText("Path")
        elif sort_kind.startswith("size"):
            self.path_button.setText("Path")
            if sort_kind.endswith("asc"):
                self.size_button.setText(self.size_button.text().rstrip(" ↑").rstrip(" ↓") + " ↓")
            else:
                self.size_button.setText(self.size_button.text().rstrip(" ↑").rstrip(" ↓") + " ↑")
        else:
            self.size_button.setText(self.size_button.text().rstrip(" ↓").rstrip(" ↑"))
            if sort_kind.endswith("asc"):
                self.path_button.setText("Path ↓")
            else:
                self.path_button.setText("Path ↑")


    def import_data(self) -> None:
        """Asks for filepath (askopenfile) and calls the datbase import method."""

        filepath = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "CSV files (*.csv)")[0]
        if self.database.import_data(filepath):
            self.print_data()
            self.print_metadata()


    def visit(self, url: str) -> None:
        """Visit either GitHub or open the manual html"""
        if url == "GitHub":
            webbrowser.open("https://github.com/Nick-Bounatsos/file-system-viewer")
        elif url == "Manual":
            webbrowser.open("manual.html")
