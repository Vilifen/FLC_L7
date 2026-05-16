from .scanner import Scanner
from .parser import Parser
from .semantic_analyzer import SemanticAnalyzer

def run_scanner(editor):
    text = editor.toPlainText()
    scanner = Scanner()
    tokens, lex_errors = scanner.scan(text)
    parser = Parser(tokens)
    ast_nodes, syntax_errors = parser.parse()
    semantic_errors = []

    if ast_nodes:
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast_nodes)

    all_errors = lex_errors + syntax_errors
    token_rows = []
    error_rows = []

    for t in tokens:
        token_rows.append({
            "code": t.type.value,
            "type": t.type.name,
            "lexeme": t.value,
            "location": f"строка {t.line}, {t.column}",
            "line": t.line,
            "col": t.column
        })

    for e in all_errors:
        error_rows.append({
            "code": e.code,
            "lexeme": e.char,
            "description": e.message,
            "location": f"строка {e.line}, {e.column}",
            "line": e.line,
            "col": e.column
        })

    for se in semantic_errors:
        error_rows.append({
            "code": "SEMANTIC_ERROR",
            "lexeme": se.char if hasattr(se, 'char') else "",
            "description": se.message,
            "location": f"строка {se.line}, {se.column}",
            "line": se.line,
            "col": se.column
        })

    return token_rows, error_rows, ast_nodes