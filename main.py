#!/usr/bin/env python3

import argparse
import re

from sys import argv
from os import path
from pathlib import Path

parser = argparse.ArgumentParser(description='Compiler for murmel++ assembly')

parser.add_argument("input", type=str)
parser.add_argument('-I', '--include', action='append', help='Extra include path to search for included files')
parser.add_argument("-o", "--output", type=str, default="out.mur")
parser.add_argument("-a", "--jump_address", type=int, default=0, help="Address of the first instruction. Default: 0")
parser.add_argument("--instr_size", type=int, default=1, help="How many 'lines' one instruction takes. Default: 1")
parser.add_argument("-r", "--register_address", type=int, default=0, help="Address of the first register. Default: 0")
parser.add_argument("-sz", "--stack_size", type=int, default=128, help="Size of the stack. Default: 128")
parser.add_argument("-hz", "--heap_size", type=int, default=256, help="Size of the extra memory on top. Default: 256")
#parser.add_argument("-nl", "--no_stdlib", action="store_true")
parser.add_argument("-lib", "--use_stdlib", action="store_true", help="Use stdlib (std.main) with stack protector and extra features")

parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("--assemble", action="store_true", help="Assemble the program with the murbin standart. Overwrites instr_size and jump_address")

args = parser.parse_args()

args.no_stdlib = not args.use_stdlib

if not args.include:
    args.include = {}
args.include = set(args.include).union({path.dirname(path.abspath(__file__)) + "/include"})

if args.assemble:
    args.jump_address = 8

entry_point = 0
meminit = []

max_addr = 0

global_offset = args.register_address

s_offset = 8
r_offset = 16
io_offset = 0
e_offset = 0
data_offset = 0

if args.assemble:
    sp_address = "7"
else:
    sp_address = "s7"

def repl_registers(text):
    global max_addr
    def match(pattern, letter, offset, text):
        global max_addr
        #print(pattern, text, end=" ")
        matches = re.findall(pattern, text)
        #print(matches)
        for i in matches:
            num = int(i.replace(letter, "")) + offset
            max_addr = max(max_addr, num)
            text = text.replace(i, str(num))
        return text

    text = text.replace("s7", sp_address)
    # general purpose
    text = match(r"r\d+", "r", r_offset+global_offset, text)
    # s
    text = match(r"s\d+", "s", s_offset+global_offset, text)
    # io
    text = match(r"io\d+", "io", io_offset+global_offset, text)
    # e
    text = match(r"e\d+", "e", e_offset+global_offset, text)
    # data
    text = match(r"d\d+", "d", data_offset, text)


    # 1+1
    matches = re.findall(r'(\d+)\+(\d+)', text)
    
    for match in matches:
        sum_result = str(int(match[0]) + int(match[1]))
        text = re.sub(r'\b' + re.escape('+'.join(match)) + r'\b', sum_result, text)

    return text

def load_file(filename):
    with open(filename) as f:
        lines = f.readlines()
        if lines[0].strip() == ";!MURBIN" and not args.assemble:
            print ("\033[91mThe file", filename, "is designed to run under the murbin standart, you are however not assembling for murbin.\nBe careful, things may break.\n\033[0m")
        lines = [line.split(";")[0].strip() for line in lines if line.split(";")[0].strip() != ""]
        lines = '\n'.join(lines)

        if re.search(r'\n\s*push', lines) and not args.assemble:
            repl_registers(lines)
            repl_registers("r7") # Make sure the stack starts at minimum r7
            lines = "mov s7 #" + str(max_addr+1) + "\n" + lines
        lines = lines.split("\n")

    # Stage 0: Parse, remove comments
    code = []
    for line in lines:
        if " 0L" in line or line.startswith("0L"):
            print(line, ": The prefix '0L' is reserved")
            exit(1)

        instr = line.split()
        if instr and instr != [] and instr != [""]:
            code.append(instr)
    return code

def find_path(path):
    for directory in args.include:
        potential_path = Path(directory) / path
        if potential_path.exists():
            return potential_path
    print("Path not found")
    exit(1)

