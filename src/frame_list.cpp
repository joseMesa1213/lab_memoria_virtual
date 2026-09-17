#include "frame_list.hpp"

#include <stdexcept>

FrameList::FrameList(std::uint32_t frames) : position_(frames), tracked_(frames, false) {}

void FrameList::pushBack(std::uint32_t frame) {
    if (tracked_[frame]) {
        moveToBack(frame);
        return;
    }
    position_[frame] = order_.insert(order_.end(), frame);
    tracked_[frame] = true;
}

void FrameList::moveToBack(std::uint32_t frame) {
    if (!tracked_[frame]) {
        return;
    }
    order_.splice(order_.end(), order_, position_[frame]);
}

bool FrameList::remove(std::uint32_t frame) {
    if (!tracked_[frame]) {
        return false;
    }
    order_.erase(position_[frame]);
    tracked_[frame] = false;
    return true;
}

std::uint32_t FrameList::popFront() {
    if (order_.empty()) {
        throw std::logic_error("no hay marcos para reemplazar");
    }
    std::uint32_t frame = order_.front();
    order_.pop_front();
    tracked_[frame] = false;
    return frame;
}
