from dataclasses import dataclass
from typing import Tuple
from enum import Enum, auto

from . import LimeError

class TokenKind(Enum):
    BIND = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    LAMBDA = auto()
    DOT = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    NEWLINE = auto()

@dataclass
class Token:
    kind: TokenKind
    value: str
    line: int
    col: int

class Tokenizer:
    simple_tokens = {
        '.': TokenKind.DOT,
        ',': TokenKind.COMMA,
        '(': TokenKind.LPAREN,
        ')': TokenKind.RPAREN,
        '[': TokenKind.LBRACKET,
        ']': TokenKind.RBRACKET,
        '\\': TokenKind.LAMBDA,
        '\n': TokenKind.NEWLINE
    }

    esc_codes = {
        'n': '\n',
        't': '\t',
        'b': '\b',
        's': ' ',
        'v': '\v',
        'f': '\f',
        'r': '\r',
        '\\': '\\',
        '\"': '\"'
    }

    whitespace = " \t\v\f\r"

    def __init__(self, file):
        self.file = file
        self.tokbuff = ""
        self.line = 1
        self.col = 1

    def next_token(self):
        while c := self.peek_next():
            if c in self.whitespace:
                self.skip_next()
                continue

            if c == ';':
                # skip comments
                while c != '\n' and c:
                    self.skip_next()
                    c = self.peek_next()

                if c == '\n':
                    self.read_next()
                    return self.make_token(TokenKind.NEWLINE)
            elif c == ':':
                self.read_next()
                if self.read_next(True) != '=':
                    self.raise_token_error("expected `=` after `:`")
                else:
                    return self.make_token(TokenKind.BIND)
            elif c == '\n':
                self.read_next()
                return self.make_token(TokenKind.NEWLINE)
            elif c == '\"':
                return self.tokenize_string()
            elif c in self.simple_tokens:
                self.read_next()
                return self.make_token(self.simple_tokens[c])
            elif c.isdigit():
                return self.tokenize_number()
            else:
                return self.tokenize_identifier()


    def read_next(self, reject_eof=False):
        c = self.file.read(1)
        if not c:
            if reject_eof:
                self.raise_token_error("unexpected EOF")
            else:
                return c

        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        self.tokbuff += c
        return c

    def peek_next(self, reject_eof=False):
        c = self.file.read(1)
        if not c:
            if reject_eof:
                self.raise_token_error("unexpected EOF")
        else:
            self.file.seek(self.file.tell()-1)

        return c

    def skip_next(self):
        if c := self.file.read(1):
            if c == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1


    def make_token(self, kind):
        tok = Token(kind, self.tokbuff, self.line if kind == TokenKind.NEWLINE else self.line, self.col-len(self.tokbuff))
        self.tokbuff = ""
        return tok

    def raise_token_error(self, msg):
        raise LimeError("token", msg, self.line, self.col)

    def tokenize_string(self):
        # skip the leading quote
        self.skip_next()

        while True:
            c = self.peek_next(True)

            if c == '\"':
                self.skip_next()
                return self.make_token(TokenKind.STRING)
            elif c == '\\':
                self.skip_next()
                c = self.peek_next(True)
                
                if c in self.esc_codes:
                    self.read_next()
                    # overwrite the escape code
                    self.tokbuff[-1] = self.esc_codes[c]
                else:
                    # read in the erroneous code we can error on it
                    self.read_next()
                    self.raise_token_error(f"invalid escape code `{c}`")
            else:
                self.read_next()

    def tokenize_number(self):
        requires_next_number = False
        hit_dot = False

        while True:
            c = self.peek_next(requires_next_number)

            if not c:
                return self.make_token(TokenKind.NUMBER)
            elif c == '.' and not hit_dot:
                self.read_next()
                requires_next_number = True
                hit_dot = True
            elif c.isdigit():
                self.read_next()
                requires_next_number = False
            elif requires_next_number:
                # read to get correct error position
                self.read_next()
                self.raise_token_error("expected digit after decimal point")
            else:
                return self.make_token(TokenKind.NUMBER)

    def tokenize_identifier(self):
        while c := self.peek_next():
            if c in self.simple_tokens or c in self.whitespace or c == '\"' or c == ';':
                return self.make_token(TokenKind.IDENTIFIER)
            else:
                self.read_next()

        return self.make_token(TokenKind.IDENTIFIER)
