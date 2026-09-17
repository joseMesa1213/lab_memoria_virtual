#pragma once

#include "config.hpp"

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

using ReferenceProbe = std::function<bool(std::uint32_t)>;

class ReplacementPolicy {
public:
    virtual ~ReplacementPolicy() = default;

    virtual void onLoad(std::uint32_t frame) = 0;
    virtual void onAccess(std::uint32_t frame) = 0;
    virtual void onRelease(std::uint32_t frame) = 0;
    virtual std::uint32_t selectVictim(const ReferenceProbe& testAndClearReference) = 0;
    virtual std::string name() const = 0;
};

std::unique_ptr<ReplacementPolicy> makePolicy(PolicyKind kind, std::uint32_t frames);
