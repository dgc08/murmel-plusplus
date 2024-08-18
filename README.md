# Murmel++ — A toolchain for the Bonsai Computer and the Murbin VM
This project is a collection of programs I've built while experimenting with the Bonsai Computer (more about that in the introduction). This is also the repository for my 'Murbin VM', which is based on the Bonsai architecture.

## Introduction
This project started out as a way to simpler write programs for the Bonsai Computer (or Murmel Computer, as it has the same instruction set). The Bonsai Computer is an educational computer architecture based on the [Paper Computer model from the 1980s](https://en.wikipedia.org/wiki/WDR_paper_computer) created by Klaus Merkert for Computer Science classes. You find the resources on the Bonsai Computer and Murmel Computer, which is a kind of 'role play' simplification of the Bonsai architecture, at [the original source](https://inf-schule.de/rechner/bonsai/murmelrechner) (German).

There is also a real hardware version of the Bonsai Computer, which you can theoretically build yourself. More information on that [here](https://github.com/michAtEl/Bonsai-Modellcomputer) (German).

Also check out [my fork](https://github.com/dgc08/MurmelRechner) of a simulator for the Murmel Computer, originally created by [Felix Selter](https://github.com/FelixSelter/MurmelRechner). There were some issues with the original version, which I tried to fix.

The Bonsai architecture has a set of four or five instructions:

- `inc` Increment the value at the given address
- `dec` Decrement the value at the given address
- `jmp` Jump to the given address in the code/memory (depending on if the code and memory lie in the same space)
- `tst` Check the value at the given address: if it's zero, skip the next instruction
- `hlt` Stop the execution

The Bonsai computer (and also the Murbin VM) are von Neumann machines, so the code and the writable memory lie in the same memory/address space. On the Murmel computer, both are separated for simplicity.

The memory usually starts at 0, each address can store an unsigned number. If these 'cells' have a limit or if memory addresses must be initialized before running the program, depends on the interpreter/emulator. 

This architecture is Turing complete, so you can write anything for it, for example a small program adding the numbers in address 0 and 1 together:

```
tst 1
jmp 3
jmp 6
dec 1
inc 0
jmp 0
hlt
```

## About this project
This project started with writing a kind of compiler for a superset of this assembler. The 'assembler language' is called 'MURPP' (better name needed ;) )

It contains a bunch of different programs:
- The compiler for MURPP assembly. It can compile to Bonsai assembly and assemble for the Murbin VM. See more under [the MURPP language](#the-murpp-language) and [using the compiler](#using-the-compiler)
- [An interpreter for Bonsai assembly](#the-bonsai-emulator), made because Felix Selter's interpreter (or rather my fork of it) running in the browser and written in JavaScript was too slow
- [The Murbin Virtual Machine](#the-murbin-vm-also-called-murbin-standard)
- [The Murbin standard library](#the-standard-library), which can be used in MURPP programs compiled for the Murbin VM

## The MURPP language
MURPP is a superset of the Bonsai assembly (see in the [Introduction](#introduction)). It aims to abstract some simple things, so you can write in a assembly-like language, don't have to calculate offset in your head and use more than 4 instructions.

It's key features are:
- Labels to make jumps easier and denote data locations in Murbin
- Higher-level instructions like `mov` or `add`, which get replaced with their Bonsai implementations during compilation
- Utilization of certain addresses as registers (for example `r0`)
- Macros, which behave like C-style `#define` function macros, but with multiple lines

If you compile for Murbin, you have additional features like functions with a callstack. These are not possible if you have an interpreter for Bonsai Assembly [like this one](https://github.com/dgc08/MurmelRechner) because memory and executable code are seperated. More about that under [Special features for Murbin](#special-features-for-murbin)

### Instructions
An instruction can take up to arguments, sometimes these arguments can be comma-seperated lists. In that case, the signature shows this by showing `[]` around the argument. 
Sometimes, arguments are optional, which will be marked by `()` around the argument.

You can look up the implentation of each instruction in Bonsai assembly in the source code, however some instructions, especially the ones taking lists as arguments, have more dynamically gernerated assembly. The implmentations of the instructions are marked by the comment `### View instruction implementations down here`

It is important to note that all instructions except `cpy` clear the source register (for example `mov` clears the source, `mul` cleasr the multiplicand etc.)

As MURPP is a superset of Bonsai assembly, the four/five basic Bonsai assembly instructions still work. `jmp` is still as important, `inc` and `dec` are still used sometimes.
`tst` however is often unclear, so you should always use `jz` and `jnz`.

#### 'mov'
`mov [destination] source`

Moves the value if the `source` address to the destination addresses. The `source` address will be zero afterwards, if you want to copy the value, use `cpy` instead.

Example:
`mov r1,r2,r3 r0`
Moves the value of r0 into the registers r1, r2 and r3.

You can also provide a immediate value.

Example:
`mov r0 #4`
This is equivalent to
```
movz r0
inc r0
inc r0
inc r0
inc r0
```

 
> NOTE: If you are writing code for murbin, consider using a data section / global or local variable which is initialized with the immediate instead; as this is more space- and time efficient.

#### 'movz'
`movz [adresses]`

Equivalent to `mov [addresses] #0`

#### 'jz' and 'jnz'
`jz condition location`

`jnz condition location`

`jz` and `jnz` is the primary way to abstract the confusing `tst`-instruction.

#### 'add'
`add [summand1/destinations] summand2`

Note that `add` works exactly the same as `mov`, with the only difference that the destination registers aren't cleared beforehand. So if you know the destination of a `mov`-instruction is empty, you can use `add` instead to save a few processor cycles.

Example:
`add r0 r1` -> r0 = r0 + r1; r1 = 0
#### 'sub'
`sub minuend/destination subtrahend`

Example:
`sub r0 r1` -> r0 = r0 - r1; r1 = 0

If the result of the subtraction produces a negative number, the `s5` register will be set to 1
For example, if `r0` is 3 and `r1` is 5, `r0` would end up being 3 and `s5` will be set to 1.

#### 'mul' and 'div'

> NOTE: When using murbin, consider using the math.mul and math.div functions from std.math, as they are both really instruction heavy and a lot of time is saved by calling them as a function. Additionally, the implementation for `div` in std.math is about ~2x faster than the implementation of the `div` instruction, as it doesn't need to be compact.

`mul/div destination arg1 arg2`

The remainder of the division is stored in the `s5` register.

> Attention: The output register can't be one of the arguments! There will be no warning if you reuse an argument as destination, your code will just not work.

Example:

```
mov r0 #11
mov r1 #2
div r2 r0 r1 ;; r2 = r0 / r1, remainder is stored in s5 
```

#### 'cpy'
`cpy [destinations] source (temporaryRegister)`

Copies the value in `source` to the provided destination addresses.

`temporaryRegister` will be `s0` by default.

The usage is identical to the usage of `mov`

#### 'push' and 'pop'
Although the stack is available for Bonsai assembly mode, it is recommeded to only use it on the Murbin VM. 

Stack operations use pointers in the sense of `inc *s7`, which effectively no Bonsai assembler interpreter does, as it isn't even really a part of the assembly.

Keep in mind that if you are not writing code for Murbin, the stack pointer is set to point to r8, which means you can only go to r7 in that case. On Murbin, the stack pointer gets set after the compilation process. More about that in [TODO].

`push source`

Increments the stack pointer and moves the value onto the stack. If the standard library is not used, a stack overflow check is performed.

`pop destination`

Pops the top element from the stack into the specified destination. If no destination is provided, the top element is just removed and the stack pointer is decremented.

#### 'cmp'
`cmp adress1 adress2`

Compares the values in adress1 and adress2. Sets s4 to 0 if they are equal, 1 if adress1 is greater, and 2 if adress2 is greater.

Example:

```
cmp r0 r1
```

If r0 == r1, s4 = 0
If r0 > r1,  s4 = 1
If r0 < r1,  s4 = 2

This instruction works great in combination with `case`:

```
cmp r0 r1
case s4 equal,firstbigger,secondbigger

equal:         ;; s4 == 0
    ;; if they are equal
firstbigger:   ;; s4 == 1 
    ;; if r0 is bigger
secondbigger:  ;; s4 == 2
    ;; if r1 is bigger
```

#### 'int'
int (code) (address)

Sets the specified address to the specified code and blocks the execution until the value at the specified address is set to zero. This is usually used to await input from the user. The default code is 1, the default address is `e6`

#### 'case'
`case register [labels] (defaultLabel)`

A kind of decoder. If the address's value matches the index of one of the labels, it jumps to that label. If the value doesn't match any label, it jumps to the default label, if provided.

Look to the documentation of `cmp` for an example.

### Labels, Registers and Addresses
### Macros, includes and scopes
### Special features for Murbin
#### The standard library
### Using the compiler
## The Bonsai Emulator
## The Murbin VM (Also called Murbin standard)
### The executable format
### The VM specification
### Using the virtual machine (binary-emulator)
