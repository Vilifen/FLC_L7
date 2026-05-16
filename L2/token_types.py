from enum import Enum

class TokenType(Enum):
    KEYWORD = 1
    IDENTIFIER = 2
    NUMBER = 3
    OPERATOR = 4
    SEPARATOR = 5
    WHITESPACE = 6
    UNKNOWN = 7
    EOF = 8
