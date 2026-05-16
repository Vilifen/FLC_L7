from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
import os


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("О программе")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        self.viewer = QTextBrowser()
        layout.addWidget(self.viewer)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, "html files", "about.html")

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                self.viewer.setHtml(f.read())
        except:
            self.viewer.setHtml("<h1>Ошибка загрузки файла about.html</h1>")
