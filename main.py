import argparse
import re

from sys import argv

parser = argparse.ArgumentParser(description='Compiler for murmel++ assembly')

parser.add_argument("input", type=str)
parser.add_argument("-o", "--output", type=str, default="out.mur")
parser.add_argument("-a", "--jump_address", type=int, default=0, help="Address of the first instruction. Default: 0")
parser.add_argument("--instr_size", type=int, default=1, help="How many 'lines' one instruction takes. Default: 1")
parser.add_argument("-r", "--register_address", type=int, default=0, help="Address of the first register. Default: 0")

parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("--assemble", action="store_true", help="Assemble the program with the murbin standart. Overwrites instr_size and jump_address")

#parser.add_argument("-s", "--stack", action="store_true", help="Activate stack operations like push & pop (requires pointers to be working)")
#parser.add_argument("-f", "--func", action="store_true", help="Activate the base miv instruction and with it call & ret")

args = parser.parse_args()

if args.assemble:
    args.instr_size = 2
    args.jump_address = 7

global_offset = args.register_address

s_offset = 8
r_offset = 16
io_offset = 0
e_offset = 0


def repl_registers(text):
    def match(pattern, letter, offset, text):
        #print(pattern, text, end=" ")
        matches = re.findall(pattern, text)
        #print(matches)
        for i in matches:
            text = text.replace(i, str(int(i.replace(letter, "")) + offset))
        return text

    # general purpose
    text = match(r"r\d+", "r", r_offset+global_offset, text)
    # s
    text = match(r"s\d+", "s", s_offset+global_offset, text)
    # io
    text = match(r"io\d+", "io", io_offset+global_offset, text)
    # e
    text = match(r"e\d+", "e", e_offset+global_offset, text)

    return text


def compile():
    with open(args.input) as f:
        lines = f.readlines()

    # Stage 0: Parse, remove comments
    code = []
    for line in lines:
        code.append(line.split(";")[0].strip().replace("jz", "jiz").replace("jnz", "jinz").split())

    if args.verbose:
        print ("Read code", code, "\n\n")
    # Stage 1
    i = 0
    builtin_labels = 0
    while i < len(code):
        if code[i] == []:
            i += 1
            continue

        ###
        if code[i][0].lower() == "movz":
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
        elif code[i][0].lower() == "mov" and code[i][2][0] == "#":
            max_label = -1
            asm = "{movzs}\n{incs}"
            form = {"incs":""}

            found = False
            for dest in code[i][1].split(","):
                found = True
                form["movzs"] = form.get("movzs", "") + f"movz {dest}\n"
                for inc in range(int(code[i][2][1:])):
                    form["incs"] = form.get("incs", "") + f"inc {dest}\n"

            if not found:
                print("Wrong number of argumentss:", " ".join(code[i]))
                exit(1)

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
        elif code[i][0].lower() == "add" and code[i][2][0] != "#":
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
        elif code[i][0].lower() == "sub" and code[i][2][0] != "#":
            max_label = 3
            asm = """\
movz s5
{label0}:
jiz {op1} {label2}
jiz {op0} {label1}
dec {op0}
dec {op1}
jmp {label0}
{label1}:
inc s5
{label2}:
jiz {op1} {label3}
inc {op0}
dec {op1}
jmp {label2}
{label3}:
"""
            form = {"op0": code[i][1], "op1":code[i][2]}


        ###
        elif code[i][0].lower() == "mul":
            max_label = 4
            asm = """\
movz s0
movz {dest}
{label0}:
jiz {op0} {label4}
dec {op0}
{label1}:
jiz {op1} {label2}
dec {op1}
inc s0
inc {dest}
jmp {label1}
{label2}:
jiz {op0} {label4}
dec {op0}
{label3}:
jiz s0 {label0}
dec s0
inc {op1}
inc {dest}
jmp {label3}
{label4}:
movz {op1}
"""
            form = {"dest":code[i][1], "op0": code[i][2], "op1":code[i][3]}


        ###
        elif code[i][0].lower() == "div" and code[i][2][0] != "#":
            max_label = 6
            asm = """\
jiz {op1} {label6}
movz {dest}
{label0}:
cpy s1 {op1}
{label1}:
jiz {op0} {label3}
jiz s1 {label2}
dec s1
dec {op0}
jmp {label1}
{label2}:
inc {dest}
jmp {label0}
{label3}:
jinz s1 {label4}
inc {dest}
movz s5
jmp {label5}
{label6}:
mov io6 #3
hlt 3
{label4}:
mov s5 s1
{label5}:
movz {op1}
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
        elif code[i][0].lower() == "jiz" and code[i][2][0] != "#":
            max_label = 0
            asm = """\
tst {value}
jmp {label0}
jmp {to}
{label0}:
"""
            form = {"value": code[i][1], "to":code[i][2]}

        ###
        elif code[i][0].lower() == "jinz" and code[i][2][0] != "#":
            max_label = 0
            asm = """\
tst {value}
jmp {to}
jmp {label0}
{label0}:
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
jiz {op0} {label2}
jiz {op1} {label3}
jmp {label0}
{label2}:
jiz {op1} {label4}
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
            asm = "mov {reg} #{code}\n{label0}:\njinz {reg} {label0}\n"

        ###
        elif code[i][0].lower() == "case" and code[i][2][0] != "#":
            max_label = -1
            asm = ""
            form = {"r": code[i][1]}

            found = False
            for lbl in code[i][2].split(","):
                found = True
                asm += """
jiz {r} lbl
dec {r}
""".replace("lbl", lbl)

            if len(code[i]) > 3:
                asm += "inc {r}\n" + f"jmp {code[i][3]}\n"

        ####
        else:
            i += 1
            continue

        try:
            form
        except NameError:
            print("a")
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
        print ("PRE-LINKING", code)
    i = 0
    instr_offset = args.jump_address
    labels = {}
    while i < len(code):
        if code[i] == []:
            pass
        elif code[i][0].endswith(":"):
            labels[code[i][0].replace(":", "")] = instr_offset
            code[i] = None
        else:
            instr_offset += args.instr_size
        i += 1
    i = 0
    while i < len(code):
        if code[i] == [] or code[i] is None:
            i += 1
            continue
        if code[i][0].endswith(":"):
            continue
        if code[i][0] == "jmp":
            if code[i][1][0] == "*" or code[i][1].isdigit():
                pass
            else:
                try:
                    code[i][1] = str(labels[code[i][1].replace("$", "")])
                except KeyError:
                    print("Unrecognized label", code[i][1])
                    exit(1)

        i +=1

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

        inp = inp.replace("inc *", "5\n")
        inp = inp.replace("dec *", "6\n")
        inp = inp.replace("jmp *", "7\n")
        inp = inp.replace("tst *", "8\n")

        inp = inp.replace("inc ", "0\n")
        inp = inp.replace("dec ", "1\n")
        inp = inp.replace("jmp ", "2\n")
        inp = inp.replace("tst ", "3\n")

        inp = inp.replace("hlt *", "9\n")

        inp = inp.replace("hlt\n", "4\n0\n")
        inp = inp.replace("hlt \n", "4\n0\n")
        inp = inp.replace("hlt ", "4\n")
        inp = inp.replace("hlt", "4\n0\n")

        print (inp, "lol", len(inp.split("\n")))
        global_offset = len(inp.split("\n")) + 7
        out = "7\n" + str(global_offset) + "\n0\n0\n" + str(global_offset) + "\n0"*2 + "\n" + repl_registers(inp)
        args.output += "bin"

    with open(args.output, "w") as f:
            f.write(out)
