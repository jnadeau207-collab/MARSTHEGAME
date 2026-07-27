#pragma once

#include "game/game_state.h"

#include <cstdint>
#include <vector>

namespace mars::game
{
struct ReplayCommand
{
    std::int8_t move_x = 0;
    std::int8_t move_z = 0;
    bool sprint = false;
    std::uint16_t ticks = 0;
};

class ReplayTape final
{
public:
    void Append(const InputState& input, std::uint16_t ticks);
    void Play(GameState& game) const;

    [[nodiscard]] std::uint64_t Hash() const noexcept;
    [[nodiscard]] const std::vector<ReplayCommand>& Commands() const noexcept;

private:
    std::vector<ReplayCommand> commands_{};
};
} // namespace mars::game
