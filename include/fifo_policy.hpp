#pragma once

#include "frame_list.hpp"
#include "replacement_policy.hpp"

class FifoPolicy : public ReplacementPolicy {
public:
    explicit FifoPolicy(std::uint32_t frames);

    void onLoad(std::uint32_t frame) override;
    void onAccess(std::uint32_t frame) override;
    void onRelease(std::uint32_t frame) override;
    std::uint32_t selectVictim(const ReferenceProbe& testAndClearReference) override;
    std::string name() const override { return "FIFO"; }

private:
    FrameList queue_;
};
