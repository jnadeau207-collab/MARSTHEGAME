#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace mars::game
{
struct RigVector3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct RigColor
{
    float r = 1.0f;
    float g = 1.0f;
    float b = 1.0f;
    float a = 1.0f;
};

enum class CharacterPart : std::size_t
{
    Torso = 0,
    Head = 1,
    Pelvis = 2,
    LeftArm = 3,
    RightArm = 4,
    LeftLeg = 5,
    RightLeg = 6,
    Backpack = 7,
    Visor = 8,
    Count = 9,
};

inline constexpr std::size_t kCharacterPartCount =
    static_cast<std::size_t>(CharacterPart::Count);

struct CharacterPartPose
{
    RigVector3 offset{};
    RigVector3 rotation_radians{};
    RigVector3 scale{1.0f, 1.0f, 1.0f};
    RigColor tint{};
    std::uint32_t mesh_slot = 0;
};

struct CharacterPose
{
    std::array<CharacterPartPose, kCharacterPartCount> parts{};
    float gait_phase = 0.0f;
    float animation_weight = 0.0f;
};

[[nodiscard]] CharacterPose EvaluateCharacterPose(
    float elapsed_seconds,
    float planar_speed,
    bool mission_complete) noexcept;
[[nodiscard]] bool ValidateCharacterPose(const CharacterPose& pose) noexcept;
[[nodiscard]] std::uint64_t HashCharacterPose(const CharacterPose& pose) noexcept;
} // namespace mars::game
