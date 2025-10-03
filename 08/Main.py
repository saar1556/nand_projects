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
from Parser import Parser
from CodeWriter import CodeWriter


def translate_file(
        input_file: typing.TextIO, output_file: typing.TextIO,
        bootstrap: bool) -> None:
    """Translates a single file.

    Args:
        input_file (typing.TextIO): the file to translate.
        output_file (typing.TextIO): writes all output to this file.
        bootstrap (bool): if this is True, the current file is the 
            first file we are translating.
    """
    parser = Parser(input_file)
    code_writer = CodeWriter(output_file)
    filename = input_file.name
    code_writer.set_file_name(filename)

    if bootstrap:

        # set SP to 256
        code_writer.output_stream.write("@256\n")
        code_writer.output_stream.write("D=A\n")
        code_writer.output_stream.write("@SP\n")
        code_writer.output_stream.write("M=D\n")

        # call(Sys.init)
        code_writer.write_call("Sys.init", 0)

    while parser.has_more_commands():
        parser.advance()
        command_type = parser.command_type()

        if command_type == "C_ARITHMETIC":
            command = parser.arg1()
            code_writer.write_arithmetic(command)

        elif command_type in {"C_PUSH", "C_POP"}:
            segment = parser.arg1()
            index = parser.arg2()
            code_writer.write_push_pop(command_type, segment, index)

        elif command_type == "C_LABEL":
            label = parser.arg1()
            code_writer.write_label(label)

        elif command_type == "C_GOTO":
            address = parser.arg1()
            code_writer.write_goto(address)
        
        elif command_type == "C_IF":
            address = parser.arg1()
            code_writer.write_if(address)

        elif command_type == "C_CALL":
            function_name = parser.arg1()
            n_args = parser.arg2()
            code_writer.write_call(function_name, n_args)

        elif command_type == "C_FUNCTION":
            function_name = parser.arg1()
            n_vars = parser.arg2()
            code_writer.write_function(function_name, n_vars)

        elif command_type == "C_RETURN":
            code_writer.write_return()


if "__main__" == __name__:
    # Parses the input path and calls translate_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: VMtranslator <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_translate = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
        output_path = os.path.join(argument_path, os.path.basename(
            argument_path))
    else:
        files_to_translate = [argument_path]
        output_path, extension = os.path.splitext(argument_path)
    output_path += ".asm"
    bootstrap = True
    with open(output_path, 'w') as output_file:
        for input_path in files_to_translate:
            filename, extension = os.path.splitext(input_path)
            if extension.lower() != ".vm":
                continue
            with open(input_path, 'r') as input_file:
                translate_file(input_file, output_file, bootstrap)
            bootstrap = False
