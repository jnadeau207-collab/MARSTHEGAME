#include "game/replay.h"

#include <algorithm>
#include <stdexcept>

namespace mars::game
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

std::int8_t QuantizeAxis(const float value)
{
    if (value < -0.5f)
    {
        return -1;
    }
    if (value > 0.5f)
    {
        return 1;
    }
    return 0;
}
} // namespace

void ReplayTape::Append(const InputState& input, const std::uint16_t ticks)
{
    if (ticks == 0)
    {
        throw std::invalid_argument("Replay commands require at least one tick");
    }
    commands_.push_back({
        .move_x = QuantizeAxis(input.move_x),
        .move_z = QuantizeAxis(input.move_z),
        .sprint = input.sprint,
        .ticks = ticks,
    });
}

void ReplayTape::Play(GameState& game) const
{
    for (const ReplayCommand& command : commands_)
    {
        InputState input{};
        input.move_x = static_cast<float>(command.move_x);
        input.move_z = static_cast<float>(command.move_z);
        input.sprint = command.sprint;
        for (std::uint16_t tick = 0; tick < command.ticks; ++tick)
        {
            game.Update(input, GameState::kFixedStepSeconds);
        }
    }
}

std::uint64_t ReplayTape::Hash() const noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    for (const ReplayCommand& command : commands_)
    {
        const std::uint8_t bytes[] = {
            static_cast<std::uint8_t>(command.move_x),
            static_cast<std::uint8_t>(command.move_z),
            static_cast<std::uint8_t>(command.sprint),
            static_cast<std::uint8_t>(command.ticks & 0xFFU),
            static_cast<std::uint8_t>((command.ticks >> 8U) & 0xFFU),
        };
        for (const std::uint8_t value : bytes)
        {
            hash ^= value;
            hash *= kFnvPrime;
        }
    }
    return hash;
}

const std::vector<ReplayCommand>& ReplayTape::Commands() const noexcept
{
    return commands_;
}
} // namespace mars::game
