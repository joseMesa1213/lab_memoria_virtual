#include "backing_store.hpp"

#include <algorithm>

BackingStore::BackingStore(std::uint32_t pageSize) : pageSize_(pageSize) {}

void BackingStore::store(std::uint32_t pageNumber, const std::uint8_t* data) {
    std::vector<std::uint8_t>& page = pages_[pageNumber];
    page.assign(data, data + pageSize_);
}

bool BackingStore::load(std::uint32_t pageNumber, std::uint8_t* destination) const {
    auto it = pages_.find(pageNumber);
    if (it == pages_.end()) {
        return false;
    }
    std::copy(it->second.begin(), it->second.end(), destination);
    return true;
}

void BackingStore::discard(std::uint32_t pageNumber) {
    pages_.erase(pageNumber);
}
