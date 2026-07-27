#pragma once

#include <cstddef>
#include <cstdint>
#include <deque>
#include <stdexcept>
#include <utility>

namespace mars::renderer
{
template <typename Resource>
class FenceRetirementQueue final
{
public:
    void Retire(const std::uint64_t fence_value, Resource resource)
    {
        if (!entries_.empty() && fence_value < entries_.back().fence_value)
        {
            throw std::invalid_argument("Fence retirement values must be nondecreasing");
        }
        entries_.push_back({fence_value, std::move(resource)});
    }

    std::size_t Collect(const std::uint64_t completed_fence)
    {
        std::size_t released = 0;
        while (!entries_.empty() && entries_.front().fence_value <= completed_fence)
        {
            entries_.pop_front();
            ++released;
        }
        return released;
    }

    void Clear() noexcept
    {
        entries_.clear();
    }

    [[nodiscard]] std::size_t PendingBatchCount() const noexcept
    {
        return entries_.size();
    }

    [[nodiscard]] bool Empty() const noexcept
    {
        return entries_.empty();
    }

private:
    struct Entry
    {
        std::uint64_t fence_value = 0;
        Resource resource{};
    };

    std::deque<Entry> entries_{};
};
} // namespace mars::renderer
