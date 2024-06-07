import argparse
import re

parser = argparse.ArgumentParser(description='Compiler for murmel++ assembly')

parser.add_argument("input", type=str)
parser.add_argument("-o", "--output", type=str, default="out.mur")
parser.add_argument("-a", "--jump_address", type=int, default=1, help="Address of the first instruction. Default: 1")
parser.add_argument("-v", "--verbose", action="store_true")

args = parser.parse_args()

global_offset = 0

s_offset = 8
r_offset = 16
io_offset = 0
e_offset = 0


if __name__ == '__main__':
    with open(args.input) as f:
        lines = f.readlines()

    # Stage 0: Parse, remove comments
    code = []
    for line in lines:
        code.append(re.findall(r"\S+",  line.split(";")[0].strip()))

    if args.verbose:
        print ("Read code", code, "\n\n")
    # Stage 1
    i = 0
    builtin_labels = 0
    while i < len(code):
        if len(code[i]) < 2:
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
        elif code[i][0].lower() == "cpy" and code[i][2][0] != "#":
            max_label = -1
            asm = """\
mov s0 {value}
mov {value},{dst} s0
"""
            form = {"value": code[i][2], "dst":code[i][1]}

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
        ####
        else:
            i += 1
            continue

        try:
            form
        except NameError:
            i += 1

        for j in range(max_label+1):
                form["label"+str(j)] = "0L"+str(j+builtin_labels)

        instr = asm.format(**form).split("\n")
        code_repl = []
        for j in instr:
            code_repl.append(j.split())

        code[i:i+1] = code_repl

        builtin_labels += max_label + 1

    # Stage 2: Replace register names
    i = 0
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


    while i < len(code):
        if code[i] == [] or code[i][0].endswith(":"):
            pass
        elif len(code[i]) == 2:
            #print("before", code[i][1], end=" ")
            code[i][1] = repl_registers(code[i][1])
            #print("after", code[i][1])
        elif len(code[i]) == 3:
            code[i][1] = repl_registers(code[i][1])
            code[i][2] = repl_registers(code[i][2])
        elif code[i][0] == "hlt":
            pass
        else:
            print(code)
            print("Wrong number of arguments:", code[i])
            exit(1)
        i += 1

    # Stage 3
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
            instr_offset += 1
        i += 1
    i = 0
    while i < len(code):
        if code[i] == [] or code[i] is None:
            i += 1
            continue
        if code[i][0].endswith(":"):
            continue
        if code[i][0] == "jmp":
            if code[i][1][0] == "*":
                pass
            else:
                try:
                    code[i][1] = str(labels[code[i][1]])
                except KeyError:
                    print("Unrecognized label", code[i][1])
                    exit(1)

        instr_offset += 1
        i +=1

    code_new = []
    for i in code:
        if i and i != [""]:
            code_new.append(i)
    code = code_new

    with open(args.output, "w") as f:
        i = 0
        while i < len(code):
            code[i] = " ".join(code[i])
            i += 1

        info = f";;; MURMEL++ OUTPUT ;;;\n;; instr_offset {args.jump_address}, register_offset {global_offset}\n;; r0 = {r_offset}, s0 = {s_offset}"
        f.write(info + "\n" + "\n".join(code))
