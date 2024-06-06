import argparse
import re

parser = argparse.ArgumentParser(description='Compiler for murmel++ assembly')

parser.add_argument("input", type=str)
parser.add_argument("-o", "--output", type=str, default="out.mur")

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
        code.append(line.split(";")[0].split())

    # Stage 1


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
        print(code[i], len(code[i]))
        if len(code[i]) == 0 or code[i][0].endswith(":") or code[i][0] == "jmp":
            pass
        elif len(code[i]) == 2:
            #print("before", code[i][1], end=" ")
            code[i][1] = repl_registers(code[i][1])
            #print("after", code[i][1])
        elif len(code[i]) == 3:
            code[i][1] = repl_registers(code[i][1])
            code[i][2] = repl_registers(code[i][2])
        else:
            print("Wrong number of arguments:", " ".join(code[i]))
        i += 1
    # Stage 3
    i = 0
    instr_offset = 1
    labels = {}
    while i < len(code):
        if code[i] == []:
            i += 1
            continue
        if code[i][0].endswith(":"):
            labels[code[i][0].replace(":", "")] = instr_offset
            instr_offset += 1
            code[i] = None
            i += 1
            continue

        if code[i][0] == "jmp":
            try:
                code[i][1] = str(labels[code[i][1]])
            except KeyError:
                print("Unrecognized label", code[i][1])
                exit(1)

        instr_offset += 1
        i +=1

    code_new = []
    for i in code:
        if i:
            code_new.append(i)
    code = code_new

    with open(args.output, "w") as f:
        i = 0
        while i < len(code):
            code[i] = " ".join(code[i])
            i += 1

        f.write("\n".join(code))
