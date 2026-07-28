#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace mars::renderer
{
enum class GeneratedMaterialSlot : std::uint32_t
{
    HardSurface = 0,
    MarsRock = 1,
    BeaconColumn = 2,
    Terrain = 3,
    SuitFabric = 4,
    SuitAbrasion = 5,
    SuitShell = 6,
    SuitMechanism = 7,
    Visor = 8,
    Count = 9,
};

inline constexpr std::size_t kGeneratedMaterialCount =
    static_cast<std::size_t>(GeneratedMaterialSlot::Count);
inline constexpr std::uint32_t kGeneratedTextureWidth = 64;
inline constexpr std::uint32_t kGeneratedTextureHeight = 64;

struct GeneratedTextureArray
{
    std::uint32_t width = 0;
    std::uint32_t height = 0;
    std::uint32_t layers = 0;
    std::vector<std::uint8_t> rgba8{};
};

struct GeneratedMaterial
{
    std::uint32_t texture_layer = 0;
    float texture_scale = 1.0f;
    float normal_strength = 1.0f;
    float roughness = 0.5f;
    float metallic = 0.0f;
    float mask_strength = 1.0f;
    std::array<float, 3> base_color_tint{1.0f, 1.0f, 1.0f};
};

struct GeneratedMaterialCatalog
{
    std::array<GeneratedMaterial, kGeneratedMaterialCount> materials{};
    GeneratedTextureArray base_color{};
    GeneratedTextureArray normal{};
    GeneratedTextureArray surface{};
    std::uint64_t aggregate_hash = 0;
};

[[nodiscard]] GeneratedMaterialCatalog GenerateMaterialCatalog();
[[nodiscard]] bool ValidateMaterialCatalog(const GeneratedMaterialCatalog& catalog) noexcept;
[[nodiscard]] std::uint64_t HashMaterialCatalog(const GeneratedMaterialCatalog& catalog) noexcept;
} // namespace mars::renderer
