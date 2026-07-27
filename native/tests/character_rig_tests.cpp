#include "game/character_rig.h"

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
    using namespace mars::game;
    const CharacterPose idle = EvaluateCharacterPose(2.0f, 0.0f, false);
    const CharacterPose walk = EvaluateCharacterPose(2.0f, 5.0f, false);
    const CharacterPose walk_repeat = EvaluateCharacterPose(2.0f, 5.0f, false);
    const CharacterPose complete = EvaluateCharacterPose(2.0f, 0.0f, true);
    Require(ValidateCharacterPose(idle), "idle pose must validate");
    Require(ValidateCharacterPose(walk), "walk pose must validate");
    Require(HashCharacterPose(walk) == HashCharacterPose(walk_repeat), "rig evaluation must be deterministic");
    Require(HashCharacterPose(idle) != HashCharacterPose(walk), "movement must change the pose");
    Require(HashCharacterPose(idle) != HashCharacterPose(complete), "completion state must change presentation");
    Require(walk.animation_weight > idle.animation_weight, "movement weight must respond to speed");
    std::cout << "MARSTHEGAME procedural character rig tests passed\n";
    return 0;
}
