from dataclasses import dataclass

@dataclass
class ScanError:
    code: int
    message: str
    line: int
    column: int
    char: str
