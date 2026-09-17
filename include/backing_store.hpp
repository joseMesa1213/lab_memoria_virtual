#pragma once

#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

class BackingStore {
public:
    explicit BackingStore(std::uint32_t pageSize);

    void store(std::uint32_t pageNumber, const std::uint8_t* data);
    bool load(std::uint32_t pageNumber, std::uint8_t* destination) const;
    void discard(std::uint32_t pageNumber);
    std::size_t pages() const { return pages_.size(); }

private:
    std::uint32_t pageSize_;
    std::unordered_map<std::uint32_t, std::vector<std::uint8_t>> pages_;
};
