#include <stdio.h>
#include <stdlib.h>

size_t size;
unsigned int* ins;
unsigned int PC;

int segfault(char* msg) {
  fprintf(stderr, "Segmentation fault of emulated program: %s\n", msg);
  printf("%u: %u, %u\n",PC-1, ins[PC-1], ins[PC]);
  exit(EXIT_FAILURE);
}

// Function by ChatGPT
unsigned int* readFileIntoArray(const char* filename, size_t* outSize) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        perror("Error opening file");
        exit(EXIT_FAILURE);
    }

    // Determine the number of lines (unsigned integers) in the file
    unsigned int temp;
    size_t size = 0;
    while (fscanf(file, "%u", &temp) == 1) {
        size++;
    }

    // Allocate memory for the array
    unsigned int* array = (unsigned int*)malloc(size * sizeof(unsigned int));
    if (!array) {
        perror("Error allocating memory");
        fclose(file);
        exit(EXIT_FAILURE);
    }

    // Rewind the file pointer to the beginning of the file
    rewind(file);

    // Read the unsigned integers into the array
    size_t index = 0;
    while (fscanf(file, "%u", &array[index]) == 1) {
        index++;
    }

    fclose(file);
    *outSize = size;
    return array;
}

unsigned int* deref(unsigned int pointer) {
  if (pointer >= size) segfault("Access to unitialised memory region");
  return ins+pointer;
}

// All excellency of the murbin standart comes here
void syscall() {
  //printf("syscall %u %u: ", ins[4], ins[5]);
  switch (ins[4]) {
    case 0: // putchar
      putchar(ins[5]);
      ins[5] = 0;
      ins[6] = 0;
      break;
    case 1: // getchar
      {
        int ch = getchar();
        if (ch == EOF) {
          ins[6] = 0;
          ins[5] = 1;
        }
        else {
          ins[6] = ch;
          ins[5] = 0;
        }
        break;
      }
  }

  ins[3] = 0;
  ins[4] = 0;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char* filename = argv[1];
    ins = readFileIntoArray(filename, &size);

    PC = ins[0];

    while (PC < size-1) {
      unsigned int instr = ins[PC];
      PC++;
      /* printf("%u: %u, %u\n",PC-1, instr, ins[PC]); */
      switch (instr) {
        case 0:
          {
            unsigned int* p = deref(ins[PC]) ;
            (*p)++;
            if (p-ins == 3) syscall();
          }
          break;
        case 1:
          (*deref(ins[PC]))--;
          break;
        case 2:
          PC = ins[PC];
          continue;
        case 3:
          if (*deref((ins[PC]))  == 0) {
            PC+=2;
          }
          break;
        case 4:
          exit(ins[PC]);
        case 5:
          {
            unsigned int* p = deref(*deref(ins[PC]));
            (*p)++;
            if (p-ins == 3) syscall();
          }
          break;
        case 6:
          (*deref(*deref(ins[PC])))--;
          break;
        case 7:
          PC = *deref(ins[PC]);
          continue;
        case 8:
          if (*deref(*deref((ins[PC]))) == 0) {
            PC+=2;
          }
          break;
        case 9:
          exit(*deref(ins[PC]));
          break;
        default:
          segfault("Unrecognised instruction");
      }
      PC++;
    }
    segfault("No hlt called");
}
