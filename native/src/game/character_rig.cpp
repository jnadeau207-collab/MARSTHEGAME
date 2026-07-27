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
constexpr std::uint32_t kRoundedBoxMesh = 0U;
constexpr std::uint32_t kRoundedColumnMesh = 2U;

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

void SetPart(
    CharacterPose& pose,
    const CharacterPart part,
    const CharacterPartPose value) noexcept
{
    pose.parts[static_cast<std::size_t>(part)] = value;
}

bool Finite(const float value) noexcept
{
    return std::isfinite(value);
}

void HashFloat(std::uint64_t& hash, const float value) noexcept
{
    const std::uint32_t word = std::bit_cast<std::uint32_t>(value);
    for (std::uint32_t shift = 0; shift < 32U; shift += 8U)
    {
        hash ^= static_cast<std::uint8_t>(word >> shift);
        hash *= kFnvPrime;
    }
}

RigVector3 LimbDirection(const float angle) noexcept
{
    return {0.0f, -std::cos(angle), -std::sin(angle)};
}

RigVector3 Add(const RigVector3 first, const RigVector3 second) noexcept
{
    return {first.x + second.x, first.y + second.y, first.z + second.z};
}

RigVector3 Scale(const RigVector3 value, const float scale) noexcept
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

RigVector3 SegmentCenter(
    const RigVector3 joint,
    const float angle,
    const float length) noexcept
{
    return Add(joint, Scale(LimbDirection(angle), length * 0.5f));
}

