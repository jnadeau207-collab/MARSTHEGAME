#include "game/character_rig.h"

#include <algorithm>
#include <bit>
#include <cmath>

namespace mars::game
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

CharacterPartPose MakePart(
    const RigVector3 offset,
    const RigVector3 rotation,
    const RigVector3 scale,
    const RigColor tint,
    const std::uint32_t mesh_slot) noexcept
{
    return {
        .offset = offset,
        .rotation_radians = rotation,
        .scale = scale,
        .tint = tint,
        .mesh_slot = mesh_slot,
    };
}

bool Finite(const float value) noexcept
{
    return std::isfinite(value);
}

void HashFloat(std::uint64_t& hash, const float value) noexcept
{
    const std::uint32_t word = std::bit_cast<std::uint32_t>(value);
    for (std::uint32_t shift = 0; shift < 32; shift += 8)
    {
        hash ^= static_cast<std::uint8_t>(word >> shift);
        hash *= kFnvPrime;
    }
}
} // namespace

CharacterPose EvaluateCharacterPose(
    const float elapsed_seconds,
    const float planar_speed,
    const bool mission_complete) noexcept
{
    const float safe_time = Finite(elapsed_seconds) ? (std::max)(elapsed_seconds, 0.0f) : 0.0f;
    const float safe_speed = Finite(planar_speed) ? (std::clamp)(planar_speed, 0.0f, 12.0f) : 0.0f;
    const float movement_weight = (std::clamp)(safe_speed / 7.0f, 0.0f, 1.0f);
    const float cadence = 1.85f + safe_speed * 0.48f;
    const float phase = safe_time * cadence;
    const float stride = std::sin(phase) * 0.44f * movement_weight;
    const float counter_stride = -stride;
    const float bob = std::abs(std::sin(phase)) * 0.026f * movement_weight;
    const float completion_lift = mission_complete ? 0.018f : 0.0f;

    // Recovery previsualization palette: human-scale field engineer rather than toy-orange blocks.
    const RigColor suit_fabric{0.46f, 0.43f, 0.37f, 1.0f};
    const RigColor hard_shell{0.62f, 0.54f, 0.34f, 1.0f};
    const RigColor mechanisms{0.105f, 0.12f, 0.13f, 1.0f};
    const RigColor helmet{0.52f, 0.53f, 0.50f, 1.0f};
    const RigColor pack{0.095f, 0.105f, 0.115f, 1.0f};
    const RigColor visor = mission_complete
        ? RigColor{0.055f, 0.22f, 0.18f, 1.45f}
        : RigColor{0.025f, 0.075f, 0.10f, 1.12f};

    CharacterPose pose{};
    pose.gait_phase = phase;
    pose.animation_weight = movement_weight;

    // Approximately seven-head adult silhouette. These primitives remain a previsualization
    // fixture only; the approval build requires a dedicated skinned character mesh.
    pose.parts[static_cast<std::size_t>(CharacterPart::Torso)] = MakePart(
        {0.0f, 1.48f + bob + completion_lift, 0.0f},
        {0.018f * std::sin(phase * 0.5f), 0.0f, stride * 0.035f},
        {0.34f, 0.34f, 0.22f}, hard_shell, 0U);
    pose.parts[static_cast<std::size_t>(CharacterPart::Head)] = MakePart(
        {0.0f, 2.00f + bob + completion_lift, 0.0f},
        {0.0f, std::sin(safe_time * 0.42f) * 0.055f, 0.0f},
        {0.20f, 0.15f, 0.20f}, helmet, 2U);
    pose.parts[static_cast<std::size_t>(CharacterPart::Pelvis)] = MakePart(
        {0.0f, 1.04f + bob + completion_lift, 0.0f},
        {0.0f, 0.0f, -stride * 0.025f},
        {0.30f, 0.16f, 0.21f}, mechanisms, 0U);
    pose.parts[static_cast<std::size_t>(CharacterPart::LeftArm)] = MakePart(
        {-0.47f, 1.43f + bob + completion_lift, 0.0f},
        {counter_stride, 0.0f, -0.055f},
        {0.115f, 0.38f, 0.115f}, suit_fabric, 2U);
    pose.parts[static_cast<std::size_t>(CharacterPart::RightArm)] = MakePart(
        {0.47f, 1.43f + bob + completion_lift, 0.0f},
        {stride, 0.0f, 0.055f},
        {0.115f, 0.38f, 0.115f}, suit_fabric, 2U);
    pose.parts[static_cast<std::size_t>(CharacterPart::LeftLeg)] = MakePart(
        {-0.18f, 0.48f + completion_lift, 0.0f},
        {stride, 0.0f, 0.0f},
        {0.135f, 0.48f, 0.15f}, mechanisms, 2U);
    pose.parts[static_cast<std::size_t>(CharacterPart::RightLeg)] = MakePart(
        {0.18f, 0.48f + completion_lift, 0.0f},
        {counter_stride, 0.0f, 0.0f},
        {0.135f, 0.48f, 0.15f}, mechanisms, 2U);
    pose.parts[static_cast<std::size_t>(CharacterPart::Backpack)] = MakePart(
        {0.0f, 1.48f + bob + completion_lift, -0.27f},
        {0.0f, 0.0f, 0.0f},
        {0.25f, 0.32f, 0.105f}, pack, 0U);
    pose.parts[static_cast<std::size_t>(CharacterPart::Visor)] = MakePart(
        {0.0f, 2.00f + bob + completion_lift, 0.205f},
        {0.0f, 0.0f, 0.0f},
        {0.165f, 0.085f, 0.040f}, visor, 0U);
    return pose;
}

bool ValidateCharacterPose(const CharacterPose& pose) noexcept
{
    if (!Finite(pose.gait_phase) || !Finite(pose.animation_weight)
        || pose.animation_weight < 0.0f || pose.animation_weight > 1.0f)
    {
        return false;
    }
    for (const CharacterPartPose& part : pose.parts)
    {
        const std::array<float, 13> values = {
            part.offset.x, part.offset.y, part.offset.z,
            part.rotation_radians.x, part.rotation_radians.y, part.rotation_radians.z,
            part.scale.x, part.scale.y, part.scale.z,
            part.tint.r, part.tint.g, part.tint.b, part.tint.a,
        };
        for (const float value : values)
        {
            if (!Finite(value))
            {
                return false;
            }
        }
        if (part.scale.x <= 0.0f || part.scale.y <= 0.0f || part.scale.z <= 0.0f
            || part.mesh_slot > 3U)
        {
            return false;
        }
    }
    return true;
}

std::uint64_t HashCharacterPose(const CharacterPose& pose) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    HashFloat(hash, pose.gait_phase);
    HashFloat(hash, pose.animation_weight);
    for (const CharacterPartPose& part : pose.parts)
    {
        HashFloat(hash, part.offset.x);
        HashFloat(hash, part.offset.y);
        HashFloat(hash, part.offset.z);
        HashFloat(hash, part.rotation_radians.x);
        HashFloat(hash, part.rotation_radians.y);
        HashFloat(hash, part.rotation_radians.z);
        HashFloat(hash, part.scale.x);
        HashFloat(hash, part.scale.y);
        HashFloat(hash, part.scale.z);
        HashFloat(hash, part.tint.r);
        HashFloat(hash, part.tint.g);
        HashFloat(hash, part.tint.b);
        HashFloat(hash, part.tint.a);
        hash ^= part.mesh_slot;
        hash *= kFnvPrime;
    }
    return hash;
}
} // namespace mars::game
