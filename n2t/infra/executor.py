import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from n2t.core import Assembler


@dataclass
class Executor:
    current_file: str
    ROM: list[str]
    ticks: int
    RAM: dict[int, int] = field(default_factory=lambda: {})
    A: int = field(default_factory=lambda: 0)
    D: int = field(default_factory=lambda: 0)
    powers: list[int] = field(default_factory=lambda: [2**i for i in range(16)])
    comp_table: dict[str, str] = field(
        default_factory=lambda: {
            "101010": "0",
            "111111": "1",
            "111010": "-1",
            "001100": "D",
            "110000": "A",
            "001101": "!D",
            "110001": "!A",
            "001111": "-D",
            "110011": "-A",
            "011111": "D+1",
            "110111": "A+1",
            "001110": "D-1",
            "110010": "A-1",
            "000010": "D+A",
            "010011": "D-A",
            "000111": "A-D",
            "000000": "D&A",
            "010101": "D|A",
        }
    )

    @staticmethod
    def get_jmp(bits: str, comp: int) -> bool:
        res: bool = False
        if bits[0] == "1":
            res = res or comp < 0
        if bits[1] == "1":
            res = res or comp == 0
        if bits[2] == "1":
            res = res or comp > 0
        return res

    @staticmethod
    def get_dest(bits: str) -> str:
        result: str = ""
        if bits[0] == "1":
            result += "A"
        if bits[1] == "1":
            result += "D"
        if bits[2] == "1":
            result += "M"
        return result

    def get_value(self, bits: str) -> int:
        result: int = 0
        for i in range(16):
            if bits[15 - i] == "0":
                continue
            result += self.powers[i]
        return result

    def get_m(self) -> int:
        if self.A in self.RAM:
            return self.RAM[self.A]
        else:
            self.RAM[self.A] = 0
            return 0

    def evaluate_comp(self, bits: str) -> int:
        comp_str: str = self.comp_table[bits[1:]]
        if comp_str == "0":
            return 0
        if comp_str == "1":
            return 1
        if comp_str == "-1":
            return -1
        cur_a: int = self.A
        if "A" in comp_str and bits[0] == "1":
            cur_a = self.get_m()
        if comp_str == "D":
            return self.D
        if comp_str == "A":
            return cur_a
        if comp_str == "!D":
            return ~self.D
        if comp_str == "!A":
            return ~cur_a
        if comp_str == "-D":
            return -1 * self.D
        if comp_str == "-A":
            return -1 * cur_a
        if comp_str == "D+1":
            return self.D + 1
        if comp_str == "A+1":
            return cur_a + 1
        if comp_str == "D-1":
            return self.D - 1
        if comp_str == "A-1":
            return cur_a - 1
        if comp_str == "D+A":
            return self.D + cur_a
        if comp_str == "D-A":
            return self.D - cur_a
        if comp_str == "A-D":
            return cur_a - self.D
        if comp_str == "D&A":
            return self.D & cur_a
        if comp_str == "D|A":
            return self.D | cur_a
        return -1

    def assign_dest(self, dest: str, comp: int) -> None:
        for reg in dest:
            if reg == "A":
                self.A = comp
            if reg == "D":
                self.D = comp
            if reg == "M":
                self.RAM[self.A] = comp

    def compile(self) -> None:
        tick: int = self.ticks
        inf: bool = tick == -1
        line_ind: int = 0
        while inf or tick >= 0:
            tick -= 1
            if line_ind >= len(self.ROM):
                if inf:
                    break
                continue
            cur_line: str = self.ROM[line_ind]
            if cur_line[0] == "0":
                self.A = self.get_value(cur_line)
                line_ind += 1
                continue
            dest: str = Executor.get_dest(cur_line[10:13])
            comp: int = self.evaluate_comp(cur_line[3:10])
            self.assign_dest(dest, comp)
            jmp: bool = Executor.get_jmp(cur_line[13:], comp)
            if jmp:
                line_ind = self.A
            else:
                line_ind += 1

    @classmethod
    def load_from(cls, file: str, cycles: int) -> Self:
        file_path: Path = Path(file)
        txt: str = read_file(file)
        txt = txt.replace("\t", "")
        res: list[str] = txt.split("\n")
        if file_path.suffix == ".asm":
            assembler: Assembler = Assembler.create()
            res = list(assembler.assemble(res))
        return cls(file, res, cycles, RAM={0: 256})

    def dump_json(self) -> None:
        file_path: Path = Path(self.current_file)
        new_path: Path = file_path.with_suffix(".json")
        with open(new_path, "w") as json_file:
            json.dump(self.RAM, json_file, indent=4)


def read_file(file: str) -> str:
    with open(file, "r", newline=None) as f1:
        return f1.read()
