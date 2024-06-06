# concept
## registers
- e[0-inf] maps 0-inf
- io[0-7] maps 0-7
- s[0-7] maps 8-15
- r[0-inf] maps 16-inf

### special
- sp: s2 or e10

## stages
stage 1:
replace functions
stage 2:
compute register offsets
stage 3:
link labels

## instr
labels: you can only jump to labels

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
label 1:
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
    movF l0,{destination} {value}
    movF {value} l0
```
