import database
import gui

app = gui.QtWidgets.QApplication(gui.sys.argv)
db = database.Database()
win = gui.MainWindow(db)

win.show()

gui.sys.exit(app.exec_())
