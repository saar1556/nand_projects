// This file is part of www.nand2tetris.org
// Custom test for comparison and shift operations
// File name: projects/07/7tests/testCases.tst

load testCases.asm,
output-file testCases.out,
compare-to testCases.cmp,
output-list RAM[256]%D1.6.1 RAM[257]%D1.6.1 RAM[258]%D1.6.1 
            RAM[259]%D1.6.1 RAM[260]%D1.6.1 RAM[261]%D1.6.1;

set RAM[0] 256,   // SP
set RAM[1] 300,   // LCL
set RAM[2] 400,   // ARG
set RAM[3] 3000,  // THIS
set RAM[4] 3010,  // THAT

repeat 500 {
  ticktock;
}

output;
