from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QRect, Qt
from .line_numbers import LineNumberArea
from .highlighter import PHPHighlighter


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.setAcceptDrops(False)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.update)
        self.update_line_number_area_width(0)

        self.highlighter = PHPHighlighter(self.document())

    def dragEnterEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        event.ignore()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(245, 245, 245))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        fm = self.fontMetrics()

        while block.isValid():
            rect = self.blockBoundingGeometry(block).translated(offset)
            top = rect.top()
            bottom = rect.bottom()

            if bottom >= event.rect().top() and top <= event.rect().bottom():
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(
                    0,
                    int(top),
                    self.line_number_area.width() - 4,
                    fm.height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1)
                )

            if top > event.rect().bottom():
                break

            block = block.next()
            block_number += 1
