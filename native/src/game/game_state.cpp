#include "game/game_state.h"

#include "game/collision.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

namespace mars::game
{
namespace
{
constexpr DirectX::XMFLOAT3 kLandingPosition{0.0f, 0.0f, -8.0f};
constexpr DirectX::XMFLOAT3 kCheckpointPosition{0.0f, 0.0f, 5.0f};
constexpr DirectX::XMFLOAT3 kObjectivePosition{0.0f, 0.0f, 18.0f};
constexpr float kObjectiveRadius = 1.6f;
constexpr float kPlayerRadius = 0.42f;
constexpr float kWalkSpeed = 5.0f;
constexpr float kSprintSpeed = 8.0f;
constexpr float kAcceleration = 18.0f;
constexpr float kDamping = 10.0f;

constexpr std::array<CollisionBox, 10> kCollisionBoxes = {{
    {-12.0f, -10.8f, -11.0f, 21.0f},
    {10.8f, 12.0f, -11.0f, 21.0f},
    {-7.4f, -4.6f, -2.8f, 0.8f},
    {5.0f, 8.6f, 1.8f, 4.2f},
    {-5.5f, -3.5f, 8.0f, 10.0f},
    {3.8f, 6.2f, 10.4f, 13.6f},
    {-9.0f, -6.0f, 14.9f, 17.1f},
    {6.3f, 8.7f, 16.8f, 19.2f},
    {-3.48f, -2.92f, 4.72f, 5.28f},
    {2.92f, 3.48f, 4.72f, 5.28f},
}};

float Approach(const float current, const float target, const float max_delta)
{
    if (current < target)
    {
        return (std::min)(current + max_delta, target);
    }
    return (std::max)(current - max_delta, target);
}

renderer::RenderInstance Instance(
    const DirectX::XMFLOAT3 position,
    const DirectX::XMFLOAT3 scale,
    const DirectX::XMFLOAT4 tint)
{
    return {.position = position, .scale = scale, .tint = tint};
}

bool Finite(const DirectX::XMFLOAT3 value) noexcept
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}
} // namespace

GameState::GameState()
{
    Reset();
}

