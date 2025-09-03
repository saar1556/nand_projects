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
    
       

    
    """
    Compiles a static declaration or a field declaration.
    classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    """
    def compile_class_var_dec(self) -> None:
        

        
        
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
        


    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        pass

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
        
        