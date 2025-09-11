"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
'''import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    class Symbol:
        name: str
        type: str
        kind: str
        index: int
        
        def __init__(self,name:str ,type: str, kind: str, index: int) -> None:
            self.name = name    
            self.type = type
            self.kind = kind
            self.index = index

    class_scope: typing.Dict[str, Symbol]
    function_scope: typing.Dict[str, Symbol]
    segments_lengths: typing.Dict[str, int] = {
        "STATIC": 0,
        "FIELD": 0,
        "ARG": 0,
        "VAR": 0,
    }

    def __init__(self) -> None:
        """Creates a new empty symbol function_scope."""
        self.class_scope = {}
        self.function_scope = {}

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol function_scope).
        """
        self.function_scope = {}
        self.segments_lengths["ARG"] = 0
        self.segments_lengths["VAR"] = 0

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        if kind not in self.segments_lengths:
            raise ValueError(f"Invalid kind: {kind}")
        
        index = self.segments_lengths[kind]
        self.segments_lengths[kind] += 1

        symbol = self.Symbol(name, type, kind, index)
        if kind in ("STATIC", "FIELD"):
            self.class_scope[name] = symbol
        else:
            self.function_scope[name] = symbol



    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        if kind not in self.segments_lengths:
            raise ValueError(f"Invalid kind: {kind}")
        return self.segments_lengths[kind]

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        if name in self.function_scope:
            return self.function_scope[name].kind
        elif name in self.class_scope:
            return self.class_scope[name].kind
        else:
            return None

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        if name in self.function_scope:
            return self.function_scope[name].type
        elif name in self.class_scope:
            return self.class_scope[name].type
        else:
            return None

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        if name in self.function_scope:
            return self.function_scope[name].index
        elif name in self.class_scope:
            return self.class_scope[name].index
        else:
            return None