RigVector3 SegmentEnd(
    const RigVector3 joint,
    const float angle,
    const float length) noexcept
{
    return Add(joint, Scale(LimbDirection(angle), length));
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
    const float cadence = 1.75f + safe_speed * 0.46f;
    const float phase = safe_time * cadence;
    const float gait = std::sin(phase);
    const float stride = gait * 0.46f * movement_weight;
    const float body_bob = std::abs(gait) * 0.025f * movement_weight;
    const float breathing = std::sin(safe_time * 1.55f) * 0.008f;
    const float completion_lift = mission_complete ? 0.012f : 0.0f;
    const float left_knee_bend = (std::max)(0.0f, gait) * 0.28f * movement_weight;
    const float right_knee_bend = (std::max)(0.0f, -gait) * 0.28f * movement_weight;

    const RigColor suit_fabric{0.42f, 0.405f, 0.37f, 1.0f};
    const RigColor abrasion_fabric{0.285f, 0.295f, 0.29f, 1.0f};
    const RigColor hard_shell{0.58f, 0.51f, 0.34f, 1.0f};
    const RigColor mechanisms{0.085f, 0.095f, 0.10f, 1.0f};
    const RigColor helmet{0.48f, 0.49f, 0.47f, 1.0f};
    const RigColor pack{0.095f, 0.105f, 0.11f, 1.0f};
    const RigColor visor = mission_complete
        ? RigColor{0.045f, 0.19f, 0.155f, 1.18f}
        : RigColor{0.022f, 0.060f, 0.078f, 1.02f};

    CharacterPose pose{};
    pose.gait_phase = phase;
    pose.animation_weight = movement_weight;

    const float torso_y = 1.43f + body_bob + breathing + completion_lift;
    SetPart(pose, CharacterPart::Torso, MakePart(
        {0.0f, torso_y, 0.0f},
        {0.014f * std::sin(phase * 0.5f), 0.0f, stride * 0.025f},
        {0.29f, 0.34f, 0.19f},
        suit_fabric,
        kRoundedBoxMesh));
    SetPart(pose, CharacterPart::ChestPlate, MakePart(
        {0.0f, torso_y + 0.075f, 0.175f},
        {0.0f, 0.0f, stride * 0.018f},
        {0.30f, 0.19f, 0.095f},
        hard_shell,
        kRoundedBoxMesh));
    SetPart(pose, CharacterPart::Head, MakePart(
        {0.0f, 1.97f + body_bob + completion_lift, 0.0f},
        {0.0f, std::sin(safe_time * 0.38f) * 0.045f, 0.0f},
        {0.20f, 0.17f, 0.20f},
        helmet,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::HelmetRing, MakePart(
        {0.0f, 1.80f + body_bob + completion_lift, 0.0f},
        {},
        {0.225f, 0.055f, 0.225f},
        mechanisms,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::Pelvis, MakePart(
        {0.0f, 1.025f + body_bob * 0.45f + completion_lift, 0.0f},
        {0.0f, 0.0f, -stride * 0.020f},
        {0.245f, 0.15f, 0.18f},
        abrasion_fabric,
        kRoundedBoxMesh));

    SetPart(pose, CharacterPart::LeftShoulder, MakePart(
        {-0.405f, 1.58f + body_bob + completion_lift, 0.015f},
        {0.0f, 0.0f, -0.12f},
        {0.13f, 0.12f, 0.16f},
        hard_shell,
        kRoundedBoxMesh));
    SetPart(pose, CharacterPart::RightShoulder, MakePart(
        {0.405f, 1.58f + body_bob + completion_lift, 0.015f},
        {0.0f, 0.0f, 0.12f},
        {0.13f, 0.12f, 0.16f},
        hard_shell,
        kRoundedBoxMesh));

    constexpr float upper_arm_length = 0.34f;
    constexpr float forearm_length = 0.32f;
    const float left_arm_angle = -stride * 0.86f - 0.045f;
    const float right_arm_angle = stride * 0.86f - 0.045f;
    const RigVector3 left_shoulder{-0.47f, 1.56f + body_bob + completion_lift, 0.0f};
    const RigVector3 right_shoulder{0.47f, 1.56f + body_bob + completion_lift, 0.0f};
    const RigVector3 left_elbow = SegmentEnd(left_shoulder, left_arm_angle, upper_arm_length);
    const RigVector3 right_elbow = SegmentEnd(right_shoulder, right_arm_angle, upper_arm_length);
    const float left_forearm_angle = left_arm_angle * 0.54f - 0.055f;
    const float right_forearm_angle = right_arm_angle * 0.54f - 0.055f;

    SetPart(pose, CharacterPart::LeftUpperArm, MakePart(
        SegmentCenter(left_shoulder, left_arm_angle, upper_arm_length),
        {left_arm_angle, 0.0f, -0.025f},
        {0.098f, upper_arm_length * 0.5f, 0.10f},
        suit_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::LeftForearm, MakePart(
        SegmentCenter(left_elbow, left_forearm_angle, forearm_length),
        {left_forearm_angle, 0.0f, -0.015f},
        {0.088f, forearm_length * 0.5f, 0.092f},
        abrasion_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::RightUpperArm, MakePart(
        SegmentCenter(right_shoulder, right_arm_angle, upper_arm_length),
        {right_arm_angle, 0.0f, 0.025f},
        {0.098f, upper_arm_length * 0.5f, 0.10f},
        suit_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::RightForearm, MakePart(
        SegmentCenter(right_elbow, right_forearm_angle, forearm_length),
        {right_forearm_angle, 0.0f, 0.015f},
        {0.088f, forearm_length * 0.5f, 0.092f},
        abrasion_fabric,
        kRoundedColumnMesh));

    constexpr float thigh_length = 0.39f;
    constexpr float shin_length = 0.41f;
    const float left_thigh_angle = stride;
    const float right_thigh_angle = -stride;
    const float left_shin_angle = left_thigh_angle * 0.32f - left_knee_bend;
    const float right_shin_angle = right_thigh_angle * 0.32f - right_knee_bend;
    const RigVector3 left_hip{-0.16f, 0.98f + body_bob * 0.35f + completion_lift, 0.0f};
    const RigVector3 right_hip{0.16f, 0.98f + body_bob * 0.35f + completion_lift, 0.0f};
    const RigVector3 left_knee = SegmentEnd(left_hip, left_thigh_angle, thigh_length);
    const RigVector3 right_knee = SegmentEnd(right_hip, right_thigh_angle, thigh_length);
    const RigVector3 left_ankle = SegmentEnd(left_knee, left_shin_angle, shin_length);
    const RigVector3 right_ankle = SegmentEnd(right_knee, right_shin_angle, shin_length);

    SetPart(pose, CharacterPart::LeftThigh, MakePart(
        SegmentCenter(left_hip, left_thigh_angle, thigh_length),
        {left_thigh_angle, 0.0f, 0.0f},
        {0.12f, thigh_length * 0.5f, 0.13f},
        suit_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::LeftShin, MakePart(
        SegmentCenter(left_knee, left_shin_angle, shin_length),
        {left_shin_angle, 0.0f, 0.0f},
        {0.105f, shin_length * 0.5f, 0.115f},
        abrasion_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::RightThigh, MakePart(
        SegmentCenter(right_hip, right_thigh_angle, thigh_length),
        {right_thigh_angle, 0.0f, 0.0f},
        {0.12f, thigh_length * 0.5f, 0.13f},
        suit_fabric,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::RightShin, MakePart(
        SegmentCenter(right_knee, right_shin_angle, shin_length),
        {right_shin_angle, 0.0f, 0.0f},
        {0.105f, shin_length * 0.5f, 0.115f},
        abrasion_fabric,
        kRoundedColumnMesh));

    const float left_foot_lift = (std::max)(0.0f, gait) * 0.055f * movement_weight;
    const float right_foot_lift = (std::max)(0.0f, -gait) * 0.055f * movement_weight;
    SetPart(pose, CharacterPart::LeftBoot, MakePart(
        {left_ankle.x, 0.13f + left_foot_lift + completion_lift, left_ankle.z + 0.115f},
        {left_thigh_angle * 0.16f, 0.0f, 0.0f},
        {0.135f, 0.105f, 0.22f},
        mechanisms,
        kRoundedBoxMesh));
    SetPart(pose, CharacterPart::RightBoot, MakePart(
        {right_ankle.x, 0.13f + right_foot_lift + completion_lift, right_ankle.z + 0.115f},
        {right_thigh_angle * 0.16f, 0.0f, 0.0f},
        {0.135f, 0.105f, 0.22f},
        mechanisms,
        kRoundedBoxMesh));

    SetPart(pose, CharacterPart::Backpack, MakePart(
        {0.0f, 1.40f + body_bob + completion_lift, -0.27f},
        {},
        {0.23f, 0.30f, 0.105f},
        pack,
        kRoundedBoxMesh));
    SetPart(pose, CharacterPart::PackCanisterLeft, MakePart(
        {-0.165f, 1.40f + body_bob + completion_lift, -0.39f},
        {},
        {0.055f, 0.20f, 0.055f},
        mechanisms,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::PackCanisterRight, MakePart(
        {0.165f, 1.40f + body_bob + completion_lift, -0.39f},
        {},
        {0.055f, 0.20f, 0.055f},
        mechanisms,
        kRoundedColumnMesh));
    SetPart(pose, CharacterPart::Visor, MakePart(
        {0.0f, 1.98f + body_bob + completion_lift, 0.205f},
        {},
        {0.158f, 0.074f, 0.037f},
        visor,
        kRoundedBoxMesh));
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
