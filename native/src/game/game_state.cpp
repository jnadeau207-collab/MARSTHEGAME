#include "game/game_state.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <span>
#include <stdexcept>

namespace mars::game
{
namespace
{
constexpr float kObjectiveRadius = 1.6f;
constexpr float kPlayerRadius = 0.42f;
constexpr float kWalkSpeed = 5.0f;
constexpr float kSprintSpeed = 8.0f;
constexpr float kAcceleration = 18.0f;
constexpr float kDamping = 10.0f;
constexpr float kMinimumX = -10.5f;
constexpr float kMaximumX = 10.5f;
constexpr float kMinimumZ = -10.0f;
constexpr float kMaximumZ = 20.0f;

float Approach(const float current, const float target, const float max_delta)
{
    if (current < target)
    {
        return (std::min)(current + max_delta, target);
    }
    return (std::max)(current - max_delta, target);
}

bool Finite(const DirectX::XMFLOAT3 value) noexcept
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

renderer::MeshKind ToRenderMeshKind(const assets::SceneMeshKind mesh)
{
    switch (mesh)
    {
    case assets::SceneMeshKind::Cube:
        return renderer::MeshKind::Cube;
    case assets::SceneMeshKind::MarsRock:
        return renderer::MeshKind::MarsRock;
    case assets::SceneMeshKind::BeaconColumn:
        return renderer::MeshKind::BeaconColumn;
    case assets::SceneMeshKind::TerrainPatch:
        return renderer::MeshKind::TerrainPatch;
    }
    throw std::invalid_argument("Scene contains an unsupported generated mesh kind");
}

renderer::MeshKind ToRenderMeshKind(const std::uint32_t slot)
{
    if (slot >= static_cast<std::uint32_t>(renderer::MeshKind::Count))
    {
        throw std::invalid_argument("Character rig contains an invalid generated mesh slot");
    }
    return static_cast<renderer::MeshKind>(slot);
}

renderer::RenderInstance RigInstance(
    const DirectX::XMFLOAT3 player_position,
    const CharacterPartPose& part)
{
    return {
        .position = {
            player_position.x + part.offset.x,
            player_position.y + part.offset.y,
            player_position.z + part.offset.z,
        },
        .rotation_radians = {
            part.rotation_radians.x,
            part.rotation_radians.y,
            part.rotation_radians.z,
        },
        .scale = {part.scale.x, part.scale.y, part.scale.z},
        .tint = {part.tint.r, part.tint.g, part.tint.b, part.tint.a},
        .mesh = ToRenderMeshKind(part.mesh_slot),
        .material_slot = part.material_slot,
    };
}
} // namespace

GameState::GameState(const assets::SceneDefinition& scene)
{
    InitializeScene(scene);
    Reset();
}

void GameState::InitializeScene(const assets::SceneDefinition& scene)
{
    if (scene.schema_version != assets::SceneDefinition::kSchemaVersion || scene.entities.empty())
    {
        throw std::invalid_argument("GameState requires a valid cooked scene definition");
    }

    base_instances_.clear();
    collision_boxes_.clear();
    player_instance_index_ = kInvalidIndex;
    checkpoint_instance_index_ = kInvalidIndex;
    objective_instance_index_ = kInvalidIndex;

    for (const assets::SceneEntity& entity : scene.entities)
    {
        std::size_t render_index = kInvalidIndex;
        if (assets::HasFlag(entity, assets::SceneEntityRender))
        {
            const assets::SceneMeshKind scene_mesh = assets::MeshKindForEntity(entity);
            render_index = base_instances_.size();
            base_instances_.push_back({
                .position = entity.position,
                .rotation_radians = {},
                .scale = entity.scale,
                .tint = entity.tint,
                .mesh = ToRenderMeshKind(scene_mesh),
                .material_slot = static_cast<std::uint32_t>(scene_mesh),
            });
        }
        if (assets::HasFlag(entity, assets::SceneEntityCollider))
        {
            collision_boxes_.push_back({
                .min_x = entity.position.x - entity.scale.x,
                .max_x = entity.position.x + entity.scale.x,
                .min_z = entity.position.z - entity.scale.z,
                .max_z = entity.position.z + entity.scale.z,
            });
        }
        if (assets::HasFlag(entity, assets::SceneEntityPlayer))
        {
            if (render_index == kInvalidIndex || player_instance_index_ != kInvalidIndex)
            {
                throw std::invalid_argument("Scene requires one renderable player entity");
            }
            landing_position_ = entity.position;
            player_instance_index_ = render_index;
        }
        if (assets::HasFlag(entity, assets::SceneEntityCheckpoint))
        {
            if (render_index == kInvalidIndex || checkpoint_instance_index_ != kInvalidIndex)
            {
                throw std::invalid_argument("Scene requires one renderable checkpoint entity");
            }
            checkpoint_position_ = entity.position;
            checkpoint_instance_index_ = render_index;
        }
        if (assets::HasFlag(entity, assets::SceneEntityObjective))
        {
            if (render_index == kInvalidIndex || objective_instance_index_ != kInvalidIndex)
            {
                throw std::invalid_argument("Scene requires one renderable objective entity");
            }
            objective_position_ = entity.position;
            objective_instance_index_ = render_index;
        }
    }

    if (player_instance_index_ == kInvalidIndex || checkpoint_instance_index_ == kInvalidIndex
        || objective_instance_index_ == kInvalidIndex || collision_boxes_.empty())
    {
        throw std::invalid_argument("Scene is missing required gameplay entities or collision");
    }
    checkpoint_position_.y = landing_position_.y;
    instances_ = base_instances_;
}

void GameState::Reset()
{
    player_position_ = landing_position_;
    player_velocity_ = {};
    accumulator_seconds_ = 0.0f;
    elapsed_seconds_ = 0.0f;
    reset_latched_ = false;
    checkpoint_latched_ = false;
    checkpoint_reached_ = false;
    mission_state_ = MissionState::Traverse;
    RebuildScene();
}

void GameState::RestoreCheckpoint()
{
    if (!checkpoint_reached_)
    {
        Reset();
        return;
    }
    player_position_ = checkpoint_position_;
    player_velocity_ = {};
    accumulator_seconds_ = 0.0f;
    mission_state_ = MissionState::Traverse;
    RebuildScene();
}

void GameState::Restore(const GameSnapshot& snapshot)
{
    if (snapshot.schema_version != GameSnapshot::kSchemaVersion)
    {
        throw std::invalid_argument("Unsupported native game snapshot schema");
    }
    if (!Finite(snapshot.player_position) || !Finite(snapshot.player_velocity)
        || !std::isfinite(snapshot.elapsed_seconds) || snapshot.elapsed_seconds < 0.0f)
    {
        throw std::invalid_argument("Native game snapshot contains invalid values");
    }
    if (snapshot.mission_state != MissionState::Traverse
        && snapshot.mission_state != MissionState::Complete)
    {
        throw std::invalid_argument("Native game snapshot contains an invalid mission state");
    }
    if (snapshot.player_position.x < kMinimumX || snapshot.player_position.x > kMaximumX
        || snapshot.player_position.z < kMinimumZ || snapshot.player_position.z > kMaximumZ)
    {
        throw std::invalid_argument("Native game snapshot is outside mission bounds");
    }
    for (const CollisionBox& box : collision_boxes_)
    {
        if (CircleIntersectsBox(
                snapshot.player_position.x,
                snapshot.player_position.z,
                kPlayerRadius,
                box))
        {
            throw std::invalid_argument("Native game snapshot intersects scene collision");
        }
    }

    player_position_ = snapshot.player_position;
    player_velocity_ = snapshot.player_velocity;
    elapsed_seconds_ = snapshot.elapsed_seconds;
    mission_state_ = snapshot.mission_state;
    checkpoint_reached_ = snapshot.checkpoint_reached;
    accumulator_seconds_ = 0.0f;
    reset_latched_ = false;
    checkpoint_latched_ = false;
    RebuildScene();
}

void GameState::Update(const InputState& input, const float delta_seconds)
{
    if (input.reset && !reset_latched_)
    {
        Reset();
        reset_latched_ = true;
        return;
    }
    reset_latched_ = input.reset;

    if (input.restore_checkpoint && !checkpoint_latched_)
    {
        RestoreCheckpoint();
        checkpoint_latched_ = true;
        return;
    }
    checkpoint_latched_ = input.restore_checkpoint;

    const float bounded_delta = (std::clamp)(delta_seconds, 0.0f, 0.25f);
    accumulator_seconds_ += bounded_delta;
    while (accumulator_seconds_ >= kFixedStepSeconds)
    {
        IntegrateFixedStep(input);
        accumulator_seconds_ -= kFixedStepSeconds;
        elapsed_seconds_ += kFixedStepSeconds;
    }
    RebuildScene();
}

GameSnapshot GameState::Snapshot() const noexcept
{
    return {
        .schema_version = GameSnapshot::kSchemaVersion,
        .player_position = player_position_,
        .player_velocity = player_velocity_,
        .elapsed_seconds = elapsed_seconds_,
        .mission_state = mission_state_,
        .checkpoint_reached = checkpoint_reached_,
    };
}

MissionState GameState::Mission() const noexcept
{
    return mission_state_;
}

bool GameState::CheckpointReached() const noexcept
{
    return checkpoint_reached_;
}

DirectX::XMFLOAT3 GameState::PlayerPosition() const noexcept
{
    return player_position_;
}

renderer::RenderScene GameState::Scene() const noexcept
{
    const float lateral_velocity = player_velocity_.x * 0.030f;
    const float reveal_progress = (std::clamp)(
        (player_position_.z - landing_position_.z) / 6.0f,
        0.0f,
        1.0f);
    const float shoulder_offset = 0.98f - reveal_progress * 0.22f;
    const float relay_bias = (objective_position_.x - player_position_.x) * 0.065f * reveal_progress;
    const DirectX::XMFLOAT3 eye{
        player_position_.x + shoulder_offset - lateral_velocity,
        player_position_.y + 2.72f,
        player_position_.z - 5.65f,
    };
    const DirectX::XMFLOAT3 target{
        player_position_.x + relay_bias + lateral_velocity * 0.30f,
        player_position_.y + 1.20f,
        player_position_.z + 4.65f,
    };
    const DirectX::XMFLOAT4 clear = mission_state_ == MissionState::Complete
        ? DirectX::XMFLOAT4{0.020f, 0.030f, 0.027f, 1.0f}
        : DirectX::XMFLOAT4{0.028f, 0.020f, 0.016f, 1.0f};
    const std::array<renderer::PointLight, 4> lights = {{
        {
            .position = {objective_position_.x, objective_position_.y + 0.75f, objective_position_.z},
            .radius = mission_state_ == MissionState::Complete ? 7.0f : 4.8f,
            .color = mission_state_ == MissionState::Complete
                ? DirectX::XMFLOAT3{0.12f, 0.62f, 0.48f}
                : DirectX::XMFLOAT3{0.08f, 0.30f, 0.50f},
            .intensity = mission_state_ == MissionState::Complete ? 3.0f : 1.05f,
        },
        {
            .position = {checkpoint_position_.x, checkpoint_position_.y + 0.65f, checkpoint_position_.z},
            .radius = 3.6f,
            .color = {0.92f, 0.38f, 0.11f},
            .intensity = checkpoint_reached_ ? 0.95f : 0.55f,
        },
        {
            .position = {player_position_.x, player_position_.y + 1.58f, player_position_.z - 0.28f},
            .radius = 2.4f,
            .color = {0.18f, 0.42f, 0.55f},
            .intensity = 0.48f,
        },
        {
            .position = {-2.0f, 1.15f, 13.4f},
            .radius = 5.4f,
            .color = {0.94f, 0.36f, 0.10f},
            .intensity = 1.35f,
        },
    }};
    return {
        .camera_eye = eye,
        .camera_target = target,
        .clear_color = clear,
        .point_lights = lights,
        .particle_emitter = {objective_position_.x, objective_position_.y + 0.45f, objective_position_.z},
        .elapsed_seconds = elapsed_seconds_,
        .player_velocity = player_velocity_,
        .target_exposure = mission_state_ == MissionState::Complete ? 1.04f : 0.98f,
        .mission_complete = mission_state_ == MissionState::Complete,
        .supplemental_character_instances = supplemental_character_instances_,
        .supplemental_character_count = static_cast<std::uint32_t>(supplemental_character_instances_.size()),
        .instances = std::span<const renderer::RenderInstance>(instances_),
    };
}

void GameState::IntegrateFixedStep(const InputState& input)
{
    if (mission_state_ == MissionState::Complete)
    {
        player_velocity_.x = Approach(player_velocity_.x, 0.0f, kDamping * kFixedStepSeconds);
        player_velocity_.z = Approach(player_velocity_.z, 0.0f, kDamping * kFixedStepSeconds);
        return;
    }

    float move_x = (std::clamp)(input.move_x, -1.0f, 1.0f);
    float move_z = (std::clamp)(input.move_z, -1.0f, 1.0f);
    const float magnitude = std::sqrt(move_x * move_x + move_z * move_z);
    if (magnitude > 1.0f)
    {
        move_x /= magnitude;
        move_z /= magnitude;
    }

    const float speed = input.sprint ? kSprintSpeed : kWalkSpeed;
    const float target_x = move_x * speed;
    const float target_z = move_z * speed;
    const float acceleration = (move_x == 0.0f && move_z == 0.0f) ? kDamping : kAcceleration;
    player_velocity_.x = Approach(
        player_velocity_.x,
        target_x,
        acceleration * kFixedStepSeconds);
    player_velocity_.z = Approach(
        player_velocity_.z,
        target_z,
        acceleration * kFixedStepSeconds);

    const DirectX::XMFLOAT2 before{player_position_.x, player_position_.z};
    const DirectX::XMFLOAT2 desired{
        player_velocity_.x * kFixedStepSeconds,
        player_velocity_.z * kFixedStepSeconds,
    };
    DirectX::XMFLOAT2 resolved = ResolvePlanarMovement(
        before,
        desired,
        kPlayerRadius,
        std::span<const CollisionBox>(collision_boxes_));
    resolved.x = (std::clamp)(resolved.x, kMinimumX, kMaximumX);
    resolved.y = (std::clamp)(resolved.y, kMinimumZ, kMaximumZ);
    if (resolved.x == before.x && desired.x != 0.0f)
    {
        player_velocity_.x = 0.0f;
    }
    if (resolved.y == before.y && desired.y != 0.0f)
    {
        player_velocity_.z = 0.0f;
    }
    player_position_.x = resolved.x;
    player_position_.z = resolved.y;

    if (!checkpoint_reached_ && player_position_.z >= checkpoint_position_.z)
    {
        checkpoint_reached_ = true;
    }

    const float objective_dx = player_position_.x - objective_position_.x;
    const float objective_dz = player_position_.z - objective_position_.z;
    if (objective_dx * objective_dx + objective_dz * objective_dz <= kObjectiveRadius * kObjectiveRadius)
    {
        mission_state_ = MissionState::Complete;
    }
}

void GameState::RebuildScene()
{
    instances_ = base_instances_;
    const float planar_speed = std::sqrt(
        player_velocity_.x * player_velocity_.x + player_velocity_.z * player_velocity_.z);
    const CharacterPose pose = EvaluateCharacterPose(
        elapsed_seconds_,
        planar_speed,
        mission_state_ == MissionState::Complete);
    instances_[player_instance_index_] = RigInstance(
        player_position_,
        pose.parts[static_cast<std::size_t>(CharacterPart::Torso)]);
    for (std::size_t part_index = 1; part_index < kCharacterPartCount; ++part_index)
    {
        supplemental_character_instances_[part_index - 1U] = RigInstance(
            player_position_,
            pose.parts[part_index]);
    }

    renderer::RenderInstance& objective = instances_[objective_instance_index_];
    objective.scale = base_instances_[objective_instance_index_].scale;
    objective.tint = mission_state_ == MissionState::Complete
        ? DirectX::XMFLOAT4{0.10f, 0.48f, 0.36f, 2.15f}
        : base_instances_[objective_instance_index_].tint;

    instances_[checkpoint_instance_index_].tint = checkpoint_reached_
        ? DirectX::XMFLOAT4{0.38f, 0.31f, 0.20f, 1.0f}
        : base_instances_[checkpoint_instance_index_].tint;
}
} // namespace mars::game
