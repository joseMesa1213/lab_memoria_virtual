#include "physical_memory.hpp"

#include <algorithm>

PhysicalMemory::PhysicalMemory(std::uint64_t size, std::uint32_t pageSize)
    : pageSize_(pageSize), bytes_(size, 0), frames_(size / pageSize) {
    freeList_.reserve(frames_.size());
    for (std::uint32_t frame = frameCount(); frame > 0; --frame) {
        freeList_.push_back(frame - 1);
    }
}

std::optional<std::uint32_t> PhysicalMemory::acquireFrame(std::uint32_t pageNumber) {
    if (freeList_.empty()) {
        return std::nullopt;
    }
    std::uint32_t frame = freeList_.back();
    freeList_.pop_back();
    frames_[frame].used = true;
    frames_[frame].pageNumber = pageNumber;
    return frame;
}

void PhysicalMemory::releaseFrame(std::uint32_t frame) {
    frames_[frame] = FrameInfo{};
    freeList_.push_back(frame);
}

std::uint8_t PhysicalMemory::readByte(std::uint64_t physicalAddress) const {
    return bytes_[physicalAddress];
}

void PhysicalMemory::writeByte(std::uint64_t physicalAddress, std::uint8_t value) {
    bytes_[physicalAddress] = value;
}

std::uint8_t* PhysicalMemory::frameData(std::uint32_t frame) {
    return bytes_.data() + static_cast<std::uint64_t>(frame) * pageSize_;
}

void PhysicalMemory::zeroFrame(std::uint32_t frame) {
    std::uint8_t* data = frameData(frame);
    std::fill(data, data + pageSize_, static_cast<std::uint8_t>(0));
}
