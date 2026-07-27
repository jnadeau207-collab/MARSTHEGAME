#include "platform/native_input.h"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>

namespace
{
void Require(const bool condition, const char* message)
{
    if (!condition)
    {
        std::cerr << "FAILED: " << message << '\n';
        std::exit(1);
    }
}
} // namespace

int main()
{
    using mars::platform::GamepadSample;
    using mars::platform::InputSettings;
    using mars::platform::KeyboardSample;

    Require(
        mars::platform::NormalizeStickAxis(2'000, 0.18f) == 0.0f,
        "stick values inside the deadzone map to zero");
    Require(
        mars::platform::NormalizeStickAxis(
            (std::numeric_limits<std::int16_t>::max)(),
            0.18f) > 0.99f,
        "positive stick maximum maps to one");
    Require(
        mars::platform::NormalizeStickAxis(
            (std::numeric_limits<std::int16_t>::min)(),
            0.18f) < -0.99f,
        "negative stick maximum maps to negative one");

    KeyboardSample keyboard{};
    keyboard.forward = true;
    keyboard.sprint = true;
    auto input = mars::platform::MapInput(keyboard, {});
    Require(input.move_z == 1.0f && input.sprint, "keyboard mapping preserves movement and sprint");

    GamepadSample gamepad{};
    gamepad.connected = true;
    gamepad.left_x = (std::numeric_limits<std::int16_t>::max)();
    gamepad.left_trigger = 255;
    gamepad.restore_checkpoint = true;
    input = mars::platform::MapInput({}, gamepad);
    Require(input.move_x > 0.99f, "gamepad stick maps to native movement");
    Require(input.sprint, "gamepad trigger maps to sprint");
    Require(input.restore_checkpoint, "gamepad X maps to checkpoint restore");

    keyboard.left = true;
    gamepad.left_x = (std::numeric_limits<std::int16_t>::max)();
    input = mars::platform::MapInput(keyboard, gamepad, InputSettings{});
    Require(std::abs(input.move_x) < 0.01f, "keyboard and gamepad axes combine deterministically");

    std::cout << "MARSTHEGAME native input parity tests passed\n";
    return 0;
}
