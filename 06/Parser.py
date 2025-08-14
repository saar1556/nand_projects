"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """
    input_lines: list[str]
    current_command: str

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.input_lines = []
        for line in input_file.read().splitlines():
            clean_line = line.split('//')[0].strip()
            if clean_line:
                self.input_lines.append(clean_line)
        self.current_line = 0

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
        self.current_line = 0

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        self.current_command = self.input_lines[self.current_line]
        self.current_line += 1
        

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        if self.current_command.startswith('@'):
            return "A_COMMAND"
        elif self.current_command.startswith('('):
            return "L_COMMAND"
        else:
            return "C_COMMAND"
        

    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        if self.command_type() == "A_COMMAND":
            return self.current_command[1:]
        elif self.command_type() == "L_COMMAND":
            return self.current_command[1:-1]
        else:
            raise ValueError("symbol() should only be called for A_COMMAND or L_COMMAND")

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if '=' in self.current_command:
            return self.current_command.split('=')[0]
        else:
            return 'null'

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if ';' in self.current_command:
            comp_part = self.current_command.split(';')[0]
        else:
            comp_part = self.current_command
        if '=' in comp_part:
            return comp_part.split('=')[1]
        else:
            return comp_part

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if ';' in self.current_command:
            return self.current_command.split(';')[1]
        else:
            return 'null'