def immediate_to_array(immediate):
    val = eval(immediate)
    arr = []

    if type(val) == int:
        arr.append(str(val))
    if type(val) == str:
        if len(val) > 1:
            val += "\0"
        for char in val:
            arr.append(str(ord(char)))
    return arr

def compile():
    code = load_file(args.input)
    if args.verbose:
        print ("Read code", code, "\n\n")

    if args.no_stdlib:
        pass
    else:
        code.insert(0, ["include", "std.main"])

    # Stage 1
    i = 0
    builtin_labels = 0
    scope = 0
    macros = {}
    included = []
    while i < len(code):
        if code[i] == []:
            i += 1
            continue
        code[i] = [s.replace("l.", f"0L{str(scope)}L.") for s in code[i]]

        ####
        if code[i][0].lower() == "scope":
            scope += 1
            del code[i]
            continue
        ###
        elif code[i][0].lower() == "include":
            path = " ".join(code[i][1:]).replace(".", "/") + ".murpp"
            path = find_path(path)
            if path in included:
                del code[i]
            else:
                included.append(path)
                code[i:i+1] = load_file(path)
            continue
        ###
        elif code[i][0].lower() == "defmacro":
            macro_name = code[i][1].replace(":", "")
            try:
                macro_args = code[i][2].strip()[:-1].split(",") # take the ":" at end out ("defmacro hello arg,arg2:")
            except IndexError:
                macro_args = ["0"]
            macro_code = []

            orig_i = i
            i += 1
            while code[i][0].lower() != "macro_end":
                macro_code.append(code[i])
                i += 1
                if i == len(code):
                    print("Missing 'macro_end")
                    exit(1)


            macros[macro_name] = (macro_args, macro_code)

            del code[orig_i:i+1]
            i = orig_i
            continue
        ###
        elif code[i][0].lower() == "putmacro":
            macro_name = code[i][1]
            try:
                macro_args = code[i][2].strip().split(",")
            except IndexError:
                macro_args = ["0"]

            macro_code = macros[macro_name][1]
            code_repl = []


            for arg_num, repl in enumerate(macros[macro_name][0]):
                for line in macro_code:
                    if arg_num == 0:
                        code_repl.append([ele.replace(repl, macro_args[0]).replace("l.", f"0L{str(builtin_labels)}L.") for ele in line])
                    else:
                        code_repl.append([ele.replace(repl, macro_args[arg_num]) for ele in line])

            code[i:i+1] = code_repl
            continue

        ###
        elif code[i][0].lower() == "mov" and code[i][2][0] == "#":
            max_label = -1
            asm = "{movzs}\n{incs}"
            form = {"incs":""}

            found = False
            for dest in code[i][1].split(","):
                found = True
                form["movzs"] = form.get("movzs", "") + f"movz {dest}\n"
                expr = eval(" ".join(code[i][2:])[1:])
                if type(expr) == int:
                    for inc in range(expr):
                        form["incs"] = form.get("incs", "") + f"inc {dest}\n"
                if type(expr) == str:
                    # if len(expr) < 1:
                    #     form["incs"] = form.get("incs", "") + f"movz {dest}\n"
                    # if len(expr) > 1:
                    if len(expr) > 1:
                        expr += "\0"
                    for j, char in enumerate(expr):
                        form["incs"] = form.get("incs", "") + f"mov {dest}+{j} #"+ str(ord(char)) + "\n"
                    # elif len(expr) == 1:
                    #     form["incs"] = form.get("incs", "") + f"mov {dest} #"+ str(ord(expr)) + "\n"

            if not found:
                print("Wrong number of argumentss:", " ".join(code[i]))
                exit(1)


        ###
        elif code[i][0].lower() == "movz":
            if "," in code[i][1]:
                code[i][0] = "mov"
                if len(code[i]) > 2:
                    code[i][2] = "#0"
                else:
                    code[i].append("#0")
                continue

            max_label = 2
            asm = """\
{label0}:
    tst {value}
    jmp {label1}
    jmp {label2}
{label1}:
    dec {value}
    jmp {label0}
{label2}:"""
            form = {"value": code[i][1]}

        ###
        elif code[i][0].lower() == "mov" and code[i][2][0] != "#":
            max_label = 2
            asm = """\
{movzs}
{label0}:
    tst {value}
    jmp {label1}
    jmp {label2}
{label1}:
    dec {value}
    {incs}    jmp {label0}
{label2}:"""
            form = {"value": code[i][2]}

            found = False
            for dest in code[i][1].split(","):
                found = True
                form["incs"] = form.get("incs", "") + f"inc {dest}\n"
                form["movzs"] = form.get("movzs", "") + f"movz {dest}\n"

            if not found:
                print("Wrong number of argumentss:", " ".join(code[i]))
                exit(1)
        ###
        elif code[i][0].lower() == "push":
            max_label = -1
            if not args.no_stdlib:
                extra = "\njnz h0 STD.stack_overflown"
            else:
                extra = ""
            asm = """\
inc s7
mov *s7 {value}{extra}
"""
            form = {"value": code[i][1], "extra": extra}

        ###
        elif code[i][0].lower() == "pop" and len(code[i]) > 1:
            max_label = -1
            asm = """\
mov {value} *s7
dec s7
"""
            form = {"value": code[i][1]}

        ###
        elif code[i][0].lower() == "call" and len(code[i]) > 1:
            max_label = 0
            asm = """\
cpy s1 ${label0}
push s1
jmp {func}
${label0}:
"""
            form = {"func": code[i][1]}

        ###
        elif code[i][0].lower() == "ret":
            max_label = -1
            asm = """\
pop s2
jmp *s2
"""
            form = {}

        ###
        elif code[i][0].lower() == "syscall":
            max_label = -1
            asm = """\
inc 3
"""
            form = {}

            ###
        elif code[i][0].lower() == "pop" and len(code[i]) == 1:
            max_label = -1
            asm = """\
movz *s7
dec s7
"""
            form = {}
        ###
        elif code[i][0].lower() == "add" and len(code[i]) > 1 and code[i][2][0] != "#":
            max_label = 2
            asm = """\
{label0}:
    tst {value}
    jmp {label1}
    jmp {label2}
{label1}:
    dec {value}
    {incs}    jmp {label0}
{label2}:"""
            form = {"value": code[i][2]}

            found = False
            for dest in code[i][1].split(","):
                found = True
                form["incs"] = form.get("incs", "") + f"inc {dest}\n"

            if not found:
                print("Wrong number of argumentss:", " ".join(code[i]))
                exit(1)

        ###
        elif code[i][0].lower() == "sub" and len(code[i]) > 1 and code[i][2][0] != "#":
            max_label = 3
            asm = """\
movz s5
{label0}:
jz {op1} {label2}
jz {op0} {label1}
dec {op0}
dec {op1}
jmp {label0}
{label1}:
inc s5
{label2}:
jz {op1} {label3}
inc {op0}
dec {op1}
jmp {label2}
{label3}:
"""
            form = {"op0": code[i][1], "op1":code[i][2]}


        ###
        elif code[i][0].lower() == "mul" and len(code[i]) > 1 :
            max_label = 4
            asm = """\
movz s0
movz {dest}
{label0}:
jz {op0} {label4}
dec {op0}
{label1}:
jz {op1} {label2}
dec {op1}
inc s0
inc {dest}
jmp {label1}
{label2}:
jz {op0} {label4}
dec {op0}
{label3}:
jz s0 {label0}
dec s0
inc {op1}
inc {dest}
jmp {label3}
{label4}:
movz {op1}
"""
            form = {"dest":code[i][1], "op0": code[i][2], "op1":code[i][3]}


        ###
        elif code[i][0].lower() == "div" and len(code[i]) > 1 and code[i][2][0] != "#":
            max_label = 6
            asm = """\
jz {op1} {label5}
movz s2
{label0}:
jz {op0} {label4}
cpy s1 {op1}
{label1}:
jz s1 {label2}
jz {op0} {label3}
dec {op0}
dec s1
jmp {label1}
{label2}:
inc s2
jmp {label0}
{label3}:
sub {op1} s1
mov s5 {op1}
jmp {label6}
{label4}:
movz {op1}
jmp {label6}
{label5}:
hlt 3
{label6}:
mov {dest} s2
"""
            form = {"dest":code[i][1], "op0": code[i][2], "op1":code[i][3]}

        ###
        elif code[i][0].lower() == "cpy" and code[i][2][0] != "#":
            max_label = -1
            if len(code[i]) == 3:
                code[i].append("s0")
            asm = """\
mov {reg} {value}
mov {value},{dst} {reg}
"""
            form = {"value": code[i][2], "dst":code[i][1], "reg":code[i][3]}

            found = False
            for dest in code[i][1].split(","):
                found = True
                form["incs"] = form.get("incs", "") + f"inc {dest}\n"

            if not found:
                print("Wrong number of argumentss:", " ".join(code[i]))
                exit(1)

        ###
        elif code[i][0].lower() == "jz" and code[i][2][0] != "#":
            max_label = 0
            asm = """\
tst {value}
jmp {label0}
jmp {to}
{label0}:
"""
            form = {"value": code[i][1], "to":code[i][2]}

        ###
        elif code[i][0].lower() == "jnz" and code[i][2][0] != "#":
            max_label = -1
            asm = """\
tst {value}
jmp {to}
"""
            form = {"value": code[i][1], "to":code[i][2]}

        ###
        elif code[i][0].lower() == "cmp" and code[i][2][0] != "#":
            max_label = 5
            asm = """\
jmp {label1}
{label0}:
dec {op0}
dec {op1}
{label1}:
jz {op0} {label2}
jz {op1} {label3}
jmp {label0}
{label2}:
jz {op1} {label4}
mov s4 #2
jmp {label5}
{label3}:
mov s4 #1
jmp {label5}
{label4}:
mov s4 #0
{label5}:
movz {op0}
movz {op1}
"""
            form = {"op0": code[i][1], "op1":code[i][2]}

        ###
        elif code[i][0].lower() == "int":
            if code[i] == ["int"]:
                code[i] = ["int", "1"]
            if len(code[i]) == 2:
                code[i].append("io6")
            max_label = 0
            form = {"code":code[i][1], "reg":code[i][2]}
            asm = "mov {reg} #{code}\n{label0}:\njnz {reg} {label0}\n"

        ###
        elif code[i][0].lower() == "case" and code[i][2][0] != "#":
            max_label = -1
            asm = ""
            form = {"r": code[i][1]}

            found = False
            for lbl in code[i][2].split(","):
                found = True
                asm += """
jz {r} lbl
dec {r}
""".replace("lbl", lbl)

            if len(code[i]) > 3:
                asm += "inc {r}\n" + f"jmp {code[i][3]}\n"

        ###
        elif args.assemble and code[i][0].startswith("#"): # inline data
            extra_data = immediate_to_array(" ".join(code[i])[1:])
            code[i:i+1] = [[j] for j in extra_data]
            i += 1
            continue
        ####
        elif args.assemble:
            line = " ".join(code[i])
            line = line.replace("inc *", "5\n")
            line = line.replace("dec *", "6\n")
            line = line.replace("jmp *", "7\n")
            line = line.replace("tst *", "8\n")

            line = line.replace("inc ", "0\n")
            line = line.replace("dec ", "1\n")
            line = line.replace("jmp ", "2\n")
            line = line.replace("tst ", "3\n")

            line = line.replace("hlt *", "9\n")
            
            line = line.replace("hlt\n", "4\n0\n")
            line = line.replace("hlt \n", "4\n0\n")
            line = line.replace("hlt ", "4\n")
            line = line.replace("hlt", "4\n0\n")

            lines = line.split("\n")
            if len(lines) > 1:
                lines = [line.strip().split(" ") for line in lines]
                code[i:i+1] = lines

            i += 1
            continue
        ####
        else:
            i += 1
            continue

        try:
            form
        except NameError:
            print("no form")
            i += 1
            continue
        
        for j in range(max_label+1):
            form["label"+str(j)] = "0L"+str(j+builtin_labels)

        try:
            instr = asm.format(**form).split("\n")
        except ValueError as e:
            print("Value Error:", e, "at", code[i], asm)
            exit(1)
        code_repl = []
        for j in instr:
            code_repl.append(j.split())

        code[i:i+1] = code_repl

        builtin_labels += max_label + 1

    # Stage 2 Linking
    if args.verbose:
        print ("PRE-LINKING\n", "\n".join([" ".join(j) for j in code]))
    i = 0
    instr_offset = args.jump_address
    labels = {}
    data_index = 0
    while i < len(code):
        if code[i] == []:
            pass
        elif code[i][0].endswith(":"):
            name = code[i][0].replace(":", "")

            if name in labels.keys():
                print("Double definition of memory reference", name)
                exit(1)
            if name.startswith("$"):
                global meminit
                meminit.append(str(instr_offset))
                labels[name] = "d"+str(data_index)
                data_index += 1
            else:
                labels[name] = instr_offset

            code[i] = None
        else:
            instr_offset += args.instr_size
        i += 1
    i = 0
    while i < len(code):
        if code[i] == [] or code[i] is None:
            i += 1
            continue
        try:
            target = 1
            if len(code[i]) == 1:
                target = 0
            code[i][target] = str(labels[code[i][target]])
        except KeyError:
            if "$"+code[i][target] in labels.keys():
                code[i][target] = str(meminit[int(labels["$"+code[i][target]][1:])])
            elif code[i][target].isnumeric() or (len(code[i][target]) > 1 and (code[i][target][1:].isnumeric() or code[i][target][2].isnumeric())):
                pass
            elif code[i][0] in ["inc", "dec", "tst", "hlt"]:
                pass
            else:
                print("Unrecognized label", code[i][target])
                exit(1)

        i +=1

    global entry_point
    try:
        entry_point = labels["_start"]
    except KeyError:
        print ("Missing label '_start'")
        exit(1)


    code_new = []
    for i in code:
        if i and i != [""]:
            code_new.append(i)
    code = code_new

    i = 0
    while i < len(code):
        code[i] = " ".join(code[i])
        i += 1

    return "\n".join(code)



