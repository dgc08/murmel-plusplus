#include <stdio.h>
#include <stdlib.h>

size_t size;
unsigned int* ins;

int segfault(char* msg) {
  printf("Segmentation fault of emulated program: %s\n", msg);
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

// All excellency of the murbin standart comes here
void syscall() {
  //printf("syscall %u\n", ins[4]);
  switch (ins[4]) {
    case 0:
      putchar(ins[5]);
      ins[5] = 0;
      ins[6] = 0;
      break;
    case 1:
      {
        int ch = getchar();
        if (ch == EOF) {
          ins[6] = 0;
          ins[5] = 1;
        }
        else {
          ins[6] = ch;
          ins[5] = 0;
          break;
        }
      }
  }

  ins[3] = 0;
  ins[4] = 0;
}

unsigned int* deref(unsigned int pointer) {
  if (pointer >= size) segfault("Access to unitialised memory region");
  return ins+pointer;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char* filename = argv[1];
    ins = readFileIntoArray(filename, &size);

    while (ins[0] < size-1) {
      unsigned int instr = ins[ins[0]];
      ins[0]++;
      //printf("%u: %u, %u\n",ins[0]-1, instr, ins[ins[0]]);
      switch (instr) {
        case 0:
          {
            unsigned int* p = deref(ins[ins[0]]) ;
            (*p)++;
            if (p-ins == 3) syscall();
          }
          break;
        case 1:
          (*deref(ins[ins[0]]))--;
          break;
        case 2:
          ins[0] = ins[ins[0]];
          continue;
        case 3:
          if (*deref((ins[ins[0]]))  == 0) {
            ins[0]+=2;
          }
          break;
        case 4:
          exit(ins[ins[0]]);
        case 5:
          {
            unsigned int* p = deref(*deref(ins[ins[0]]));
            (*p)++;
            if (p-ins == 3) syscall();
          }
          break;
        case 6:
          (*deref(*deref(ins[ins[0]])))--;
          break;
        case 7:
          ins[0] = *deref(ins[ins[0]]);
          continue;
        case 8:
          if (*deref(*deref((ins[ins[0]] == 0)))) {
            ins[0]+=2;
          }
          break;
        case 9:
          exit(*deref(ins[ins[0]]));
          break;
        default:
          segfault("Unrecognised instruction");
      }
      ins[0]++;
    }
    segfault("No hlt called");
}
