"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from collections import deque
import re


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and 
    // comment until the line’s end.

    - ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’).
    - xxx: regular typeface is used for names of language constructs 
           (‘non-terminals’).
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName | 
            varName '['expression']' | subroutineCall | '(' expression ')' | 
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """

    symbols =  {
        '{', '}', '(', ')', '[', ']', '.',
        ',', ';', '+', '-', '*', '/', '&',
        '|', '<', '>', '=', '~', '^', '#' }

    keywords = {
        'class': 'CLASS',
        'constructor': 'CONSTRUCTOR',
        'function': 'FUNCTION',
        'method': 'METHOD',
        'field': 'FIELD',
        'static': 'STATIC',
        'var': 'VAR',
        'int': 'INT',
        'char': 'CHAR',
        'boolean': 'BOOLEAN',
        'void': 'VOID',
        'true': 'TRUE',
        'false': 'FALSE',
        'null': 'NULL',
        'this': 'THIS',
        'let': 'LET',
        'do': 'DO',
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'return': 'RETURN'
    }


    
    """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
    """
    def __init__(self, input_stream: typing.TextIO) -> None:
        
        self.tokens: deque[str] = deque()
        self.current_token: str | None = None
        sentences_list: list[str] = []
        inside_block_comment = False

        for line in input_stream.read().splitlines():
            line = line.strip()

            if inside_block_comment:
                if "*/" in line:
                    inside_block_comment = False 
                continue

            if line.startswith("/*") or line.startswith("/**"):
                if not "*/" in line: 
                    inside_block_comment = True
                continue

            clean_line = line.split("//")[0].strip()
            if clean_line:
                sentences_list.append(clean_line)
        
        symbols_regex = "[" + "".join(re.escape(sym) for sym in self.symbols) + "]"
        token_pattern = re.compile( r"\"[^\n\"]*\"|[A-Za-z_][A-Za-z0-9_]*|\d+|" + symbols_regex)
        
        for sentence in sentences_list:
            self.tokens.extend(token_pattern.findall(sentence))

        
    """
    Do we have more tokens in the input?

    Returns:
        bool: True if there are more tokens, False otherwise.
    """
    def has_more_tokens(self) -> bool:
        
        if self.tokens:
            return True
        return False

    """
    Gets the next token from the input and makes it the current token. 
    This method should be called if has_more_tokens() is true. 
    Initially there is no current token.
    """
    def advance(self) -> None:
        
        self.current_token = self.tokens.popleft()

    """
    Returns:
        str: the type of the current token, can be
        "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
    """
    def token_type(self) -> str:
        
        if self.current_token in self.keywords:
            return "KEYWORD"
        
        elif self.current_token in self.symbols:
            return "SYMBOL"

        elif self.current_token.isdigit():
            value = int(self.current_token)
            if not (0 <= value <= 32767):
                raise ValueError (f"Integer constant out of range: {self.current_token} (must be 0–32767)")
            else:
                return "INT_CONST"
        
        elif self.current_token.startswith('"') and self.current_token.endswith('"'):
            return "STRING_CONST"

        else:
            return "IDENTIFIER"


    """
    Returns:
        str: the keyword which is the current token.
        Should be called only when token_type() is "KEYWORD".
        Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
        "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
        "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
    """
    def keyword(self) -> str:
        return self.keywords[self.current_token]

    
    """
    Returns:
        str: the character which is the current token.
        Should be called only when token_type() is "SYMBOL".
        Recall that symbol was defined in the grammar like so:
        symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
            '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    """
    def symbol(self) -> str:
        return self.current_token
        
    
    """
    Returns:
        str: the identifier which is the current token.
        Should be called only when token_type() is "IDENTIFIER".
        Recall that identifiers were defined in the grammar like so:
        identifier: A sequence of letters, digits, and underscore ('_') not 
                starting with a digit. You can assume keywords cannot be
                identifiers, so 'self' cannot be an identifier, etc'.
    """
    def identifier(self) -> str:
        return self.current_token

    
    """
    Returns:
        str: the integer value of the current token.
        Should be called only when token_type() is "INT_CONST".
        Recall that integerConstant was defined in the grammar like so:
        integerConstant: A decimal number in the range 0-32767.
    """
    def int_val(self) -> int:
        return int(self.current_token)

    
    """
    Returns:
        str: the string value of the current token, without the double 
        quotes. Should be called only when token_type() is "STRING_CONST".
        Recall that StringConstant was defined in the grammar like so:
        StringConstant: '"' A sequence of Unicode characters not including 
                    double quote or newline '"'
    """
    def string_val(self) -> str:
        return self.current_token[1:-1]
