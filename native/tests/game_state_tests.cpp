#include "game/game_state.h"

#include <cmath>
#include <cstdlib>
#include <iostream>

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
    mars::game::GameState game;
    Require(game.Mission() == mars::game::MissionState::Traverse, "mission starts in traverse state");

    const auto start = game.PlayerPosition();
    mars::game::InputState forward{};
    forward.move_z = 1.0f;
    for (int frame = 0; frame < 60; ++frame)
    {
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    }
    const auto advanced = game.PlayerPosition();
    Require(advanced.z > start.z + 3.0f, "forward input advances the player deterministically");

    for (int frame = 0; frame < 420; ++frame)
    {
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    }
    Require(game.Mission() == mars::game::MissionState::Complete, "objective beacon completes the mission");

    const auto completed = game.PlayerPosition();
    for (int frame = 0; frame < 60; ++frame)
    {
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    }
    const auto stopped = game.PlayerPosition();
    Require(std::abs(stopped.z - completed.z) < 0.75f, "completion arrests player movement");

    mars::game::InputState reset{};
    reset.reset = true;
    game.Update(reset, mars::game::GameState::kFixedStepSeconds);
    Require(game.Mission() == mars::game::MissionState::Traverse, "reset restores active mission state");
    Require(game.PlayerPosition().z < -7.5f, "reset restores landing position");

    const auto scene = game.Scene();
    Require(scene.instances.size() == 18, "native graybox exposes the complete scene instance set");
    std::cout << "MARSTHEGAME native gameplay tests passed\n";
    return 0;
}
