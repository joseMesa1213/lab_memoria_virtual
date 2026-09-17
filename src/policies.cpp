#include "clock_policy.hpp"
#include "fifo_policy.hpp"
#include "lru_policy.hpp"

#include <stdexcept>

FifoPolicy::FifoPolicy(std::uint32_t frames) : queue_(frames) {}

void FifoPolicy::onLoad(std::uint32_t frame) {
    queue_.pushBack(frame);
}

void FifoPolicy::onAccess(std::uint32_t) {}

void FifoPolicy::onRelease(std::uint32_t frame) {
    queue_.remove(frame);
}

std::uint32_t FifoPolicy::selectVictim(const ReferenceProbe&) {
    return queue_.popFront();
}

LruPolicy::LruPolicy(std::uint32_t frames) : recency_(frames) {}

void LruPolicy::onLoad(std::uint32_t frame) {
    recency_.pushBack(frame);
}

void LruPolicy::onAccess(std::uint32_t frame) {
    recency_.moveToBack(frame);
}

void LruPolicy::onRelease(std::uint32_t frame) {
    recency_.remove(frame);
}

std::uint32_t LruPolicy::selectVictim(const ReferenceProbe&) {
    return recency_.popFront();
}

ClockPolicy::ClockPolicy(std::uint32_t frames) : occupied_(frames, false) {}

void ClockPolicy::onLoad(std::uint32_t frame) {
    if (!occupied_[frame]) {
        occupied_[frame] = true;
        ++loaded_;
    }
}

void ClockPolicy::onAccess(std::uint32_t) {}

void ClockPolicy::onRelease(std::uint32_t frame) {
    if (occupied_[frame]) {
        occupied_[frame] = false;
        --loaded_;
    }
}

std::uint32_t ClockPolicy::selectVictim(const ReferenceProbe& testAndClearReference) {
    if (loaded_ == 0) {
        throw std::logic_error("no hay marcos para reemplazar");
    }
    const std::uint32_t frames = static_cast<std::uint32_t>(occupied_.size());
    while (true) {
        std::uint32_t candidate = hand_;
        hand_ = (hand_ + 1) % frames;
        if (occupied_[candidate] && !testAndClearReference(candidate)) {
            occupied_[candidate] = false;
            --loaded_;
            return candidate;
        }
    }
}

std::unique_ptr<ReplacementPolicy> makePolicy(PolicyKind kind, std::uint32_t frames) {
    switch (kind) {
        case PolicyKind::Fifo:
            return std::make_unique<FifoPolicy>(frames);
        case PolicyKind::Lru:
            return std::make_unique<LruPolicy>(frames);
        case PolicyKind::Clock:
            return std::make_unique<ClockPolicy>(frames);
    }
    throw std::invalid_argument("política desconocida");
}
