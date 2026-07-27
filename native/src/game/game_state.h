#pragma once

#include "assets/scene_asset.h"
#include "game/character_rig.h"
#include "game/collision.h"
#include "renderer/render_scene.h"

#include <DirectXMath.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

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
    DirectX::XMFLOAT3 player_position{};
    DirectX::XMFLOAT3 player_velocity{};
    float elapsed_seconds = 0.0f;
    MissionState mission_state = MissionState::Traverse;
    bool checkpoint_reached = false;
};

class GameState final
{
public:
    static constexpr float kFixedStepSeconds = 1.0f / 60.0f;

    explicit GameState(const assets::SceneDefinition& scene);

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
    static constexpr std::size_t kInvalidIndex = (std::numeric_limits<std::size_t>::max)();

    void InitializeScene(const assets::SceneDefinition& scene);
    void RebuildScene();
    void IntegrateFixedStep(const InputState& input);

    std::vector<renderer::RenderInstance> base_instances_{};
    std::vector<renderer::RenderInstance> instances_{};
    std::vector<CollisionBox> collision_boxes_{};
    std::array<std::size_t, kCharacterPartCount> character_instance_indices_{};
    DirectX::XMFLOAT3 landing_position_{};
    DirectX::XMFLOAT3 checkpoint_position_{};
    DirectX::XMFLOAT3 objective_position_{};
    DirectX::XMFLOAT3 player_position_{};
    DirectX::XMFLOAT3 player_velocity_{};
    std::size_t player_instance_index_ = kInvalidIndex;
    std::size_t checkpoint_instance_index_ = kInvalidIndex;
    std::size_t objective_instance_index_ = kInvalidIndex;
    float accumulator_seconds_ = 0.0f;
    float elapsed_seconds_ = 0.0f;
    bool reset_latched_ = false;
    bool checkpoint_latched_ = false;
    bool checkpoint_reached_ = false;
    MissionState mission_state_ = MissionState::Traverse;
};
} // namespace mars::game
