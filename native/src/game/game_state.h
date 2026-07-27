#pragma once

#include "renderer/render_scene.h"

#include <DirectXMath.h>

#include <array>
#include <cstddef>
#include <cstdint>

namespace mars::game
{
struct InputState
{
    float move_x = 0.0f;
    float move_z = 0.0f;
    bool sprint = false;
    bool reset = false;
    bool restore_checkpoint = false;
};

enum class MissionState : std::uint32_t
{
    Traverse = 0,
    Complete = 1,
};

struct GameSnapshot
{
    static constexpr std::uint32_t kSchemaVersion = 1;

    std::uint32_t schema_version = kSchemaVersion;
    DirectX::XMFLOAT3 player_position{0.0f, 0.0f, -8.0f};
    DirectX::XMFLOAT3 player_velocity{};
    float elapsed_seconds = 0.0f;
    MissionState mission_state = MissionState::Traverse;
    bool checkpoint_reached = false;
};

class GameState final
{
public:
    static constexpr float kFixedStepSeconds = 1.0f / 60.0f;

    GameState();

    void Reset();
    void RestoreCheckpoint();
    void Restore(const GameSnapshot& snapshot);
    void Update(const InputState& input, float delta_seconds);

    [[nodiscard]] GameSnapshot Snapshot() const noexcept;
    [[nodiscard]] MissionState Mission() const noexcept;
    [[nodiscard]] bool CheckpointReached() const noexcept;
    [[nodiscard]] DirectX::XMFLOAT3 PlayerPosition() const noexcept;
    [[nodiscard]] renderer::RenderScene Scene() const noexcept;

private:
    static constexpr std::size_t kInstanceCount = 18;

    void RebuildScene();
    void IntegrateFixedStep(const InputState& input);

    std::array<renderer::RenderInstance, kInstanceCount> instances_{};
    DirectX::XMFLOAT3 player_position_{0.0f, 0.0f, -8.0f};
    DirectX::XMFLOAT3 player_velocity_{};
    float accumulator_seconds_ = 0.0f;
    float elapsed_seconds_ = 0.0f;
    bool reset_latched_ = false;
    bool checkpoint_latched_ = false;
    bool checkpoint_reached_ = false;
    MissionState mission_state_ = MissionState::Traverse;
};
} // namespace mars::game
