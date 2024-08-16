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
This project started with writing a kind of compiler for a superset of this assembler. The 'assembler language' is called 'murpp' (better name needed ;) )

It contains a bunch of different programs:
- The compiler for murpp assembly. It can compile to Bonsai assembly and assemble for the Murbin VM. See more under [the MURPP language](#the-murpp-language) and [using the compiler](#using-the-compiler)
- [An interpreter for Bonsai assembly](#the-bonsai-emulator), made because Felix Selter's interpreter (or rather my fork of it) running in the browser and written in JavaScript was too slow
- [The Murbin Virtual Machine](#the-murbin-vm-also-called-murbin-standard)
- [The standard library](#the-standard-library), which can be used in MURPP programs compiled for the Murbin VM

## The MURPP language
### Using the compiler
### Special features for Murbin
#### The standard library
## The Bonsai Emulator
## The Murbin VM (Also called Murbin standard)
### The executable format
### The VM specification
### Using the virtual machine (binary-emulator)
