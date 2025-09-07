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
    xml_tags  = {
        "KEYWORD" : "keyword",
        "SYMBOL" : "symbol",
        "IDENTIFIER" : "identifier",
        "INT_CONST" : "integerConstant",
        "STRING_CONST" : "stringConstant"
        }
    
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

    
    def __init__(self, tokenizer, output_stream):
        """
        Initialize the CompilationEngine.

        Args:
            tokenizer (JackTokenizer): Tokenizer providing Jack tokens.
            output_stream: Stream to write VM code to via VMWriter.
        """
        self.tokenizer = tokenizer
        self.vm_writer = VMWriter(output_stream)
        self.symbolTable = SymbolTable()
        self.label_counter = 0
        self.className = ""

        # Mapping from token types to functions returning their values
        self.token_value_getters  = {
            "KEYWORD" : self.tokenizer.keyword,
            "SYMBOL" : self.tokenizer.symbol,
            "IDENTIFIER" : self.tokenizer.identifier,
            "INT_CONST" : self.tokenizer.int_val,
            "STRING_CONST" : self.tokenizer.string_val
        }


    def advance(self) -> None:
        """Advances the tokenizer to the next token."""
        if not self.tokenizer.has_more_tokens():
            raise ValueError("No more tokens available.")
        self.tokenizer.advance()


    def _expect(self, token: str, context: str) -> None:
        """
        Expect the current token to match the given value.

        Args:
            token: The expected token string.
            context: Context of the call (function name) for error messages.

        Raises:
            ValueError if the current token does not match.
        """
        if self.tokenizer.current_token != token:
            raise ValueError(
                f"[{context}] Expected '{token}', got '{self.tokenizer.current_token}'"
            )
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
    
    
    def compile_class(self) -> None:
        """
        Compile a complete Jack class.

        Grammar:
            class: 'class' className '{' classVarDec* subroutineDec* '}'
        """
        self.advance()
        self._expect('class', 'compile_class')
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(
                f"[compile_class] Expected class name (identifier), "
                f"got '{self.tokenizer.current_token}'"
            )
        self.className = self.tokenizer.current_token
        self.advance()
        self._expect('{', 'compile_class')
        while self.tokenizer.current_token in {'static', 'field'}:
            self.compile_class_var_dec()
        while self.tokenizer.current_token in {'constructor', 'function', 'method'}:
            self.compile_subroutine()
        self._expect('}', 'compile_class')
        
       
    def compile_var_declaration(self, kind: str) -> None:
        """
        Compile a variable declaration of a given kind (helper).

        Args:
            kind: Variable kind ('STATIC', 'FIELD', or 'VAR').

        Grammar:
            type varName (',' varName)* ';'
        """
        # Parse type
        if self.tokenizer.current_token in {'int', 'char', 'boolean'} :
            type_name = self.tokenizer.current_token
            self.advance()
        elif self.tokenizer.token_type() == 'IDENTIFIER':
            type_name = self.tokenizer.current_token
            self.advance()
        else:
            raise ValueError(
                f"Expected type (int, char, boolean, or className), "
                f"got '{self.tokenizer.current_token}'"
            )

        # first varName
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(
                f"Expected varName (identifier), got '{self.tokenizer.current_token}'"
            )
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
        self._expect( '(', 'compile_subroutine')
        self.compile_parameter_list()
        self._expect(')', 'compile_subroutine')
        self._expect('{', 'compile_subroutine')

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
        self._expect('}', 'compile_subroutine')

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
                    f"Expected type (int, char, boolean, or className) in parameterList, "
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
        """
        Compile a 'let' statement.

        Grammar:
            let varName ('[' expression ']')? '=' expression ';'
        Notes:
            - Handles array assignments by computing the target address in TEMP 0.
        """
        self._expect('let', 'compile_let')
        
        # Variable name
        if self.tokenizer.token_type() != 'IDENTIFIER':
            raise ValueError(
                f"Expected varName (identifier) after 'let', got '{self.tokenizer.current_token}'"
            )
        var_name = self.tokenizer.current_token
        kind = self.kinds[self.symbolTable.kind_of(var_name)]
        index = self.symbolTable.index_of(var_name)
        self.advance()
        
        # Array assignment?
        is_array = False
        if self.tokenizer.current_token == '[':
            is_array = True
            self.advance()  # eat '['
            # push base address
            self.vm_writer.write_push(kind, index) 
            self.compile_expression()       
            self._expect( ']', 'compile_let')
            self.vm_writer.write_arithmetic("ADD")
            self.vm_writer.write_pop("TEMP", 0)  # Store the address in TEMP 0
        
        self._expect('=', 'compile_let')
        self.compile_expression()
        self._expect(';', 'compile_let')

        if is_array:
            self.vm_writer.write_push("TEMP", 0)  # Retrieve the address from TEMP 0
            self.vm_writer.write_pop("POINTER", 1)  # THAT points to the target address
            self.vm_writer.write_pop("THAT", 0)  # Pop the value into THAT 0  
        else:
            self.vm_writer.write_pop(kind, index)  


    def compile_while(self) -> None:
        """
        Compile a 'while' statement.

        Grammar:
            while '(' expression ')' '{' statements '}'
        """
        self._expect('while', 'compile_while')

        # Generate unique labels
        label_start = f"WHILE_EXP{self.label_counter}"
        label_end = f"WHILE_END{self.label_counter}"
        self.label_counter += 1

        self.vm_writer.write_label(label_start)
        self._expect("(", 'compile_while')
        self.compile_expression()

        # Exit loop if condition is false (0)
        self._expect( ")", 'compile_while')  
        self.vm_writer.write_arithmetic("NOT")
        self.vm_writer.write_if(label_end)

        # Parse body
        self._expect("{", 'compile_while')     
        self.compile_statements()
        self._expect( "}", 'compile_while') 
        self.vm_writer.write_goto(label_start)
        self.vm_writer.write_label(label_end)  


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
        """
        Compile an 'if' statement, optionally with an 'else' clause.

        Grammar:
            if '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        """
        self._expect('if', 'compile_if')

        # Parse condition
        self._expect("(", 'compile_if')
        self.compile_expression()
        self._expect(")", 'compile_if')
        
        # Generate unique labels
        label_else = f"IF_ELSE{self.label_counter}"
        label_end = f"IF_END{self.label_counter}"
        self.label_counter += 1
        
        # Jump to ELSE if condition is false
        self.vm_writer.write_arithmetic("NOT")
        self.vm_writer.write_if(label_else)
        
        # Compile "then" block
        self._expect("{", 'compile_if')
        self.compile_statements()
        self._expect( "}", 'compile_if')
        self.vm_writer.write_goto(label_end)
        
        # Compile "else" block if present
        self.vm_writer.write_label(label_else)
        if self.tokenizer.current_token == 'else':
            self.advance()
            self._expect("{", 'compile_if')
            self.compile_statements()
            self._expect("}", 'compile_if')
        
        self.vm_writer.write_label(label_end)
        

    def compile_expression(self) -> None:
        """Compiles an expression."""
        if self.tokenizer.current_token in ( ';', ')', '}', ']'): 
            return
        
        self.compile_term()
        while self.tokenizer.current_token in {'+', '-', '*', '/', '&', '|', '<', '>', '='}:
            op = self.tokenizer.current_token
            self.advance()
            self.compile_term()
            if op in self.arithmeticsOps:
                self.vm_writer.write_arithmetic(self.arithmeticsOps[op])
            elif op == '*':
                self.vm_writer.write_call("Math.multiply", 2)
            elif op == '/':
                self.vm_writer.write_call("Math.divide", 2)
            else:
                raise ValueError(f"Unknown binary operator: {op}")


    def compile_term(self) -> None:
        """
        Compile a single term.

        Grammar:
            term: integerConstant | stringConstant | keywordConstant | varName 
                  | varName '[' expression ']' | subroutineCall | '(' expression ')' 
                  | unaryOp term
        """
        name = self.tokenizer.current_token
        
        # integer constant
        if self.tokenizer.token_type() == 'INT_CONST':
            self.vm_writer.write_push("CONST", int(name))
            self.advance()
        
        # string constant
        elif self.tokenizer.token_type() == 'STRING_CONST':
            string_val = self.tokenizer.string_val() 
            str_len = len(string_val)
            self.vm_writer.write_push("CONST", str_len)
            self.vm_writer.write_call("String.new", 1)
            for char in string_val:
                self.vm_writer.write_push("CONST", ord(char))
                self.vm_writer.write_call("String.appendChar", 2)
            self.advance()

        # keyword constant
        elif self.tokenizer.token_type() == 'KEYWORD':
            #and name in ('true', 'false', 'null', 'this'):
            if name == 'true':
                self.vm_writer.write_push("CONST", 0)
                self.vm_writer.write_arithmetic("NOT")
            elif name in {'false', 'null'}:
                self.vm_writer.write_push("CONST", 0)
            elif name == 'this':
                self.vm_writer.write_push("POINTER", 0)
            else:
                raise ValueError(f"Unexpected keyword in term: {name}")
            self.advance()

        # unary operation
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

        # parenthesized expression
        elif name == '(':
            self._expect('(', 'compile_term')
            self.compile_expression()
            self._expect( ')', 'compile_term')

        # identifier: variable, array access, or subroutine call 
        elif self.tokenizer.token_type() == "IDENTIFIER":
            next_tok = self.tokenizer.peek()
            
            # array access
            if next_tok == '[':  
                var_name = self.tokenizer.current_token
                self.vm_writer.write_push(
                        self.kinds[self.symbolTable.kind_of(var_name)], 
                        self.symbolTable.index_of(var_name)
                    )                
                self.advance()  # eat varName
                self.advance()  # eat '['
                self.compile_expression()       
                self._expect( ']', 'compile_term')
                self.vm_writer.write_arithmetic("ADD")
                self.vm_writer.write_pop("POINTER", 1)
                self.vm_writer.write_push("THAT", 0)  

            # method call on 'this' object
            elif next_tok == '(': 
                func_name = self.className + '.' + name 
                self.advance()  # eat name
                self._expect( '(', 'compile_term')
                self.vm_writer.write_push("POINTER", 0)  # push 'this'
                n_args = self.compile_expression_list()
                self._expect(')', 'compile_term')
                self.vm_writer.write_call(func_name, n_args + 1) # include 'this' as an argument

             # subroutine call with class or object
            elif next_tok == '.': 
                self._expect(name, 'compile_term')
                self._expect('.', 'compile_term')
                if self.tokenizer.token_type() != 'IDENTIFIER':
                    raise ValueError(
                        f"Expected subroutineName (identifier) after '.', "
                        f"got '{self.tokenizer.current_token}'"
                    )

                if self.symbolTable.kind_of(name) is not None:
                    # method call on an object
                    func_name = self.symbolTable.type_of(name) + '.' + self.tokenizer.current_token 
                    self.advance()
                    # push the object as the first argument
                    self.vm_writer.write_push(self.kinds[self.symbolTable.kind_of(name)],
                                            self.symbolTable.index_of(name))
                    self._expect('(', 'compile_term')
                    n_args = self.compile_expression_list() + 1 # include object as argument
                else:
                    # class function call
                    func_name = name + '.' + self.tokenizer.current_token
                    self.advance()
                    self._expect( '(', 'compile_term')
                    n_args = self.compile_expression_list()
                self._expect(')', 'compile_term')

                self.vm_writer.write_call(func_name, n_args)

            # simple variable
            else: 
                var_name = self.tokenizer.current_token
                self.vm_writer.write_push(
                        self.kinds[self.symbolTable.kind_of(var_name)], 
                        self.symbolTable.index_of(var_name)
                    )                
                self.advance()
        else:
            raise ValueError(f"Unexpected token in term: {name}")


    def compile_expression_list(self) -> int:
        """
        Compile a (possibly empty) comma-separated list of expressions.

        Returns:
            int: Number of expressions compiled (used for argument count).
        """
        n_args = 0
        if self.tokenizer.current_token != ")":
            self.compile_expression()
            n_args += 1
            while self.tokenizer.current_token == ',':
                self.advance()
                self.compile_expression()
                n_args += 1
        return n_args
        