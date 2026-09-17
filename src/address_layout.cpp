#include "address_layout.hpp"

#include <stdexcept>

static std::uint32_t log2Exact(std::uint32_t value) {
    if (value == 0 || (value & (value - 1)) != 0) {
        throw std::invalid_argument("el tamaño de página debe ser potencia de 2");
    }
    std::uint32_t bits = 0;
    while ((1U << bits) != value) {
        ++bits;
    }
    return bits;
}

AddressLayout::AddressLayout(std::uint32_t pageSize)
    : pageSize_(pageSize), offsetBits_(log2Exact(pageSize)), pt1Bits_(0), pt2Bits_(0) {
    std::uint32_t indexBits = kVirtualBits - offsetBits_;
    pt2Bits_ = indexBits / 2;
    pt1Bits_ = indexBits - pt2Bits_;
}

VirtualAddressParts AddressLayout::split(std::uint32_t virtualAddress) const {
    VirtualAddressParts parts{};
    parts.offset = virtualAddress & (pageSize_ - 1);
    parts.pt2 = (virtualAddress >> offsetBits_) & (pt2Entries() - 1);
    parts.pt1 = virtualAddress >> (offsetBits_ + pt2Bits_);
    return parts;
}

std::uint32_t AddressLayout::pageNumber(std::uint32_t virtualAddress) const {
    return virtualAddress >> offsetBits_;
}

std::uint32_t AddressLayout::pageBase(std::uint32_t pageNumber) const {
    return pageNumber << offsetBits_;
}

std::uint64_t AddressLayout::physicalAddress(std::uint32_t frame, std::uint32_t offset) const {
    return (static_cast<std::uint64_t>(frame) << offsetBits_) | offset;
}
