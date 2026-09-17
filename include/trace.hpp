#pragma once

#include <cstddef>
#include <cstdint>
#include <istream>
#include <string>
#include <vector>

enum class CommandType { Alloc, Write, Read, Free };

struct Command {
    CommandType type = CommandType::Read;
    std::uint64_t first = 0;
    std::uint64_t second = 0;
    std::size_t line = 0;
};

struct TraceError {
    std::size_t line = 0;
    std::string message;
};

struct Trace {
    std::vector<Command> commands;
    std::vector<TraceError> errors;
};

Trace loadTrace(const std::string& path);
Trace parseTrace(std::istream& input);
std::string commandName(CommandType type);
