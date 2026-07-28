#pragma once

#include "renderer/procedural_geometry.h"

#include <array>
#include <cstddef>
#include <cstdint>

namespace mars::renderer
{
enum class ProceduralMeshSlot : std::size_t
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

inline constexpr std::size_t kProceduralMeshCount =
    static_cast<std::size_t>(ProceduralMeshSlot::Count);

struct ProceduralMeshCatalog
{
    std::array<MeshData, kProceduralMeshCount> meshes{};
    std::array<std::uint64_t, kProceduralMeshCount> mesh_hashes{};
    std::uint64_t aggregate_hash = 0;
};

[[nodiscard]] ProceduralMeshCatalog GenerateProceduralMeshCatalog();
} // namespace mars::renderer
