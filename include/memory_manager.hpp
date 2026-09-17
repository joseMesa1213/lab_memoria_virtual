#pragma once

#include "address_layout.hpp"
#include "backing_store.hpp"
#include "config.hpp"
#include "page_table.hpp"
#include "physical_memory.hpp"
#include "replacement_policy.hpp"
#include "statistics.hpp"
#include "virtual_allocator.hpp"

#include <cstdint>
#include <memory>
#include <optional>
#include <string>

enum class AccessKind { Read, Write };

enum class AccessStatus { Ok, SegmentationFault };

struct AccessResult {
    AccessStatus status = AccessStatus::Ok;
    VirtualAddressParts parts{};
    std::uint64_t physicalAddress = 0;
    std::uint32_t frame = 0;
    std::uint8_t value = 0;
    bool pageFault = false;
    bool replacement = false;
    bool swapIn = false;
    std::uint32_t evictedPage = 0;
    bool evictedDirty = false;
};

class MemoryManager {
public:
    MemoryManager(const Config& config, PolicyKind policy);

    MemoryManager(const MemoryManager&) = delete;
    MemoryManager& operator=(const MemoryManager&) = delete;

    std::optional<std::uint32_t> allocate(std::uint64_t bytes);
    std::optional<std::uint64_t> release(std::uint32_t virtualAddress);
    AccessResult read(std::uint32_t virtualAddress);
    AccessResult write(std::uint32_t virtualAddress, std::uint8_t value);

    Statistics& statistics() { return stats_; }
    const Statistics& statistics() const { return stats_; }
    const AddressLayout& layout() const { return layout_; }
    std::uint32_t frameCount() const { return physical_.frameCount(); }
    std::size_t freeFrames() const { return physical_.freeFrames(); }
    std::string policyName() const { return policy_->name(); }
    const PageTable& pageTable() const { return pageTable_; }
    std::size_t swappedPages() const { return swap_.pages(); }

private:
    AccessResult translate(std::uint32_t virtualAddress, AccessKind kind);
    void handlePageFault(std::uint32_t virtualAddress, PageTableEntry& entry, AccessResult& result);
    std::uint32_t obtainFrame(std::uint32_t pageNumber, AccessResult& result);
    void evict(std::uint32_t frame, AccessResult& result);
    PageTableEntry& entryForFrame(std::uint32_t frame);

    AddressLayout layout_;
    PageTable pageTable_;
    PhysicalMemory physical_;
    BackingStore swap_;
    VirtualAllocator allocator_;
    std::unique_ptr<ReplacementPolicy> policy_;
    Statistics stats_;
};
