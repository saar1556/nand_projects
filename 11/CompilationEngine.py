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


    
    def __init__(self, tokenizer, output_stream):
        self.tokenizer = tokenizer
        self.vm_writer = VMWriter(output_stream)
        self.symbolTable = SymbolTable()


        # Mapping from token types to functions returning their values
        self.token_value_getters  = {
            "KEYWORD" : self.tokenizer.keyword,
            "SYMBOL" : self.tokenizer.symbol,
            "IDENTIFIER" : self.tokenizer.identifier,
            "INT_CONST" : self.tokenizer.int_val,
            "STRING_CONST" : self.tokenizer.string_val
        }
    
    
    def compile_class(self) -> None:
    
       

    def compile_var_declaration(self, kind: str) -> None:
        """
        Helper for compiling variable declarations (class or subroutine).
        kindToken type varName (',' varName)* ';'
        """
        # type: either keyword (int|char|boolean) or identifier (className)
        if self.tokenizer.current_token in {'int', 'char', 'boolean'}:
            type_name = self.tokenizer.current_token
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == 'IDENTIFIER':
            type_name = self.tokenizer.current_token
            self.tokenizer.advance()
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
        self.SymbolTable.define(name, type_name, kind)
        self.tokenizer.advance()

        # additional varNames separated by commas
        while self.tokenizer.current_token == ',':
            self.tokenizer.advance()
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(
                    f"Expected varName after ',', got '{self.tokenizer.current_token}'"
                )
            name = self.tokenizer.current_token
            self.SymbolTable.define(name, type_name, kind)
            self.tokenizer.advance()

        # final semicolon
        if self.tokenizer.current_token != ';':
            raise ValueError(
                f"Expected ';' at the end of var declaration, got '{self.tokenizer.current_token}'"
            )
        self.tokenizer.advance()

    
    
    """
    Compiles a static declaration or a field declaration.
    classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    """
    def compile_class_var_dec(self) -> None:

        if self.tokenizer.current_token not in {'static', 'field'}:
            raise ValueError(
                f"Expected 'static' or 'field' in classVarDec, "
                f"got '{self.tokenizer.current_token}'"
            )
        kind = self.tokenizer.current_token.upper()
        self.tokenizer.advance()

        # call the helper with the appropriate allowed kinds
        self.compile_var_declaration(kind)
        
        
    """
    Compiles a complete method, function, or constructor.
    subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
            subroutineName '(' parameterList ')' subroutineBody
    subroutineBody: '{' varDec* statements '}'
    """
    def compile_subroutine(self) -> None:
        
        
    
    
    """
    Compiles a (possibly empty) parameter list, not including the enclosing "()".

    Grammar:
        parameterList: ((type varName) (',' type varName)*)?

    Examples:
        ()                      -> empty parameter list
        (int x)                 -> one parameter
        (int x, boolean flag)   -> multiple parameters
    """
    def compile_parameter_list(self) -> None:
        while self.tokenizer.current_token != ')':
            # type: either keyword (int|char|boolean) or identifier (className)
            if self.tokenizer.current_token in {'int', 'char', 'boolean'}:
                type_name = self.tokenizer.current_token
                self.tokenizer.advance()
            elif self.tokenizer.token_type() == 'IDENTIFIER':
                type_name = self.tokenizer.current_token
                self.tokenizer.advance()
            else:
                raise ValueError(
                    f"Expected type (int, char, boolean, or className) in parameterList, "
                    f"got '{self.tokenizer.current_token}'"
                )

            # first varName
            if self.tokenizer.token_type() != 'IDENTIFIER':
                raise ValueError(
                    f"Expected varName (identifier), got '{self.tokenizer.current_token}'"
                )
            name = self.tokenizer.current_token
            self.SymbolTable.define(name, type_name, 'ARG')
            self.tokenizer.advance()


    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        if self.tokenizer.current_token != 'var':
            raise ValueError(
                f"Expected 'var' in subroutineVarDec, "
                f"got '{self.tokenizer.current_token}'"
            )
        self.tokenizer.advance()

        # call the helper with the appropriate allowed kind
        self.compile_var_declaration('VAR')

    
    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        # Your code goes here!
        pass

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Your code goes here!
        pass

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # Your code goes here!
        pass

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Your code goes here!
        pass

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Your code goes here!
        pass

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        pass

    def compile_expression(self) -> None:
        """Compiles an expression."""
        # Your code goes here!
        pass

    
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
    def compile_term(self) -> None:
        name = self.tokenizer.current_token
        
        # integer constant
        if self.tokenizer.token_type() == 'INT_CONST':
            self.vm_writer.write_push("CONST", self.tokenizer.int_val())
        
        # string constant
        elif self.tokenizer.token_type() == 'STRING_CONST':
            strLen = len(self.tokenizer.string_val())
            self.vm_writer.write_push("CONST", strLen)
            self.vm_writer.write_call("String.new", 1)
            for char in self.tokenizer.string_val():
                self.vm_writer.write_push("CONST", ord(char))
                self.vm_writer.write_call("String.appendChar", 2)

        # keyword constant
        elif self.tokenizer.token_type() == 'KEYWORD':
            

        # unary operation
        elif self.tokenizer.current_token in {'-', '~', '^', '#'}:
            self.eat(name)

        # parenthesized expression
        elif name == '(':
            self.eat('(')
            self.compile_expression_list()
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
        

    """Compiles a (possibly empty) comma-separated list of expressions."""
    def compile_expression_list(self) -> None:
        
        