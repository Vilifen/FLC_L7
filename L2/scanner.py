from .token_types import TokenType
from .token import Token
from .scan_error import ScanError
from .error_codes import ERROR_CODES


class Scanner:
    KEYWORDS = {"while"}

    OPERATORS = {
        "++", "--",
        "<=", ">=", "==", "!=", "&&", "||",
        "<", ">", "_",
    }

    SEPARATORS = {"(", ")", "{", "}", ";"}

    def __init__(self):
        self.text = ""
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = 0
        self.tokens = []
        self.errors = []

    def scan(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)
        self.tokens = []
        self.errors = []

        while not self._eof():
            ch = self._cur()

            if ch in " \t\r":
                self._add(TokenType.WHITESPACE, ch)
                self._advance()
            elif ch == "\n":
                self._add(TokenType.WHITESPACE, ch)
                self._advance()
            elif ch == "$":
                self._consume_identifier()
            elif ch.isalpha() or ch == "_":
                self._consume_word()
            elif ch.isdigit():
                self._consume_number()
            elif ch in self.SEPARATORS:
                self._add(TokenType.SEPARATOR, ch)
                self._advance()
            elif self._starts_operator():
                self._consume_operator()
            else:
                self._consume_invalid()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens, self.errors

    def _eof(self):
        return self.pos >= self.length

    def _cur(self):
        return "" if self._eof() else self.text[self.pos]

    def _peek(self, offset=1):
        idx = self.pos + offset
        return "" if idx >= self.length else self.text[idx]

    def _advance(self, steps=1):
        for _ in range(steps):
            if self._eof():
                return
            ch = self.text[self.pos]
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def _add(self, ttype, value):
        self.tokens.append(Token(ttype, value, self.line, self.col))

    def _error(self, message, code_key, value, line=None, col=None):
        code = ERROR_CODES[code_key]
        self.errors.append(
            ScanError(code, message, line if line is not None else self.line,
                      col if col is not None else self.col, value)
        )

    def _consume_identifier(self):
        start_line, start_col = self.line, self.col
        value = self._cur()
        self._advance()

        while not self._eof() and not self._is_separator_or_space_or_op_start(self._cur()):
            value += self._cur()
            self._advance()

        self.tokens.append(Token(TokenType.IDENTIFIER, value, start_line, start_col))

    def _consume_word(self):
        start_line, start_col = self.line, self.col
        value = ""

        while not self._eof() and not self._is_separator_or_space_or_op_start(self._cur()):
            value += self._cur()
            self._advance()

        if value in self.KEYWORDS:
            self.tokens.append(Token(TokenType.KEYWORD, value, start_line, start_col))
            return

        self.tokens.append(Token(TokenType.IDENTIFIER, value, start_line, start_col))

    def _consume_number(self):
        start_line, start_col = self.line, self.col
        value = ""

        while not self._eof() and self._cur().isdigit():
            value += self._cur()
            self._advance()

        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))

    def _starts_operator(self):
        ch1 = self._cur()
        ch2 = self._peek()
        return (ch1 + ch2) in self.OPERATORS or ch1 in self.OPERATORS

    def _consume_operator(self):
        start_line, start_col = self.line, self.col
        ch1 = self._cur()
        ch2 = self._peek()

        if ch1 + ch2 in self.OPERATORS:
            value = ch1 + ch2
            self._advance(2)
        else:
            value = ch1
            self._advance(1)

        self.tokens.append(Token(TokenType.OPERATOR, value, start_line, start_col))

    def _is_separator_or_space_or_op_start(self, ch):
        if ch == "":
            return True
        if ch.isspace():
            return True
        if ch in self.SEPARATORS:
            return True
        if (ch + self._peek()) in self.OPERATORS or ch in self.OPERATORS:
            return True
        return False

    def _is_valid_char(self, ch):
        if ch == "":
            return False
        if ch.isspace():
            return True
        if ch.isalnum():
            return True
        if ch in self.SEPARATORS:
            return True
        if ch == "$":
            return True
        if (ch + self._peek()) in self.OPERATORS or ch in self.OPERATORS:
            return True
        return False

    def _consume_invalid(self):
        start_line, start_col = self.line, self.col
        value = ""

        while not self._eof() and not self._is_valid_char(self._cur()):
            value += self._cur()
            self._advance()

        if value:
            self._error("Недопустимая последовательность символов", "INVALID_CHAR", value, start_line, start_col)
