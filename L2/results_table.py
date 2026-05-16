from .token_codes import TOKEN_CODES


def build_table_rows(tokens, errors):
    token_rows = []
    error_rows = []

    for t in tokens:
        if t.type.name == "WHITESPACE":
            continue

        code = TOKEN_CODES[t.type.name]
        lexeme = t.value
        location = f"строка {t.line}, {t.column}-{t.column + len(t.value) - 1}"

        token_rows.append({
            "code": code,
            "type": t.type.name,
            "lexeme": lexeme,
            "location": location,
            "line": t.line,
            "col": t.column,
        })

    for e in errors:
        error_rows.append({
            "code": e.code,
            "type": "ERROR",
            "lexeme": e.char,
            "location": f"строка {e.line}, {e.column}",
            "line": e.line,
            "col": e.column,
        })

    return token_rows, error_rows
