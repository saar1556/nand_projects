"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class VMWriter:
    """
    Writes VM commands into a file. Encapsulates the VM command syntax.
    """

    SEGMENTS = {
       "CONST": "constant",
        "ARG": "argument",
        "LOCAL": "local",
        "STATIC": "static",
        "THIS": "this",
        "THAT": "that",
        "POINTER": "pointer",
        "TEMP": "temp"
    }

    ARITHMETICS = {
        "ADD": "add",
        "SUB": "sub",
        "NEG": "neg",
        "EQ": "eq",
        "GT": "gt",
        "LT": "lt",
        "AND": "and",
        "OR": "or",
        "NOT": "not",
        "SHIFTLEFT": "shiftleft",
        "SHIFTRIGHT": "shiftright"
    }

    kind_to_segment = {
        "STATIC": "STATIC",
        "FIELD": "THIS",
        "ARG": "ARG",
        "VAR": "LOCAL"
    }

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Creates a new file and prepares it for writing VM commands."""
        self.output = output_stream


    def translate_segment(self, ttype: str) -> str:
        if ttype in self.kind_to_segment:
            return self.kind_to_segment[ttype]
        return ttype

    
    def write_push(self, segment: str, index: int) -> None:
        """Writes a VM push command.

        Args:
            segment (str): the segment to push to, can be "CONST", "ARG", 
            "LOCAL", "STATIC", "THIS", "THAT", "POINTER", "TEMP"
            index (int): the index to push to.
        """
        segment=self.translate_segment(segment)
        if segment not in self.SEGMENTS :
            raise ValueError(f"Invalid segment: {segment}")

        self.output.write(f"push {self.SEGMENTS[segment]} {index}\n")

    
    def write_pop(self, segment: str, index: int) -> None:
        """Writes a VM pop command.

        Args:
            segment (str): the segment to pop from, can be "CONST", "ARG", 
            "LOCAL", "STATIC", "THIS", "THAT", "POINTER", "TEMP".
            index (int): the index to pop from.
        """
        segment=self.translate_segment(segment)

        if segment not in self.SEGMENTS :
            raise ValueError(f"Invalid segment: {segment}")

        self.output.write(f"pop {self.SEGMENTS[segment]} {index}\n")

    
    def write_arithmetic(self, command: str) -> None:
        """Writes a VM arithmetic command.

        Args:
            command (str): the command to write, can be "ADD", "SUB", "NEG", 
            "EQ", "GT", "LT", "AND", "OR", "NOT", "SHIFTLEFT", "SHIFTRIGHT".
        """
        if command not in self.ARITHMETICS:
            raise ValueError(f"Invalid arithmetic command: {command}")
        
        self.output.write(f"{self.ARITHMETICS[command]}\n")

    
    def write_label(self, label: str) -> None:
        """Writes a VM label command.

        Args:
            label (str): the label to write.
        """
        self.output.write(f"label {label}\n")
        

    def write_goto(self, label: str) -> None:
        """Writes a VM goto command.

        Args:
            label (str): the label to go to.
        """
        self.output.write(f"goto {label}\n")

    
    def write_if(self, label: str) -> None:
        """Writes a VM if-goto command.

        Args:
            label (str): the label to go to.
        """
        self.output.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int) -> None:
        """Writes a VM call command.

        Args:
            name (str): the name of the function to call.
            n_args (int): the number of arguments the function receives.
        """
        self.output.write(f"call {name} {n_args}\n")

    
    def write_function(self, name: str, n_locals: int) -> None:
        """Writes a VM function command.

        Args:
            name (str): the name of the function.
            n_locals (int): the number of local variables the function uses.
        """
        self.output.write(f"function {name} {n_locals}\n")

    def write_return(self) -> None:
        """Writes a VM return command."""
        self.output.write(f"return\n")
