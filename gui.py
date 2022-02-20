from PyQt5 import QtCore, QtGui, QtWidgets
import webbrowser
import subprocess
import sys
import os


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app: object, database: object) -> None:
        """Setup the UI, connect to the database and add event listeners."""
        super(MainWindow, self).__init__()
        self.database = database

        self.setup_interface(app)

        # Load previous data, if they exist
        if self.database.load_data():
            self.print_data()
            self.print_metadata()


    def setup_interface(self, app: object) -> None:
        """Get the main window and setup the whole UI."""
        
        # Get system screen width and height, to enable fullscreen
        system_screen = app.primaryScreen()
        screen_dimensions = system_screen.size()
        # TODO: There's an offset, possibly the menubars outside the app. Need to add relative positioning
        WIN_W, WIN_H = screen_dimensions.width() - 73, screen_dimensions.height() - 67
        FONT = QtGui.QFont("Constantia Monospace", 10)
        self.setFont(FONT)
        
        # Window size/name customization
        self.setWindowTitle("Database")
        self.showMaximized()
        self.setMinimumSize(WIN_W, WIN_H)


        # Application Icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("database.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setMinimumSize(QtCore.QSize(0, 0))

        # The same frame height will be used for both frames
        FRAME_HEIGHT = 20

        # The top frame, data and search info are displayed here
        self.data_display_frame = QtWidgets.QFrame(self.centralwidget)
        self.data_display_frame.setEnabled(True)
        self.data_display_frame.setGeometry(QtCore.QRect(0, 0, WIN_W, FRAME_HEIGHT))
                
        # Data display frame dimensions
        DATE_LABEL_W = 40
        DATE_VAL_W = 95
        FILES_LABEL_W = 40
        FILES_VAL_W = 75
        PROC_TIME_LABEL_W = 95
        PROC_TIME_VAL_W = 50
        
        SEARCH_RESULTS_W = 200
        SEARCH_BAR_W = 250
        SEARCH_BTN_W = 60

        TOTAL_DATA_W = DATE_LABEL_W + DATE_VAL_W + FILES_LABEL_W + FILES_VAL_W + PROC_TIME_LABEL_W + PROC_TIME_VAL_W
        TOTAL_SEARCH_W = SEARCH_RESULTS_W + SEARCH_BAR_W + SEARCH_BTN_W
        
        # Data display frame positions
        DATE_VAL_X = DATE_LABEL_W
        FILES_X = DATE_LABEL_W + DATE_VAL_W
        FILES_VAL_X = FILES_X + FILES_LABEL_W
        PROC_TIME_X = FILES_VAL_X + FILES_VAL_W
        PROC_TIME_VAL_X = PROC_TIME_X + PROC_TIME_LABEL_W

        # TODO: Not a clue on why there's this offset
        SEARCH_BAR_GAP = WIN_W - TOTAL_DATA_W - TOTAL_SEARCH_W + 50
        # It's not always the case
        SEARCH_RESULTS_X = SEARCH_BAR_GAP + PROC_TIME_VAL_X
        SEARCH_BAR_X = SEARCH_RESULTS_X + SEARCH_RESULTS_W
        SEARCH_BTN_X = SEARCH_BAR_X + SEARCH_BAR_W
        
        # Date label, fixed value
        self.date_label = QtWidgets.QLabel(self.data_display_frame)
        self.date_label.setGeometry(QtCore.QRect(0, 0, DATE_LABEL_W, FRAME_HEIGHT))
        self.date_label.setText("Date:")
        
        # Date value label, accessed by database
        self.date_value = QtWidgets.QLabel(self.data_display_frame)
        self.date_value.setGeometry(QtCore.QRect(DATE_VAL_X, 0, DATE_VAL_W, FRAME_HEIGHT))
        self.date_value.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
       
        # Files label, fixed value
        self.files_label = QtWidgets.QLabel(self.data_display_frame)
        self.files_label.setGeometry(QtCore.QRect(FILES_X, 0, FILES_LABEL_W, FRAME_HEIGHT))
        self.files_label.setText("Files:")
        
        # Files value label, accessed by database
        self.files_value = QtWidgets.QLabel(self.data_display_frame)
        self.files_value.setGeometry(QtCore.QRect(FILES_VAL_X, 0, FILES_VAL_W, FRAME_HEIGHT))
        self.files_value.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        
        # Process time label, fixed value
        self.proc_time_label = QtWidgets.QLabel(self.data_display_frame)
        self.proc_time_label.setGeometry(QtCore.QRect(PROC_TIME_X, 0, PROC_TIME_LABEL_W, FRAME_HEIGHT))
        self.proc_time_label.setText("Process time:")

        # Process time value label, accessed by database
        self.proc_time = QtWidgets.QLabel(self.data_display_frame)
        self.proc_time.setGeometry(QtCore.QRect(PROC_TIME_VAL_X, 0, PROC_TIME_VAL_W, FRAME_HEIGHT))
        self.proc_time.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        
        
        # Search results output
        self.search_info = QtWidgets.QLabel(self.data_display_frame)
        self.search_info.setGeometry(QtCore.QRect(SEARCH_RESULTS_X, 0, SEARCH_RESULTS_W, FRAME_HEIGHT))
        self.search_info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.search_info.setText("")
        
        # Search text box
        self.search_bar = QtWidgets.QLineEdit(self.data_display_frame)
        self.search_bar.setGeometry(QtCore.QRect(SEARCH_BAR_X, 0, SEARCH_BAR_W, FRAME_HEIGHT))
        
        # Search Button, Bound to <Return> (Enter)
        self.search_button = QtWidgets.QPushButton(self.data_display_frame)
        self.search_button.setGeometry(QtCore.QRect(SEARCH_BTN_X, 0, SEARCH_BTN_W, FRAME_HEIGHT))
        self.search_button.setText("Search")
        self.search_button.setShortcut("Return")
        self.search_button.clicked.connect(self.search_data)

        # Main screen area, data will be displayed here
        SCREEN_W = WIN_W
        # 3 * FRAME_HEIGHT, the 3rd "frame" is the menubar
        SCREEN_H = WIN_H - 3 * FRAME_HEIGHT

        self.screen = QtWidgets.QListWidget(self.centralwidget)
        self.screen.setGeometry(QtCore.QRect(0, 2 * FRAME_HEIGHT, SCREEN_W, SCREEN_H))
        self.screen.itemDoubleClicked.connect(self.open_directory)

        
        # Scrollbars
        self.scroll_bar_v = QtWidgets.QScrollBar(self.screen)
        self.scroll_bar_h = QtWidgets.QScrollBar(self.screen)

        self.scroll_bar_v.setStyleSheet("background : lightgray;")
        self.scroll_bar_h.setStyleSheet("background : lightgray;")

        self.screen.setVerticalScrollBar(self.scroll_bar_v)
        self.screen.setHorizontalScrollBar(self.scroll_bar_h)


        # The bottom (2nd) frame, containing buttons that'll sort the data
        self.buttons_frame = QtWidgets.QFrame(self.centralwidget)
        # y is FRAME_HEIGHT so that it always starts right under the first frame
        self.buttons_frame.setGeometry(QtCore.QRect(0, FRAME_HEIGHT, WIN_W, FRAME_HEIGHT))
        
        # Button widths
        SIZE_BTN_W = 150
        PATH_BTN_X = SIZE_BTN_W
        PATH_BTN_W = WIN_W - SIZE_BTN_W

        # Size Button. Will be accessed, so that the text changes depending on sorting
        self.size_button = QtWidgets.QPushButton(self.buttons_frame)
        self.size_button.setGeometry(QtCore.QRect(0, 0, SIZE_BTN_W, FRAME_HEIGHT))
        self.size_button.setText("Size")
        self.size_button.clicked.connect(self.sort_by_size)
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.size_button.sizePolicy().hasHeightForWidth())
        self.size_button.setSizePolicy(sizePolicy)
        self.size_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        
        # Path Button. Will be accessed, so that the text changes depending on sorting
        self.path_button = QtWidgets.QPushButton(self.buttons_frame)
        self.path_button.setGeometry(QtCore.QRect(PATH_BTN_X, 0, PATH_BTN_W, FRAME_HEIGHT))
        self.path_button.setText("Path")
        self.path_button.clicked.connect(self.sort_by_name)
        
        self.setCentralWidget(self.centralwidget)
        
        # Menu Bar
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, WIN_W, FRAME_HEIGHT))
        
        # Main Menu Categories
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.setMenuBar(self.menubar)
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
        
        # Scatter Plot
        self.actionScatter_Plot_Search_Results = QtWidgets.QAction(self)
        self.actionScatter_Plot_Search_Results.setText("Scatter Plot")
        self.actionScatter_Plot_Search_Results.setShortcut("Ctrl+P")
        self.actionScatter_Plot_Search_Results.triggered.connect(self.database.plot_data)
        
        # Export As, and its' subcategories
        self.menuExport_As = QtWidgets.QMenu(self.menuFile)
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
        self.actionExit.triggered.connect(lambda: sys.exit(app.exec_))
        
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
        self.menuFile.addAction(self.actionScatter_Plot_Search_Results)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.menuExport_As.menuAction())
        self.menuFile.addAction(self.actionImport)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        
        # Adding Help categories to Help
        self.menuHelp.addAction(self.actionVisit_GitHub)
        self.menuHelp.addAction(self.actionManual)
        
        # Adding the big categories to the menu bar
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())


    def gather_data(self) -> None:
        """Gather data action (menubar). Get a new dirpath, and call database gather_data method"""

        # askopendir. if it's cancelled, returns an empty string
        dirpath = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if dirpath:
            self.database.gather_data(dirpath)

            self.print_data()
            self.print_metadata()


    def update_data(self) -> None:
        """Update data action (menubar). Get location from metadata, and call database gather data method
        with the location as dirpath. Then print the new data."""

        self.database.gather_data(self.database.get_metadata()[0])

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

        filepath = location + item_selected.split(location)[-1]

        if os.path.exists(filepath):
            item_directory = filepath.rstrip(filepath.split(os.sep)[-1])
            
            if sys.platform.startswith("win"):
                os.starfile(item_directory)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", item_directory])
            else:
                subprocess.run(["open", item_directory])


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
            for file in data:
                self.screen.addItem(f"{f'{file.size:>10}':^31}{file.path}")
        else:
            self.screen.addItem("No files found.")

        self.update_sort_buttons()


    def print_metadata(self) -> None:
        """Gets metadata from the database and updates the respective widgets"""

        location, date, time, total_files, total_size = self.database.get_metadata()
        self.setWindowTitle(f"Database - {location}")
        self.date_value.setText(date)
        self.proc_time.setText(time)
        self.files_value.setText(f"{total_files:,}")
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
                self.size_button.setText(self.size_button.text().rstrip(" ↑") + " ↓")
            else:
                self.size_button.setText(self.size_button.text().rstrip(" ↓") + " ↑")
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
