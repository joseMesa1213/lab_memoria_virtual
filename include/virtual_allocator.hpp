#pragma once

#include <cstdint>
#include <map>
#include <optional>

class VirtualAllocator {
public:
    static constexpr std::uint64_t kAddressSpace = 1ULL << 32;

    explicit VirtualAllocator(std::uint32_t pageSize);

    std::optional<std::uint32_t> allocate(std::uint64_t bytes);
    std::optional<std::uint64_t> release(std::uint32_t start);
    bool contains(std::uint32_t virtualAddress) const;
    std::uint64_t reservedBytes() const { return reserved_; }
    std::size_t regions() const { return regions_.size(); }

private:
    std::uint32_t pageSize_;
    std::map<std::uint32_t, std::uint64_t> regions_;
    std::uint64_t reserved_ = 0;
};
