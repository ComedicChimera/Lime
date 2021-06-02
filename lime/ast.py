from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Text

@dataclass
class TextPosition:
    line: int
    start_col: int
    end_col: int 

class AST(ABC):
    @abstractmethod
    def position(self) -> TextPosition:
        pass

@dataclass
class LimeIdentifier(AST):
    name: str
    line: int
    col: int

    def position(self) -> TextPosition:
        return TextPosition(self.line, self.col, self.col + len(self.name))

    def __repr__(self):
        return self.name

@dataclass
class LimeValue(AST):
    value: Any
    pos: TextPosition

    def position(self) -> TextPosition:
        return self.pos

    def __repr__(self):
        if not self.value:
            return "()"

        return self.value.__repr__()

@dataclass
class LimeList(AST):
    exprs: List[AST]
    pos: TextPosition

    def position(self) -> TextPosition:
        return self.pos

    def __repr__(self):
        return self.exprs.__repr__()

@dataclass
class LimeFuncApp(AST):
    func: AST
    arg: AST

    def position(self) -> TextPosition:
        return TextPosition(
            self.func.position().line, 
            self.func.position().start_col, 
            self.arg.position().end_col
            )

    def __repr__(self):
        return f'({self.func} {self.arg})'

@dataclass
class LimeFuncAbs(AST):
    args: List[str]
    expr: AST
    args_start_col: int

    def position(self) -> TextPosition:
        return TextPosition(
            self.expr.position().line,
            self.args_start_col,
            self.expr.position().end_col
        )

    def __repr__(self):
        return "".join("\\{arg}." for arg in self.args) + self.expr

@dataclass
class LimeBind(AST):
    var_name: str
    expr: AST
    var_start_col: int

    def position(self) -> TextPosition:
        return TextPosition(
            self.expr.position().line,
            self.vars_start_col,
            self.expr.position().end_col
        )
