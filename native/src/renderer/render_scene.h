#pragma once

#include <DirectXMath.h>

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
    Count = 4,
};

struct RenderInstance
{
    DirectX::XMFLOAT3 position{};
    DirectX::XMFLOAT3 scale{1.0f, 1.0f, 1.0f};
    DirectX::XMFLOAT4 tint{1.0f, 1.0f, 1.0f, 1.0f};
    MeshKind mesh = MeshKind::Cube;
};

struct RenderScene
{
    DirectX::XMFLOAT3 camera_eye{0.0f, 5.0f, -10.0f};
    DirectX::XMFLOAT3 camera_target{0.0f, 0.0f, 0.0f};
    DirectX::XMFLOAT4 clear_color{0.018f, 0.022f, 0.035f, 1.0f};
    std::span<const RenderInstance> instances{};
};
} // namespace mars::renderer
