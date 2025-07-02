from dataclasses import dataclass, field
from enum import Enum, auto


class Token(Enum):
    KEYWORD = auto()
    SYMBOL = auto()
    IDENTIFIER = auto()
    INT_CONST = auto()
    STRING_CONST = auto()


@dataclass
class JackTokenizer:
    input: str
    tokens: list[str] = field(default_factory=lambda: [])
    counter: int = 0
    keywords: set[str] = field(
        default_factory=lambda: {
            "class",
            "method",
            "function",
            "constructor",
            "int",
            "boolean",
            "char",
            "void",
            "var",
            "static",
            "field",
            "let",
            "do",
            "if",
            "else",
            "while",
            "return",
            "true",
            "false",
            "null",
            "this",
        }
    )
    token_types: set[str] = field(
        default_factory=lambda: {
            "keyword",
            "symbol",
            "identifier",
            "int_const",
            "string_const",
        }
    )
    symbols: str = field(default_factory=lambda: "{}()[].,;+-*/&|<>=~")
    operations: set[str] = field(
        default_factory=lambda: {"+", "-", "*", "/", "&", "|", "<", ">", "="}
    )

    def create_tokens(self) -> None:
        for i in range(0, len(self.symbols)):
            character = self.symbols[i]
            mod = " " + self.symbols[i] + " "
            self.input = self.input.replace(character, mod)
        self.tokens = self.input.split(" ")
        self.tokens = [token for token in self.tokens if token != ""]
        final_tokens = []
        ind: int = 0
        while ind < len(self.tokens):
            if self.tokens[ind][0] == '"':
                cur_string: str = ""
                while True:
                    cur_string += self.tokens[ind]
                    if self.tokens[ind][len(self.tokens[ind]) - 1] == '"':
                        break
                    cur_string += " "
                    ind += 1
                final_tokens.append(str(cur_string))
                ind += 1
                continue
            final_tokens.append(self.tokens[ind])
            ind += 1
        self.tokens = final_tokens

    def increment_counter(self) -> None:
        self.counter += 1

    def current_token(self) -> str:
        token = self.tokens[self.counter]
        if token[0] == '"':
            token = token[1 : len(token) - 1]
        if token in self.operations:
            if token == "<":
                token = "&lt;"
            if token == ">":
                token = "&gt;"
            if token == "&":
                token = "&amp;"
        return token

    def has_token(self) -> bool:
        return self.counter < len(self.tokens)

    def token_keyword(self) -> str:
        current_token = self.tokens[self.counter].lower()
        if current_token in self.keywords:
            return "keyword"
        if current_token in self.symbols:
            return "symbol"
        if current_token[0] == '"':
            return "stringConstant"
        try:
            int(current_token[0])
            return "integerConstant"
        except ValueError:
            return "identifier"
