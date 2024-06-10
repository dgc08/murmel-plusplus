// THIS IS FOR SPEED. NO DELAYS!!!

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <thread>
#include <mutex>
#include <chrono>
#include <iomanip>

#define REPRINT_TIME 50

enum class Opcode {
    inc,
    dec,
    jmp,
    tst,
    hlt
};

struct Instr {
    Opcode code;
    std::string arg;
};

std::vector<Instr> instrs;
std::vector<unsigned int> mem(32, 0);

std::thread exec;
volatile bool running = false;

size_t view = 0;
std::vector<unsigned int> last_prints(32, 0);

std::chrono::steady_clock::time_point lastExecutionTime = std::chrono::steady_clock::now();
int instr_count = 0;
bool newline_needed = false;


inline bool is_int(const std::string& str) {
    try {
        std::stoi(str);
        return true;
    } catch (...) {
        return false;
    }
}

inline void set_mem(size_t one, unsigned int two) {
    if (one >= mem.size()) mem.resize(std::max(one + 1, mem.size() * 2));
    mem[one] = two;
}

inline unsigned int get_mem(size_t one) {
    if (one >= mem.size()) return 0;
    else return mem.at(one);
}

void load_mem(const std::string& filename) {
    mem.clear();
    mem.resize(128, 0);

    std::ifstream file(filename);
    std::string line;
    size_t offset = 0;

    while (std::getline(file, line)) {
        // Trim leading and trailing whitespace
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        unsigned int two;
        try {
            two = std::stoi(line);
        }
        catch (...) {
            std::cout << "Error while parsing your shit" << std::endl;
            exit(1);
        }
        set_mem(offset, two);

        offset++;
    }
}
void load_instrs(const std::string& filename) {
    instrs.clear();

    std::ifstream file(filename);
    std::string line;

    while (std::getline(file, line)) {
        // Trim leading and trailing whitespace
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        // Skip empty lines or lines starting with ';'
        if (line.empty() || line[0] == ';') {
            continue;
        }

        // Split the line by spaces
        std::string first;
        std::string second;
        std::istringstream iss(line);
        if (!(iss >> first)) {
            // If there are no whitespace-separated tokens, set second to an empty string
            second = "";
        } else {
            // Extract the second token
            iss >> second;
        }
        if (first != "") {
            Opcode code;
            if (first == "inc") code = Opcode::inc;
            else if (first == "dec") code = Opcode::dec;
            else if (first == "jmp") code = Opcode::jmp;
            else if (first == "tst") code = Opcode::tst;
            else if (first == "hlt") code = Opcode::hlt;
            else {
                std::cout << "failed to parse line " << line << std::endl;
                exit(1);
            }

            instrs.push_back(Instr{.code = code, .arg = second});
        }
    }
}


inline void listInstrsuctions() {
    for (const auto& instr : instrs) {
        std::cout << "(" << (int)instr.code << ", " << instr.arg << ")" << std::endl;
    }
}


void print_io(size_t ip, Instr& instr, bool force_reprint = false)  {
    auto currentTime = std::chrono::steady_clock::now();
    auto elapsedTime = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - lastExecutionTime).count();

    if (elapsedTime < REPRINT_TIME && !force_reprint) {
        return; // Return if less than 50ms elapsed since last execution
    }
    lastExecutionTime = std::chrono::steady_clock::now();

    std::cout << std::flush;
    std::cout << "\r\033[K";
    std::cout << "\r\033[K";

    // Print the first 8 items of the vector
    for (size_t i = view; i < view+8; ++i) {
        std::string form = ": \033[94m";
        if (get_mem(i) != last_prints[i-view]) {
            form = ": \033[96m";
            last_prints[i - view] = get_mem(i);
        }
        else if (get_mem(i) == 0) {
            form = ": \033[90m";
        }
        std::cout << "[" << i << form << std::setw(4) << std::setfill('0') << get_mem(i) << "\033[0m]  ";
    }

    std::stringstream extra;
    if (!force_reprint) {
        extra << (instr_count*1000)/REPRINT_TIME << " instr/s";
    }

    if (ip == 0) {
        std::cout << "IP \033[90m[" << std::setw(4) << std::setfill('0') << ip << "] \033[0m(" << (int)instr.code << ", " << instr.arg << ")" ;
    } else {
        std::cout << "IP \033[91m[" << std::setw(4) << std::setfill('0') << ip << "] \033[0m(" << (int)instr.code << ", " << instr.arg << ") " << extra.str();
    }

    std::cout << " > ";

    // Flush the output to ensure it's displayed immediately
    std::cout << std::flush;
    instr_count = 0;
}

