#include "game/game_state.h"

#include <algorithm>
#include <cmath>

namespace mars::game
{
namespace
{
constexpr DirectX::XMFLOAT3 kObjectivePosition{0.0f, 0.0f, 18.0f};
constexpr float kObjectiveRadius = 1.6f;
constexpr float kWalkSpeed = 5.0f;
constexpr float kSprintSpeed = 8.0f;
constexpr float kAcceleration = 18.0f;
constexpr float kDamping = 10.0f;

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
} // namespace

GameState::GameState()
{
    Reset();
}

void GameState::Reset()
{
    player_position_ = {0.0f, 0.0f, -8.0f};
    player_velocity_ = {};
    accumulator_seconds_ = 0.0f;
    elapsed_seconds_ = 0.0f;
    reset_latched_ = false;
    mission_state_ = MissionState::Traverse;
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

MissionState GameState::Mission() const noexcept
{
    return mission_state_;
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

    player_position_.x += player_velocity_.x * kFixedStepSeconds;
    player_position_.z += player_velocity_.z * kFixedStepSeconds;
    player_position_.x = (std::clamp)(player_position_.x, -10.5f, 10.5f);
    player_position_.z = (std::clamp)(player_position_.z, -10.0f, 20.0f);

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
    instances_[17] = Instance({0.0f, -0.35f, 18.0f}, {2.0f, 0.12f, 2.0f}, structure);
}
} // namespace mars::game
