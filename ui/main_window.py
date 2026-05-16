import json
import os
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QStatusBar, QDialog,
    QVBoxLayout, QTextBrowser, QWidget, QSplitter, QFileDialog, QTextEdit
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont

from ui.central.central_widget import CentralWidget
from ui.actions import ActionManager
from ui.menus import MenuBuilder
from ui.toolbar import ToolbarBuilder
from ui.ast_visualizer import ASTVisualizer

from L2.integration import run_scanner
from L2.navigation import navigate_to_error
from L2.ast_nodes import IRBuilder, optimize_while_to_for, optimize_increment_to_ssa

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.labels_ru = {
            "file": "Файл", "edit": "Правка", "text": "Текст", "run": "Пуск",
            "help": "Справка", "localization": "Локализация", "view": "Вид",
            "font_size": "Размер шрифта", "new": "Создать", "open": "Открыть",
            "save": "Сохранить", "save_as": "Сохранить как", "exit": "Выход",
            "undo": "Отменить", "redo": "Повторить", "cut": "Вырезать",
            "copy": "Копировать", "paste": "Вставить", "delete": "Удалить",
            "select_all": "Выделить всё", "task": "Постановка задачи",
            "grammar": "Грамматика", "grammar_class": "Классификация грамматики",
            "method": "Метод анализа", "example": "Тестовый пример",
            "literature": "Список литературы", "source": "Исходный код программы",
            "about": "О программе", "info_title": "Информация",
            "error_label": "Ошибка", "forbidden_word": "Ошибка",
            "line_word": "строка", "pos_word": "позиция",
            "no_errors": "Ошибок не найдено.", "help_text": "Справка",
            "about_text": "О программе", "save_title": "Сохранить файл?",
            "save_text": "Save changes to file", "yes": "Да", "no": "Нет",
            "cancel": "Отмена", "status_lang": "Язык", "status_size": "Размер",
            "status_lines": "Строк", "build": "Сборка", "errors": "Ошибки",
            "ast_text": "Сохранить дерево (JSON)", "ast_visual": "Показать AST",
            "ir_tab": "IR (TAC)"
        }
        self.labels_en = {
            "file": "File", "edit": "Edit", "text": "Text", "run": "Run",
            "help": "Help", "localization": "Language", "view": "View",
            "font_size": "Font size", "new": "New", "open": "Open",
            "save": "Save", "save_as": "Save As", "exit": "Exit",
            "undo": "Undo", "redo": "Redo", "cut": "Cut", "copy": "Copy",
            "paste": "Paste", "delete": "Delete", "select_all": "Select All",
            "task": "Task", "grammar": "Grammar", "grammar_class": "Grammar classification",
            "method": "Parsing method", "example": "Example", "literature": "References",
            "source": "Source code", "about": "About", "info_title": "Information",
            "error_label": "Error", "forbidden_word": "Error", "line_word": "line",
            "pos_word": "position", "no_errors": "No errors found.", "help_text": "Help",
            "about_text": "About", "save_title": "Save file?",
            "save_text": "Save changes to file", "yes": "Yes", "no": "No",
            "cancel": "Cancel", "status_lang": "Lang", "status_size": "Size",
            "status_lines": "Lines", "build": "Build", "errors": "Errors",
            "ast_text": "Save Tree (JSON)", "ast_visual": "Show AST",
            "ir_tab": "IR (TAC)"
        }
        self.labels = self.labels_ru
        self.language = "ru"
        self.font_menu = None
        self.last_ast = []
        self.setWindowTitle("Текстовый редактор")
        self.resize(1000, 700)
        self.menuBar().setNativeMenuBar(False)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.central = CentralWidget()
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.central.editor_area)
        splitter.addWidget(self.central.results_area)
        splitter.setSizes([600, 300])
        splitter.setHandleWidth(6)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.error_status = QStatusBar()
        layout.addWidget(self.error_status)
        self.setCentralWidget(container)
        self.actions = ActionManager(self, controller)
        self.menu_builder = MenuBuilder(self, self.actions)
        ToolbarBuilder(self, self.actions)
        self._build_font_menu()
        self.central.editor.textChanged.connect(self.update_status_bar)
        self.central.table.itemClicked.connect(self._on_table_item_clicked)
        self.central.error_table.itemClicked.connect(self._on_table_item_clicked)

    def save_ast_json(self):
        _, _, ast_nodes = run_scanner(self.central.editor)
        if not ast_nodes:
            QMessageBox.warning(self, "AST", "Дерево пустое или содержит ошибки.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить AST в JSON", "", "JSON Files (*.json)")
        if path:
            def to_dict(node):
                if node is None: return None
                d = {"node": node.__class__.__name__}
                for k, v in node.__dict__.items():
                    if isinstance(v, (int, str, float, bool)):
                        d[k] = v
                    elif isinstance(v, list):
                        d[k] = [to_dict(i) if hasattr(i, "__dict__") else i for i in v]
                    elif hasattr(v, "__dict__"):
                        d[k] = to_dict(v)
                return d

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump([to_dict(n) for n in ast_nodes], f, ensure_ascii=False, indent=4)
                self.status.showMessage(f"AST сохранено: {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def _on_table_item_clicked(self, item):
        editor = self.central.editor
        row = item.row()
        rows = self.central.token_rows if self.central.results_tabs.currentIndex() == 0 else self.central.error_rows
        if 0 <= row < len(rows):
            navigate_to_error(editor, rows[row]["line"], rows[row]["col"])

    def set_language(self, lang):
        self.labels = self.labels_en if lang == "en" else self.labels_ru
        self.language = lang
        self.actions.update_texts()
        self.menu_builder.update_menu_titles()
        if self.font_menu: self.font_menu.setTitle(self.labels["font_size"])
        self.update_ui_language()
        self.update_status_bar()

    def update_ui_language(self):
        self.central.results_tabs.setTabText(0, self.labels["build"])
        self.central.results_tabs.setTabText(1, self.labels["errors"])
        self.central.results_tabs.setTabText(2, "AST")
        self.central.results_tabs.setTabText(3, self.labels["ir_tab"])

    def run_scanner_action(self):
        token_rows, error_rows, ast_nodes = run_scanner(self.central.editor)
        self.last_ast = ast_nodes
        self.central.set_results(token_rows, error_rows)

        ast_text = "ДЕРЕВО AST:\n" + "\n".join([n.get_tree_str().rstrip() for n in ast_nodes]) if ast_nodes else "Пусто"
        self.central.ast_display.setPlainText(ast_text)

        ir_text = "ВХОДНОЙ IR И ОПТИМИЗАЦИИ:\n\n"
        if ast_nodes and not error_rows:
            builder = IRBuilder()
            for node in ast_nodes:
                if hasattr(node, 'generate_tac'):
                    node.generate_tac(builder)

            orig_ir_str = builder.format_ir(builder.code)
            ir_text += "ВХОДНОЙ IR\n" + orig_ir_str + "\n\n"

            opt1_code = optimize_while_to_for(builder.code)
            ir_text += "- ОПТИМИЗАЦИЯ 1: Преобразование while в for\n"
            ir_text += builder.format_ir(opt1_code) + "\n\n"

            opt2_code = optimize_increment_to_ssa(opt1_code)
            ir_text += "- ОПТИМИЗАЦИЯ 2: Перевод инкремента в SSA-форму\n"
            ir_text += builder.format_ir(opt2_code) + "\n"
        else:
            ir_text += "Дерево пустое или содержит ошибки. Генерация IR прервана."

        self.central.ir_display.setPlainText(ir_text)
        self.error_status.showMessage(f"Ошибок: {len(error_rows)}")

    def show_ast_visual(self):
        self.run_scanner_action()
        if not self.last_ast:
            QMessageBox.warning(self, "AST", "Дерево пустое.")
            return
        ASTVisualizer(self.last_ast, self).exec()

    def show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.labels["help_text"])
        dlg.resize(900, 650)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        layout.addWidget(browser)
        browser.setSource(QUrl.fromLocalFile(os.path.abspath("ui/html files/user_guide.html")))
        dlg.exec()

    def _build_font_menu(self):
        view_menu = next(
            (a.menu() for a in self.menuBar().actions() if a.menu() and a.menu().title() == self.labels["view"]), None)
        if not view_menu: return
        self.font_menu = view_menu.addMenu(self.labels["font_size"])
        for s in [8, 10, 12, 14, 16, 18, 24, 32]:
            self.font_menu.addAction(str(s)).triggered.connect(lambda _, size=s: self.central.set_font_size(size))

    def update_status_bar(self):
        text = self.central.editor.toPlainText()
        self.status.showMessage(
            f"{self.labels['status_lang']}: {self.language.upper()} | {len(text.encode())} B | {text.count(chr(10)) + 1} L")

    def get_editor(self):
        return self.central.editor

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        self.central.dropEvent(e)