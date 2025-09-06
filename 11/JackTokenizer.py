"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from typing import Union,TextIO
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
    
    def __init__(self, input_stream: TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
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

            clean_line = ""
            i = 0
            in_string = False
            while i < len(line):
                if line[i] == '"':  # Toggle string state
                    in_string = not in_string
                    clean_line += line[i]
                elif line[i:i+2] == "//" and not in_string:
                    break  # Comment found outside string
                else:
                    clean_line += line[i]
                i += 1

            clean_line = clean_line.strip() 
            if clean_line:             
                sentences_list.append(clean_line)
                
        symbols_regex = "[" + "".join(re.escape(sym) for sym in self.symbols) + "]"
        token_pattern = re.compile( r"\"[^\n\"]*\"|[A-Za-z_][A-Za-z0-9_]*|\d+|" + symbols_regex)
        
        for sentence in sentences_list:
            temp = token_pattern.findall(sentence)
            self.tokens.extend(temp)
        
    def peek(self) -> Union[str,None]:
        """Return the next token without advancing the tokenizer."""
        if self.tokens:
            return self.tokens[0]
        return None

    def has_more_tokens(self) -> bool:
        """
        Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return len(self.tokens) > 0

    def advance(self) -> None:
        """
        Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        if not self.has_more_tokens():
            raise ValueError("No more tokens available to advance.")
        self.current_token = self.tokens.popleft()

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        
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
   
    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        if self.token_type() != "KEYWORD":
            raise ValueError(f"Current token is not a keyword: {self.current_token}")
        return self.keywords[self.current_token]
    
    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
                '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        if self.token_type() != "SYMBOL":
            raise ValueError(f"Current token is not a symbol: {self.current_token}")
        return self.current_token
        
    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                    starting with a digit. You can assume keywords cannot be
                    identifiers, so 'self' cannot be an identifier, etc'.
        """
        if self.token_type() != "IDENTIFIER":
            raise ValueError(f"Current token is not an identifier: {self.current_token}")
        return self.current_token

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        if self.token_type() != "INT_CONST":
            raise ValueError(f"Current token is not an integer constant: {self.current_token}")
        return int(self.current_token)

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                        double quote or newline '"'
        """
        if self.token_type() != "STRING_CONST":
            raise ValueError(f"Current token is not a string constant: {self.current_token}")
        return self.current_token[1:-1]
