from .ast_nodes import VarNode, BinOpNode, UnaryOpNode, BlockNode, WhileNode


class SymbolTable:
    def __init__(self):
        self.symbols = set()

    def declare(self, name):
        self.symbols.add(name)

    def lookup(self, name):
        return name in self.symbols

    def clear(self):
        self.symbols.clear()


class SemanticError:
    def __init__(self, message, line, column, value=""):
        self.message = message
        self.line = line
        self.column = column
        self.code = "SEMANTIC_ERROR"
        self.char = value
        self.value = value


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.symbol_table = SymbolTable()

    def _collect_vars(self, node, vars_list):
        if node is None:
            return

        if isinstance(node, VarNode):
            vars_list.append(node)

        if hasattr(node, 'left'): self._collect_vars(node.left, vars_list)
        if hasattr(node, 'right'): self._collect_vars(node.right, vars_list)
        if hasattr(node, 'operand'): self._collect_vars(node.operand, vars_list)
        if hasattr(node, 'condition'): self._collect_vars(node.condition, vars_list)
        if hasattr(node, 'body'): self._collect_vars(node.body, vars_list)
        if hasattr(node, 'statements'):
            for stmt in node.statements:
                self._collect_vars(stmt, vars_list)

    def analyze(self, ast_nodes):
        self.errors = []
        for node in ast_nodes:
            self._recursive_search(node)
        return self.errors

    def _recursive_search(self, node):
        if isinstance(node, WhileNode):
            self._analyze_while_node(node)

        if hasattr(node, 'statements'):
            for stmt in node.statements:
                self._recursive_search(stmt)
        elif hasattr(node, 'body'):
            self._recursive_search(node.body)

    def _analyze_while_node(self, while_node):
        self.symbol_table.clear()

        cond_vars = []
        self._collect_vars(while_node.condition, cond_vars)

        for v in cond_vars:
            self.symbol_table.declare(v.name)

        body_vars = []
        self._collect_vars(while_node.body, body_vars)

        body_var_names = set()
        for b_var in body_vars:
            body_var_names.add(b_var.name)
            if not self.symbol_table.lookup(b_var.name):
                self.errors.append(SemanticError(
                    f"идентификатор '{b_var.name}' используется, но не был объявлен в условии цикла",
                    b_var.line, b_var.column, b_var.name))

        cond_var_names = {v.name for v in cond_vars}
        if cond_var_names and not cond_var_names.intersection(body_var_names):
            trigger_v = cond_vars[0]
            self.errors.append(SemanticError(
                "Переменная условия не появляется в теле цикла",
                trigger_v.line, trigger_v.column, trigger_v.name))