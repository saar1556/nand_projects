"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """
    # Parser
    
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.

    ## VM Language Specification

    A .vm file is a stream of characters. If the file represents a
    valid program, it can be translated into a stream of valid assembly 
    commands. VM commands may be separated by an arbitrary number of whitespace
    characters and comments, which are ignored. Comments begin with "//" and
    last until the line's end.
    The different parts of each VM command may also be separated by an arbitrary
    number of non-newline whitespace characters.

    - Arithmetic commands:
      - add, sub, and, or, eq, gt, lt
      - neg, not, shiftleft, shiftright
    - Memory segment manipulation:
      - push <segment> <number>
      - pop <segment that is not constant> <number>
      - <segment> can be any of: argument, local, static, constant, this, that, 
                                 pointer, temp
    - Branching (only relevant for project 8):
      - label <label-name>
      - if-goto <label-name>
      - goto <label-name>
      - <label-name> can be any combination of non-whitespace characters.
    - Functions (only relevant for project 8):
      - call <function-name> <n-args>
      - function <function-name> <n-vars>
      - return
    """

    arithmetic_commands = {
        'add', 'sub', 'and', 'or',
        'eq', 'gt', 'lt', 'neg',
        'not', 'shiftleft', 'shiftright'}

    non_arithmetic_commands = {
        'push':'C_PUSH', 'pop':'C_POP', 'label':'C_LABEL', 'if-goto':'C_IF',  
        'goto':'C_GOTO', 'call':'C_CALL', 'function':'C_FUNCTION', 'return':'C_RETURN'}

    def __init__(self, input_file: typing.TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.input_lines = []
        for line in input_file.read().splitlines():
            clean_line = line.split('//')[0].strip()
            if clean_line:
                self.input_lines.append(clean_line)
        self.current_line = 0
        self.current_command = None

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        if len(self.input_lines) == self.current_line:
            return False
        else:
            return True

    def reset(self) -> None:
        """
        Resets the parser's internal state to the beginning of the input.
        After calling this method, `advance()` will read the first command
        in the file again.
        """
        self.current_line = 0

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        self.current_command = self.input_lines[self.current_line]
        self.current_line += 1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        command = self.current_command.split()[0].strip()
        if command in self.arithmetic_commands:
            return "C_ARITHMETIC"
        elif command in self.non_arithmetic_commands:
            return self.non_arithmetic_commands[command]
        else:
            raise ValueError(f"Unknown command: {command}")

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        command_parts = self.current_command.split()
        if len(command_parts) == 1:
            return command_parts[0].strip()
        else:
            return command_parts[1].strip()

    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        return int(self.current_command.split()[2].strip())
