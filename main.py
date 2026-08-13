import sys

from PyQt5 import QtWidgets

from database import Database
from gui import MainWindow


def main() -> int:
    """Start the File System Viewer application."""

    app = QtWidgets.QApplication(sys.argv)

    try:
        database = Database()
        window = MainWindow(app, database)

        window.show()

        return app.exec_()

    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            None,
            "File System Viewer",
            (
                "The application encountered an unexpected error "
                "during startup.\n\n"
                f"{type(exc).__name__}: {exc}"
            ),
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
