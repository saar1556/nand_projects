"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import sys
import typing
from SymbolTable import SymbolTable
from Parser import Parser
from Code import Code


def first_pass(parser: Parser, symbol_table: SymbolTable) -> None:
    """Populates the symbol table with labels from the assembly code.

    Args:
        parser (Parser): the parser to read commands from.
        symbol_table (SymbolTable): the symbol table to populate.
    """    
    parser.reset()
    rom_address = 0
    while parser.has_more_commands():
        parser.advance()
        ct = parser.command_type()
        if ct == "L_COMMAND":
            symbol = parser.symbol()
            if not symbol_table.contains(symbol):
                symbol_table.add_entry(symbol, rom_address)
        else:
            rom_address += 1
    parser.reset()


FIRST_VARIABLE_ADDRESS = 16

def second_pass(parser: Parser, symbol_table: SymbolTable, output_file: typing.TextIO) -> None:

    current_variable_address = FIRST_VARIABLE_ADDRESS

    while parser.has_more_commands():
        parser.advance()
        output_command = ""
        command_type = parser.command_type()

        if command_type == "A_COMMAND":
            symbol = parser.symbol()
            if symbol.isdigit():
                output_command =  f"0{int(symbol):015b}"
            else:
                if not symbol_table.contains(symbol):
                    symbol_table.add_entry(symbol, current_variable_address)
                    current_variable_address += 1
                address = symbol_table.get_address(symbol)
                output_command = f"{address:016b}"
        elif command_type == "C_COMMAND":
            dest,comp,jump = parser.dest(),parser.comp(),parser.jump()
            output_command = (Code.comp(comp) + Code.dest(dest) + Code.jump(jump))

        if output_command != "": 
            output_file.write(output_command + "\n") 
       
    output_file.flush()

def assemble_file(
        input_file: typing.TextIO, output_file: typing.TextIO) -> None:
    """Assembles a single file.

    Args:
        input_file (typing.TextIO): the file to assemble.
        output_file (typing.TextIO): writes all output to this file.
    """

    parser = Parser(input_file)
    symbol_table = SymbolTable()
    first_pass(parser, symbol_table)
    second_pass(parser, symbol_table, output_file)


    

if "__main__" == __name__:
    # Parses the input path and calls assemble_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: Assembler <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_assemble = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
    else:
        files_to_assemble = [argument_path]
    for input_path in files_to_assemble:
        filename, extension = os.path.splitext(input_path)
        if extension.lower() != ".asm":
            continue
        output_path = filename + ".hack"
        with open(input_path, 'r') as input_file, \
                open(output_path, 'w') as output_file:
            assemble_file(input_file, output_file)
