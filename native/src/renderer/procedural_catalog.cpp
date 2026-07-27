#include "renderer/procedural_catalog.h"

#include <cstddef>
#include <stdexcept>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;
constexpr std::uint32_t kCatalogSchemaVersion = 1;

void HashAppend(std::uint64_t& hash, const void* data, const std::size_t size) noexcept
{
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::size_t index = 0; index < size; ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
}
} // namespace

ProceduralMeshCatalog GenerateProceduralMeshCatalog()
{
    ProceduralMeshCatalog catalog{};
    catalog.meshes = {
        GenerateUnitCube(),
        GenerateMarsRock(0xA51E5U, 12, 20, 0.26f),
        GenerateBeaconColumn(32),
        GenerateTerrainPatch(0x4D415253U, 32, 48, 24.0f, 32.0f, 0.82f),
    };

    std::uint64_t aggregate = kFnvOffsetBasis;
    HashAppend(aggregate, &kCatalogSchemaVersion, sizeof(kCatalogSchemaVersion));
    for (std::size_t index = 0; index < catalog.meshes.size(); ++index)
    {
        if (!ValidateMesh(catalog.meshes[index]))
        {
            throw std::runtime_error("Canonical procedural mesh catalog contains invalid topology");
        }
        catalog.mesh_hashes[index] = HashMesh(catalog.meshes[index]);
        if (catalog.mesh_hashes[index] == 0)
        {
            throw std::runtime_error("Canonical procedural mesh catalog produced an invalid hash");
        }
        HashAppend(aggregate, &catalog.mesh_hashes[index], sizeof(catalog.mesh_hashes[index]));
    }
    catalog.aggregate_hash = aggregate;
    return catalog;
}
} // namespace mars::renderer
