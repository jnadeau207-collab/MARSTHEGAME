#pragma once

#include "renderer/render_scene.h"

#include <DirectXMath.h>

#include <array>
#include <cstddef>

namespace mars::game
{
struct InputState
{
    float move_x = 0.0f;
    float move_z = 0.0f;
    bool sprint = false;
    bool reset = false;
};

enum class MissionState
{
    Traverse,
    Complete,
};

class GameState final
{
public:
    static constexpr float kFixedStepSeconds = 1.0f / 60.0f;

    GameState();

    void Reset();
    void Update(const InputState& input, float delta_seconds);

    [[nodiscard]] MissionState Mission() const noexcept;
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
    MissionState mission_state_ = MissionState::Traverse;
};
} // namespace mars::game
