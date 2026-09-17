#include "page_table.hpp"

#include <algorithm>

SecondLevelTable::SecondLevelTable(std::uint32_t entries) : entries_(entries) {}

bool SecondLevelTable::empty() const {
    return std::none_of(entries_.begin(), entries_.end(),
                        [](const PageTableEntry& e) { return e.inUse(); });
}

PageTable::PageTable(const AddressLayout& layout)
    : layout_(layout), directory_(layout.pt1Entries()) {}

PageTableEntry* PageTable::find(std::uint32_t virtualAddress) {
    VirtualAddressParts parts = layout_.split(virtualAddress);
    const std::unique_ptr<SecondLevelTable>& table = directory_[parts.pt1];
    if (!table) {
        return nullptr;
    }
    return &table->entry(parts.pt2);
}

PageTableEntry& PageTable::resolve(std::uint32_t virtualAddress) {
    VirtualAddressParts parts = layout_.split(virtualAddress);
    std::unique_ptr<SecondLevelTable>& table = directory_[parts.pt1];
    if (!table) {
        table = std::make_unique<SecondLevelTable>(layout_.pt2Entries());
        ++live_;
        ++created_;
    }
    return table->entry(parts.pt2);
}

void PageTable::compact(std::uint32_t virtualAddress) {
    VirtualAddressParts parts = layout_.split(virtualAddress);
    std::unique_ptr<SecondLevelTable>& table = directory_[parts.pt1];
    if (table && table->empty()) {
        table.reset();
        --live_;
        ++released_;
    }
}
