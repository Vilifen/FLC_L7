def navigate_to_error(editor, line, col):
    block = editor.document().findBlockByNumber(line - 1)
    pos = block.position() + (col - 1)
    cursor = editor.textCursor()
    cursor.setPosition(pos)
    editor.setTextCursor(cursor)
    editor.setFocus()
