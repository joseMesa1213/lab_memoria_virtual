#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

struct Options {
    std::string pattern;
    std::uint32_t pages = 0;
    std::uint64_t accesses = 0;
    std::uint32_t seed = 42;
    std::uint32_t pageSize = 4096;
};

static void usage(const char* program) {
    std::cerr << "Uso: " << program << " <seq|random|locality|matrix> <paginas> <accesos> [semilla] [tam_pagina]\n";
}

class Generator {
public:
    explicit Generator(const Options& options)
        : options_(options), rng_(options.seed), touched_(options.pages, false) {}

    void emit(std::ostream& out) {
        out << "alloc " << static_cast<std::uint64_t>(options_.pages) * options_.pageSize << '\n';
        if (options_.pattern == "seq") {
            sequential(out);
        } else if (options_.pattern == "random") {
            uniform(out);
        } else if (options_.pattern == "locality") {
            locality(out);
        } else if (options_.pattern == "matrix") {
            matrix(out);
        } else {
            throw std::invalid_argument("patrón desconocido: " + options_.pattern);
        }
    }

private:
    std::uint32_t randomBelow(std::uint32_t limit) {
        return std::uniform_int_distribution<std::uint32_t>(0, limit - 1)(rng_);
    }

    void access(std::uint32_t page, std::ostream& out) {
        const std::uint64_t address =
            static_cast<std::uint64_t>(page) * options_.pageSize + randomBelow(options_.pageSize);
        const bool write = !touched_[page] || randomBelow(100) < 30;
        touched_[page] = true;
        if (write) {
            out << "write " << address << ' ' << randomBelow(256) << '\n';
        } else {
            out << "read " << address << '\n';
        }
    }

    void sequential(std::ostream& out) {
        for (std::uint64_t i = 0; i < options_.accesses; ++i) {
            access(static_cast<std::uint32_t>((i / kBurst) % options_.pages), out);
        }
    }

    void uniform(std::ostream& out) {
        for (std::uint64_t i = 0; i < options_.accesses; ++i) {
            access(randomBelow(options_.pages), out);
        }
    }

    void locality(std::ostream& out) {
        const std::uint32_t window = std::max<std::uint32_t>(4, options_.pages / 10);
        const std::uint64_t phase = std::max<std::uint64_t>(1, options_.accesses / 20);
        std::uint32_t base = 0;
        std::vector<std::uint32_t> hot;
        for (std::uint64_t i = 0; i < options_.accesses; ++i) {
            if (i % phase == 0) {
                base = randomBelow(options_.pages);
                hot.clear();
                for (std::uint32_t k = 0; k < 3; ++k) {
                    hot.push_back((base + k) % options_.pages);
                }
            }
            const std::uint32_t dice = randomBelow(100);
            std::uint32_t page = 0;
            if (dice < 50) {
                page = hot[randomBelow(static_cast<std::uint32_t>(hot.size()))];
            } else if (dice < 90) {
                page = (base + randomBelow(window)) % options_.pages;
            } else {
                page = randomBelow(options_.pages);
            }
            access(page, out);
        }
    }

    std::uint32_t cellPage(std::uint32_t matrixIndex, std::uint32_t row, std::uint32_t column,
                           std::uint32_t order) const {
        const std::uint32_t perMatrix = std::max<std::uint32_t>(1, options_.pages / 3);
        const std::uint64_t cell = static_cast<std::uint64_t>(row) * order + column;
        const std::uint64_t cells = static_cast<std::uint64_t>(order) * order;
        return matrixIndex * perMatrix + static_cast<std::uint32_t>(cell * perMatrix / cells);
    }

    void matrix(std::ostream& out) {
        const std::uint32_t order = 96;
        std::uint64_t emitted = 0;
        for (std::uint32_t i = 0; i < order && emitted < options_.accesses; ++i) {
            for (std::uint32_t j = 0; j < order && emitted < options_.accesses; ++j) {
                for (std::uint32_t k = 0; k < order && emitted < options_.accesses; ++k) {
                    access(cellPage(0, i, k, order), out);
                    access(cellPage(1, k, j, order), out);
                    access(cellPage(2, i, j, order), out);
                    emitted += 3;
                }
            }
        }
    }

    static constexpr std::uint64_t kBurst = 16;

    Options options_;
    std::mt19937 rng_;
    std::vector<bool> touched_;
};

int main(int argc, char** argv) {
    if (argc < 4 || argc > 6) {
        usage(argv[0]);
        return 2;
    }
    try {
        Options options;
        options.pattern = argv[1];
        options.pages = static_cast<std::uint32_t>(std::stoul(argv[2]));
        options.accesses = std::stoull(argv[3]);
        if (argc >= 5) {
            options.seed = static_cast<std::uint32_t>(std::stoul(argv[4]));
        }
        if (argc == 6) {
            options.pageSize = static_cast<std::uint32_t>(std::stoul(argv[5]));
        }
        if (options.pages == 0 || options.pageSize == 0) {
            throw std::invalid_argument("páginas y tamaño de página deben ser positivos");
        }
        if (static_cast<std::uint64_t>(options.pages) * options.pageSize > (1ULL << 32)) {
            throw std::invalid_argument("la región excede el espacio virtual de 32 bits");
        }
        Generator generator(options);
        generator.emit(std::cout);
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        usage(argv[0]);
        return 1;
    }
    return 0;
}
