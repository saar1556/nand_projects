"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import os


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    dynamic_segments = {'local':'LCL', 'argument':'ARG', 'this':'THIS', 'that':'THAT'}

    output_stream: typing.TextIO
    file_name: str
    current_function_name: str
    comp_counter: int
    call_counter: int

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        self.output_stream = output_stream
        self.file_name = None
        self.current_function_name = None
        self.comp_counter = 0
        self.call_counter = 0

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is 
        started.

        Args:
            filename (str): The name of the VM file.
        """
        self.file_name = os.path.splitext(os.path.basename(filename))[0].strip()

    def write_add_sub(self, command: str) -> str:
        """Generates Hack assembly code for the add or sub arithmetic commands.

        Args:
            command (str): 'add' or 'sub'.

        Returns:
            str: The assembly code for the command.
        """
        self.output_stream.write(f"// {command} operation\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        if command == 'add':
            self.output_stream.write("M=M+D\n")
        else:
            self.output_stream.write("M=M-D\n")

    def write_compare(self, command: str) -> str:
        """Generates Hack assembly code for comparison commands (eq, gt, lt).

        This code pops the top two values from the stack, compares them, and
        pushes -1 (true) or 0 (false) back onto the stack. It uses a unique 
        label to handle the branching logic.

        Args:
            command (str): 'eq', 'gt', or 'lt'.

        Returns:
            str: The assembly code for the command.
        """
        if command == 'eq':
            jump = 'JEQ'
        elif command == 'gt':
            jump = 'JGT'
        else: # command == 'lt'
            jump = 'JLT'
        self.output_stream.write(f"// {command} operation\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        self.output_stream.write("D=M-D\n")
        self.output_stream.write(f"@{command.upper()}_{self.comp_counter}\n")
        self.output_stream.write(f"D;{jump}\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        self.output_stream.write("M=0\n")
        self.output_stream.write(f"@{command.upper()}_{self.comp_counter}_END\n")
        self.output_stream.write("0;JMP\n")
        self.output_stream.write(f"({command.upper()}_{self.comp_counter})\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        self.output_stream.write("M=-1\n")
        self.output_stream.write(f"({command.upper()}_{self.comp_counter}_END)\n")
        
        self.comp_counter += 1

    def write_and_or(self, command: str) -> str:
        """Generates Hack assembly code for the bitwise and or or commands.

        Args:
            command (str): 'and' or 'or'.

        Returns:
            str: The assembly code for the command.
        """
        self.output_stream.write(f"// {command} operation\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        if command == 'and':
            self.output_stream.write("M=M&D\n")
        else:
            self.output_stream.write("M=M|D\n")

    def write_not_neg_shift(self, command: str) -> str:
        """Generates Hack assembly code for the unary not or neg commands.

        Args:
            command (str): 'not' or 'neg'.

        Returns:
            str: The assembly code for the command.
        """
        
        self.output_stream.write(f"// {command} operation\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M-1\n")
        if command == 'not':
            self.output_stream.write("M=!M\n")
        elif command == 'neg':
            self.output_stream.write("M=-M\n")
        elif command == 'shiftleft':
            self.output_stream.write("M=M<<\n")
        else: # command == 'shiftright'
            self.output_stream.write("M=M>>\n")


    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given 
        arithmetic command. For the commands eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        if command in {'not', 'neg', 'shiftleft', 'shiftright'}:
            self.write_not_neg_shift(command)
        elif command in {'add', 'sub'}:
            self.write_add_sub(command)
        elif command in {'eq', 'gt', 'lt'}:
            self.write_compare(command)
        elif command in {'and', 'or'}:
            self.write_and_or(command)
        else:
            raise ValueError(f"Invalid arithmetic command: {command}\n")
        
    def write_push(self, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the push command.

        It calculates the memory address based on the segment and index and 
        pushes the value at that address onto the stack.

        Args:
            segment (str): the memory segment to push from.
            index (int): the index in the memory segment.
        """
        self.output_stream.write("// push operation\n")
        if segment == 'constant':
            self.output_stream.write(f"@{index}\n")
            self.output_stream.write("D=A\n")

        elif segment == 'static':
            self.output_stream.write(f"@{self.file_name}.{index}\n")
            self.output_stream.write("D=M\n")

        elif segment in self.dynamic_segments:
            self.output_stream.write(f"@{self.dynamic_segments[segment]}\n")
            self.output_stream.write("D=M\n")
            self.output_stream.write(f"@{index}\n")
            self.output_stream.write("A=D+A\n")
            self.output_stream.write("D=M\n")

        elif segment == 'pointer':
            # pointer 0 -> THIS (RAM[3]), pointer 1 -> THAT (RAM[4])
            self.output_stream.write(f"@{3 + index}\n")
            self.output_stream.write("D=M\n")
        
        elif segment == 'temp':
            self.output_stream.write(f"@{5 + index}\n")
            self.output_stream.write("D=M\n")

        else:
            raise ValueError(f"Invalid segment '{segment}' in push command")
        
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M\n")
        self.output_stream.write("M=D\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("M=M+1\n")

    
    def write_pop(self, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the pop command.

        It pops a value from the stack and stores it at the memory address 
        determined by the segment and index.

        Args:
            segment (str): the memory segment to pop to.
            index (int): the index in the memory segment.
        """
        self.output_stream.write("// pop operation\n")
        if segment == 'static':
            self.output_stream.write(f"@{self.file_name}.{index}\n")
            self.output_stream.write("D=A\n")

        elif segment in self.dynamic_segments:
            self.output_stream.write(f"@{self.dynamic_segments[segment]}\n")
            self.output_stream.write("D=M\n")
            self.output_stream.write(f"@{index}\n")
            self.output_stream.write("D=D+A\n")

        elif segment == 'pointer':
            self.output_stream.write(f"@{3 + index}\n")
            self.output_stream.write("D=A\n")
        
        elif segment == 'temp':
            self.output_stream.write(f"@{5 + index}\n")
            self.output_stream.write("D=A\n")

        else:
            raise ValueError(f"Invalid segment '{segment}' in pop command")

        # Store target address in R13:
        self.output_stream.write("@R13\n")
        self.output_stream.write("M=D\n")

        # Pop stack into D:
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")

        # Write D into *R13:
        self.output_stream.write("@R13\n")
        self.output_stream.write("A=M\n")
        self.output_stream.write("M=D\n")


    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given 
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        if command == "C_PUSH":
            self.write_push(segment, index)
        elif command == "C_POP":
            self.write_pop(segment, index)
        else:
            raise ValueError(f"Invalid command: {command}. Expected 'C_PUSH' or 'C_POP'.")

    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command. 
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        if self.current_function_name:
            self.output_stream.write(f"({self.current_function_name}${label})\n")
        else:
            self.output_stream.write(f"({self.file_name}${label})\n")
    

    ###### what if not self.current_function_name??? ######
    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        self.output_stream.write("// goto operation\n")
        if self.current_function_name:
            perfix = self.current_function_name
        else:
            perfix = self.file_name
        self.output_stream.write(f"@{perfix}${label}\n")
        self.output_stream.write("0;JMP\n")
    
    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command. 

        Args:
            label (str): the label to go to.
        """
        self.output_stream.write("// if-goto operation\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")
        if self.current_function_name:
            perfix = self.current_function_name
        else:
            perfix = self.file_name
        self.output_stream.write(f"@{perfix}${label}\n")
        self.output_stream.write("D;JNE\n")
    
    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command. 
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this 
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        self.current_function_name = function_name

        # (function_name)
        self.output_stream.write(f"({function_name})\n")

        # push constant 0 n_vars times
        for _ in range(n_vars):
            self.write_push("constant", 0)
    
    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command. 
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's 
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        self.output_stream.write("// call operation\n")

         # push return_address
        self.output_stream.write("// push return_address\n")
        self.output_stream.write(f"@{function_name}$ret.{self.call_counter}\n")
        self.output_stream.write("D=A\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("A=M\n")
        self.output_stream.write("M=D\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("M=M+1\n")

        # push LCL, ARG, THIS, THAT
        self.output_stream.write("// push LCL, ARG, THIS, THAT\n")
        for arg in ["LCL", "ARG", "THIS", "THAT"]:
            self.output_stream.write(f"@{arg}\n")
            self.output_stream.write("D=M\n")
            self.output_stream.write("@SP\n")
            self.output_stream.write("A=M\n")
            self.output_stream.write("M=D\n")
            self.output_stream.write("@SP\n")
            self.output_stream.write("M=M+1\n")

        # ARG = SP-5-n_args
        self.output_stream.write("// ARG = SP-5-n_args\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write(f"@{n_args+5}\n")
        self.output_stream.write("D=D-A\n")
        self.output_stream.write("@ARG\n")
        self.output_stream.write("M=D\n")

        # LCL = SP
        self.output_stream.write("// LCL = SP\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@LCL\n")
        self.output_stream.write("M=D\n")

        # goto function_name
        self.output_stream.write("// goto function_name\n")
        self.output_stream.write(f"@{function_name}\n")
        self.output_stream.write("0;JMP\n")

        # (return_address)
        self.output_stream.write(f"({function_name}$ret.{self.call_counter})\n")

        self.call_counter += 1
        return
    
    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        self.output_stream.write("// return operation\n")
        
        # frame = LCL 
        self.output_stream.write("// frame = LCL\n")
        self.output_stream.write("@LCL\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@R13\n") 
        self.output_stream.write("M=D\n")
        
        # return_address = *(frame-5)
        self.output_stream.write("// return_address = *(frame-5)\n")
        self.output_stream.write("@R13\n") 
        self.output_stream.write("D=M\n")
        self.output_stream.write("@5\n")
        self.output_stream.write("A=D-A\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@R14\n")
        self.output_stream.write("M=D\n")

        # *ARG = pop()
        self.output_stream.write("// *ARG = pop()\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("AM=M-1\n")
        self.output_stream.write("D=M\n")
        self.output_stream.write("@ARG\n")
        self.output_stream.write("A=M\n")
        self.output_stream.write("M=D\n")

        # SP = ARG + 1
        self.output_stream.write("// SP = ARG + 1\n")
        self.output_stream.write("@ARG\n")
        self.output_stream.write("D=M+1\n")
        self.output_stream.write("@SP\n")
        self.output_stream.write("M=D\n")

        # THAT = *(frame-1), THIS = *(frame-2), ARG = *(frame-3), LCL = *(frame-4)
        self.output_stream.write("// THAT = *(frame-1), THIS = *(frame-2), ARG = *(frame-3), LCL = *(frame-4)\n")
        for address, val in [("THAT",1), ("THIS",2), ("ARG",3), ("LCL",4)]:
            self.output_stream.write("@R13\n")
            self.output_stream.write("D=M\n")
            self.output_stream.write(f"@{val}\n")
            self.output_stream.write("A=D-A\n")
            self.output_stream.write("D=M\n")
            self.output_stream.write(f"@{address}\n")
            self.output_stream.write("M=D\n")

        # goto return_address
        self.output_stream.write("// goto return_address\n")
        self.output_stream.write("@R14\n")
        self.output_stream.write("A=M\n")
        self.output_stream.write("0;JMP\n")
