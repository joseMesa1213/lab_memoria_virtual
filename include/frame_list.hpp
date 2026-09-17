#pragma once

#include <cstdint>
#include <list>
#include <vector>

class FrameList {
public:
    explicit FrameList(std::uint32_t frames);

    void pushBack(std::uint32_t frame);
    void moveToBack(std::uint32_t frame);
    bool remove(std::uint32_t frame);
    std::uint32_t popFront();
    bool contains(std::uint32_t frame) const { return tracked_[frame]; }
    bool empty() const { return order_.empty(); }

private:
    std::list<std::uint32_t> order_;
    std::vector<std::list<std::uint32_t>::iterator> position_;
    std::vector<bool> tracked_;
};
