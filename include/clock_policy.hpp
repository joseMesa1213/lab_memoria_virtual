#pragma once

#include "replacement_policy.hpp"

#include <vector>

class ClockPolicy : public ReplacementPolicy {
public:
    explicit ClockPolicy(std::uint32_t frames);

    void onLoad(std::uint32_t frame) override;
    void onAccess(std::uint32_t frame) override;
    void onRelease(std::uint32_t frame) override;
    std::uint32_t selectVictim(const ReferenceProbe& testAndClearReference) override;
    std::string name() const override { return "CLOCK"; }

private:
    std::vector<bool> occupied_;
    std::uint32_t hand_ = 0;
    std::uint32_t loaded_ = 0;
};
