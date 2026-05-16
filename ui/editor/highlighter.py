from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class PHPHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(600)
            return f

        keywords = [
            "if", "else", "elseif", "endif", "while", "endwhile", "for", "foreach",
            "endforeach", "function", "return", "class", "public", "private",
            "protected", "static", "var", "const", "new", "try", "catch", "finally",
            "throw", "extends", "implements", "interface", "trait", "use", "as",
            "global", "unset", "isset", "empty", "echo", "print", "include",
            "include_once", "require", "require_once", "switch", "case", "default",
            "break", "continue", "do"
        ]

        keyword_format = fmt("#0077cc", True)
        for kw in keywords:
            self.rules.append((QRegularExpression(rf"\b{kw}\b"), keyword_format))

        var_format = fmt("#aa00aa", True)
        self.rules.append((QRegularExpression(r"\$[A-Za-z_][A-Za-z0-9_]*"), var_format))

        string_format = fmt("#dd1144")
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = fmt("#009933")
        self.rules.append((QRegularExpression(r"//.*"), comment_format))
        self.rules.append((QRegularExpression(r"/\*.*\*/"), comment_format))

        number_format = fmt("#aa00aa")
        self.rules.append((QRegularExpression(r"\b[0-9]+\b"), number_format))

        tag_format = fmt("#cc7700", True)
        self.rules.append((QRegularExpression(r"<\?php"), tag_format))
        self.rules.append((QRegularExpression(r"\?>"), tag_format))

    def highlightBlock(self, text):
        for pattern, form in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), form)
