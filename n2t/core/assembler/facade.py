from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class Assembler:
    @classmethod
    def create(cls) -> Assembler:
        return cls()

    symbol_table = {
        "R0": 0,
        "R1": 1,
        "R2": 2,
        "R3": 3,
        "R4": 4,
        "R5": 5,
        "R6": 6,
        "R7": 7,
        "R8": 8,
        "R9": 9,
        "R10": 10,
        "R11": 11,
        "R12": 12,
        "R13": 13,
        "R14": 14,
        "R15": 15,
        "SCREEN": 16384,
        "KBD": 24576,
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
    }

    comp_table = {
        "0": "0101010",
        "1": "0111111",
        "-1": "0111010",
        "D": "0001100",
        "A": "0110000",
        "!D": "0001101",
        "!A": "0110001",
        "-D": "0001111",
        "-A": "0110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "D+A": "0000010",
        "D-A": "0010011",
        "A-D": "0000111",
        "D&A": "0000000",
        "D|A": "0010101",
        "M": "1110000",
        "!M": "1110001",
        "-M": "1110011",
        "M+1": "1110111",
        "M-1": "1110010",
        "D+M": "1000010",
        "D-M": "1010011",
        "M-D": "1000111",
        "D&M": "1000000",
        "D|M": "1010101",
    }

    dest_table = {
        "M": "001",
        "D": "010",
        "DM": "011",
        "A": "100",
        "AM": "101",
        "AD": "110",
        "ADM": "111",
    }

    jump_table = {
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111",
    }

    def get_assembly_size(self, assembly: Iterable[str]) -> int:
        res: int = 0
        for line in assembly:
            line = line.replace(" ", "")
            if line == "":
                continue
            if line[0] != "/" and (
                line.find("@") != -1 or line.find("=") != -1 or line.find(";") != -1
            ):
                res += 1
        return res

    def build_label_table(
        self, table: dict[str, int], assembly: Iterable[str], assembly_size: int
    ) -> None:
        cur_instruction: int = 0
        counter: int = 0
        reversed_assembly = reversed(list(assembly))
        for rev_line in reversed_assembly:
            if rev_line.find("//") != -1:
                rev_line = rev_line[0 : rev_line.find("//")]
            rev_line = rev_line.replace(" ", "")
            if rev_line == "" or rev_line[0] == "/":
                continue
            if rev_line[0] != "(":
                counter += 1
                cur_instruction = assembly_size - counter
            else:
                table[rev_line[1 : rev_line.find(")")]] = cur_instruction

    def build_variable_table(
        self, table: dict[str, int], assembly: Iterable[str]
    ) -> None:
        cur_ind: int = 16
        for line in assembly:
            line = line.replace(" ", "")
            if line.find("//") != -1:
                line = line[0 : line.find("//")]
            if line == "" or line[0] == "/":
                continue
            try:
                int(line[1:])
            except ValueError:
                if line[0] == "@" and line[1:] not in table:
                    table[line[1:]] = cur_ind
                    cur_ind += 1

    def handle_A_instruction(self, line: str, keyword_table: dict[str, int]) -> str:
        res = "0"
        try:
            value: int = int(line[1:])
            binary: str = bin(value).replace("0b", "")
            res = "0" * (16 - len(binary)) + binary
        except ValueError:
            tmp = bin(keyword_table[line[1:]]).replace("0b", "")
            res = "0" * (16 - len(tmp)) + tmp
        return res

    def handle_C_instruction(self, line: str, keyword_table: dict[str, int]) -> str:
        res = "111"
        if line.find("=") == -1:
            res += self.comp_table[line[0 : line.find(";")]]
            res += "000"
            res += self.jump_table[line[line.find(";") + 1 :]]
        elif line.find(";") == -1:
            res += self.comp_table[line[line.find("=") + 1 :]]
            res += self.dest_table["".join(sorted(line[0 : line.find("=")]))]
            res += "000"
        else:
            res += self.comp_table[line[line.find("=") + 1 : line.find(";")]]
            res += self.dest_table["".join(sorted(line[0 : line.find("=")]))]
            res += self.jump_table[line[line.find(";") + 1 :]]
        return res

    def assemble(self, assembly: Iterable[str]) -> Iterable[str]:
        result: list[str] = []
        assembly_size: int = self.get_assembly_size(assembly)
        keywords: dict[str, int] = self.symbol_table.copy()
        self.build_label_table(keywords, assembly, assembly_size)
        self.build_variable_table(keywords, assembly)

        for line in assembly:
            if line.find("//") != -1:
                line = line[0 : line.find("//")]
            line = line.replace(" ", "")
            if line == "":
                continue
            if line[0] == "@":
                result.append(self.handle_A_instruction(line, keywords))
            elif line[0] == "/":
                continue
            elif line.find("=") != -1 or line.find(";") != -1:
                result.append(self.handle_C_instruction(line, keywords))

        return result
