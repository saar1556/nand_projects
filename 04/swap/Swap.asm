// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

// Pseudo code:
// set min, max
// for i = 1 to R15
//     if array[i] < min
//         min = i
//     if array[i] > max
//         max = i

// put arr[min] in temp
// put arr[max] in arr[min]
// put temp in arr[max]

// Put your code here.
@R14
D=M
@min
M=D
@max
M=D

A=D
D=M
@min_val
M=D
@max_val
M=D

@i
M=0

(LOOP)
    // Check if i == R15
    @R15
    D=M

    @i
    D=D-M

    @SWAP
    D;JEQ

    // load the value of the current element
    @R14
    D=M
    @i
    A=M+D
    D=M

    // check minumum
    @min_val
    D=D-M

    @SET_MIN
    D;JLE

    // load the value of the current element
    @R14
    D=M
    @i
    A=M+D
    D=M

    // check maximum
    @max_val
    D=D-M

    @SET_MAX
    D;JGE

    // increment i and loop
    @i
    M=M+1

    @LOOP
    0;JMP

(SET_MIN)
    // load the address of the current element
    @R14
    D=M
    @i
    D=D+M
    
    // save the new min index
    @min
    M=D

    // save the new min value
    A=D
    D=M

    @min_val
    M=D

    // increment i and loop
    @i
    M=M+1

    @LOOP
    0;JMP

(SET_MAX)
    // load the address of the current element
    @R14
    D=M
    @i
    D=D+M

    // save the new max index
    @max
    M=D

    // save the new max value
    A=D
    D=M

    @max_val
    M=D

    // increment i and loop
    @i
    M=M+1

    @LOOP
    0;JMP

(SWAP)
    // load min_val into temp
    @min_val
    D=M
    @temp
    M=D

    // load max_val into min cell
    @max_val
    D=M
    @min
    A=M
    M=D

    // load temp into max cell
    @temp
    D=M
    @max
    A=M
    M=D

    @END
    0;JMP

(END)
    @END
    0;JMP