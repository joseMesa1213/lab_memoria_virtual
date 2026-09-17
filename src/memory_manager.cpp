#include "memory_manager.hpp"

#include <chrono>
#include <stdexcept>

MemoryManager::MemoryManager(const Config& config, PolicyKind policy)
    : layout_(config.pageSize),
      pageTable_(layout_),
      physical_(config.physicalMemory, config.pageSize),
      swap_(config.pageSize),
      allocator_(config.pageSize),
      policy_(makePolicy(policy, physical_.frameCount())) {}

std::optional<std::uint32_t> MemoryManager::allocate(std::uint64_t bytes) {
    std::optional<std::uint32_t> base = allocator_.allocate(bytes);
    if (base) {
        ++stats_.allocations;
    } else {
        ++stats_.failedAllocations;
    }
    return base;
}

std::optional<std::uint64_t> MemoryManager::release(std::uint32_t virtualAddress) {
    std::optional<std::uint64_t> length = allocator_.release(virtualAddress);
    if (!length) {
        ++stats_.invalidReleases;
        return std::nullopt;
    }
    const std::uint64_t end = static_cast<std::uint64_t>(virtualAddress) + *length;
    for (std::uint64_t address = virtualAddress; address < end; address += layout_.pageSize()) {
        std::uint32_t va = static_cast<std::uint32_t>(address);
        PageTableEntry* entry = pageTable_.find(va);
        if (entry == nullptr) {
            continue;
        }
        if (entry->valid) {
            policy_->onRelease(entry->frame);
            physical_.releaseFrame(entry->frame);
        }
        if (entry->swapped) {
            swap_.discard(layout_.pageNumber(va));
        }
        *entry = PageTableEntry{};
        pageTable_.compact(va);
    }
    ++stats_.releases;
    return length;
}

AccessResult MemoryManager::read(std::uint32_t virtualAddress) {
    AccessResult result = translate(virtualAddress, AccessKind::Read);
    if (result.status == AccessStatus::Ok) {
        result.value = physical_.readByte(result.physicalAddress);
    }
    return result;
}

AccessResult MemoryManager::write(std::uint32_t virtualAddress, std::uint8_t value) {
    AccessResult result = translate(virtualAddress, AccessKind::Write);
    if (result.status == AccessStatus::Ok) {
        physical_.writeByte(result.physicalAddress, value);
        result.value = value;
    }
    return result;
}

AccessResult MemoryManager::translate(std::uint32_t virtualAddress, AccessKind kind) {
    AccessResult result;
    result.parts = layout_.split(virtualAddress);
    if (!allocator_.contains(virtualAddress)) {
        result.status = AccessStatus::SegmentationFault;
        ++stats_.segmentationFaults;
        return result;
    }
    if (kind == AccessKind::Read) {
        ++stats_.reads;
    } else {
        ++stats_.writes;
    }
    PageTableEntry& entry = pageTable_.resolve(virtualAddress);
    if (!entry.valid) {
        handlePageFault(virtualAddress, entry, result);
    } else {
        policy_->onAccess(entry.frame);
    }
    entry.accessed = true;
    if (kind == AccessKind::Write) {
        entry.dirty = true;
    }
    result.frame = entry.frame;
    result.physicalAddress = layout_.physicalAddress(entry.frame, result.parts.offset);
    return result;
}

void MemoryManager::handlePageFault(std::uint32_t virtualAddress, PageTableEntry& entry,
                                    AccessResult& result) {
    const auto start = std::chrono::steady_clock::now();
    ++stats_.pageFaults;
    result.pageFault = true;
    const std::uint32_t pageNumber = layout_.pageNumber(virtualAddress);
    const std::uint32_t frame = obtainFrame(pageNumber, result);
    if (entry.swapped && swap_.load(pageNumber, physical_.frameData(frame))) {
        ++stats_.swapIns;
        result.swapIn = true;
    } else {
        physical_.zeroFrame(frame);
        ++stats_.zeroFills;
    }
    entry.frame = frame;
    entry.valid = true;
    entry.dirty = false;
    policy_->onLoad(frame);
    stats_.faultTime += std::chrono::steady_clock::now() - start;
}

std::uint32_t MemoryManager::obtainFrame(std::uint32_t pageNumber, AccessResult& result) {
    std::optional<std::uint32_t> frame = physical_.acquireFrame(pageNumber);
    if (frame) {
        return *frame;
    }
    ReferenceProbe probe = [this](std::uint32_t candidate) {
        PageTableEntry& entry = entryForFrame(candidate);
        const bool referenced = entry.accessed;
        entry.accessed = false;
        return referenced;
    };
    const std::uint32_t victim = policy_->selectVictim(probe);
    evict(victim, result);
    frame = physical_.acquireFrame(pageNumber);
    if (!frame) {
        throw std::logic_error("no se pudo obtener un marco tras el reemplazo");
    }
    return *frame;
}

void MemoryManager::evict(std::uint32_t frame, AccessResult& result) {
    const std::uint32_t pageNumber = physical_.ownerOf(frame);
    PageTableEntry& entry = entryForFrame(frame);
    result.replacement = true;
    result.evictedPage = pageNumber;
    result.evictedDirty = entry.dirty;
    if (entry.dirty) {
        swap_.store(pageNumber, physical_.frameData(frame));
        entry.swapped = true;
        ++stats_.swapOuts;
    }
    entry.valid = false;
    entry.accessed = false;
    entry.dirty = false;
    physical_.releaseFrame(frame);
    ++stats_.replacements;
}

PageTableEntry& MemoryManager::entryForFrame(std::uint32_t frame) {
    PageTableEntry* entry = pageTable_.find(layout_.pageBase(physical_.ownerOf(frame)));
    if (entry == nullptr) {
        throw std::logic_error("marco sin entrada de tabla de páginas");
    }
    return *entry;
}
