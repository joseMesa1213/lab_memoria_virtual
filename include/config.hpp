#pragma once

#include <cstdint>
#include <string>
#include <vector>

enum class PolicyKind { Fifo, Lru, Clock };

struct Config {
    std::uint32_t pageSize = 4096;
    std::uint64_t physicalMemory = 256 * 1024;
    std::vector<PolicyKind> policies{PolicyKind::Fifo};
    bool verbose = false;
    bool csv = false;
    bool help = false;
    std::string inputPath;
};

constexpr std::uint64_t kMinPhysicalMemory = 256 * 1024;
constexpr std::uint64_t kMaxPhysicalMemory = 1ULL << 30;
constexpr std::uint32_t kMinPageSize = 1024;
constexpr std::uint32_t kMaxPageSize = 1U << 20;

std::string policyName(PolicyKind kind);
std::vector<PolicyKind> parsePolicies(const std::string& text);
std::uint64_t parseSize(const std::string& text);
Config parseArguments(int argc, char** argv);
void validateConfig(const Config& config);
void printUsage(const char* program);
