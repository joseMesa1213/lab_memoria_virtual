#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

class PhysicalMemory {
public:
    PhysicalMemory(std::uint64_t size, std::uint32_t pageSize);

    std::optional<std::uint32_t> acquireFrame(std::uint32_t pageNumber);
    void releaseFrame(std::uint32_t frame);

    std::uint32_t ownerOf(std::uint32_t frame) const { return frames_[frame].pageNumber; }
    bool inUse(std::uint32_t frame) const { return frames_[frame].used; }
    std::uint32_t frameCount() const { return static_cast<std::uint32_t>(frames_.size()); }
    std::size_t freeFrames() const { return freeList_.size(); }

    std::uint8_t readByte(std::uint64_t physicalAddress) const;
    void writeByte(std::uint64_t physicalAddress, std::uint8_t value);
    std::uint8_t* frameData(std::uint32_t frame);
    void zeroFrame(std::uint32_t frame);

private:
    struct FrameInfo {
        bool used = false;
        std::uint32_t pageNumber = 0;
    };

    std::uint32_t pageSize_;
    std::vector<std::uint8_t> bytes_;
    std::vector<FrameInfo> frames_;
    std::vector<std::uint32_t> freeList_;
};
