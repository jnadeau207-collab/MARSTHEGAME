#pragma once

#include "game/game_state.h"

#include <filesystem>
#include <optional>

namespace mars::game
{
class SaveRepository final
{
public:
    static void Write(const std::filesystem::path& path, const GameSnapshot& snapshot);
    [[nodiscard]] static std::optional<GameSnapshot> Load(const std::filesystem::path& path);
};
} // namespace mars::game