if __name__ == "__main__":
    if not args.assemble:
        info = f";;; MURMEL++ OUTPUT ({args.input}) ;;;\n;; instr_offset {args.jump_address}, register_offset {global_offset}\n;; r0 = {r_offset}, s0 = {s_offset}\n"
        out = info + repl_registers(compile())
    else:
        inp = compile()

        inp = inp.split("\n")
        if inp == [""]:
            inp = []

        mem = [str(entry_point), "0", "0", "0", "0", "0", "0", "0"]
        mem[8:] = inp

        data_offset = len(mem)
        # data = []
        # for i in meminit:
        #     if i[0].startswith("d"):
        #         addr = int(i[0][1:])
        #         data[addr:addr+len(i[1])] = i[1]
        mem += meminit

        global_offset = len(mem)
        mem[1] = str(global_offset)
        mem[6] = str(global_offset)
        mem[5] = str(data_offset)
        
        mem = [repl_registers(line) for line in mem]
        repl_registers("r7") # Make sure the stack starts at minimum r7


        mem += ["0"] * (max_addr - len(mem))

        mem[7] = str(max_addr+1)
        mem += ["0"] * (args.stack_size)

        # one extra before heap is stack canary
        mem[4] = str(len(mem)+1)
        mem += ["0"] * (args.heap_size+1)

        new_mem = []
        for i in mem:
            if i != "h0":
                new_mem.append(i)
            else:
                new_mem.append(str(int(mem[4])-1))

        out = "\n".join(new_mem)

        [int(i) for i in new_mem] # check if everything is a number. user if something errors here it's your fault
        
        args.output += "bin"

    with open(args.output, "w") as f:
            f.write(out)
