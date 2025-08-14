"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""


class Code:
    """Translates Hack assembly language mnemonics into binary codes."""
    dest_mnemonics = {
        'null': '000',
        'M': '001',
        'D': '010',
        'MD': '011',
        'A': '100',
        'AM': '101',
        'AD': '110',
        'AMD': '111'
    }

    comp_mnemonics = {
        '0': '1110101010',
        '1': '1110111111',
        '-1': '1110111010',
        'D': '1110001100',
        'A': '1110110000', 
        'M': '1111110000',
        '!D': '1110001101',
        '!A': '1110110001',
        '!M': '1111110001',
        '-D': '1110001111',
        '-A': '1110110011',
        '-M': '1111110011',
        'D+1': '1110011111',
        'A+1': '1110110111',
        'M+1': '1111110111',
        'D-1': '1110001110',
        'A-1': '1110110010',
        'M-1': '1111110010',
        'D+A': '1110000010',
        'D+M': '1111000010',
        'D-A': '1110010011',
        'D-M': '1111010011',
        'A-D': '1110000111',
        'M-D': '1111000111',
        'D&A': '1110000000',
        'D&M': '1111000000',
        'D|A': '1110010101',
        'D|M': '1111010101',
        'A<<': '1010100000', 
        'D<<': '1010110000', 
        'M<<': '1011100000',
        'A>>': '1010000000',
        'D>>': '1010010000',
        'M>>': '1011000000'
    }

    jump_mnemonics = {
        'null': '000',
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLT': '100',
        'JNE': '101',
        'JLE': '110',
        'JMP': '111'
    }
    
    @staticmethod
    def dest(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a dest mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        if mnemonic not in Code.dest_mnemonics:
            raise ValueError(f"Invalid dest mnemonic: {mnemonic}")
        return Code.dest_mnemonics[mnemonic]

    @staticmethod
    def comp(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a comp mnemonic string.

        Returns:
            str: the binary code of the given mnemonic.
        """
        if mnemonic not in Code.comp_mnemonics:
            raise ValueError(f"Invalid comp mnemonic: {mnemonic}")
        return Code.comp_mnemonics[mnemonic]

    @staticmethod
    def jump(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a jump mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        if mnemonic not in Code.jump_mnemonics:
            raise ValueError(f"Invalid jump mnemonic: {mnemonic}")
        return Code.jump_mnemonics[mnemonic]
