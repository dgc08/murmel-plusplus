##
#
#
# @file
# @version 0.1

# Compiler
CXX = gcc

# Compiler flags
CXXFLAGS = -Wall -Wextra -g

# Source directory
SRC_DIR = src

# Source files
SRCS = $(wildcard $(SRC_DIR)/*.c)

# Object directory
OBJ_DIR = obj

# Object files
OBJS = $(patsubst $(SRC_DIR)/%., $(OBJ_DIR)/%.o, $(SRCS))

# Executable name
TARGET = emulator

# Default target
all: $(TARGET)

# Compile source files into object files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Link object files into the executable
$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $(OBJS) -o $(TARGET)

# Clean up object files and executable
clean:
	rm -rf $(OBJ_DIR) $(TARGET)
