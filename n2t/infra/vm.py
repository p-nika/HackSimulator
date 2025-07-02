from __future__ import annotations

import os.path
from dataclasses import dataclass
from pathlib import Path

from n2t.infra.io import File, FileFormat


@dataclass
class VmProgram:  # TODO: your work for Projects 7 and 8 starts here
    src_file: File
    dst_file: File
    offset = {
        "sp": 0,
        "local": 1,
        "argument": 2,
        "this": 3,
        "that": 4,
        "temp": 5,
        "static": 16,
    }
    is_dir: bool
    bool_op_cnt: int = 0
    return_cnt: int = 0

    @classmethod
    def load_from(cls, file_or_directory_name: str) -> VmProgram:
        cur_path: Path = Path(file_or_directory_name)
        if cur_path.is_dir():
            asm_file_path: Path = cur_path / (
                os.path.basename(os.path.normpath(file_or_directory_name)) + ".asm"
            )
            asm_file_path.touch()
            asm_file: File = File(asm_file_path)
            arch: bool = len(set(cur_path.glob("*.vm"))) > 1
            if arch:
                vm_file_name: str = (
                    os.path.basename(os.path.normpath(file_or_directory_name)) + ".vm"
                )
                vm_file_path: Path = cur_path / vm_file_name
                vm_file_path.touch()
                vm_file_content = Path(vm_file_path)
                vm_code: str = ""
                files = cur_path.iterdir()
                for file in files:
                    if file.name.endswith(".vm") and file.name != vm_file_name:
                        vm_code += f"$$ {file.name[:len(file.name)-3]}\n"
                        vm_code += file.read_text()
                vm_file_content.write_text(vm_code)
                vm_file = File(vm_file_content)
                return cls(vm_file, asm_file, True)
            files = cur_path.iterdir()
            for file in files:
                if file.name.endswith(".vm"):
                    return cls(File(file), asm_file, False)
        assembly_path: Path = FileFormat.asm.convert(Path(file_or_directory_name))
        assembly_path.touch()
        return cls(File(cur_path), File(assembly_path), is_dir=False)

    def translate(self) -> None:
        lines = []
        result: list[str] = []
        if self.is_dir:
            lines.append("call Sys.init 0")
            result.append("@256")
            result.append("D=A")
            result.append("@0")
            result.append("M=D")
        lines.extend(self.src_file.load())
        cur_file = ""
        for line in lines:
            line = line.replace("\t", " ")
            instructions = line.split(" ")
            if instructions[0] == "$$":
                cur_file = instructions[1]
            if instructions[0] == "push":
                value: int = int(instructions[2])
                if instructions[1] == "constant":
                    self.push_constant(value, result)
                if instructions[1] in ("local", "argument", "this", "that"):
                    self.push_frame(instructions[1], value, result)
                if instructions[1] == "temp":
                    self.push_vars(instructions[1], value, result)
                if instructions[1] == "pointer":
                    self.push_pointer(value, result)
                if instructions[1] == "static":
                    self.push_static(cur_file, value, result)
            if instructions[0] == "pop":
                value = int(instructions[2])
                if instructions[1] in ("local", "argument", "this", "that"):
                    self.pop_frame(instructions[1], value, result)
                if instructions[1] == "temp":
                    self.pop_vars(instructions[1], value, result)
                if instructions[1] == "pointer":
                    self.pop_pointer(value, result)
                if instructions[1] == "static":
                    self.pop_static(cur_file, value, result)
            if instructions[0] == "add":
                self.add(result)
            if instructions[0] == "sub":
                self.sub(result)
            if instructions[0] in ("eq", "lt", "gt"):
                condition = "D;JEQ"
                if instructions[0] == "lt":
                    condition = "D;JLT"
                if instructions[0] == "gt":
                    condition = "D;JGT"
                self.sub(result)
                self.pop(result)
                result.append("D=M")
                result.append(f"@BOOLOP{self.bool_op_cnt}")
                result.append(condition)
                self.push_constant(0, result)
                result.append(f"@FALSEOP{self.bool_op_cnt}")
                result.append("0;JMP")
                result.append(f"(BOOLOP{self.bool_op_cnt})")
                self.push_constant(1, result)
                self.neg(result)
                result.append(f"(FALSEOP{self.bool_op_cnt})")
                self.bool_op_cnt += 1
            if instructions[0] == "neg":
                self.neg(result)
            if instructions[0] == "and":
                self.pop(result)
                result.append("D=M")
                self.pop(result)
                result.append("D=D & M")
                self.push(result)
            if instructions[0] == "or":
                self.pop(result)
                result.append("D=M")
                self.pop(result)
                result.append("D=D | M")
                self.push(result)
            if instructions[0] == "not":
                self.pop(result)
                result.append("D=!M")
                self.push(result)
            if instructions[0] == "label":
                result.append(f"({instructions[1]})")
            if instructions[0] == "goto":
                result.append(f"@{instructions[1]}")
                result.append("0;JMP")
            if instructions[0] == "if-goto":
                self.pop(result)
                result.append("D=M")
                result.append(f"@{instructions[1]}")
                result.append("D;JNE")
            if instructions[0] == "function":
                result.append(f"({instructions[1]})")
                nvars = int(instructions[2])
                for i in range(0, nvars):
                    self.push_constant(0, result)
            if instructions[0] == "call":
                nargs = int(instructions[2])
                if nargs == 0 and instructions[1] != "Sys.init":
                    nargs = 1
                    self.push_constant(0, result)
                result.append(f"@ret{self.return_cnt}")
                result.append("D=A")
                self.push(result)
                for i in range(1, 5):
                    result.append(f"@{i}")
                    result.append("D=M")
                    self.push(result)
                result.append("@0")
                result.append("D=M")
                self.push(result)
                self.push_constant(5, result)
                self.sub(result)
                self.push_constant(nargs, result)
                self.sub(result)
                self.pop(result)
                result.append("D=M")
                result.append("@2")
                result.append("M=D")
                result.append("@0")
                result.append("D=M")
                result.append("@1")
                result.append("M=D")
                result.append(f"@{instructions[1]}")
                result.append("0;JMP")
                result.append(f"(ret{self.return_cnt})")
                self.return_cnt += 1
            if instructions[0] == "return":
                self.pop_frame("argument", 0, result)
                result.append("@2")
                result.append("D=M")
                result.append("D=D+1")
                self.push(result)
                result.append("@1")
                result.append("D=M")
                self.push(result)
                self.push_constant(5, result)
                self.sub(result)

                result.append("@1")
                result.append("D=M")
                self.push(result)
                self.push_constant(1, result)
                self.sub(result)
                self.pop(result)
                result.append("A=M")
                result.append("D=M")
                result.append("@4")
                result.append("M=D")

                result.append("@1")
                result.append("D=M")
                self.push(result)
                self.push_constant(2, result)
                self.sub(result)
                self.pop(result)
                result.append("A=M")
                result.append("D=M")
                result.append("@3")
                result.append("M=D")

                result.append("@1")
                result.append("D=M")
                self.push(result)
                self.push_constant(3, result)
                self.sub(result)
                self.pop(result)
                result.append("A=M")
                result.append("D=M")
                result.append("@2")
                result.append("M=D")

                result.append("@1")
                result.append("D=M")
                self.push(result)
                self.push_constant(4, result)
                self.sub(result)
                self.pop(result)
                result.append("A=M")
                result.append("D=M")
                result.append("@1")
                result.append("M=D")

                self.pop(result)
                result.append("D=M")
                result.append("@R13")
                result.append("M=D")
                self.pop(result)
                result.append("D=M")
                result.append("@0")
                result.append("M=D")
                result.append("@R13")
                result.append("A=M")
                result.append("A=M")
                result.append("0;JMP")
        self.dst_file.save(result)

    def push_constant(self, value: int, result: list[str]) -> None:
        result.append(f"@{value}")
        result.append("D=A")
        self.push(result)

    def push_frame(self, frame: str, frame_offset: int, result: list[str]) -> None:
        result.append(f"@{self.offset[frame]}")
        result.append("D=M")
        result.append(f"@{frame_offset}")
        result.append("D=D+A")
        result.append("A=D")
        result.append("D=M")
        self.push(result)

    def push_vars(self, frame: str, frame_offset: int, result: list[str]) -> None:
        result.append(f"@{self.offset[frame]}")
        result.append("D=A")
        result.append(f"@{frame_offset}")
        result.append("D=D+A")
        result.append("A=D")
        result.append("D=M")
        self.push(result)

    def push_static(self, file_name: str, frame_offset: int, result: list[str]) -> None:
        result.append(f"@{file_name}.{frame_offset}")
        result.append("D=M")
        self.push(result)

    def push_pointer(self, value: int, result: list[str]) -> None:
        pointer = "this"
        if value == 1:
            pointer = "that"
        result.append(f"@{self.offset[pointer]}")
        result.append("D=M")
        self.push(result)

    def pop_frame(self, frame: str, frame_offset: int, result: list[str]) -> None:
        result.append(f"@{self.offset[frame]}")
        result.append("D=M")
        result.append(f"@{frame_offset}")
        result.append("D=D+A")
        result.append("@R13")
        result.append("M=D")
        self.pop(result)
        result.append("D=M")
        result.append("@R13")
        result.append("A=M")
        result.append("M=D")

    def pop_vars(self, frame: str, frame_offset: int, result: list[str]) -> None:
        result.append(f"@{self.offset[frame]}")
        result.append("D=A")
        result.append(f"@{frame_offset}")
        result.append("D=D+A")
        result.append("@R13")
        result.append("M=D")
        self.pop(result)
        result.append("D=M")
        result.append("@R13")
        result.append("A=M")
        result.append("M=D")

    def pop_static(self, file_name: str, frame_offset: int, result: list[str]) -> None:
        self.pop(result)
        result.append("D=M")
        result.append(f"@{file_name}.{frame_offset}")
        result.append("M=D")

    def pop_pointer(self, value: int, result: list[str]) -> None:
        self.pop(result)
        result.append("D=M")
        pointer = "this"
        if value == 1:
            pointer = "that"
        result.append(f"@{self.offset[pointer]}")
        result.append("M=D")

    def increment_sp(self, result: list[str]) -> None:
        result.append(f"@{self.offset['sp']}")
        result.append("M=M-1")

    def pop(self, result: list[str]) -> None:
        result.append(f"@{self.offset['sp']}")
        result.append("M=M-1")
        result.append("A=M")

    def store_sp(self, result: list[str]) -> None:
        result.append(f"@{self.offset['sp']}")
        result.append("A=M")
        result.append("M=D")

    def push(self, result: list[str]) -> None:
        result.append(f"@{self.offset['sp']}")
        result.append("M=M+1")
        result.append("A=M-1")
        result.append("M=D")

    def sub(self, result: list[str]) -> None:
        self.pop(result)
        result.append("D=M")
        self.pop(result)
        result.append("D=M-D")
        self.push(result)

    def add(self, result: list[str]) -> None:
        self.pop(result)
        result.append("D=M")
        self.pop(result)
        result.append("D=D+M")
        self.push(result)

    def neg(self, result: list[str]) -> None:
        self.pop(result)
        result.append("D=-M")
        self.push(result)


prog = VmProgram.load_from(
    r"C:\Users\PC\Desktop\nand2tetris\projects\7\StackArithmetic\StackTest\StackTest.vm"
)
prog.translate()
