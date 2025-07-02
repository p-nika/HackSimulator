from dataclasses import dataclass, field

from n2t.core.parser.JackTokenizer import JackTokenizer


@dataclass
class CompilationEngine:
    tokenizer: JackTokenizer
    result: list[str] = field(default_factory=lambda: [])
    cur_pad: int = field(default=0)
    subroutines: set[str] = field(
        default_factory=lambda: {"function", "method", "constructor"}
    )
    class_vars: set[str] = field(default_factory=lambda: {"static", "field"})
    statements: set[str] = field(
        default_factory=lambda: {"let", "if", "while", "do", "return"}
    )
    operations: set[str] = field(
        default_factory=lambda: {"+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="}
    )
    keyword_constants: set[str] = field(
        default_factory=lambda: {"true", "false", "null", "this"}
    )
    unary_op: set[str] = field(default_factory=lambda: {"-", "~"})

    def open_header(self, header: str) -> None:
        self.result.append(self.cur_pad * " " + f"<{header}>")
        self.cur_pad += 2

    def close_header(self, header: str) -> None:
        self.cur_pad -= 2
        self.result.append(self.cur_pad * " " + f"</{header}>")

    def add_xml_tag(self) -> None:
        self.result.append(
            self.cur_pad * " " + f"<{self.tokenizer.token_keyword()}>"
            f" {self.tokenizer.current_token()}"
            f" </{self.tokenizer.token_keyword()}>"
        )
        self.tokenizer.increment_counter()

    def compile_class(self) -> None:
        self.open_header("class")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == "{":
                break
        self.add_xml_tag()  # {
        while self.tokenizer.current_token() != "}":
            if self.tokenizer.current_token() in self.subroutines:
                self.compile_subroutine_dec()
            if self.tokenizer.current_token() in self.class_vars:
                self.compile_class_var_dec()
        self.add_xml_tag()  # }
        self.close_header("class")

    def compile_subroutine_dec(self) -> None:
        self.open_header("subroutineDec")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == "(":
                break
        self.add_xml_tag()
        self.compile_parameter_list()
        self.add_xml_tag()
        self.compile_subroutine_body()
        self.close_header("subroutineDec")

    def compile_class_var_dec(self) -> None:
        self.open_header("classVarDec")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == ";":
                break
        self.add_xml_tag()
        self.close_header("classVarDec")

    def compile_parameter_list(self) -> None:
        self.open_header("parameterList")
        while True:
            if self.tokenizer.current_token() == ")":
                break
            self.add_xml_tag()
        self.close_header("parameterList")

    def compile_subroutine_body(self) -> None:
        self.open_header("subroutineBody")
        self.add_xml_tag()  # {
        while self.tokenizer.current_token() == "var":
            self.compile_var_dec()
        self.compile_statements()
        self.add_xml_tag()  # }
        self.close_header("subroutineBody")

    def compile_var_dec(self) -> None:
        self.open_header("varDec")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == ";":
                break
        self.add_xml_tag()
        self.close_header("varDec")

    def compile_statements(self) -> None:
        self.open_header("statements")
        while self.tokenizer.current_token() in self.statements:
            if self.tokenizer.current_token() == "let":
                self.compile_let_statement()
            if self.tokenizer.current_token() == "if":
                self.compile_if_statement()
            if self.tokenizer.current_token() == "while":
                self.compile_while_statement()
            if self.tokenizer.current_token() == "do":
                self.compile_do_statement()
            if self.tokenizer.current_token() == "return":
                self.compile_return_statement()
        self.close_header("statements")

    def compile_let_statement(self) -> None:
        self.open_header("letStatement")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == "=":
                self.add_xml_tag()
                self.compile_expression()
                break
            if self.tokenizer.current_token() == "[":
                self.add_xml_tag()
                self.compile_expression()
        self.add_xml_tag()  # ;
        self.close_header("letStatement")

    def compile_if_statement(self) -> None:
        self.open_header("ifStatement")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == "(":
                break
        self.add_xml_tag()
        self.compile_expression()
        self.add_xml_tag()  # )
        self.add_xml_tag()  # {
        self.compile_statements()
        self.add_xml_tag()  # }
        if self.tokenizer.current_token() == "else":
            self.add_xml_tag()  # else
            self.add_xml_tag()  # {
            self.compile_statements()
            self.add_xml_tag()  # }
        self.close_header("ifStatement")

    def compile_while_statement(self) -> None:
        self.open_header("whileStatement")
        while True:
            self.add_xml_tag()
            if self.tokenizer.current_token() == "(":
                break
        self.add_xml_tag()
        self.compile_expression()
        self.add_xml_tag()  # )
        self.add_xml_tag()  # {
        self.compile_statements()
        self.add_xml_tag()  # }
        self.close_header("whileStatement")

    def compile_do_statement(self) -> None:
        self.open_header("doStatement")
        self.add_xml_tag()  # do
        self.add_xml_tag()  # name
        if self.tokenizer.current_token() == "(":
            self.add_xml_tag()  # (
            self.compile_expression_list()
            self.add_xml_tag()  # )
        elif self.tokenizer.current_token() == ".":
            self.add_xml_tag()  # .
            self.add_xml_tag()  # subroutineName
            self.add_xml_tag()  # (
            self.compile_expression_list()
            self.add_xml_tag()  # )
        self.add_xml_tag()  # ;
        self.close_header("doStatement")

    def compile_return_statement(self) -> None:
        self.open_header("returnStatement")
        self.add_xml_tag()  # return
        if self.tokenizer.current_token() != ";":
            self.compile_expression()
        self.add_xml_tag()
        self.close_header("returnStatement")

    def compile_expression(self) -> None:
        self.open_header("expression")
        self.compile_term()
        while self.tokenizer.current_token() in self.operations:
            self.add_xml_tag()
            self.compile_term()
        self.close_header("expression")

    def compile_term(self) -> None:
        self.open_header("term")
        if self.tokenizer.token_keyword() == "integerConstant":
            self.add_xml_tag()
        elif self.tokenizer.token_keyword() == "stringConstant":
            self.add_xml_tag()
        elif self.tokenizer.current_token() in self.keyword_constants:
            self.add_xml_tag()
        elif self.tokenizer.current_token() in self.unary_op:
            self.add_xml_tag()
            self.compile_term()
        elif self.tokenizer.current_token() == "(":
            self.add_xml_tag()  # (
            self.compile_expression()
            self.add_xml_tag()  # )
        else:
            self.add_xml_tag()  # varName or subroutineName
            if (
                self.tokenizer.current_token() == "("
            ):  # means that it's a subroutine call
                self.add_xml_tag()  # (
                self.compile_expression_list()
                self.add_xml_tag()  # )
            elif self.tokenizer.current_token() == ".":  # subroutine call again
                self.add_xml_tag()  # .
                self.add_xml_tag()  # subroutineName
                self.add_xml_tag()  # (
                self.compile_expression_list()
                self.add_xml_tag()  # )
            elif (
                self.tokenizer.current_token() == "["
            ):  # means that it's varName['expression']
                self.add_xml_tag()  # [
                self.compile_expression()
                self.add_xml_tag()  # ]
        self.close_header("term")

    def compile_expression_list(self) -> None:
        self.open_header("expressionList")
        while self.tokenizer.current_token() != ")":
            self.compile_expression()
            if self.tokenizer.current_token() == ",":
                self.add_xml_tag()
        self.close_header("expressionList")

    def get_result(self) -> list[str]:
        return self.result
