from n2t.core.vm_translator.SymbolTable import SymbolTable
from n2t.core.vm_translator.VmWriter import VmWriter


class VmCompilationEngine:
    tokens: list[str]
    token_ind: int
    cur_class: str
    class_table: SymbolTable
    out_file: str
    vm_writer: VmWriter
    field_count: int
    bool_cnt: int

    operations: set[str] = {"+", "-", "*", "/", "&lt;", "&gt;", "&amp;", "|", "="}

    def __init__(self, tokens: list[str], out_file: str):
        self.tokens = tokens
        self.token_ind = 0
        self.field_count = 0
        self.bool_cnt = 0
        self.out_file = out_file
        self.vm_writer = VmWriter(out_file)

    def extract_from_tags(self) -> str:
        start: int = self.tokens[self.token_ind].find(">")
        end: int = self.tokens[self.token_ind].find("</")
        return self.tokens[self.token_ind][start + 1 : end - 1].strip()

    def get_tag(self) -> str:
        start: int = self.tokens[self.token_ind].find("<")
        end: int = self.tokens[self.token_ind].find(">")
        return self.tokens[self.token_ind][start + 1 : end].strip()

    def compile_class(self) -> None:
        self.token_ind += 2
        self.cur_class = self.extract_from_tags()
        self.class_table = SymbolTable()
        self.token_ind += 2
        while True:
            cur_tag: str = self.get_tag()
            if cur_tag == "symbol":
                break
            if cur_tag == "classVarDec":
                self.token_ind += 1
                self.compile_class_var_dec()
            elif cur_tag == "subroutineDec":
                self.token_ind += 1
                self.compile_subroutine_dec()
        self.token_ind += 1
        self.vm_writer.close()

    def compile_class_var_dec(self) -> None:
        kind: str = self.extract_from_tags()
        kind_str: str = kind
        if kind == "field":
            self.field_count += 1
            kind_str = "this"
        self.token_ind += 1
        symbol_type: str = self.extract_from_tags()
        self.token_ind += 1
        name: str = self.extract_from_tags()
        self.token_ind += 1
        self.class_table.define(name, symbol_type, kind_str)
        while self.extract_from_tags() == ",":
            self.token_ind += 1
            name = self.extract_from_tags()
            kind_str = kind
            if kind == "field":
                self.field_count += 1
                kind_str = "this"
            self.class_table.define(name, symbol_type, kind_str)
            self.token_ind += 1
        self.token_ind += 2

    def compile_subroutine_dec(self) -> None:
        keyword: str = self.extract_from_tags()
        var_size: int = 0
        method_name: str
        function_table: SymbolTable = SymbolTable()
        if keyword == "function":
            self.token_ind += 2
            method_name = f"{self.cur_class}.{self.extract_from_tags()}"
            self.token_ind += 3
        elif keyword == "method":
            self.token_ind += 2
            method_name = f"{self.cur_class}.{self.extract_from_tags()}"
            self.token_ind += 3
        elif keyword == "constructor":
            method_name = f"{self.cur_class}.new"
            self.token_ind += 5
        self.compile_parameter_list(function_table, keyword == "method")
        self.token_ind += 3
        while self.get_tag() == "varDec":
            kind: str = "local"
            self.token_ind += 2
            symbol_type: str = self.extract_from_tags()
            self.token_ind += 1
            name: str = self.extract_from_tags()
            self.token_ind += 1
            function_table.define(name, symbol_type, kind)
            var_size += 1
            while self.extract_from_tags() == ",":
                self.token_ind += 1
                name = self.extract_from_tags()
                function_table.define(name, symbol_type, kind)
                var_size += 1
                self.token_ind += 1
            self.token_ind += 2
        self.vm_writer.write_function(method_name, var_size)
        if keyword == "constructor":
            self.vm_writer.write_push("constant", self.field_count)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)
        if keyword == "method":
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)
        while self.get_tag() == "statements":
            self.token_ind += 1
            self.compile_statements(function_table)
        self.token_ind += 3

    def compile_parameter_list(self, function_table: SymbolTable, method: bool) -> None:
        if method:
            function_table.define("this", self.cur_class, "argument")
        while self.get_tag() != "/parameterList":
            kind: str = "argument"
            symbol_type: str = self.extract_from_tags()
            self.token_ind += 1
            name: str = self.extract_from_tags()
            function_table.define(name, symbol_type, kind)
            self.token_ind += 1
            if self.get_tag() == "/parameterList":
                break
            self.token_ind += 1
        self.token_ind += 1

    def compile_statements(self, function_table: SymbolTable) -> None:
        while True:
            if self.get_tag() == "/statements":
                self.token_ind += 1
                break
            if self.get_tag() == "letStatement":
                self.token_ind += 1
                self.compile_let_statement(function_table)
            if self.get_tag() == "doStatement":
                self.token_ind += 1
                self.compile_do_statement(function_table)
            if self.get_tag() == "returnStatement":
                self.token_ind += 1
                self.compile_return_statement(function_table)
            if self.get_tag() == "ifStatement":
                self.token_ind += 1
                self.compile_if_statement(function_table)
            if self.get_tag() == "whileStatement":
                self.token_ind += 1
                self.compile_while_statement(function_table)

    def compile_let_statement(self, function_table: SymbolTable) -> None:
        self.token_ind += 1
        name: str = self.extract_from_tags()
        segment: str = ""
        index: int = 0
        if function_table.has_name(name):
            segment = function_table.kind_of(name)
            index = function_table.index_of(name)
        else:
            segment = self.class_table.kind_of(name)
            index = self.class_table.index_of(name)
        self.token_ind += 1
        if self.get_tag() == "symbol" and self.extract_from_tags() == "[":
            self.token_ind += 2
            self.compile_expression(function_table)
            self.vm_writer.write_push(segment, index)
            self.vm_writer.write_arithmetic("add")
            self.token_ind += 3
            self.compile_expression(function_table)
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)
            self.token_ind += 2
            return
        self.token_ind += 2
        self.compile_expression(function_table)
        self.token_ind += 2
        self.vm_writer.write_pop(segment, index)

    def compile_do_statement(self, function_table: SymbolTable) -> None:
        self.token_ind += 1
        self.compile_term(function_table)  # as in subroutine call
        self.token_ind += 1
        self.vm_writer.write_pop("temp", 0)

    def compile_return_statement(self, function_table: SymbolTable) -> None:
        self.token_ind += 1
        if self.get_tag() == "expression":
            self.token_ind += 1
            self.compile_expression(function_table)
        else:
            self.vm_writer.write_push("constant", 0)
        self.vm_writer.write_return()
        self.token_ind += 2

    def compile_if_statement(self, function_table: SymbolTable) -> None:
        self.token_ind += 3
        self.compile_expression(function_table)
        self.vm_writer.write_arithmetic("not")
        self.bool_cnt += 2
        cur_bool: int = self.bool_cnt
        self.vm_writer.write_if(f"{self.cur_class}.bool{cur_bool-2}")
        self.token_ind += 3  # statements
        self.compile_statements(function_table)
        self.vm_writer.write_goto(f"{self.cur_class}.bool{cur_bool-1}")
        self.vm_writer.write_label(f"{self.cur_class}.bool{cur_bool-2}")
        self.token_ind += 1
        if self.get_tag() != "/ifStatement":  # means we are in else
            self.token_ind += 3
            self.compile_statements(function_table)
            self.token_ind += 1
        self.vm_writer.write_label(f"{self.cur_class}.bool{cur_bool-1}")
        self.bool_cnt += 1
        self.token_ind += 1

    def compile_while_statement(self, function_table: SymbolTable) -> None:
        self.bool_cnt += 2
        cur_bool: int = self.bool_cnt
        self.vm_writer.write_label(f"{self.cur_class}.bool{cur_bool-2}")
        self.token_ind += 3
        self.compile_expression(function_table)
        self.token_ind += 3  # statements
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if(f"{self.cur_class}.bool{cur_bool-1}")
        self.compile_statements(function_table)
        self.vm_writer.write_goto(f"{self.cur_class}.bool{cur_bool-2}")
        self.vm_writer.write_label(f"{self.cur_class}.bool{cur_bool-1}")
        self.token_ind += 2

    def compile_expression(self, function_table: SymbolTable) -> None:
        while True:
            if self.get_tag() == "term":
                self.token_ind += 1
                self.compile_term(function_table)
            if self.get_tag() == "symbol":
                operation: str = self.extract_from_tags()
                self.token_ind += 2
                self.compile_term(function_table)
                self.compile_operation(operation)
            if self.get_tag() == "/expression":
                self.token_ind += 1
                return

    def compile_term(self, function_table: SymbolTable) -> None:
        if self.get_tag() == "integerConstant":
            self.vm_writer.write_push("constant", int(self.extract_from_tags()))
            self.token_ind += 2
            return
        if self.get_tag() == "stringConstant":
            self.vm_writer.write_string(self.extract_from_tags())
            self.token_ind += 2
            return
        if self.get_tag() == "keyword":
            val: str = self.extract_from_tags()
            if val == "this":
                self.vm_writer.write_push("pointer", 0)
            elif val == "true":
                self.vm_writer.write_push("constant", 1)
                self.vm_writer.write_arithmetic("neg")
            else:
                self.vm_writer.write_push("constant", 0)
            self.token_ind += 2
            return
        if self.get_tag() == "symbol":
            if self.extract_from_tags() == "(":
                self.token_ind += 2
                self.compile_expression(function_table)
                self.token_ind += 2
                return
            else:
                unary_op: str = self.extract_from_tags()
                self.token_ind += 2
                self.compile_term(function_table)
                self.compile_unary_op(unary_op)
                self.token_ind += 1
                return
        if self.get_tag() == "identifier":  # subroutine or var
            name: str = self.extract_from_tags()
            self.token_ind += 1
            if self.get_tag() == "/term" or (
                self.get_tag() == "symbol" and self.extract_from_tags() == "["
            ):
                segment: str
                index: int
                if function_table.has_name(name):
                    index = function_table.index_of(name)
                    segment = function_table.kind_of(name)
                else:
                    index = self.class_table.index_of(name)
                    segment = self.class_table.kind_of(name)
                if self.get_tag() == "symbol" and self.extract_from_tags() == "[":
                    self.token_ind += 2
                    self.compile_expression(function_table)
                    self.vm_writer.write_push(segment, index)
                    self.vm_writer.write_arithmetic("add")
                    self.vm_writer.write_pop("pointer", 1)
                    self.vm_writer.write_push("that", 0)
                    self.token_ind += 2
                    return
                self.vm_writer.write_push(segment, index)
                self.token_ind += 1
            else:
                if self.extract_from_tags() == ".":  # method call
                    self.token_ind += 1
                    method_name: str = self.extract_from_tags()
                    arg_num: int = 0
                    class_name: str = name
                    if function_table.has_name(name):
                        class_name = function_table.type_of(name)
                        self.vm_writer.write_push(
                            function_table.kind_of(name), function_table.index_of(name)
                        )
                        arg_num += 1
                    elif self.class_table.has_name(name):
                        class_name = self.class_table.type_of(name)
                        self.vm_writer.write_push(
                            self.class_table.kind_of(name),
                            self.class_table.index_of(name),
                        )
                        arg_num += 1
                    self.token_ind += 3
                    arg_num += self.compile_expression_list(function_table)
                    self.vm_writer.write_call(f"{class_name}.{method_name}", arg_num)
                    self.token_ind += 2
                else:
                    self.token_ind += 2
                    self.vm_writer.write_push("pointer", 0)
                    arg_num = self.compile_expression_list(function_table)
                    self.vm_writer.write_call(f"{self.cur_class}.{name}", arg_num + 1)
                    self.token_ind += 2

    def compile_expression_list(self, function_table: SymbolTable) -> int:
        cnt: int = 0
        while self.get_tag() == "expression":
            cnt += 1
            self.token_ind += 1
            self.compile_expression(function_table)
            if self.get_tag() == "/expressionList":
                break
            self.token_ind += 1
        self.token_ind += 1
        return cnt

    def compile_operation(self, operation: str) -> None:
        if operation == "+":
            self.vm_writer.write_arithmetic("add")
        if operation == "-":
            self.vm_writer.write_arithmetic("sub")
        if operation == "*":
            self.vm_writer.write_call("Math.multiply", 2)
        if operation == "/":
            self.vm_writer.write_call("Math.divide", 2)
        if operation == "&amp;":
            self.vm_writer.write_arithmetic("and")
        if operation == "|":
            self.vm_writer.write_arithmetic("or")
        if operation == "&gt;":
            self.vm_writer.write_arithmetic("gt")
        if operation == "&lt;":
            self.vm_writer.write_arithmetic("lt")
        if operation == "=":
            self.vm_writer.write_arithmetic("eq")

    def compile_unary_op(self, operation: str) -> None:
        if operation == "-":
            self.vm_writer.write_arithmetic("neg")
        if operation == "~":
            self.vm_writer.write_arithmetic("not")
