#pragma once

#include <DirectXMath.h>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace mars::assets
{
struct MeshVertex
{
    DirectX::XMFLOAT3 position{};
    DirectX::XMFLOAT3 normal{0.0f, 1.0f, 0.0f};
    DirectX::XMFLOAT3 color{1.0f, 1.0f, 1.0f};
};

static_assert(sizeof(MeshVertex) == 36);

struct StaticMesh
{
    std::string id{};
    std::uint64_t source_hash = 0;
    DirectX::XMFLOAT3 bounds_min{};
    DirectX::XMFLOAT3 bounds_max{};
    std::vector<MeshVertex> vertices{};
    std::vector<std::uint32_t> indices{};
};

[[nodiscard]] StaticMesh ParseGltfStaticMesh(
    std::string_view mesh_id,
    std::string_view source);
void WriteCookedMesh(const std::filesystem::path& path, const StaticMesh& mesh);
[[nodiscard]] StaticMesh LoadCookedMesh(const std::filesystem::path& path);
void CookGltfMeshFile(
    std::string_view mesh_id,
    const std::filesystem::path& source_path,
    const std::filesystem::path& output_path);
[[nodiscard]] StaticMesh MakeCubeMesh();
[[nodiscard]] std::size_t FindMeshIndex(
    std::span<const StaticMesh> meshes,
    std::string_view mesh_id);
} // namespace mars::assets
