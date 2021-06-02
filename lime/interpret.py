from typing import Dict, Any, List, Type, Union, Optional
from inspect import signature
from functools import partial
from dataclasses import dataclass
from collections import Sequence

from .tokenize import Tokenizer
from .parse import Parser
from .ast import *
from . import LimeError

@dataclass
class LimeArgValue:
    expr: AST
    result: Optional[LimeValue]
    pos: TextPosition

    def position(self):
        return self.pos

    def __repr__(self):
        if self.result:
            return self.result.__repr__()

        return self.expr.__repr__()

@dataclass
class LimeLambdaValue:
    arg_names: List[str]
    arg_values: List[LimeArgValue]
    expr: AST

    def call(self, li, arg: AST):
        llv = LimeLambdaValue(self.arg_names, self.arg_values + [LimeArgValue(arg, None, arg.position())], self.expr)
        
        if len(llv.arg_values) == len(self.arg_names):
            for arg_name, arg_val in zip(self.arg_names, llv.arg_values):
                if arg_name == "":
                    continue

                llv.expr = li.substitute(llv.expr, arg_name, arg_val)

            result = li.eval_expr(llv.expr)
            return result.value

        return llv

    def __repr__(self):
        lambda_repr = ""
        for i in range(len(self.arg_values), len(self.arg_names)):
            lambda_repr += f'\\{self.arg_names[i]}.'

        lambda_repr += self.expr.__repr__()
        return lambda_repr

class LimeInterpreter:
    tokenizer: Tokenizer
    state: Dict[str, Any]

    def __init__(self, file):
        self.tokenizer = Tokenizer(file)

        # set up builtins
        self.state = {
            "get": self.wrap_builtin(input),
            "num": self.wrap_builtin(float, str),
            "str": self.wrap_builtin(str, float),
            "at": self.wrap_builtin(lambda x, i: x[int(i)], Sequence, float),
            "cat": self.wrap_builtin(lambda a, b: a + b, str, str),
            "join": self.wrap_builtin(lambda a, b: a + b, list, list),
            "len": self.wrap_builtin(lambda s: float(len(s)), Sequence),
            "do": self.wrap_builtin(lambda _, g: g, object, object),
            "print": self.wrap_builtin(print, object),
            "+": self.wrap_builtin(lambda a, b: a + b, float, float),
            "-": self.wrap_builtin(lambda a, b: a - b, float, float),
            "*": self.wrap_builtin(lambda a, b: a * b, float, float),
            "/": self.wrap_builtin(lambda a, b: a / b, float, float),
            "%": self.wrap_builtin(lambda a, b: a % b, float, float),
            "=": self.wrap_builtin(lambda a, b, c, d: self.eval_expr(c if a == b else d).value, object, object, AST, AST),
            "<": self.wrap_builtin(lambda a, b, c, d: self.eval_expr(c if a < b else d).value, object, object, AST, AST),
            ">": self.wrap_builtin(lambda a, b, c, d: self.eval_expr(c if a > b else d).value, object, object, AST, AST),
        }

    def interpret(self):
        p = Parser(self.tokenizer)
        while ast := p.parse_line():
            self.eval_line(ast)

    def eval_line(self, ast: AST):
        if isinstance(ast, LimeBind):
            self.state[ast.var_name] = self.eval_expr(ast.expr).value
        else:
            print(self.eval_expr(ast))

    def eval_expr(self, ast: Union[AST, LimeLambdaValue, LimeArgValue]) -> LimeValue:
        if isinstance(ast, LimeValue):
            return ast
        elif isinstance(ast, LimeLambdaValue):
            return LimeValue(ast, ast.position())
        elif isinstance(ast, LimeArgValue):
            if ast.result:
                return ast.result

            result = self.eval_expr(ast.expr)
            ast.result = result
            return ast.result
        elif isinstance(ast, LimeIdentifier):
            if ast.name in self.state:
                return LimeValue(self.state[ast.name], ast.position())
            else:
                raise LimeError("name", f"`{ast.name}` is not defined", ast.line, ast.col)
        elif isinstance(ast, LimeList):
            return LimeValue([self.eval_expr(x).value for x in ast.exprs], ast.position())
        elif isinstance(ast, LimeFuncApp):
            func_lv = self.eval_expr(ast.func)
            func_value = func_lv.value

            if callable(func_value):
                if len(signature(func_value).parameters) == 0:
                    arg_lv = self.eval_expr(ast.arg)
                    if not arg_lv.value:
                        return LimeValue(func_value(), ast.position())
                    else:
                        raise LimeError("argument", "too many arguments for function", arg_lv.pos.line, arg_lv.pos.start_col)
                elif len(signature(func_value).parameters) == 1:
                    return LimeValue(func_value(ast.arg), ast.position())
                else:
                    return LimeValue(partial(func_value, ast.arg), ast.position())
            elif isinstance(func_value, LimeLambdaValue):
                return LimeValue(func_value.call(self, ast.arg), ast.position())
            else:
                raise LimeError("type", f"unable to call a type of {get_type_str(type(func_value))}", func_lv.pos.line, func_lv.pos.start_col)
        elif isinstance(ast, LimeFuncAbs):
            return LimeValue(LimeLambdaValue(ast.args, [], ast.expr), ast.position())

        # unreachable

    def substitute(self, expr: AST, arg_name: str, arg_val: LimeArgValue) -> AST:
        if isinstance(expr, LimeIdentifier):
            if expr.name == arg_name:
                return arg_val
            else:
                return expr
        elif isinstance(expr, LimeList):
            return LimeList([self.substitute(elem, arg_name, arg_val) for elem in expr.exprs], expr.pos)
        elif isinstance(expr, LimeFuncAbs):
            if arg_name in expr.args:
                return expr
            else:
                return LimeFuncAbs(expr.args, self.substitute(expr.expr, arg_name, arg_val), expr.args_start_col)
        elif isinstance(expr, LimeFuncApp):
            return LimeFuncApp(self.substitute(expr.func, arg_name, arg_val), self.substitute(expr.arg, arg_name, arg_val))
        else:
            return expr
                
    def wrap_builtin(self, func, *arg_types):
        if len(arg_types) == 0:
            def wrapper():
                return func()

            return wrapper
        elif len(arg_types) == 1:
            def wrapper(a):
                return func(self.get_value(a, arg_types[0]))

            return wrapper
        elif len(arg_types) == 2:
            def wrapper(a, b):
                return func(self.get_value(a, arg_types[0]), self.get_value(b, arg_types[1]))

            return wrapper
        elif len(arg_types) == 4:
            def wrapper(a, b, c, d):
                return func(*(self.get_value(x, t) for x, t in zip([a, b, c, d], arg_types)))

            return wrapper

    def get_value(self, v: AST, t: Type):
        if t == AST:
            return v

        lv = self.eval_expr(v)
        if isinstance(lv.value, t):
            return lv.value
        
        raise LimeError("type", f"expected type of {get_type_str(t)}; received type of {get_type_str(type(lv.value))}", lv.pos.line, lv.pos.start_col)

def get_type_str(t) -> str:
    if t == object:
        return "any"
    elif t == float:
        return "number"
    elif t == str:
        return "string"
    elif t == list:
        return "list"
    elif not t:
        return "none"
    else:
        return t.__repr__()
