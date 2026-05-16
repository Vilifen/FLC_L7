from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QTextEdit, QTabBar
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from functools import partial
from ui.editor.code_editor import CodeEditor


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.tabs = []
        self.current_index = -1
        self.untitled_counter = 1
        self.font_size = 14
        self.token_rows = []
        self.error_rows = []

        self.setAcceptDrops(True)

        self.editor_area = QWidget()
        editor_layout = QVBoxLayout(self.editor_area)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self.tab_scroll = QScrollArea()
        self.tab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tab_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_scroll.setWidgetResizable(True)
        self.tab_scroll.setFixedHeight(48)

        self.tab_bar = QWidget()
        self.tab_bar.setObjectName("tab-bar")
        self.tab_bar.setStyleSheet("""
            #tab-bar {
                background: #f0f0f0;
                border-bottom: 1px solid #c0c0c0;
            }
        """)

        self.tab_layout = QHBoxLayout(self.tab_bar)
        self.tab_layout.setContentsMargins(4, 2, 4, 0)
        self.tab_layout.setSpacing(2)

        self.tab_scroll.setWidget(self.tab_bar)

        self.plus_button = QPushButton("+")
        self.plus_button.setFixedWidth(28)
        self.plus_button.setFlat(True)
        self.plus_button.clicked.connect(self.add_tab)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.tab_layout.addWidget(self.plus_button)
        self.tab_layout.addWidget(self.spacer)

        self.editor = CodeEditor()

        editor_layout.addWidget(self.tab_scroll)
        editor_layout.addWidget(self.editor)

        self.results_area = QWidget()
        results_layout = QVBoxLayout(self.results_area)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(0)

        self.results_tabs = QTabWidget()

        self.results_tabs.tabBar().setExpanding(False)
        self.results_tabs.tabBar().setDocumentMode(False)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Код", "Тип", "Лексема", "Место"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(["Фрагмент", "Место", "Описание"])
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.error_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.ast_display = QTextEdit()
        self.ast_display.setReadOnly(True)

        # --- Новая текстовая область для IR ---
        self.ir_display = QTextEdit()
        self.ir_display.setReadOnly(True)

        self.results_tabs.addTab(self.table, "Результаты")
        self.results_tabs.addTab(self.error_table, "Ошибки")
        self.results_tabs.addTab(self.ast_display, "AST")
        self.results_tabs.addTab(self.ir_display, "IR (TAC)")  # Добавлено

        results_layout.addWidget(self.results_tabs)

        self.apply_font_size()
        self.editor.textChanged.connect(self._sync_editor)
        self.editor.textChanged.connect(self._update_status)
        self.add_tab()

    def apply_font_size(self):
        font = QFont()
        font.setPointSize(self.font_size)
        self.editor.setFont(font)
        self.table.setFont(font)
        self.error_table.setFont(font)

        mono_font = QFont("Courier New", self.font_size)
        self.ast_display.setFont(mono_font)
        self.ir_display.setFont(mono_font)  # Применение шрифта к IR

    def set_font_size(self, size):
        self.font_size = size
        self.apply_font_size()

    def _sync_editor(self):
        if 0 <= self.current_index < len(self.tabs):
            self.tabs[self.current_index]["text"] = self.editor.toPlainText()
            self.tabs[self.current_index]["modified"] = True

    def _update_status(self):
        w = self.window()
        if hasattr(w, "update_status_bar"):
            w.update_status_bar()

    def add_tab(self, title=None):
        if 0 <= self.current_index < len(self.tabs):
            self.tabs[self.current_index]["text"] = self.editor.toPlainText()

        if not title:
            base = "Без имени"
            title = f"{base} {self.untitled_counter}"
            self.untitled_counter += 1

        btn = QPushButton(f"{title}   ✕")
        btn.setCheckable(True)
        btn.setFlat(True)
        btn.setFixedHeight(32)

        index = len(self.tabs)
        btn.clicked.connect(partial(self.switch_tab, index))
        btn.mousePressEvent = partial(self._tab_mouse_press, index=index, button=btn)

        self.tab_layout.insertWidget(self.tab_layout.count() - 1, btn)

        self.tabs.append({
            "title": title,
            "text": "",
            "button": btn,
            "modified": False,
        })

        self.current_index = index
        self._load_tab()
        self._update_status()

    def _tab_mouse_press(self, event, index, button):
        if event.pos().x() > button.width() - 18:
            self._request_close_tab(index)
            return
        self.switch_tab(index)

    def _request_close_tab(self, index):
        data = self.tabs[index]
        if not data.get("modified"):
            self.close_tab(index)
            return

        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Сохранить файл?")
        msg.setText(f"Сохранить изменения в файле «{data['title']}»?")
        yes_btn = msg.addButton("Да", QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(yes_btn)
        msg.exec()
        clicked = msg.clickedButton()

        if clicked is cancel_btn:
            return
        if clicked is yes_btn:
            self.window().actions.save.trigger()

        self.close_tab(index)
        self._update_status()

    def close_tab(self, index):
        if len(self.tabs) == 1:
            return

        tab = self.tabs.pop(index)
        btn = tab["button"]

        layout_index = self.tab_layout.indexOf(btn)
        if layout_index != -1:
            item = self.tab_layout.takeAt(layout_index)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        for i, t in enumerate(self.tabs):
            t["button"].clicked.disconnect()
            t["button"].clicked.connect(partial(self.switch_tab, i))
            t["button"].mousePressEvent = partial(self._tab_mouse_press, index=i, button=t["button"])

        self.current_index = max(0, index - 1)
        self._load_tab()
        self._update_status()

    def switch_tab(self, index):
        if index == self.current_index:
            return
        if not (0 <= index < len(self.tabs)):
            return

        if 0 <= self.current_index < len(self.tabs):
            self.tabs[self.current_index]["text"] = self.editor.toPlainText()

        self.current_index = index
        self._load_tab()
        self._update_status()

    def _load_tab(self):
        data = self.tabs[self.current_index]
        self.editor.blockSignals(True)
        self.editor.setPlainText(data["text"])
        self.editor.blockSignals(False)

    def set_results(self, token_rows, error_rows):
        self.token_rows = token_rows
        self.error_rows = error_rows

        self.table.setRowCount(len(token_rows))
        for i, r in enumerate(token_rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.get("code", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(r.get("type", "")))
            self.table.setItem(i, 2, QTableWidgetItem(r.get("lexeme", "")))
            self.table.setItem(i, 3, QTableWidgetItem(r.get("location", "")))

        if not error_rows:
            self.error_table.setRowCount(1)
            self.error_table.setItem(0, 0, QTableWidgetItem(""))
            self.error_table.setItem(0, 1, QTableWidgetItem(""))
            self.error_table.setItem(0, 2, QTableWidgetItem("Ошибок не найдено"))
        else:
            self.error_table.setRowCount(len(error_rows))
            for i, r in enumerate(error_rows):
                fragment = r.get("fragment", r.get("lexeme", ""))
                self.error_table.setItem(i, 0, QTableWidgetItem(fragment))
                self.error_table.setItem(i, 1, QTableWidgetItem(r.get("location", "")))
                self.error_table.setItem(i, 2, QTableWidgetItem(r.get("description", "")))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        path = urls[0].toLocalFile()
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except:
            try:
                with open(path, "r", encoding="cp1251") as f:
                    text = f.read()
            except:
                return

        self.add_tab(title=path.split("/")[-1])
        self.editor.setPlainText(text)
        self.tabs[self.current_index]["text"] = text
        self.tabs[self.current_index]["modified"] = False