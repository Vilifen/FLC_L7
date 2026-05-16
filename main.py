from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from controller import Controller
import sys


def main():
    app = QApplication(sys.argv)

    controller = Controller()
    win = MainWindow(controller)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
