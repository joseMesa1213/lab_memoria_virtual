#pragma once

#include <cstdint>

struct VirtualAddressParts {
    std::uint32_t pt1;
    std::uint32_t pt2;
    std::uint32_t offset;
};

class AddressLayout {
public:
    static constexpr std::uint32_t kVirtualBits = 32;

    explicit AddressLayout(std::uint32_t pageSize);

    VirtualAddressParts split(std::uint32_t virtualAddress) const;
    std::uint32_t pageNumber(std::uint32_t virtualAddress) const;
    std::uint32_t pageBase(std::uint32_t pageNumber) const;
    std::uint64_t physicalAddress(std::uint32_t frame, std::uint32_t offset) const;

    std::uint32_t pageSize() const { return pageSize_; }
    std::uint32_t offsetBits() const { return offsetBits_; }
    std::uint32_t pt1Bits() const { return pt1Bits_; }
    std::uint32_t pt2Bits() const { return pt2Bits_; }
    std::uint32_t pt1Entries() const { return 1U << pt1Bits_; }
    std::uint32_t pt2Entries() const { return 1U << pt2Bits_; }

private:
    std::uint32_t pageSize_;
    std::uint32_t offsetBits_;
    std::uint32_t pt1Bits_;
    std::uint32_t pt2Bits_;
};
