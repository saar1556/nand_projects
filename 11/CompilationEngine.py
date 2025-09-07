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

    # Mapping from internal token types to XML tags
    arithmeticsOps = {
        '+': "ADD",
        '-': "SUB",
        '&': "AND",
        '|': "OR",
        '<': "LT",
        '>': "GT",
        '=': "EQ",
    }

    kinds = {
        "VAR": "LOCAL",
        "ARG": "ARG",
        "STATIC": "STATIC",
        "FIELD": "THIS"
    }

    n_args:int = 0
    label_counter:int = 0
    current_class:str = ""

    tokenizer:JackTokenizer = None
    vm_writer:VMWriter = None
    symbol_table:SymbolTable = None

    
    def __init__(self, tokenizer:JackTokenizer, output_stream:typing.TextIO) -> None:
        """
        Initialize the CompilationEngine.

        Args:
            tokenizer (JackTokenizer): Tokenizer providing Jack tokens.
            output_stream: Stream to write VM code to via VMWriter.
        """
        self.tokenizer:JackTokenizer = tokenizer
        self.vm_writer = VMWriter(output_stream)
        self.symbol_table = SymbolTable()

    
    def eat(self, expected_token: str) -> None:
        """
        Consumes the current token,and advances to the next token.
        """

        if self.tokenizer.current_token != expected_token:
            raise ValueError(
                f"Unexpected token: got '{self.tokenizer.current_token}', expected '{expected_token}'."
            )
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()


    
    '''
        # Parse type
        if self.tokenizer.current_token in {'int', 'char', 'boolean'} :
            type_name = self.tokenizer.current_token
            self.advance()
        elif self.tokenizer.token_type() == 'IDENTIFIER':
            type_name = self.tokenizer.current_token
            self.advance()
        else:
            raise ValueError(
                f"Unexpected token: got '{self.tokenizer.current_token}', expected '{expected_token}'."
            )

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        name = self.tokenizer.current_token
        self.symbolTable.define(name, type_name, kind)
        self.advance()

        # additional varNames separated by commas
        while self.tokenizer.current_token == ',':
            self.advance()
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(
                    f"Expected varName after ',', got '{self.tokenizer.current_token}'"
                )
            name = self.tokenizer.current_token
            self.symbolTable.define(name, type_name, kind)
            self.advance()
    '''

    def compile_class(self) -> None:
        self.tokenizer.advance()

        self.eat('class') 
        self.current_class = self.tokenizer.identifier()
        self.eat(self.current_class)

        self.eat('{')
        self.compile_class_var_dec()
        while self.tokenizer.current_token in {'constructor', 'function', 'method'}:
            self.compile_subroutine()

        self.eat('}')

    def compile_class_var_dec(self) -> None:
        """
        Compiles a static declaration or a field declaration.
        classVarDec: ('static' | 'field') type varName (',' varName)* ';'
        """
        current_kind = self.tokenizer.keyword()
        
        while current_kind in {'STATIC', 'FIELD'}:
            self.eat(current_kind.lower())
             
            type_name = self.tokenizer.token_type()
            if type_name == 'KEYWORD':
                type_name = self.tokenizer.keyword().lower()
                if type_name not in {'int', 'char', 'boolean'}:
                    raise ValueError(
                        f"Expected type (int, char, boolean, or className) in varDec, "
                        f"got '{self.tokenizer.current_token}'"
                    )
            elif type_name == 'IDENTIFIER':
                type_name = self.tokenizer.identifier()
            else:
                raise ValueError(
                    f"Expected type (int, char, boolean, or className) in varDec, "
                    f"got '{self.tokenizer.current_token}'"
                )

            self.eat(type_name)

            name = self.tokenizer.identifier()
            self.eat(name)
            self.symbol_table.define(name,type_name, current_kind)

            while self.tokenizer.current_token == ',':
                self.eat(',')
                name = self.tokenizer.identifier()
                self.eat(name)
                self.symbol_table.define(name,type_name, current_kind)

            # ';'
            self.eat(';')
            current_kind = self.tokenizer.keyword()
            
    def compile_subroutine(self) -> None:
        # subroutineDec:
        #   ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        kind = self.tokenizer.current_token            # 'constructor'|'function'|'method'
        self.eat(kind)

        ret_type = self.tokenizer.current_token        # 'void' | type
        self.eat(ret_type)

        name = self.tokenizer.current_token            # subroutineName
        self.eat(name)

        # reset subroutine scope
        self.symbol_table.start_subroutine()

        # For methods, predefine "this" as argument 0 so user params start at index 1
        if kind == 'method':
            self.symbol_table.define('this', self.current_class, 'ARG')

        # ( parameterList )
        self.eat('(')
        self.compile_parameter_list()
        self.eat(')')

        # subroutineBody: '{' varDec* statements '}'
        self.eat('{')

        # varDec*
        self.compile_var_dec()

        # Emit VM function header with local count
        n_locals = self.symbol_table.var_count('VAR')
        full_name = f"{self.current_class}.{name}"
        self.vm_writer.write_function(full_name, n_locals)

        # Prologue:
        if kind == 'constructor':
            # allocate memory for fields and anchor 'this'
            n_fields = self.symbol_table.var_count('FIELD') 
            self.vm_writer.write_push('CONST', n_fields)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('POINTER', 0)  # this = base
        elif kind == 'method':
            # set 'this' from argument 0
            self.vm_writer.write_push('ARG', 0)
            self.vm_writer.write_pop('POINTER', 0)

        # statements
        self.compile_statements()

        self.eat('}')

    def compile_parameter_list(self) -> None:
        # final semicolon
        self._expect(';', 'compile_var_declaration')
    
    
    def compile_class_var_dec(self) -> None:
        """
        Compile a class-level variable declaration ('static' or 'field').

        Grammar:
            classVarDec: ('static' | 'field') type varName (',' varName)* ';'
        """
        if self.tokenizer.current_token not in {'static', 'field'}:
            raise ValueError(
                f"Expected 'static' or 'field' in classVarDec, "
                f"got '{self.tokenizer.current_token}'"
            )
        kind = self.tokenizer.current_token.upper()
        self.advance()
        self.compile_var_declaration(kind)
        
        
    def compile_subroutine(self) -> None:
        """
        Compile a subroutine: constructor, function, or method.

        Grammar:
            subroutineDec: ('constructor' | 'function' | 'method') ('void' | type)
                           subroutineName '(' parameterList ')' subroutineBody
            subroutineBody: '{' varDec* statements '}'
        """
        if self.tokenizer.current_token not in {'constructor', 'function', 'method'}:
            raise ValueError(
                f"Expected 'constructor', 'function', or 'method' in subroutineDec, "
                f"got '{self.tokenizer.current_token}'"
            )
        
        # Start a new subroutine scope
        subroutine_type = self.tokenizer.current_token
        self.symbolTable.start_subroutine()
        self.advance()

        # Handle 'method': add 'this' as the first argument
        if subroutine_type == 'method':
            self.symbolTable.define('this', self.className, 'ARG')

        # Parse return type
        void_func = False
        if self.tokenizer.current_token == 'void':
            void_func = True
        elif self.tokenizer.current_token not in {'int', 'char', 'boolean'} \
            and self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError( 
                f"Expected return type (void, int, char, boolean, or className), "
                f"got '{self.tokenizer.current_token}'"
            )
        self.advance()

        # Parse subroutine name
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(
                f"Expected subroutineName (identifier), got '{self.tokenizer.current_token}'"
            )
        subroutine_name = f"{self.className}.{self.tokenizer.current_token}"
        self.advance()

        # Parse parameter list
        self._expect('(', 'compile_subroutine')
        self.compile_parameter_list()
        self._expect( ')', 'compile_subroutine')
        self._expect( '{', 'compile_subroutine')

        # Compile all varDecs and count local variables
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()
        n_locals = self.symbolTable.var_count('VAR')

        # VM function declaration
        self.vm_writer.write_function(subroutine_name, n_locals)
        
        # Handle 'constructor': allocate memory for the new object
        if subroutine_type == 'constructor':
            n_fields = self.symbolTable.var_count('FIELD')
            self.vm_writer.write_push("CONST", n_fields)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("POINTER", 0)
        # Handle 'method': set 'this' to point to the object
        elif subroutine_type == 'method':
            self.vm_writer.write_push("ARG", 0)
            self.vm_writer.write_pop("POINTER", 0)

        # Compile statements inside the subroutine
        self.compile_statements()
        self._expect( '}', 'compile_subroutine')

        # Remove garbage return value for void functions
        if void_func:
            self.vm_writer.write_pop("TEMP", 0) 
        

    def compile_parameter_list(self) -> None:
        """
        Compiles a (possibly empty) parameter list, not including the enclosing "()".

        Grammar:
            parameterList: ((type varName) (',' type varName)*)?
        """
        while self.tokenizer.current_token != ')':
            # type: either keyword (int|char|boolean) or identifier (className)
            if self.tokenizer.current_token in {'int', 'char', 'boolean'}:
                type_name = self.tokenizer.current_token
                self.advance()
            elif self.tokenizer.token_type() == 'IDENTIFIER':
                type_name = self.tokenizer.current_token
                self.advance()
            else:
                raise ValueError(
                    f"Expected type (int, char, boolean, or className) in varDec, "
                    f"got '{self.tokenizer.current_token}'"
                )

            # varName
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(
                    f"Expected varName (identifier), got '{self.tokenizer.current_token}'"
                )
            name = self.tokenizer.current_token
            self.symbolTable.define(name, type_name, 'ARG')
            self.advance()

            # additional varNames separated by commas
            if self.tokenizer.current_token == ',':
                self.advance()


    def compile_var_dec(self) -> None:
        """Compile a local variable declaration within a subroutine."""
        self._expect('var', 'compile_var_dec')
        self.compile_var_declaration('VAR')

    
    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing."""
        while self.tokenizer.current_token in {'let', 'if', 'while', 'do', 'return'}:
            if self.tokenizer.current_token == 'let':
                self.compile_let()
            elif self.tokenizer.current_token == 'if':
                self.compile_if()
            elif self.tokenizer.current_token == 'while':
                self.compile_while()
            elif self.tokenizer.current_token == 'do':
                self.compile_do()
            else:
                self.compile_return()


    def compile_do(self) -> None:
        """
        Compile a 'do' statement.

        Notes:
            - The return value of the call is discarded (popped into TEMP 0).
        """
        self._expect('do', 'compile_do')
        self.compile_term()
        self._expect(';', 'compile_do')
        self.vm_writer.write_pop("TEMP", 0)  # Discard return value


    def compile_let(self) -> None:
        """let var = expr; | let arr[expr] = expr;"""
        self.eat('let')
        name = self.tokenizer.identifier()
        kind = self.symbol_table.kind_of(name)
        idx  = self.symbol_table.index_of(name)
        if kind is None:
            raise ValueError(f"Undeclared variable: {name}")
        self.eat(name)

        is_array = False
        if self.tokenizer.current_token == '[':
            is_array = True
            self.eat('[')
            # base address
            self.vm_writer.write_push(kind, idx)
            # index
            self.compile_expression()
            self.eat(']')
            self.vm_writer.write_arithmetic("ADD")   # address on stack

        self.eat('=')
        self.compile_expression()

        if is_array:
            # stack: ... [address, value]
            self.vm_writer.write_pop("TEMP", 0)      # value
            self.vm_writer.write_pop("POINTER", 1)   # THAT = address
            self.vm_writer.write_push("TEMP", 0)     # value
            self.vm_writer.write_pop("THAT", 0)
        else:
            self.vm_writer.write_pop(kind, idx)

        self.eat(';')

    def compile_while(self) -> None:
        """while (expr) { statements }"""
        idx = self.label_counter
        self.label_counter += 1

        self.vm_writer.write_label(f"WHILE_EXP{idx}")
        self.eat('while')
        self.eat('(')
        self.compile_expression()
        self.eat(')')

        self.vm_writer.write_arithmetic("NOT")
        self.vm_writer.write_if(f"WHILE_END{idx}")

        self.eat('{')
        self.compile_statements()
        self.eat('}')

        self.vm_writer.write_goto(f"WHILE_EXP{idx}")
        self.vm_writer.write_label(f"WHILE_END{idx}")

    def compile_return(self) -> None:
        """
        Compile a 'return' statement.

        Notes:
            - If the function is void, pushes 0 as a dummy return value.
        """
        self._expect('return', 'compile_return')

        # non-void function
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        
        # void function
        else:
            self.vm_writer.write_push("CONST", 0)
        self._expect(';', 'compile_return')
        
        self.vm_writer.write_return()

    
    
    def compile_if(self) -> None:
        """if (expr) { statements } (else { statements })?"""
        self.eat('if')
        self.eat('(')
        self.compile_expression()
        self.eat(')')

        idx = self.label_counter
        self.label_counter += 1

        self.vm_writer.write_arithmetic("NOT")
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

    def aritmetic_op(self, op: str) -> str:
        if op == '+':
                self.vm_writer.write_arithmetic("ADD")
        elif op == '-':
            self.vm_writer.write_arithmetic("SUB")
        elif op == '*':
            self.vm_writer.write_call("Math.multiply",2)
        elif op == '/':
            self.vm_writer.write_call("Math.divide",2)
        elif op == '&':
            self.vm_writer.write_arithmetic("AND")
        elif op == '|':
            self.vm_writer.write_arithmetic("OR")
        elif op == '<':
            self.vm_writer.write_arithmetic("LT")
        elif op == '>':
            self.vm_writer.write_arithmetic("GT")
        elif op == '=':
            self.vm_writer.write_arithmetic("EQ")
        elif op == '^': 
            self.vm_writer.write_arithmetic("SHIFTLEFT")
        elif op == '#':
            self.vm_writer.write_arithmetic("SHIFTRIGHT")  

    def _jack_char_code(self, ch: str) -> int:
        # normalize curly quotes if you want to be nice:
        if ch == '“' or ch == '”': ch = '"'
        if ch == '’': ch = "'"

        c = ord(ch)
        if 32 <= c <= 126:
            return c
        # Optional escape handling (non-standard Jack; implement only if your tokenizer supports it):
        if ch == '\n':
            return 128   # Jack OS "newLine"
        if ch == '\b':
            return 129   # Jack OS "backSpace"
        raise ValueError(f"Illegal character in Jack string literal: {repr(ch)}")

    def compile_expression(self) -> None:
        """term (op term)*"""
        self.compile_term()
        ops = {'+', '-', '*', '/', '&', '|', '<', '>', '=', '^', '#'}
        while self.tokenizer.current_token in ops:
            op = self.tokenizer.current_token
            self.eat(op)
            self.compile_term()
            self.aritmetic_op(op)
         
    def compile_term(self) -> None:
        """
        Compiles a single term in a Jack expression.

        A term can be one of the following:
            - integerConstant
            - stringConstant
            - keywordConstant (true, false, null, this)
            - varName (simple variable)
            - varName '[' expression ']' (array access)
            - subroutineCall:
                - subroutineName '(' expressionList ')'
                - (className | varName) '.' subroutineName '(' expressionList ')'
            - '(' expression ')' (parenthesized expression)
            - unaryOp term (unary operations like -x or ~x)

        Notes:
            - If the current token is an identifier, a single look-ahead token
            (peek) is sufficient to distinguish between a variable, array access, 
            or subroutine call.
            - Raises ValueError if the current token does not match any valid term.
        """
        tok   = self.tokenizer.current_token
        ttype = self.tokenizer.token_type()

        # (debug print removed)
        if ttype == 'INT_CONST':
            self.vm_writer.write_push("CONST", self.tokenizer.int_val())
            self.eat(tok)
            return

        elif ttype == 'STRING_CONST':
            s = self.tokenizer.string_val()
            self.eat(tok)
            self.vm_writer.write_push("CONST", len(s))
            self.vm_writer.write_call("String.new", 1)
            for ch in s:
                self.vm_writer.write_push("CONST", self._jack_char_code(ch))
                self.vm_writer.write_call("String.appendChar", 2)
            return

        elif ttype == 'KEYWORD':
            if tok in ('false', 'null'):
                self.vm_writer.write_push("CONST", 0)
            elif tok == 'true':
                self.vm_writer.write_push("CONST", 0)
                self.vm_writer.write_arithmetic("NOT")
            elif tok == 'this':
                self.vm_writer.write_push("POINTER", 0)
            else:
                raise ValueError(f"unexpected keyword in term: {tok}")
            self.eat(tok)
            return

        elif tok == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')
            return

        elif name in {'-', '~', '^', '#'}:
            op = name
            self.advance()
            self.compile_term()
            if op == '-':
                self.vm_writer.write_arithmetic("NEG")
            elif op == '~':
                self.vm_writer.write_arithmetic("NOT")
            elif op == '^':
                self.vm_writer.write_arithmetic("SHIFTLEFT")
            elif op == '#':
                self.vm_writer.write_arithmetic("SHIFTRIGHT")
            else:
                raise ValueError(f"Unknown unary operator: {op}")

        elif ttype == 'IDENTIFIER':
            name = tok
            nxt  = self.tokenizer.peek()

            # subroutine calls
            if nxt in ('(', '.'):
                extra = 0
                if nxt == '.':  # name.sub(...)
                    self.eat(name)
                    self.eat('.')
                    sub = self.tokenizer.identifier()
                    self.eat(sub)
                    if self.symbol_table.kind_of(name) is not None: # method of other object
                        seg = self.symbol_table.kind_of(name)
                        idx = self.symbol_table.index_of(name)
                        typ = self.symbol_table.type_of(name)
                        self.vm_writer.write_push(seg, idx)
                        callee = f"{typ}.{sub}"
                        extra = 1
                    else:               # function of other object
                        callee = f"{name}.{sub}"
                else: # method
                    self.eat(name)
                    self.vm_writer.write_push("POINTER", 0)
                    callee = f"{self.current_class}.{name}"
                    extra = 1

                self.eat('(')
                self.compile_expression_list()
                self.eat(')')
                self.vm_writer.write_call(callee, self.n_args + extra)
                return

            # array access: varName[expr]
            if nxt == '[':
                seg = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.write_push(seg, idx)  # base
                self.eat(name)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
                self.vm_writer.write_arithmetic("ADD")
                self.vm_writer.write_pop("POINTER", 1)
                self.vm_writer.write_push("THAT", 0)
                return

            # simple var
            seg = self.symbol_table.kind_of(name)
            idx = self.symbol_table.index_of(name)
            self.vm_writer.write_push(seg, idx)
            self.eat(name)
            return

        else:
            raise ValueError(f"Invalid term: {tok} ({ttype})")

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        self.n_args = 0
        while self.tokenizer.current_token != ')':
            if self.tokenizer.current_token == ',':
                self.eat(',')
            self.compile_expression()
            self.n_args += 1
        
        