void GameState::Reset()
{
    player_position_ = kLandingPosition;
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
    player_position_ = kCheckpointPosition;
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
    if (snapshot.player_position.x < -10.5f || snapshot.player_position.x > 10.5f
        || snapshot.player_position.z < -10.0f || snapshot.player_position.z > 20.0f)
    {
        throw std::invalid_argument("Native game snapshot is outside mission bounds");
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
    const DirectX::XMFLOAT3 eye{
        player_position_.x,
        player_position_.y + 6.0f,
        player_position_.z - 9.5f,
    };
    const DirectX::XMFLOAT3 target{
        player_position_.x,
        player_position_.y + 0.5f,
        player_position_.z + 3.0f,
    };
    const DirectX::XMFLOAT4 clear = mission_state_ == MissionState::Complete
        ? DirectX::XMFLOAT4{0.025f, 0.060f, 0.052f, 1.0f}
        : DirectX::XMFLOAT4{0.038f, 0.018f, 0.012f, 1.0f};
    return {
        .camera_eye = eye,
        .camera_target = target,
        .clear_color = clear,
        .instances = instances_,
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
    DirectX::XMFLOAT2 resolved = ResolvePlanarMovement(before, desired, kPlayerRadius, kCollisionBoxes);
    resolved.x = (std::clamp)(resolved.x, -10.5f, 10.5f);
    resolved.y = (std::clamp)(resolved.y, -10.0f, 20.0f);
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

    if (!checkpoint_reached_ && player_position_.z >= kCheckpointPosition.z)
    {
        checkpoint_reached_ = true;
    }

    const float objective_dx = player_position_.x - kObjectivePosition.x;
    const float objective_dz = player_position_.z - kObjectivePosition.z;
    if (objective_dx * objective_dx + objective_dz * objective_dz <= kObjectiveRadius * kObjectiveRadius)
    {
        mission_state_ = MissionState::Complete;
    }
}

void GameState::RebuildScene()
{
    const DirectX::XMFLOAT4 mars_ground{0.34f, 0.12f, 0.055f, 1.0f};
    const DirectX::XMFLOAT4 basalt{0.12f, 0.095f, 0.085f, 1.0f};
    const DirectX::XMFLOAT4 structure{0.30f, 0.34f, 0.38f, 1.0f};
    const DirectX::XMFLOAT4 player_tint{0.12f, 0.62f, 0.78f, 1.0f};
    const float pulse = 1.0f + std::sin(elapsed_seconds_ * 4.0f) * 0.12f;
    const DirectX::XMFLOAT4 beacon_tint = mission_state_ == MissionState::Complete
        ? DirectX::XMFLOAT4{0.18f, 0.95f, 0.48f, 1.0f}
        : DirectX::XMFLOAT4{1.0f, 0.62f, 0.08f, 1.0f};

    instances_[0] = Instance({0.0f, -1.25f, 5.0f}, {12.0f, 0.75f, 16.0f}, mars_ground);
    instances_[1] = Instance({0.0f, -0.55f, -8.0f}, {3.5f, 0.18f, 3.5f}, structure);
    instances_[2] = Instance({-11.4f, 1.5f, 5.0f}, {0.6f, 2.7f, 16.0f}, basalt);
    instances_[3] = Instance({11.4f, 1.5f, 5.0f}, {0.6f, 2.7f, 16.0f}, basalt);
    instances_[4] = Instance({-6.0f, 0.0f, -1.0f}, {1.4f, 1.2f, 1.8f}, basalt);
    instances_[5] = Instance({6.8f, 0.2f, 3.0f}, {1.8f, 1.4f, 1.2f}, basalt);
    instances_[6] = Instance({-4.5f, 0.1f, 9.0f}, {1.0f, 1.3f, 1.0f}, basalt);
    instances_[7] = Instance({5.0f, 0.0f, 12.0f}, {1.2f, 1.1f, 1.6f}, basalt);
    instances_[8] = Instance({-7.5f, 0.3f, 16.0f}, {1.5f, 1.5f, 1.1f}, basalt);
    instances_[9] = Instance({7.5f, 0.2f, 18.0f}, {1.2f, 1.4f, 1.2f}, basalt);
    instances_[10] = Instance({-3.2f, 0.1f, 5.0f}, {0.28f, 1.6f, 0.28f}, structure);
    instances_[11] = Instance({3.2f, 0.1f, 5.0f}, {0.28f, 1.6f, 0.28f}, structure);
    instances_[12] = Instance({0.0f, 1.8f, 5.0f}, {3.5f, 0.22f, 0.22f}, structure);
    instances_[13] = Instance({-2.4f, 0.0f, 14.5f}, {0.25f, 1.2f, 0.25f}, structure);
    instances_[14] = Instance({2.4f, 0.0f, 14.5f}, {0.25f, 1.2f, 0.25f}, structure);
    instances_[15] = Instance(
        {kObjectivePosition.x, 1.0f, kObjectivePosition.z},
        {0.38f * pulse, 2.0f * pulse, 0.38f * pulse},
        beacon_tint);
    instances_[16] = Instance(
        {player_position_.x, player_position_.y, player_position_.z},
        {0.45f, 0.72f, 0.45f},
        player_tint);
    const DirectX::XMFLOAT4 checkpoint_tint = checkpoint_reached_
        ? DirectX::XMFLOAT4{0.20f, 0.78f, 0.44f, 1.0f}
        : structure;
    instances_[17] = Instance({0.0f, -0.35f, 5.0f}, {1.8f, 0.12f, 1.8f}, checkpoint_tint);
}
} // namespace mars::game
