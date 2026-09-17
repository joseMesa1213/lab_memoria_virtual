#pragma once

#include "address_layout.hpp"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

struct PageTableEntry {
    std::uint32_t frame = 0;
    bool valid = false;
    bool accessed = false;
    bool dirty = false;
    bool swapped = false;

    bool inUse() const { return valid || swapped; }
};

class SecondLevelTable {
public:
    explicit SecondLevelTable(std::uint32_t entries);

    PageTableEntry& entry(std::uint32_t index) { return entries_[index]; }
    bool empty() const;

private:
    std::vector<PageTableEntry> entries_;
};

class PageTable {
public:
    explicit PageTable(const AddressLayout& layout);

    PageTableEntry* find(std::uint32_t virtualAddress);
    PageTableEntry& resolve(std::uint32_t virtualAddress);
    void compact(std::uint32_t virtualAddress);

    std::size_t liveTables() const { return live_; }
    std::size_t createdTables() const { return created_; }
    std::size_t releasedTables() const { return released_; }

private:
    AddressLayout layout_;
    std::vector<std::unique_ptr<SecondLevelTable>> directory_;
    std::size_t live_ = 0;
    std::size_t created_ = 0;
    std::size_t released_ = 0;
};
