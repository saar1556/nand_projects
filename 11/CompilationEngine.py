"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackTokenizer import JackTokenizer
from VMWriter import VMWriter
from SymbolTable import SymbolTable


class CompilationEngine:
    """
    Compilation engine for the Jack programming language.

    This class parses a stream of Jack tokens (provided by JackTokenizer)
    and generates VM code using VMWriter. It also manages variable scopes
    via SymbolTable. The engine implements the Jack grammar rules
    and compiles classes, subroutines, statements, expressions, and terms.
    """

    # Optional op name map (unused by code, kept for readability)
    arithmeticsOps = {
        '+': "ADD",
        '-': "SUB",
        '&': "AND",
        '|': "OR",
        '<': "LT",
        '>': "GT",
        '=': "EQ",
    }

    # SymbolTable kind → VM segment mapping
    kinds = {
        "VAR": "LOCAL",
        "ARG": "ARG",
        "STATIC": "STATIC",
        "FIELD": "THIS",
    }

    n_args: int = 0
    label_counter: int = 0
    current_class: str = ""

    tokenizer: JackTokenizer = None
    vm_writer: VMWriter = None
    symbol_table: SymbolTable = None

    
    def __init__(self, tokenizer: JackTokenizer, output_stream: typing.TextIO) -> None:
        self.tokenizer = tokenizer
        self.vm_writer = VMWriter(output_stream)
        self.symbol_table = SymbolTable()

    # ---------------------------------------------------------------------
    # Core helpers
    # ---------------------------------------------------------------------

    def eat(self, expected_token: str) -> None:
        """Consumes the current token and advances to the next token."""
        if self.tokenizer.current_token != expected_token:
            raise ValueError(
                f"Unexpected token: got '{self.tokenizer.current_token}', expected '{expected_token}'."
            )
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def _seg(self, kind: str) -> str:
        """Map a SymbolTable kind to a VM segment name."""
        if kind not in self.kinds:
            raise ValueError(f"Unknown variable kind: {kind}")
        return self.kinds[kind]

    def _read_type(self) -> str:
        """Read a Jack type token (int|char|boolean|className) and advance."""
        tok = self.tokenizer.current_token
        if tok in {"int", "char", "boolean"}:
            self.eat(tok)
            return tok
        if self.tokenizer.token_type() == "IDENTIFIER":
            name = tok
            self.eat(name)
            return name
        raise ValueError(f"Expected type (int|char|boolean|className), got '{tok}'")

    # ---------------------------------------------------------------------
    # class: 'class' className '{' classVarDec* subroutineDec* '}'
    # ---------------------------------------------------------------------
    def compile_class(self) -> None:
        # prime tokenizer
        self.tokenizer.advance()

        self.eat('class')
        # className
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(f"Expected class name (identifier), got '{self.tokenizer.current_token}'")
        self.current_class = self.tokenizer.current_token
        self.eat(self.current_class)

        self.eat('{')
        # classVarDec*
        while self.tokenizer.current_token in {'static', 'field'}:
            self.compile_class_var_dec()
        # subroutineDec*
        while self.tokenizer.current_token in {'constructor', 'function', 'method'}:
            self.compile_subroutine()
        self.eat('}')

    # classVarDec: ('static'|'field') type varName (',' varName)* ';'
    def compile_class_var_dec(self) -> None:
        if self.tokenizer.current_token not in {'static', 'field'}:
            raise ValueError(f"Expected 'static' or 'field' in classVarDec, got '{self.tokenizer.current_token}'")
        kind = self.tokenizer.current_token.upper()  # STATIC | FIELD (SymbolTable kinds)
        self.eat(self.tokenizer.current_token)
        self._compile_var_declaration(kind)

    # varDec: 'var' type varName (',' varName)* ';'
    def compile_var_dec(self) -> None:
        self.eat('var')
        self._compile_var_declaration('VAR')

    def _compile_var_declaration(self, kind: str) -> None:
        type_name = self._read_type()
        # first varName
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(f"Expected varName (identifier), got '{self.tokenizer.current_token}'")
        name = self.tokenizer.current_token
        self.symbol_table.define(name, type_name, kind)
        self.eat(name)
        # additional varNames
        while self.tokenizer.current_token == ',':
            self.eat(',')
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(f"Expected varName after ',', got '{self.tokenizer.current_token}'")
            name = self.tokenizer.current_token
            self.symbol_table.define(name, type_name, kind)
            self.eat(name)
        self.eat(';')

    # ---------------------------------------------------------------------
    # subroutineDec: ('constructor'|'function'|'method') ('void'|type)
    #                 subroutineName '(' parameterList ')' subroutineBody
    # subroutineBody: '{' varDec* statements '}'
    # ---------------------------------------------------------------------
    def compile_subroutine(self) -> None:
        if self.tokenizer.current_token not in {'constructor', 'function', 'method'}:
            raise ValueError(
                f"Expected 'constructor', 'function', or 'method', got '{self.tokenizer.current_token}'"
            )
        subroutine_type = self.tokenizer.current_token  # remember kind

        # new scope
        self.symbol_table.start_subroutine()
        self.eat(subroutine_type)

        # implicit 'this' for methods
        if subroutine_type == 'method':
            self.symbol_table.define('this', self.current_class, 'ARG')

        # return type
        void_func = False
        if self.tokenizer.current_token == 'void':
            void_func = True
            self.eat('void')
        else:
            _ = self._read_type()  # discard, kept for validation

        # subroutineName
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(f"Expected subroutineName (identifier), got '{self.tokenizer.current_token}'")
        sub_name = self.tokenizer.current_token
        self.eat(sub_name)
        full_name = f"{self.current_class}.{sub_name}"

        # params
        self.eat('(')
        self.compile_parameter_list()
        self.eat(')')

        # body
        self.eat('{')
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()
        n_locals = self.symbol_table.var_count('VAR')
        self.vm_writer.write_function(full_name, n_locals)

        if subroutine_type == 'constructor':
            n_fields = self.symbol_table.var_count('FIELD')
            self.vm_writer.write_push('CONST', n_fields)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('POINTER', 0)  # this = allocated base
        elif subroutine_type == 'method':
            self.vm_writer.write_push('ARG', 0)     # push this
            self.vm_writer.write_pop('POINTER', 0)  # anchor 'this'

        self.compile_statements()
        self.eat('}')
        # We rely on an explicit 'return' inside statements.

    # parameterList: ((type varName) (',' type varName)*)?
    def compile_parameter_list(self) -> None:
        if self.tokenizer.current_token == ')':
            return  # empty
        while True:
            typ = self._read_type()
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(f"Expected parameter name, got '{self.tokenizer.current_token}'")
            name = self.tokenizer.current_token
            self.symbol_table.define(name, typ, 'ARG')
            self.eat(name)
            if self.tokenizer.current_token != ',':
                break
            self.eat(',')

    # ---------------------------------------------------------------------
    # statements: (let|if|while|do|return)*
    # ---------------------------------------------------------------------
    def compile_statements(self) -> None:
        while self.tokenizer.current_token in {'let', 'if', 'while', 'do', 'return'}:
            tok = self.tokenizer.current_token
            if tok == 'let':
                self.compile_let()
            elif tok == 'if':
                self.compile_if()
            elif tok == 'while':
                self.compile_while()
            elif tok == 'do':
                self.compile_do()
            else:
                self.compile_return()

    # do subroutineCall ';'    -- discard the return value
    def compile_do(self) -> None:
        self.eat('do')
        # subroutineCall
        self._compile_subroutine_call()
        self.eat(';')
        self.vm_writer.write_pop('TEMP', 0)

    def _compile_subroutine_call(self) -> None:
        # Read the initial identifier (subroutineName | className | varName)
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(f"Expected identifier to start subroutine call, got '{self.tokenizer.current_token}'")
        name = self.tokenizer.current_token
        self.eat(name)

        extra = 0
        callee: str
        nxt = self.tokenizer.current_token  # after eating 'name'
        if nxt == '.':
            # name.sub(...)
            self.eat('.')
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError("Expected subroutineName after '.'")
            sub = self.tokenizer.current_token
            self.eat(sub)
            if self.symbol_table.kind_of(name) is not None:
                seg = self._seg(self.symbol_table.kind_of(name))
                idx = self.symbol_table.index_of(name)
                typ = self.symbol_table.type_of(name)
                self.vm_writer.write_push(seg, idx)  # receiver
                callee = f"{typ}.{sub}"
                extra = 1
            else:
                # static call on a class
                callee = f"{name}.{sub}"
        else:
            # method on this: name(...)
            self.vm_writer.write_push('POINTER', 0)
            callee = f"{self.current_class}.{name}"
            extra = 1

        self.eat('(')
        self.compile_expression_list()
        self.eat(')')
        self.vm_writer.write_call(callee, self.n_args + extra)

    # let var = expr; | let arr[expr] = expr;
    def compile_let(self) -> None:
        self.eat('let')
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(f"Expected varName after 'let', got '{self.tokenizer.current_token}'")
        name = self.tokenizer.current_token
        kind = self.symbol_table.kind_of(name)
        if kind is None:
            raise ValueError(f"Undeclared variable: {name}")
        idx = self.symbol_table.index_of(name)
        seg = self._seg(kind)
        self.eat(name)

        is_array = False
        if self.tokenizer.current_token == '[':
            is_array = True
            self.eat('[')
            self.vm_writer.write_push(seg, idx)  # base address
            self.compile_expression()             # index
            self.eat(']')
            self.vm_writer.write_arithmetic('ADD')

        self.eat('=')
        self.compile_expression()

        if is_array:
            # stack: ... [address, value]
            self.vm_writer.write_pop('TEMP', 0)      # value
            self.vm_writer.write_pop('POINTER', 1)   # THAT = address
            self.vm_writer.write_push('TEMP', 0)     # value
            self.vm_writer.write_pop('THAT', 0)
        else:
            self.vm_writer.write_pop(seg, idx)
        self.eat(';')

    # while (expr) { statements }
    def compile_while(self) -> None:
        idx = self.label_counter
        self.label_counter += 1
        self.vm_writer.write_label(f"WHILE_EXP{idx}")

        self.eat('while')
        self.eat('(')
        self.compile_expression()
        self.eat(')')

        self.vm_writer.write_arithmetic('NOT')
        self.vm_writer.write_if(f"WHILE_END{idx}")

        self.eat('{')
        self.compile_statements()
        self.eat('}')

        self.vm_writer.write_goto(f"WHILE_EXP{idx}")
        self.vm_writer.write_label(f"WHILE_END{idx}")

    # return [expr] ;
    def compile_return(self) -> None:
        self.eat('return')
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        else:
            # void return
            self.vm_writer.write_push('CONST', 0)
        self.eat(';')
        self.vm_writer.write_return()

    # if (expr) { statements } (else { statements })?
    def compile_if(self) -> None:
        self.eat('if')
        self.eat('(')
        self.compile_expression()
        self.eat(')')

        idx = self.label_counter
        self.label_counter += 1

        self.vm_writer.write_arithmetic('NOT')
        self.vm_writer.write_if(f"IF_FALSE{idx}")

        self.eat('{')
        self.compile_statements()
        self.eat('}')

        if self.tokenizer.current_token == 'else':
            self.vm_writer.write_goto(f"IF_END{idx}")
            self.vm_writer.write_label(f"IF_FALSE{idx}")
            self.eat('else')
            self.eat('{')
            self.compile_statements()
            self.eat('}')
            self.vm_writer.write_label(f"IF_END{idx}")
        else:
            self.vm_writer.write_label(f"IF_FALSE{idx}")

    # ---------------------------------------------------------------------
    # Expressions & terms
    # ---------------------------------------------------------------------
    def aritmetic_op(self, op: str) -> None:
        if op == '+':
            self.vm_writer.write_arithmetic('ADD')
        elif op == '-':
            self.vm_writer.write_arithmetic('SUB')
        elif op == '*':
            self.vm_writer.write_call('Math.multiply', 2)
        elif op == '/':
            self.vm_writer.write_call('Math.divide', 2)
        elif op == '&':
            self.vm_writer.write_arithmetic('AND')
        elif op == '|':
            self.vm_writer.write_arithmetic('OR')
        elif op == '<':
            self.vm_writer.write_arithmetic('LT')
        elif op == '>':
            self.vm_writer.write_arithmetic('GT')
        elif op == '=':
            self.vm_writer.write_arithmetic('EQ')
        elif op == '^':
            self.vm_writer.write_arithmetic('SHIFTLEFT')
        elif op == '#':
            self.vm_writer.write_arithmetic('SHIFTRIGHT')
        else:
            raise ValueError(f"Unknown binary operator: {op}")

    def _jack_char_code(self, ch: str) -> int:
        # Normalize curly quotes, if needed
        if ch in {'“', '”'}: ## no need, illegal
            ch = '"'
        if ch == '’': ## no need, illegal
            ch = "'"
        c = ord(ch)
        if 32 <= c <= 126:
            return c
        if ch == '\n': ## no need, illegal
            return 128  # OS.newLine
        if ch == '\b':
            return 129  # OS.backSpace
        raise ValueError(f"Illegal character in Jack string literal: {repr(ch)}")

    # expression: term (op term)*
    def compile_expression(self) -> None:
        self.compile_term()
        ops = {'+', '-', '*', '/', '&', '|', '<', '>', '=', '^', '#'}
        while self.tokenizer.current_token in ops:
            op = self.tokenizer.current_token
            self.eat(op)
            self.compile_term()
            self.aritmetic_op(op)

    # term: integerConstant | stringConstant | keywordConstant | varName |
    #       varName '[' expression ']' | subroutineCall | '(' expression ')' |
    #       unaryOp term
    def compile_term(self) -> None:
        tok = self.tokenizer.current_token
        ttype = self.tokenizer.token_type()

        if ttype == 'INT_CONST':
            self.vm_writer.write_push('CONST', self.tokenizer.int_val())
            self.eat(tok)
            return

        if ttype == 'STRING_CONST':
            s = self.tokenizer.string_val()
            self.eat(tok)
            self.vm_writer.write_push('CONST', len(s))
            self.vm_writer.write_call('String.new', 1)
            for ch in s:
                self.vm_writer.write_push('CONST', self._jack_char_code(ch))
                self.vm_writer.write_call('String.appendChar', 2)
            return

        if ttype == 'KEYWORD':
            if tok in ('false', 'null'):
                self.vm_writer.write_push('CONST', 0)
            elif tok == 'true':
                self.vm_writer.write_push('CONST', 0)
                self.vm_writer.write_arithmetic('NOT')
            elif tok == 'this':
                self.vm_writer.write_push('POINTER', 0)
            else:
                raise ValueError(f"Unexpected keyword in term: {tok}")
            self.eat(tok)
            return

        if tok == '(':  # parenthesized
            self.eat('(')
            self.compile_expression()
            self.eat(')')
            return

        if tok in {'-', '~', '^', '#'}:  # unary
            op = tok
            self.eat(op)
            self.compile_term()
            if op == '-':
                self.vm_writer.write_arithmetic('NEG')
            elif op == '~':
                self.vm_writer.write_arithmetic('NOT')
            elif op == '^':
                self.vm_writer.write_arithmetic('SHIFTLEFT')
            elif op == '#':
                self.vm_writer.write_arithmetic('SHIFTRIGHT')
            return

        if ttype == 'IDENTIFIER':
            name = tok
            nxt = self.tokenizer.peek()

            # subroutine call
            if nxt in ('(', '.'):
                # Let the shared helper consume tokens & emit the call
                self._compile_subroutine_call()
                return

            # array access: varName '[' expression ']'
            if nxt == '[':
                kind = self.symbol_table.kind_of(name)
                if kind is None:
                    raise ValueError(f"Undeclared array: {name}")
                seg = self._seg(kind)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.write_push(seg, idx)  # base
                self.eat(name)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
                self.vm_writer.write_arithmetic('ADD')
                self.vm_writer.write_pop('POINTER', 1)
                self.vm_writer.write_push('THAT', 0)
                return

            # simple var
            kind = self.symbol_table.kind_of(name)
            if kind is None:
                raise ValueError(f"Undeclared variable: {name}")
            seg = self._seg(kind)
            idx = self.symbol_table.index_of(name)
            self.vm_writer.write_push(seg, idx)
            self.eat(name)
            return

        raise ValueError(f"Invalid term: {tok} ({ttype})")

    # expressionList: (expression (',' expression)*)?
    def compile_expression_list(self) -> None:
        self.n_args = 0
        if self.tokenizer.current_token == ')':
            return
        while True:
            self.compile_expression()
            self.n_args += 1
            if self.tokenizer.current_token != ',':
                break
            self.eat(',')
