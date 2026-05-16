from PyQt6.QtWidgets import QToolBar
from PyQt6.QtCore import QSize


class ToolbarBuilder:
    def __init__(self, window, actions):
        toolbar = QToolBar()
        toolbar.setMovable(False)

        toolbar.setStyleSheet("""
            QToolBar {
                background: white;
                spacing: 8px;
                padding: 6px;
                border: none;
            }
            QToolButton {
                background: white;
                border: none;
                padding: 6px;
            }
            QToolButton:hover {
                background: #f2f2f2;
            }
        """)

        toolbar.setIconSize(QSize(28, 28))

        window.addToolBar(toolbar)

        toolbar.addAction(actions.new)
        toolbar.addAction(actions.open)
        toolbar.addAction(actions.save)

        toolbar.addSeparator()

        toolbar.addAction(actions.undo)
        toolbar.addAction(actions.redo)

        toolbar.addSeparator()

        toolbar.addAction(actions.cut)
        toolbar.addAction(actions.copy)
        toolbar.addAction(actions.paste)

        toolbar.addSeparator()

        toolbar.addAction(actions.run)

        toolbar.addSeparator()

        toolbar.addAction(actions.help)
        toolbar.addAction(actions.about)
