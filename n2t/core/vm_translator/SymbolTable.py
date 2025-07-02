from dataclasses import dataclass


@dataclass
class SymbolTableEntry:
    type: str
    kind: str
    ind: int


class SymbolTable:
    table: dict[str, SymbolTableEntry]
    indexes: dict[str, int] = {}
    kinds: list[str] = ["this", "static", "argument", "local"]

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        for kind in self.kinds:
            self.indexes[kind] = 0

        self.table = {}

    def define(self, name: str, symbol_type: str, kind: str) -> None:
        self.table[name] = SymbolTableEntry(symbol_type, kind, self.indexes[kind])
        self.indexes[kind] += 1

    def var_count(self, kind: str) -> int:
        return self.indexes[kind]

    def kind_of(self, name: str) -> str:
        return self.table[name].kind

    def type_of(self, name: str) -> str:
        return self.table[name].type

    def index_of(self, name: str) -> int:
        return self.table[name].ind

    def has_name(self, name: str) -> bool:
        return name in self.table
