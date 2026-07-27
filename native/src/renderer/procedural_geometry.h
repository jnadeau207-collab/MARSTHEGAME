#pragma once

#include <DirectXMath.h>

#include <cstdint>
#include <vector>

namespace mars::renderer
{
struct MeshVertex
{
    DirectX::XMFLOAT3 position{};
    DirectX::XMFLOAT3 normal{0.0f, 1.0f, 0.0f};
    DirectX::XMFLOAT3 color{1.0f, 1.0f, 1.0f};
};

struct MeshData
{
    std::vector<MeshVertex> vertices{};
    std::vector<std::uint32_t> indices{};
};

[[nodiscard]] MeshData GenerateUnitCube();
[[nodiscard]] MeshData GenerateMarsRock(
    std::uint32_t seed,
    std::uint32_t rings = 10,
    std::uint32_t segments = 16,
    float radial_variation = 0.24f);
[[nodiscard]] MeshData GenerateBeaconColumn(std::uint32_t segments = 24);
[[nodiscard]] MeshData GenerateTerrainPatch(
    std::uint32_t seed,
    std::uint32_t cells_x = 32,
    std::uint32_t cells_z = 48,
    float width = 24.0f,
    float depth = 32.0f,
    float height_scale = 1.15f);
[[nodiscard]] std::uint64_t HashMesh(const MeshData& mesh) noexcept;
[[nodiscard]] bool ValidateMesh(const MeshData& mesh) noexcept;
} // namespace mars::renderer
