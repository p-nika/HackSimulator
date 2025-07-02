from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from n2t.core.parser.CompilationEngine import CompilationEngine
from n2t.core.parser.JackTokenizer import JackTokenizer
from n2t.core.vm_translator.VmCompilationEngine import VmCompilationEngine
from n2t.infra.io import File


@dataclass
class JackProgram:  # TODO: your work for Projects 10 and 11 starts here
    input_files: list[File]
    output_files: list[File]

    @classmethod
    def load_from(cls, file_or_directory_name: str) -> JackProgram:
        input_files: list[File] = []
        output_files: list[File] = []
        cur_path: Path = Path(file_or_directory_name)
        if cur_path.is_dir():
            for file in cur_path.iterdir():
                if file.name.endswith(".jack"):
                    input_files.append(File(file))
                    file_path: str = file_or_directory_name + "\\" + file.name
                    output_file: Path = Path(
                        file_path[0 : file_path.index(".")] + ".vm"
                    )
                    output_file.touch()
                    output_files.append(File(output_file))
        else:
            input_files.append(File(cur_path))
            cur_file: Path = Path(
                file_or_directory_name[0 : file_or_directory_name.index(".")] + ".vm"
            )
            cur_file.touch()
            output_files.append(File(cur_file))
        return cls(input_files, output_files)

    def compile(self) -> None:
        for file_index in range(len(self.input_files)):
            self.compile_one(file_index)

    def compile_one(self, file_index: int) -> None:
        tokenizer_input: str = ""
        lines: Iterable[str] = self.input_files[file_index].load()
        is_comment: bool = False
        for line in lines:
            index1: int = line.find("//")
            index2: int = line.find("/*")
            index3: int = line.find("*/")
            if index1 != -1:
                line = line[0:index1]
            if index2 != -1:
                line = line[0:index2]
                is_comment = True
            if index3 != -1:
                is_comment = False
                continue
            if not is_comment:
                tokenizer_input += line
        tokenizer: JackTokenizer = JackTokenizer(tokenizer_input)
        tokenizer.create_tokens()
        engine: CompilationEngine = CompilationEngine(tokenizer)
        engine.compile_class()
        res = engine.get_result()
        cur_name = self.output_files[file_index].path.absolute()
        vm_engine: VmCompilationEngine = VmCompilationEngine(res, str(cur_name))
        vm_engine.compile_class()
