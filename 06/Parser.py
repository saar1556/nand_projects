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
    and provides convenient access to the command's components (fields
    and symbols). In addition, removes all white space and comments.
    """
    instructions: list[str]
    current_line: int
    current_command: str

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.instructions = []

        for raw in input_file.read().splitlines():
            line = raw.split("//", 1)[0]
            line = line.replace("\u00A0", " ").expandtabs().strip()
            if not line:
                continue
            self.instructions.append(line)

        self.current_line = 0
        self.current_command = self.instructions[0] if self.instructions else ""


    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.current_line + 1 < len(self.instructions) 

    def reset(self) -> None:
        """Resets the parser to the beginning of the input."""
        self.current_line = -1
        self.current_command = ""

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        if self.has_more_commands():
            self.current_line += 1
            self.current_command = self.instructions[self.current_line]

    def command_type(self) -> str:
        """Returns the type of the current command.

        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        if self.current_command.startswith('@'):
            return "A_COMMAND"
        elif self.current_command.startswith('(') and self.current_command.endswith(')'):
            return "L_COMMAND"
        else:
            return "C_COMMAND"

    def symbol(self) -> str:
        """Returns the symbol or decimal Xxx of the current command.

        For @Xxx (A_COMMAND) returns "Xxx".
        For (Xxx) (L_COMMAND) returns "Xxx".

        Returns:
            str: the symbol or decimal of the current command.
        """
        if self.command_type() == "A_COMMAND":
            return self.current_command[1:]
        elif self.command_type() == "L_COMMAND":
            return self.current_command[1:-1]
        else:
            raise ValueError("symbol() should only be called for A_COMMAND or L_COMMAND")

    def dest(self) -> str:
        """Returns the dest mnemonic in the current C-command.

        Returns:
            str: the dest mnemonic, or "null" if no dest is present.
        """
        if self.command_type() != "C_COMMAND":
            raise ValueError("dest() should only be called for C_COMMAND")
        return self.current_command.split('=', 1)[0].strip() if '=' in self.current_command else 'null'

    def comp(self) -> str:
        """Returns the comp mnemonic in the current C-command.

        Returns:
            str: the comp mnemonic of the command.
        """
        if self.command_type() != "C_COMMAND":
            raise ValueError("comp() should only be called for C_COMMAND")

        if ';' in self.current_command:
            comp_part = self.current_command.split(';', 1)[0].strip()
        else:
            comp_part = self.current_command

        if '=' in comp_part:
            return comp_part.split('=', 1)[1].strip()
        else:
            return comp_part.strip()

    def jump(self) -> str:
        """Returns the jump mnemonic in the current C-command.

        Returns:
            str: the jump mnemonic, or "null" if no jump is present.
        """
        if self.command_type() != "C_COMMAND":
            raise ValueError("jump() should only be called for C_COMMAND")
        return self.current_command.split(';', 1)[1].strip() if ';' in self.current_command else 'null'
