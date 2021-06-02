from dataclasses import dataclass

@dataclass
class LimeError(Exception):
    kind: str
    message: str
    line: int
    col: int
