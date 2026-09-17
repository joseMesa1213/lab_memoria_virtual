CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror -O2
CPPFLAGS := -Iinclude

SRC := $(wildcard src/*.cpp)
OBJ := $(patsubst src/%.cpp,build/%.o,$(SRC))
DEP := $(OBJ:.o=.d)

BIN := vmsim
GEN := gen_trace

POLICY ?= fifo
PAGE ?= 4K
MEM ?= 256K
TRACE ?= tests/basico.txt
ARGS ?=

.PHONY: all clean run compare test traces sanitize leaks

all: $(BIN) $(GEN)

$(BIN): $(OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $@

build/%.o: src/%.cpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c $< -o $@

build:
	mkdir -p build

$(GEN): tools/gen_trace.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

run: $(BIN)
	./$(BIN) -p $(POLICY) -s $(PAGE) -m $(MEM) $(ARGS) $(TRACE)

compare: $(BIN)
	./$(BIN) -p all -s $(PAGE) -m $(MEM) $(ARGS) $(TRACE)

test: all
	./tests/run_tests.sh

traces: $(GEN)
	./$(GEN) seq 512 40000 1 > tests/secuencial.txt
	./$(GEN) random 512 40000 7 > tests/aleatorio.txt
	./$(GEN) locality 1024 100000 42 > tests/localidad.txt
	./$(GEN) matrix 768 150000 5 > tests/matrices.txt

sanitize:
	$(MAKE) clean
	$(MAKE) all CXXFLAGS="-std=c++17 -Wall -Wextra -Wpedantic -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer"
	./tests/run_tests.sh

leaks: $(BIN)
	@if command -v valgrind >/dev/null 2>&1; then \
		valgrind --leak-check=full --error-exitcode=1 ./$(BIN) -p all $(TRACE); \
	else \
		leaks --atExit -- ./$(BIN) -p all $(TRACE); \
	fi

clean:
	rm -rf build $(BIN) $(GEN)

-include $(DEP)
