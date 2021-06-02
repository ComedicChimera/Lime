from typing import List, Optional

from .tokenize import TokenKind, Tokenizer, Token
from .ast import *
from . import LimeError

def text_position_of_token(tok: Token) -> TextPosition:
    return TextPosition(
        tok.line,
        tok.col,
        tok.col + len(tok.value)
    )

class Parser:
    tk: Tokenizer
    tok_cache: List[Token] = []
    awaiting_close: List[str] = []

    def __init__(self, tokenizer):
        self.tk = tokenizer

    def consume(self) -> Optional[Token]:
        if len(self.tok_cache) == 0:
            return self.tk.next_token()

        return self.tok_cache.pop(0)

    def ahead(self) -> Optional[Token]:
        if tok := self.tk.next_token():
            self.tok_cache.append(tok)
            return self.tok_cache[-1]

        return None

    def peek(self) -> Optional[Token]:
        if len(self.tok_cache) > 0 :
            return self.tok_cache[0]
        elif tok := self.tk.next_token():
            self.tok_cache.append(tok)
            return self.tok_cache[0]
        
        return None

    def drop(self):
        if len(self.tok_cache) > 0:
            self.tok_cache.pop(0)
        else:
            self.tk.next_token()

    def unexpected_token(self, tok: Token):
        raise LimeError("parse", f"unexpected token: {tok.value}", tok.line, tok.col)

    def unexpected_end_of_file(self):
        raise LimeError("parse", "unexpected end of file", -1, -1)

    def parse_line(self) -> Optional[AST]:
        if next_tok := self.ahead():
            if next_tok.kind == TokenKind.IDENTIFIER:
                if self.ahead().kind == TokenKind.BIND:
                    name_tok = self.consume()
                    self.drop()

                    expr = self.parse_expr()

                    # consume newline
                    if self.peek():
                        self.consume()

                    return LimeBind(name_tok.value, expr, name_tok.col) 
        else:
            return None

        # handle blank lines
        if next_tok.kind == TokenKind.NEWLINE:
            self.consume()
            return self.parse_line()

        expr = self.parse_expr()

        # consume newline
        if self.peek():
            self.consume()

        return expr

    def parse_expr(self) -> Optional[AST]:
        expr_ast = None

        def update_expr_ast(new_ast: AST):
            nonlocal expr_ast
            if expr_ast == None:
                expr_ast = new_ast
            else:
                expr_ast = LimeFuncApp(expr_ast, new_ast)

        while tok := self.peek():
            if tok.kind == TokenKind.IDENTIFIER:
                update_expr_ast(LimeIdentifier(tok.value, tok.line, tok.col))
            elif tok.kind == TokenKind.NUMBER:
                update_expr_ast(LimeValue(float(tok.value), text_position_of_token(tok)))
            elif tok.kind == TokenKind.STRING:
                update_expr_ast(LimeValue(tok.value, text_position_of_token(tok)))
            elif tok.kind == TokenKind.LPAREN:
                self.awaiting_close.append('(')
                self.consume()
                expr = self.parse_expr()
                self.awaiting_close.pop()
                if expr == None:
                    # consume the unconsumed r-paren to get the "position" of nothing
                    update_expr_ast(LimeValue(None, TextPosition(tok.line, tok.col, self.consume().col-1)))
                    continue
                else:
                    # still want to consume that lingering r-paren so we don't continue here
                    update_expr_ast(expr)
            elif tok.kind == TokenKind.LBRACKET:
                self.consume()
                
                # handle empty lists (which are legal)
                if self.peek().kind == TokenKind.RBRACKET:
                    end_tok = self.consume()
                    update_expr_ast(LimeList([], TextPosition(tok.line, tok.col, end_tok.col)))
                    continue

                self.awaiting_close.append('[')
                exprs = [self.parse_expr()]
                while self.peek().kind == TokenKind.COMMA:
                    self.consume()
                    exprs.append(self.parse_expr())

                self.awaiting_close.pop()

                update_expr_ast(LimeList(exprs, TextPosition(tok.line, tok.col, self.peek().col)))
            elif tok.kind == TokenKind.RPAREN:
                if len(self.awaiting_close) == 0 or self.awaiting_close[-1] == '[':
                    self.unexpected_token(tok)
                else:
                    
                    return expr_ast
            elif tok.kind == TokenKind.COMMA or tok.kind == TokenKind.RBRACKET:
                if len(self.awaiting_close) == 0 or self.awaiting_close[-1] == '(' or expr_ast == None:
                    self.unexpected_token(tok)
                else:
                    return expr_ast
            elif tok.kind == TokenKind.LAMBDA:
                update_expr_ast(self.parse_func())
                continue
            elif tok.kind == TokenKind.NEWLINE:
                if len(self.awaiting_close) > 0:
                    raise LimeError("parse", "unexpected end of line", tok.line-1, tok.col)
                else:
                    return expr_ast
            else:
                self.unexpected_token(tok)

            self.consume()
        else:
            if len(self.awaiting_close) > 0:
                self.unexpected_end_of_file()

        return expr_ast

    def parse_func(self) -> AST:
        start_lambda = self.consume()
        expecting_arg = True
        expecting_dot = False
        args = []

        while next_tok := self.peek():
            if expecting_arg:
                if next_tok.kind == TokenKind.IDENTIFIER:
                    args.append(next_tok.value)
                    expecting_dot = True
                    expecting_arg = False
                elif next_tok.kind == TokenKind.DOT:
                    args.append("")
                    expecting_arg = False
                else:
                    self.unexpected_token(next_tok)

                self.consume()
            elif expecting_dot:
                if next_tok.kind == TokenKind.DOT:
                    expecting_dot = False
                    self.consume()
                else:
                    self.unexpected_token(next_tok)
            elif next_tok.kind == TokenKind.LAMBDA:
                self.consume()
                expecting_arg = True
            else:
                break
        else:
            if expecting_arg or len(self.awaiting_close) > 0:
                self.unexpected_end_of_file()

        expr = self.parse_expr()
        if not expr:
            if nl := self.peek():
                self.unexpected_token(nl)
            else:
                self.unexpected_end_of_file()

        return LimeFuncAbs(args, expr, start_lambda.col)
        