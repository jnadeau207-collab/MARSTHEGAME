#include "platform/native_input.h"

#include <Windows.h>
#include <Xinput.h>

#include <algorithm>
#include <cmath>
#include <limits>

namespace mars::platform
{
namespace
{
bool KeyDown(const int virtual_key) noexcept
{
    return (GetAsyncKeyState(virtual_key) & 0x8000) != 0;
}

float DigitalAxis(const bool negative, const bool positive) noexcept
{
    return static_cast<float>(positive) - static_cast<float>(negative);
}
} // namespace

float NormalizeStickAxis(const std::int16_t value, const float deadzone) noexcept
{
    const float bounded_deadzone = (std::clamp)(deadzone, 0.0f, 0.95f);
    const float denominator = value < 0
        ? static_cast<float>((std::numeric_limits<std::int16_t>::max)()) + 1.0f
        : static_cast<float>((std::numeric_limits<std::int16_t>::max)());
    const float normalized = static_cast<float>(value) / denominator;
    const float magnitude = std::abs(normalized);
    if (magnitude <= bounded_deadzone)
    {
        return 0.0f;
    }
    const float remapped = (magnitude - bounded_deadzone) / (1.0f - bounded_deadzone);
    return std::copysign((std::clamp)(remapped, 0.0f, 1.0f), normalized);
}

game::InputState MapInput(
    const KeyboardSample& keyboard,
    const GamepadSample& gamepad,
    const InputSettings& settings) noexcept
{
    const float keyboard_x = DigitalAxis(keyboard.left, keyboard.right);
    const float keyboard_z = DigitalAxis(keyboard.backward, keyboard.forward);
    const float gamepad_x = gamepad.connected
        ? NormalizeStickAxis(gamepad.left_x, settings.stick_deadzone)
        : 0.0f;
    const float gamepad_z = gamepad.connected
        ? NormalizeStickAxis(gamepad.left_y, settings.stick_deadzone)
        : 0.0f;
    const float trigger = static_cast<float>(gamepad.left_trigger) / 255.0f;

    return {
        .move_x = (std::clamp)(keyboard_x + gamepad_x, -1.0f, 1.0f),
        .move_z = (std::clamp)(keyboard_z + gamepad_z, -1.0f, 1.0f),
        .sprint = keyboard.sprint
            || (gamepad.connected && trigger >= settings.trigger_threshold),
        .reset = keyboard.reset || (gamepad.connected && gamepad.reset),
        .restore_checkpoint = keyboard.restore_checkpoint
            || (gamepad.connected && gamepad.restore_checkpoint),
    };
}

game::InputState NativeInput::Poll() const noexcept
{
    return MapInput(PollKeyboard(), PollGamepad());
}

bool NativeInput::GamepadConnected() const noexcept
{
    return PollGamepad().connected;
}

KeyboardSample NativeInput::PollKeyboard() noexcept
{
    return {
        .left = KeyDown('A') || KeyDown(VK_LEFT),
        .right = KeyDown('D') || KeyDown(VK_RIGHT),
        .forward = KeyDown('W') || KeyDown(VK_UP),
        .backward = KeyDown('S') || KeyDown(VK_DOWN),
        .sprint = KeyDown(VK_LSHIFT) || KeyDown(VK_RSHIFT),
        .reset = KeyDown('R'),
        .restore_checkpoint = KeyDown('C'),
    };
}

GamepadSample NativeInput::PollGamepad() noexcept
{
    XINPUT_STATE state{};
    if (XInputGetState(0, &state) != ERROR_SUCCESS)
    {
        return {};
    }
    const WORD buttons = state.Gamepad.wButtons;
    return {
        .connected = true,
        .left_x = state.Gamepad.sThumbLX,
        .left_y = state.Gamepad.sThumbLY,
        .left_trigger = state.Gamepad.bLeftTrigger,
        .reset = (buttons & XINPUT_GAMEPAD_Y) != 0,
        .restore_checkpoint = (buttons & XINPUT_GAMEPAD_X) != 0,
    };
}
} // namespace mars::platform
