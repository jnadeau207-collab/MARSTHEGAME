#pragma once

#include <DirectXMath.h>

#include <array>
#include <cstdint>
#include <span>

namespace mars::renderer
{
enum class MeshKind : std::uint32_t
{
    Cube = 0,
    MarsRock = 1,
    BeaconColumn = 2,
    TerrainPatch = 3,
    FieldEngineerTorso = 4,
    FieldEngineerHelmet = 5,
    FieldEngineerLimb = 6,
    Count = 7,
};

struct RenderInstance
{
    DirectX::XMFLOAT3 position{};
    DirectX::XMFLOAT3 rotation_radians{};
    DirectX::XMFLOAT3 scale{1.0f, 1.0f, 1.0f};
    DirectX::XMFLOAT4 tint{1.0f, 1.0f, 1.0f, 1.0f};
    MeshKind mesh = MeshKind::Cube;
    std::uint32_t material_slot = 0;
};

struct PointLight
{
    DirectX::XMFLOAT3 position{};
    float radius = 1.0f;
    DirectX::XMFLOAT3 color{1.0f, 1.0f, 1.0f};
    float intensity = 1.0f;
};

struct RenderScene
{
    DirectX::XMFLOAT3 camera_eye{0.0f, 5.0f, -10.0f};
    DirectX::XMFLOAT3 camera_target{0.0f, 0.0f, 0.0f};
    DirectX::XMFLOAT4 clear_color{0.018f, 0.022f, 0.035f, 1.0f};
    std::array<PointLight, 4> point_lights{};
    DirectX::XMFLOAT3 particle_emitter{};
    float elapsed_seconds = 0.0f;
    DirectX::XMFLOAT3 player_velocity{};
    float target_exposure = 1.0f;
    bool mission_complete = false;
    std::array<RenderInstance, 20> supplemental_character_instances{};
    std::uint32_t supplemental_character_count = 0;
    std::span<const RenderInstance> instances{};
};
} // namespace mars::renderer
