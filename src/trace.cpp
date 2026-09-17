#include "trace.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

static std::uint64_t parseNumber(const std::string& token) {
    if (token.empty() || token[0] == '-' || token[0] == '+') {
        throw std::invalid_argument("número inválido: " + token);
    }
    std::size_t consumed = 0;
    std::uint64_t value = 0;
    try {
        value = std::stoull(token, &consumed, 0);
    } catch (const std::exception&) {
        throw std::invalid_argument("número inválido: " + token);
    }
    if (consumed != token.size()) {
        throw std::invalid_argument("número inválido: " + token);
    }
    return value;
}

static std::uint64_t parseAddress(const std::string& token) {
    std::uint64_t value = parseNumber(token);
    if (value > 0xFFFFFFFFULL) {
        throw std::invalid_argument("dirección fuera del espacio de 32 bits: " + token);
    }
    return value;
}

static Command parseLine(const std::vector<std::string>& tokens, std::size_t line) {
    Command command;
    command.line = line;
    const std::string& op = tokens[0];
    auto expect = [&](std::size_t count) {
        if (tokens.size() != count) {
            throw std::invalid_argument("'" + op + "' espera " + std::to_string(count - 1) + " argumento(s)");
        }
    };
    if (op == "alloc") {
        expect(2);
        command.type = CommandType::Alloc;
        command.first = parseNumber(tokens[1]);
    } else if (op == "write") {
        expect(3);
        command.type = CommandType::Write;
        command.first = parseAddress(tokens[1]);
        command.second = parseNumber(tokens[2]);
        if (command.second > 0xFF) {
            throw std::invalid_argument("el valor debe estar entre 0 y 255: " + tokens[2]);
        }
    } else if (op == "read") {
        expect(2);
        command.type = CommandType::Read;
        command.first = parseAddress(tokens[1]);
    } else if (op == "free") {
        expect(2);
        command.type = CommandType::Free;
        command.first = parseAddress(tokens[1]);
    } else {
        throw std::invalid_argument("comando desconocido: " + op);
    }
    return command;
}

Trace parseTrace(std::istream& input) {
    Trace trace;
    std::string raw;
    std::size_t line = 0;
    while (std::getline(input, raw)) {
        ++line;
        std::size_t hash = raw.find('#');
        if (hash != std::string::npos) {
            raw.erase(hash);
        }
        std::istringstream stream(raw);
        std::vector<std::string> tokens;
        std::string token;
        while (stream >> token) {
            tokens.push_back(token);
        }
        if (tokens.empty()) {
            continue;
        }
        try {
            trace.commands.push_back(parseLine(tokens, line));
        } catch (const std::invalid_argument& error) {
            trace.errors.push_back({line, error.what()});
        }
    }
    return trace;
}

Trace loadTrace(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("no se pudo abrir el archivo: " + path);
    }
    return parseTrace(file);
}

std::string commandName(CommandType type) {
    switch (type) {
        case CommandType::Alloc:
            return "alloc";
        case CommandType::Write:
            return "write";
        case CommandType::Read:
            return "read";
        case CommandType::Free:
            return "free";
    }
    return "?";
}
