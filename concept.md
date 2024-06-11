# concept
Ignore this that is is kind of scratchpaper and outdated look at readme

murbin ret code:
0 - all fine
1 - general error
2 - segfault kind of error
3 - arithmetic error (div by 0)

mem layout
0 - esp
1 - before run adress of e0, then temp
2 - temp

3 - activate output (set to 1 by program, set back to 0 if read by OS/emulator)
4 - output (char)

5 - activate input (set to 1 by emulator)
6 - input (char)

## registers
- e[0-inf] maps 0-inf
- io[0-7] maps 0-7
- s[0-7] maps 8-15
- r[0-inf] maps 16-inf

## instr
labels: you can only jump to labels

movzf: zeros a register

jizF condition(register) address: jump if address is zero
```
    tst {condition}
    jmp label
    jmp {address}
label:
```

movF *destination value(register|immediate):    add value to other register (value register will be empty afterwards)
if register
```
label1:
    tst {value}
    jmp label2
    jmp label3
label2:
    dec {value}
    inc {destination}
    jmp label1
label3:
```

cpyF *destination value(register):              fucntion: copy value to other register (2x time of movF)
```
    movF s0,{destination} {value}
    movF {value} s0
```
