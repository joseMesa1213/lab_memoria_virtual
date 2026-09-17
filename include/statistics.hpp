#pragma once

#include <chrono>
#include <cstdint>

struct Statistics {
    std::uint64_t reads = 0;
    std::uint64_t writes = 0;
    std::uint64_t pageFaults = 0;
    std::uint64_t replacements = 0;
    std::uint64_t swapOuts = 0;
    std::uint64_t swapIns = 0;
    std::uint64_t zeroFills = 0;
    std::uint64_t segmentationFaults = 0;
    std::uint64_t allocations = 0;
    std::uint64_t failedAllocations = 0;
    std::uint64_t releases = 0;
    std::uint64_t invalidReleases = 0;
    std::chrono::nanoseconds faultTime{0};
    std::chrono::nanoseconds totalTime{0};

    std::uint64_t accesses() const { return reads + writes; }
    std::uint64_t hits() const { return accesses() - pageFaults; }
    double hitRate() const {
        return accesses() == 0 ? 0.0 : static_cast<double>(hits()) * 100.0 / static_cast<double>(accesses());
    }
    double faultRate() const { return accesses() == 0 ? 0.0 : 100.0 - hitRate(); }
};
