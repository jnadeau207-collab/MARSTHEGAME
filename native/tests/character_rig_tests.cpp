#include "game/character_rig.h"
#include "renderer/generated_materials.h"

#include <array>
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
    Require(HashCharacterPose(walk) == HashCharacterPose(walk_repeat),
        "rig evaluation must be deterministic");
    Require(HashCharacterPose(idle) != HashCharacterPose(walk), "movement must change the pose");
    Require(HashCharacterPose(idle) != HashCharacterPose(complete),
        "completion state must change presentation");
    Require(walk.animation_weight > idle.animation_weight, "movement weight must respond to speed");
    Require(kCharacterPartCount == 21U,
        "field-engineer recovery silhouette must retain all articulated parts");

    std::array<bool, mars::renderer::kGeneratedMaterialCount> used_materials{};
    for (const CharacterPartPose& part : walk.parts)
    {
        Require(part.material_slot < used_materials.size(),
            "field-engineer part must reference a valid generated material");
        used_materials[part.material_slot] = true;
    }
    Require(used_materials[static_cast<std::size_t>(
        mars::renderer::GeneratedMaterialSlot::SuitFabric)],
        "field engineer must use pressure-fabric material");
    Require(used_materials[static_cast<std::size_t>(
        mars::renderer::GeneratedMaterialSlot::SuitAbrasion)],
        "field engineer must use abrasion-panel material");
    Require(used_materials[static_cast<std::size_t>(
        mars::renderer::GeneratedMaterialSlot::SuitShell)],
        "field engineer must use hard-shell material");
    Require(used_materials[static_cast<std::size_t>(
        mars::renderer::GeneratedMaterialSlot::SuitMechanism)],
        "field engineer must use mechanism material");
    Require(used_materials[static_cast<std::size_t>(
        mars::renderer::GeneratedMaterialSlot::Visor)],
        "field engineer must use visor material");

    std::cout << "MARSTHEGAME articulated field-engineer rig tests passed\n";
    return 0;
}
