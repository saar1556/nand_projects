"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackTokenizer import JackTokenizer

class CompilationEngine:
    """
    Parses a stream of Jack tokens and writes its
    structured XML representation to an output stream.
    """

    # Mapping from internal token types to XML tags
    xml_tags  = {
        "KEYWORD" : "keyword",
        "SYMBOL" : "symbol",
        "IDENTIFIER" : "identifier",
        "INT_CONST" : "integerConstant",
        "STRING_CONST" : "stringConstant"
        }
    
    xml_escape_chars = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;'
    }

    
    def __init__(self, input_stream: JackTokenizer, output_stream) -> None:
        """
        Initializes a new CompilationEngine.

        Args:
            tokenizer (JackTokenizer): the tokenizer providing the input tokens
            output_stream: a writable stream where XML output is written
        """

        self.tokenizer: JackTokenizer = input_stream
        self.output_stream = output_stream
        self.indent_level = 0  # tracks the current indentation level for XML output

        # Mapping from token types to functions returning their values
        self.token_value_getters  = {
            "KEYWORD" : self.tokenizer.keyword,
            "SYMBOL" : self.tokenizer.symbol,
            "IDENTIFIER" : self.tokenizer.identifier,
            "INT_CONST" : self.tokenizer.int_val,
            "STRING_CONST" : self.tokenizer.string_val
        }

        # Start the tokenization process
        if self.tokenizer.peek() != 'class':
            raise ValueError("The first token must be 'class'")
            
    def print_tabs(self) -> None:
        """
            Writes indentation spaces to the output stream according to the current level.
        """
        for _ in range(self.indent_level):
            self.output_stream.write('  ')
     
    def eat(self, expected_token: str) -> None:
        """
        Consumes the current token, writes it as an XML element, 
        and advances to the next token.

        Args:
            expected_token (str): the token that is expected at this point

        Raises:
            ValueError: if the current token does not match expected_token
        """
        '''print(f"tokens befor advance: {self.tokenizer.tokens}")  # Debug print statement
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        else:
            raise ValueError(
                f"Unexpected end of input: expected '{expected_token}' but no more tokens were available."
            )
        print(f"tokens after advance: {self.tokenizer.tokens}")  # Debug print statement
        print(f"Eating token: expected '{expected_token}', got '{self.tokenizer.current_token}'")  # Debug print statement
        '''
        if self.tokenizer.current_token != expected_token:
            raise ValueError(
                f"Unexpected token: got '{self.tokenizer.current_token}', expected '{expected_token}'."
            )
        
        token_type = self.tokenizer.token_type()
        token_value = self.token_value_getters[token_type]() 
        if token_type == 'KEYWORD':
            token_value = token_value.lower()

        if token_value in self.xml_escape_chars:
            token_value = self.xml_escape_chars[token_value]

        self.print_tabs()
        self.output_stream.write(f"<{self.xml_tags[token_type]}> ")
        self.output_stream.write(f"{token_value} ")
        self.output_stream.write(f"</{self.xml_tags[token_type]}>\n")

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def write_headline(self, element_name: str, closing: bool) -> None:
        """
        Writes an XML opening or closing tag with proper indentation.

        Args:
            element_name (str): name of the XML element
            closing (bool): True to write a closing tag, False to write an opening tag
        """
        if closing:
            self.indent_level -= 1
            self.print_tabs()
            self.output_stream.write(f"</{element_name}>\n")
        else:
            self.print_tabs()
            self.output_stream.write(f"<{element_name}>\n")
            self.indent_level += 1
    
    def compile_class(self) -> None:  
        """
        Compiles a complete class structure in Jack and writes its XML representation.
        class: 'class' className '{' classVarDec* subroutineDec* '}'

        XML output format:
            <class> ... </class>
        """
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        else:
            raise ValueError("end of input reached before class declaration")
        self.write_headline('class', False)
        self.eat('class')
        self.eat(self.tokenizer.current_token)
        self.eat('{') 

        while self.tokenizer.current_token in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.current_token in ('constructor', 'function', 'method'):
            self.compile_subroutine()

        self.eat('}')
        self.write_headline('class', True)

    def compile_class_var_dec(self) -> None:
        """
        Compiles a static declaration or a field declaration.
        classVarDec: ('static' | 'field') type varName (',' varName)* ';'
        """
        
        self.write_headline('classVarDec', closing=False)

        # ('static' | 'field')
        if self.tokenizer.current_token in ('static', 'field'):
            self.eat(self.tokenizer.current_token)
        else: 
            raise ValueError(
                f"Syntax error in classVarDec: expected 'static' or 'field',"
                f" got '{self.tokenizer.current_token}'"
            )
        
        # type
        if self.tokenizer.current_token in ('int', 'char', 'boolean') or \
            self.tokenizer.token_type() == "IDENTIFIER":   
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(  
                f"Syntax error in classVarDec: expected type (int, char, boolean, or className),"
                f" got '{self.tokenizer.current_token}'"
            )
        
        # varName
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(
                f"Syntax error in classVarDec: expected varName (identifier),"
                f" got '{self.tokenizer.current_token}'"
            )

        # (',' varName)*
        while self.tokenizer.current_token == ',':
            self.eat(',') 
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.eat(self.tokenizer.current_token)
            else:
                raise ValueError(
                    f"Syntax error in classVarDec: expected varName after ',',"
                    f" got '{self.tokenizer.current_token}'"
                )
        
        # ';'
        self.eat(';')

        self.write_headline('classVarDec', True)

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
                subroutineName '(' parameterList ')' subroutineBody
        subroutineBody: '{' varDec* statements '}'
        """
        self.write_headline('subroutineDec', False)

        # ('constructor' | 'function' | 'method')
        if self.tokenizer.current_token in ('constructor', 'function', 'method'):
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(f"Expected subroutine keyword, got {self.tokenizer.current_token}")

        # ('void' | type)
        if self.tokenizer.current_token in ('int', 'char', 'boolean', 'void') or \
            self.tokenizer.token_type() == "IDENTIFIER": # className
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(f"Expected return type, got {self.tokenizer.current_token}")

        # subroutineName (identifier)
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(f"Expected subroutineName, got {self.tokenizer.current_token}")

        # '(' parameterList ')'
        self.eat('(')
        self.compile_parameter_list()
        self.eat(')')

        # subroutineBody
        if self.tokenizer.current_token == '{':
            self.write_headline('subroutineBody', False)
            self.eat('{')

            # varDec*
            while self.tokenizer.current_token == 'var':
                self.compile_var_dec()
            
            # statements
            self.compile_statements()
            self.eat('}')
            self.write_headline('subroutineBody', True)
        else:
            raise ValueError(f"Expected opening curly brace, got {self.tokenizer.current_token}")

        self.write_headline('subroutineDec', True)
        
    def parse_type_and_var(self) -> None:
        """
        Parses a single parameter: a type followed by a variable name.
        Example: "int x" or "Square squareObj".
        """
        if (self.tokenizer.current_token in ('int', 'char', 'boolean') or \
            self.tokenizer.token_type() == "IDENTIFIER"): 
            # consume type
            self.eat(self.tokenizer.current_token)
            
            if self.tokenizer.token_type() == "IDENTIFIER":
                # consume varName
                self.eat(self.tokenizer.current_token)
            else:
                raise ValueError(
                    f"Syntax error in parameterList: expected variable name after type, "
                    f"but got '{self.tokenizer.current_token}' instead"
                )
        else:
            raise ValueError(
                f"Syntax error in parameterList: expected type (int, char, boolean, or class name), "
                f"but got '{self.tokenizer.current_token}' instead"
            )
    
    def compile_parameter_list(self) -> None:
        """
        Compiles a (possibly empty) parameter list, not including the enclosing "()".

        Grammar:
            parameterList: ((type varName) (',' type varName)*)?

        Examples:
            ()                      -> empty parameter list
            (int x)                 -> one parameter
            (int x, boolean flag)   -> multiple parameters
        """
        self.write_headline('parameterList', False)

        # Loop until we reach the closing parenthesis ')'
        while self.tokenizer.current_token != ')':
            self.parse_type_and_var()

            # Handle additional parameters separated by commas
            while self.tokenizer.current_token == ',':
                self.eat(',') 
                self.parse_type_and_var()

        self.write_headline('parameterList', True)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        self.write_headline('varDec', closing=False)
        if self.tokenizer.current_token != 'var':
            raise ValueError(
                f"Syntax error in varDec: expected 'var', got '{self.tokenizer.current_token}'"
            )
        self.eat('var')
        self.parse_type_and_var()

        while self.tokenizer.current_token == ',':
            self.eat(',')
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.eat(self.tokenizer.current_token)
            else:
                raise ValueError(
                    f"Syntax error in varDec: expected varName after ',',"
                    f" got '{self.tokenizer.current_token}'"
                )
        self.eat(';')
        self.write_headline('varDec', True)

    def compile_statements(self) -> None:
        """
        Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.write_headline('statements', False)

        while self.tokenizer.current_token in (
            'let', 'if', 'while', 'do', 'return'):
            if self.tokenizer.current_token == 'let':
                self.compile_let()
            elif self.tokenizer.current_token == 'if':
                self.compile_if()
            elif self.tokenizer.current_token == 'while':
                self.compile_while()
            elif self.tokenizer.current_token == 'do':
                self.compile_do()
            elif self.tokenizer.current_token == 'return':
                self.compile_return()
            else:
                raise ValueError(
                    f"Unexpected statement type: {self.tokenizer.current_token}"
                )

        self.write_headline('statements', True)

    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.write_headline('doStatement', closing=False)
        self.eat('do')
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(
                f"Syntax error in do statement: expected subroutineName (identifier),"
                f" got '{self.tokenizer.current_token}'"
            )

        if self.tokenizer.current_token == '.':
            self.eat('.')
            if self.tokenizer.token_type() == "IDENTIFIER":
                self.eat(self.tokenizer.current_token)

            else:
                raise ValueError(
                    f"Syntax error in do statement: expected subroutineName (identifier),"
                    f" got '{self.tokenizer.current_token}'"
            )
        self.eat('(')
        self.compile_expression_list()
        self.eat(')')
        self.eat(';')
        self.write_headline('doStatement', True)

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.write_headline('letStatement', closing=False)
        self.eat('let')
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.eat(self.tokenizer.current_token)
        else:
            raise ValueError(
                f"Syntax error in let statement: expected varName (identifier),"
                f" got '{self.tokenizer.current_token}'"
        )

        if self.tokenizer.symbol() == '[':
            self.eat('[')
            self.compile_expression()
            self.eat(']')
        self.eat('=')
        self.compile_expression()
        self.eat(';')
        self.write_headline('letStatement', True)

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.write_headline('whileStatement', closing=False)
        self.eat('while')
        self.eat('(')
        self.compile_expression()
        self.eat(')')
        self.eat('{')
        self.compile_statements()
        self.eat('}')
        self.write_headline('whileStatement', True)

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.write_headline('returnStatement', closing=False)
        self.eat('return')
        self.compile_expression()
        self.eat(';')
        self.write_headline('returnStatement', True)

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self.write_headline('ifStatement', closing=False)
        self.eat('if')
        self.eat('(')
        self.compile_expression()
        self.eat(')')
        self.eat('{')
        self.compile_statements()
        self.eat('}')

        if self.tokenizer.current_token == 'else':
            self.eat('else')
            self.eat('{')
            self.compile_statements()
            self.eat('}')
        self.write_headline('ifStatement', True)


    def compile_expression(self) -> None:
        """Compiles an expression."""
        if self.tokenizer.current_token in (';', ')', '}'): 
            return
        self.write_headline('expression', False)
        self.compile_term()
        while self.tokenizer.symbol() in ('+', '-', '*', '/', '&', '|', '<', '>', '='):
            self.eat(self.tokenizer.current_token)
            self.compile_term()
        self.write_headline('expression', True)

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

        self.write_headline('term', False)
        name = self.tokenizer.current_token
        
        # integer constant
        if self.tokenizer.token_type() == 'INT_CONST':
            self.eat(name)
        
        # string constant
        elif self.tokenizer.token_type() == 'STRING_CONST':
            self.eat(name)

        # keyword constant
        elif self.tokenizer.token_type() == 'KEYWORD' \
            and name in ('true', 'false', 'null', 'this'):
            self.eat(name)

        # unary operation
        elif name in {'-', '~', '^', '#'}:
            self.eat(name)
            self.compile_term()

        # parenthesized expression
        elif name == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')

        # identifier: variable, array access, or subroutine call
        elif self.tokenizer.token_type() == "IDENTIFIER":
            next_tok = self.tokenizer.peek()
            if next_tok == '[':   # array access
                self.eat(name)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            elif next_tok == '(':  # simple subroutine call
                self.eat(name)
                self.eat('(')
                self.compile_expression_list()
                self.eat(')')
            elif next_tok == '.':  # subroutine call with class or object
                self.eat(name)
                self.eat('.')
                self.eat(self.tokenizer.current_token)
                self.eat('(')
                self.compile_expression_list()
                self.eat(')')
            else:  # simple variable
                self.eat(name)
        else:
            raise ValueError(f"Unexpected token in term: {name}")

        self.write_headline('term', True)
        
    def compile_expression_list(self) -> None:
            """Compiles a (possibly empty) comma-separated list of expressions."""
            self.write_headline('expressionList', False)

            if self.tokenizer.current_token != ')':
                self.compile_expression()
                while self.tokenizer.current_token == ',':
                    self.eat(',')
                    self.compile_expression()
            
            self.write_headline('expressionList', True)
