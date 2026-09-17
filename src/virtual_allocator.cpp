#include "virtual_allocator.hpp"

VirtualAllocator::VirtualAllocator(std::uint32_t pageSize) : pageSize_(pageSize) {}

std::optional<std::uint32_t> VirtualAllocator::allocate(std::uint64_t bytes) {
    if (bytes == 0 || bytes > kAddressSpace) {
        return std::nullopt;
    }
    std::uint64_t length = (bytes + pageSize_ - 1) / pageSize_ * pageSize_;
    std::uint64_t cursor = 0;
    for (const auto& [start, size] : regions_) {
        if (start - cursor >= length) {
            break;
        }
        cursor = static_cast<std::uint64_t>(start) + size;
    }
    if (cursor + length > kAddressSpace) {
        return std::nullopt;
    }
    std::uint32_t base = static_cast<std::uint32_t>(cursor);
    regions_.emplace(base, length);
    reserved_ += length;
    return base;
}

std::optional<std::uint64_t> VirtualAllocator::release(std::uint32_t start) {
    auto it = regions_.find(start);
    if (it == regions_.end()) {
        return std::nullopt;
    }
    std::uint64_t length = it->second;
    reserved_ -= length;
    regions_.erase(it);
    return length;
}

bool VirtualAllocator::contains(std::uint32_t virtualAddress) const {
    auto it = regions_.upper_bound(virtualAddress);
    if (it == regions_.begin()) {
        return false;
    }
    --it;
    return static_cast<std::uint64_t>(virtualAddress) <
           static_cast<std::uint64_t>(it->first) + it->second;
}