void execute() {
    bool guessed_waiting = false;

    std::cout << "started" << std::endl;
    size_t ip = 0;
    print_io(ip, instrs.at(ip));
    while (running && ip < instrs.size()) {
        Instr instr = instrs.at(ip);
        std::string pre_arg = instr.arg; // param in js
        unsigned int arg; // the completely derefenced arg

        int derefs = 0;
        size_t last_pos = 0;
        // Count the number of dereferences
        for (size_t i = 0; i < pre_arg.length(); i++) {
            if (pre_arg.at(i) == '*') {
                derefs++;
            } else {
                last_pos = i;
                break;
            }
        }
        if (pre_arg == "") pre_arg = "0";
        arg = std::stoi(pre_arg.substr(last_pos));
        while (derefs > 0) {
            arg = get_mem(arg);
            derefs--;
        }


        if (newline_needed) {
            std::cout << std::endl;
            newline_needed=false;
            print_io(ip, instr, true);
        }


        switch (instr.code) {
            case Opcode::inc:
                set_mem(arg,get_mem(arg)+1);
                print_io(ip, instr);
                guessed_waiting = false;
                break;
            case Opcode::dec:
                set_mem(arg,get_mem(arg)-1);
                print_io(ip, instr);
                guessed_waiting = false;
                break;
            case Opcode::jmp:
                ip = arg;
                instr_count++;
                continue;
            case Opcode::tst:
                if (!get_mem(arg)) ip++;
                break;
            case Opcode::hlt:
                running = false;
                std::cout << std::endl << "hlt called: " << arg << std::endl << std::endl << std::flush;
                break;
        }

        auto currentTime = std::chrono::steady_clock::now();
        auto elapsedTime = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - lastExecutionTime).count();

        if (elapsedTime > REPRINT_TIME+10) {
            if (!guessed_waiting) {
                guessed_waiting = true;
                print_io(ip, instr, true);
            }
            else {
                lastExecutionTime = std::chrono::steady_clock::now();
            }
        }

        instr_count++;
        ip++;
    }
    std::cout << "finished, last instr: " << ip-1 << std::endl;
    ip = 0;
    std::cout << std::endl;
    newline_needed=false;
    print_io(ip, instrs.at(ip), true);

    running = false;
}

void executeCommand(const std::vector<std::string>& tokens) {
    if (tokens[0] == "list") {
        listInstrsuctions();
    }
    else if (tokens[0] == "load-ins") {
        if (tokens.size() == 2) {
            if (running ) {
                running = false;
                exec.join();
            }
            load_instrs(tokens[1]);
        } else {
            std::cout << "Usage: load-ins <filename>" << std::endl;
        }
    }
    else if (tokens[0] == "load-mem") {
        if (tokens.size() == 2) {
            if (running ) {
                running = false;
                exec.join();
            }
            load_mem(tokens[1]);
        } else {
            std::cout << "Usage: load-mem <filename>" << std::endl;
        }
    }
    else if (tokens.size() == 1 && (is_int(tokens[0]) || (tokens[0][0] == 'e' && isdigit(tokens[0][1])))) {
        if (is_int(tokens[0]))
            std::cout << get_mem(std::stoi(tokens[0])) << std::endl;
        else {
            std::cout << get_mem(std::stoi(tokens[0].substr(1)) + view) << std::endl;
        }
    }
    else if (tokens.size() == 2 && (is_int(tokens[0]) || (tokens[0][0] == 'e' && isdigit(tokens[0][1]))) && is_int(tokens[1])) {
        unsigned int one;
        if (is_int(tokens[0]))
            one = std::stoi(tokens[0]);
        else
            one = std::stoi(tokens[0].substr(1)) + view;

        unsigned int two = std::stoi(tokens[1]);

        set_mem(one, two);
    }
    else if ((tokens[0] == "r" || tokens[0] == "run" ) && !running) {
        if (running ) {
            running = false;
            exec.join();
        }
        running = true;
        exec = std::thread(execute);
    }
    else if (tokens[0] == "h" ||tokens[0] == "stop" ) {
        if (running ) {
            running = false;
            exec.join();
        }
    }
    else if (tokens[0] == "v" || tokens[0] == "s") { // You know how often i typed s instead of v
        if (tokens.size() == 1) {
            view = 0;
            return;
        }
        view = stoi(tokens[1]);
    }
    else if (tokens[0] == "clear" ||tokens[0] == "memclear" ) {
        mem.clear();
    }
    else if (tokens[0] == "i" ||tokens[0] == "inspect" ) {
        size_t max = 0;
        for (size_t i = 0; i < mem.size(); ++i) {
            if (mem[i] != 0) max = i;
        }
        for (size_t i = 0; i < max + 1; ++i) {
            std::cout <<std::setw(4) << i << ":    " << mem[i] << std::endl;
        }
    }
    else if (tokens[0] == "exit" || tokens[0] == "q") {
        if (running) {
            running = false;
            exec.join();
        }
        exit(0);
    }
    else {
        std::cout << "Invalid command." << std::endl;
    }
}

int main() {
    while (true) {
        std::string input;
        if (instrs.empty()) std::cout << "> ";
        else if (running) {
            newline_needed = true;
        }
        else {
            print_io(0, instrs.at(0));
        }
        std::getline(std::cin, input);

        if (input == "") continue;

        std::istringstream iss(input);
        std::vector<std::string> tokens;
        std::string token;
        while (iss >> token) {
            tokens.push_back(token);
        }

        executeCommand(tokens);
    }

    return 0;
}
