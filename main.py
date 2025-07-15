import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_widget import AcrylicWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./icon.ico"))
    widget = AcrylicWidget()
    widget.show()
    sys.exit(app.exec()) 