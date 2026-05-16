from .scan_error import ScanError
from .error_codes import ERROR_CODES
from .token_types import TokenType
from .ast_nodes import VarNode, NumberNode, BinOpNode, UnaryOpNode, BlockNode, WhileNode
from .semantic_analyzer import SemanticAnalyzer


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self.stop_parsing = False
        self.consecutive_errors = 0
        self.analyzer = SemanticAnalyzer()

    def parse(self):
        self.pos = 0
        self.errors = []
        self.stop_parsing = False
        self.consecutive_errors = 0
        self._skip_ws()

        ast_nodes = []
        while not self._eof() and not self.stop_parsing:
            node = self.parse_while_statement()
            if node:
                semantic_errors = self.analyzer.analyze([node])
                if not semantic_errors:
                    ast_nodes.append(node)
                else:
                    self.errors.extend(semantic_errors)

            self._skip_ws()
            if self.consecutive_errors > 5:
                break

        return ast_nodes, self.errors

    def _match_with_recovery(self, expected_vals, sync_vals, error_msg):
        self._skip_ws()
        if self._eof():
            self._error(f"Неожиданный конец файла. Ожидалось: {error_msg}")
            return False

        tok = self.tokens[self.pos]
        if tok.value in expected_vals or tok.type in expected_vals:
            self.pos += 1
            self.consecutive_errors = 0
            return True

        self._error(f"Ожидалось: {error_msg}, получено '{tok.value}'")

        while not self._eof():
            tok = self.tokens[self.pos]
            if tok.value in expected_vals or tok.type in expected_vals:
                self.pos += 1
                self.consecutive_errors = 0
                return True
            if tok.value in sync_vals or tok.type in sync_vals:
                return False
            self.pos += 1
            self._skip_ws()
        return False

    def parse_while_statement(self):
        self._skip_ws()
        if self._eof():
            return None

        tok = self.tokens[self.pos]
        if tok.value != "while":
            self._error("ключевое слово 'while'")
            self.pos += 1
            return None

        self.pos += 1
        self.consecutive_errors = 0

        condition_node = None
        if self._match_with_recovery(["("], [TokenType.IDENTIFIER, "$", "{"], "'('"):
            condition_node = self.parse_condition()
            self._match_with_recovery([")"], ["{"], "')'")

        body_node = None
        if self._match_with_recovery(["{"], [TokenType.IDENTIFIER, "}"], "'{'"):
            body_node = self.parse_block()

        self._match_with_recovery([";"], ["while", TokenType.EOF], "';' после цикла")

        return WhileNode(condition_node, body_node)

    def parse_condition(self):
        node = self.parse_simple_expression()
        self._skip_ws()
        while not self._eof() and self.tokens[self.pos].value in ["||", "&&"]:
            op = self.tokens[self.pos].value
            self.pos += 1
            self.consecutive_errors = 0
            right = self.parse_simple_expression()
            node = BinOpNode(node, op, right)
            self._skip_ws()
        return node

    def parse_simple_expression(self):
        self._skip_ws()
        if self._eof():
            return None

        left_node = None
        tok = self.tokens[self.pos]
        if tok.type == TokenType.IDENTIFIER and tok.value.startswith("$"):
            left_node = VarNode(tok.value, tok.line, tok.column)
            self.pos += 1
            self.consecutive_errors = 0
        else:
            self._error("переменная вида '$id'")
            self.pos += 1

        self._skip_ws()
        op = None
        ops = ["<", ">", "==", ">=", "<=", "!="]
        if not self._eof() and self.tokens[self.pos].value in ops:
            op = self.tokens[self.pos].value
            self.pos += 1
            self.consecutive_errors = 0
        else:
            self._error("оператор сравнения")
            if not self._eof():
                self.pos += 1

        self._skip_ws()
        right_node = None
        if not self._eof():
            tok = self.tokens[self.pos]
            if tok.type == TokenType.NUMBER:
                right_node = NumberNode(int(tok.value), tok.line, tok.column)
                self.pos += 1
                self.consecutive_errors = 0
            elif tok.type == TokenType.IDENTIFIER and tok.value.startswith("$"):
                right_node = VarNode(tok.value, tok.line, tok.column)
                self.pos += 1
                self.consecutive_errors = 0
            else:
                self._error("число или переменная '$id'")
                self.pos += 1

        return BinOpNode(left_node, op, right_node)

    def parse_block(self):
        statements = []
        while not self._eof():
            self._skip_ws()
            tok = self.tokens[self.pos]
            if tok.value == "}":
                self.pos += 1
                self.consecutive_errors = 0
                break

            if tok.type == TokenType.IDENTIFIER and tok.value.startswith("$"):
                var_node = VarNode(tok.value, tok.line, tok.column)
                self.pos += 1
                self.consecutive_errors = 0
                self._skip_ws()
                op_tok = self.tokens[self.pos] if not self._eof() else None
                if op_tok and op_tok.value in ["++", "--"]:
                    statements.append(UnaryOpNode(var_node, op_tok.value))
                    self.pos += 1
                    self.consecutive_errors = 0
                else:
                    self._error("++ или --")
                    if not self._eof(): self.pos += 1
                self._match_with_recovery([";"], ["}", "$"], "';'")
            else:
                self._error("инструкция ($id++) или '}'")
                self.pos += 1
        return BlockNode(statements)

    def _error(self, msg):
        if self.consecutive_errors > 0:
            return
        if self._eof():
            tok = self.tokens[-1] if self.tokens else None
        else:
            tok = self.tokens[self.pos]
        if tok:
            self.errors.append(
                ScanError(ERROR_CODES["INVALID_STRUCTURE"], f"Ошибка: {msg}", tok.line, tok.column, tok.value))
            self.consecutive_errors += 1

    def _skip_ws(self):
        while not self._eof() and self.tokens[self.pos].type == TokenType.WHITESPACE:
            self.pos += 1

    def _eof(self):
        return self.pos >= len(self.tokens) or (
                self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.EOF)