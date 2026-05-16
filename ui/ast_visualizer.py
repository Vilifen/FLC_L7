from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PyQt6.QtCore import Qt


class ASTVisualizer(QDialog):
    def __init__(self, ast_nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AST")
        self.resize(800, 600)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)

        self.node_width = 140
        self.node_height = 60
        self.level_height = 120
        self.sibling_spacing = 50

        if ast_nodes:
            self.draw_tree(ast_nodes[0])

    def draw_tree(self, root_node):
        self._draw_node_recursive(root_node, 0, 0)
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))

    def _draw_node_recursive(self, node, level, x_offset):
        if node is None:
            return 0, 0

        children = node.get_children()
        y = level * self.level_height

        current_x = x_offset
        child_positions = []
        total_subtree_width = 0

        if not children:
            total_subtree_width = self.node_width
        else:
            for _, child in children:
                child_w, child_x = self._draw_node_recursive(child, level + 1, current_x)
                child_positions.append(child_x)
                current_x += child_w + self.sibling_spacing
                total_subtree_width += child_w + self.sibling_spacing
            total_subtree_width -= self.sibling_spacing

        real_x = x_offset + (total_subtree_width - self.node_width) / 2

        rect = self.scene.addRect(real_x, y, self.node_width, self.node_height,
                                  QPen(Qt.GlobalColor.black), QBrush(QColor("#ffffff")))

        label_text = node.get_node_label()
        text = self.scene.addText(label_text)
        text.setFont(QFont("Arial", 9))
        t_rect = text.boundingRect()
        text.setPos(real_x + (self.node_width - t_rect.width()) / 2,
                    y + (self.node_height - t_rect.height()) / 2)

        for cx in child_positions:
            self.scene.addLine(real_x + self.node_width / 2, y + self.node_height,
                               cx + self.node_width / 2, y + self.level_height,
                               QPen(QColor("#bdbdbd"), 1.5))

        return total_subtree_width, real_x