from typing import TextIO


class VmWriter:
    file: TextIO

    def __init__(self, file_name: str):
        open(file_name, "w").close()
        self.file = open(file_name, "a")

    def write_push(self, segment: str, index: int) -> None:
        self.file.write(f"push {segment} {index}\n")

    def write_pop(self, segment: str, index: int) -> None:
        self.file.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command: str) -> None:
        self.file.write(command + "\n")

    def write_label(self, label: str) -> None:
        self.file.write(f"label {label}\n")

    def write_goto(self, label: str) -> None:
        self.file.write(f"goto {label}\n")

    def write_if(self, label: str) -> None:
        self.file.write(f"if-goto {label}\n")

    def write_call(self, name: str, args_num: int) -> None:
        self.file.write(f"call {name} {args_num}\n")

    def write_function(self, name: str, args_num: int) -> None:
        self.file.write(f"function {name} {args_num}\n")

    def write_string(self, string: str) -> None:
        self.write_push("constant", len(string))
        self.write_call("String.new", 1)
        for i in range(len(string)):
            self.write_push("constant", ord(string[i]))
            self.write_call("String.appendChar", 2)

    def write_return(self) -> None:
        self.file.write("return\n")

    def close(self) -> None:
        self.file.close()
