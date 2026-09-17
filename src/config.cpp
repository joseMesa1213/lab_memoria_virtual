#include "config.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <stdexcept>

std::string policyName(PolicyKind kind) {
    switch (kind) {
        case PolicyKind::Fifo:
            return "FIFO";
        case PolicyKind::Lru:
            return "LRU";
        case PolicyKind::Clock:
            return "CLOCK";
    }
    return "?";
}

std::vector<PolicyKind> parsePolicies(const std::string& text) {
    std::string lower(text);
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (lower == "fifo") {
        return {PolicyKind::Fifo};
    }
    if (lower == "lru") {
        return {PolicyKind::Lru};
    }
    if (lower == "clock") {
        return {PolicyKind::Clock};
    }
    if (lower == "all") {
        return {PolicyKind::Fifo, PolicyKind::Lru, PolicyKind::Clock};
    }
    throw std::invalid_argument("política desconocida: " + text);
}

std::uint64_t parseSize(const std::string& text) {
    if (text.empty()) {
        throw std::invalid_argument("tamaño vacío");
    }
    std::size_t consumed = 0;
    std::uint64_t value = 0;
    try {
        value = std::stoull(text, &consumed, 0);
    } catch (const std::exception&) {
        throw std::invalid_argument("tamaño inválido: " + text);
    }
    std::string suffix = text.substr(consumed);
    std::transform(suffix.begin(), suffix.end(), suffix.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    std::uint64_t multiplier = 1;
    if (suffix.empty() || suffix == "B") {
        multiplier = 1;
    } else if (suffix == "K" || suffix == "KB") {
        multiplier = 1ULL << 10;
    } else if (suffix == "M" || suffix == "MB") {
        multiplier = 1ULL << 20;
    } else if (suffix == "G" || suffix == "GB") {
        multiplier = 1ULL << 30;
    } else {
        throw std::invalid_argument("sufijo de tamaño inválido: " + text);
    }
    return value * multiplier;
}

static std::string requireValue(int& index, int argc, char** argv) {
    if (index + 1 >= argc) {
        throw std::invalid_argument(std::string("falta el valor para ") + argv[index]);
    }
    return argv[++index];
}

Config parseArguments(int argc, char** argv) {
    Config config;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            config.help = true;
        } else if (arg == "-p" || arg == "--policy") {
            config.policies = parsePolicies(requireValue(i, argc, argv));
        } else if (arg == "-s" || arg == "--page-size") {
            std::uint64_t size = parseSize(requireValue(i, argc, argv));
            if (size > kMaxPageSize) {
                throw std::invalid_argument("tamaño de página demasiado grande");
            }
            config.pageSize = static_cast<std::uint32_t>(size);
        } else if (arg == "-m" || arg == "--memory") {
            config.physicalMemory = parseSize(requireValue(i, argc, argv));
        } else if (arg == "-v" || arg == "--verbose") {
            config.verbose = true;
        } else if (arg == "-c" || arg == "--csv") {
            config.csv = true;
        } else if (!arg.empty() && arg[0] == '-') {
            throw std::invalid_argument("opción desconocida: " + arg);
        } else if (config.inputPath.empty()) {
            config.inputPath = arg;
        } else {
            throw std::invalid_argument("argumento inesperado: " + arg);
        }
    }
    if (!config.help) {
        validateConfig(config);
    }
    return config;
}

void validateConfig(const Config& config) {
    if (config.inputPath.empty()) {
        throw std::invalid_argument("debe indicar el archivo de entrada");
    }
    std::uint32_t page = config.pageSize;
    if (page < kMinPageSize || page > kMaxPageSize || (page & (page - 1)) != 0) {
        throw std::invalid_argument("el tamaño de página debe ser potencia de 2 entre 1K y 1M");
    }
    if (config.physicalMemory < kMinPhysicalMemory) {
        throw std::invalid_argument("la memoria física mínima es 256K");
    }
    if (config.physicalMemory > kMaxPhysicalMemory) {
        throw std::invalid_argument("la memoria física máxima es 1G");
    }
    if (config.physicalMemory % page != 0) {
        throw std::invalid_argument("la memoria física debe ser múltiplo del tamaño de página");
    }
}

void printUsage(const char* program) {
    std::cout << "Uso: " << program << " [opciones] <archivo_trazas>\n\n"
              << "Opciones:\n"
              << "  -p, --policy <fifo|lru|clock|all>  política de reemplazo (defecto: fifo)\n"
              << "  -s, --page-size <tam>              tamaño de página, potencia de 2 (defecto: 4K)\n"
              << "  -m, --memory <tam>                 memoria física, mínimo 256K (defecto: 256K)\n"
              << "  -v, --verbose                      traza detallada de cada operación\n"
              << "  -c, --csv                          salida en formato CSV\n"
              << "  -h, --help                         muestra esta ayuda\n\n"
              << "Comandos del archivo:\n"
              << "  alloc <bytes> | write <va> <valor> | read <va> | free <va>\n";
}
