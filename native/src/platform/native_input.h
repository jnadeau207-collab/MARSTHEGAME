#pragma once

#include "game/game_state.h"

#include <cstdint>

namespace mars::platform
{
struct KeyboardSample
{
    bool left = false;
    bool right = false;
    bool forward = false;
    bool backward = false;
    bool sprint = false;
    bool reset = false;
    bool restore_checkpoint = false;
};

struct GamepadSample
{
    bool connected = false;
    std::int16_t left_x = 0;
    std::int16_t left_y = 0;
    std::uint8_t left_trigger = 0;
    bool reset = false;
    bool restore_checkpoint = false;
};

struct InputSettings
{
    float stick_deadzone = 0.18f;
    float trigger_threshold = 0.35f;
};

[[nodiscard]] float NormalizeStickAxis(std::int16_t value, float deadzone) noexcept;
[[nodiscard]] game::InputState MapInput(
    const KeyboardSample& keyboard,
    const GamepadSample& gamepad,
    const InputSettings& settings = {}) noexcept;

class NativeInput final
{
public:
    [[nodiscard]] game::InputState Poll() const noexcept;
    [[nodiscard]] bool GamepadConnected() const noexcept;

private:
    [[nodiscard]] static KeyboardSample PollKeyboard() noexcept;
    [[nodiscard]] static GamepadSample PollGamepad() noexcept;
};
} // namespace mars::platform
