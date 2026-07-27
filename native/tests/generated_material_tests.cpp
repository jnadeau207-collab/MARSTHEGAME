#include "renderer/generated_materials.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace
{
void Require(const bool condition, const char* message)
{
    if (!condition)
    {
        std::cerr << "FAILED: " << message << '\n';
        std::exit(1);
    }
}

std::uint64_t HashLayer(
    const mars::renderer::GeneratedTextureArray& texture,
    const std::size_t layer)
{
    constexpr std::uint64_t offset_basis = 1'469'598'103'934'665'603ULL;
    constexpr std::uint64_t prime = 1'099'511'628'211ULL;
    const std::size_t layer_size = static_cast<std::size_t>(texture.width)
        * static_cast<std::size_t>(texture.height) * 4U;
    const std::size_t start = layer * layer_size;
    std::uint64_t hash = offset_basis;
    for (std::size_t index = 0; index < layer_size; ++index)
    {
        hash ^= texture.rgba8[start + index];
        hash *= prime;
    }
    return hash;
}
} // namespace

int main()
{
    using namespace mars::renderer;

    const GeneratedMaterialCatalog first = GenerateMaterialCatalog();
    const GeneratedMaterialCatalog second = GenerateMaterialCatalog();
    Require(ValidateMaterialCatalog(first), "generated material catalog must validate");
    Require(ValidateMaterialCatalog(second), "second generated material catalog must validate");
    Require(first.aggregate_hash == second.aggregate_hash, "material generation must be deterministic");
    Require(first.base_color.rgba8 == second.base_color.rgba8, "base-color bytes must be deterministic");
    Require(first.normal.rgba8 == second.normal.rgba8, "normal bytes must be deterministic");
    Require(first.surface.rgba8 == second.surface.rgba8, "surface bytes must be deterministic");

    Require(first.materials.size() == kGeneratedMaterialCount, "material count must match mesh catalog");
    Require(first.base_color.layers == static_cast<std::uint32_t>(kGeneratedMaterialCount), "base-color array must contain one layer per material");
    Require(first.normal.layers == static_cast<std::uint32_t>(kGeneratedMaterialCount), "normal array must contain one layer per material");
    Require(first.surface.layers == static_cast<std::uint32_t>(kGeneratedMaterialCount), "surface array must contain one layer per material");

    for (std::size_t layer = 1; layer < kGeneratedMaterialCount; ++layer)
    {
        Require(
            HashLayer(first.base_color, layer - 1U) != HashLayer(first.base_color, layer),
            "adjacent generated base-color layers must be materially distinct");
    }

    bool found_non_flat_normal = false;
    for (std::size_t index = 0; index + 3U < first.normal.rgba8.size(); index += 4U)
    {
        const int red = static_cast<int>(first.normal.rgba8[index]);
        const int green = static_cast<int>(first.normal.rgba8[index + 1U]);
        if (std::abs(red - 128) > 3 || std::abs(green - 128) > 3)
        {
            found_non_flat_normal = true;
            break;
        }
    }
    Require(found_non_flat_normal, "generated normal arrays must contain surface detail");

    const auto roughness_bounds = std::minmax_element(
        first.surface.rgba8.begin(),
        first.surface.rgba8.end(),
        [](const std::uint8_t left, const std::uint8_t right) { return left < right; });
    Require(roughness_bounds.first != roughness_bounds.second, "surface texture must contain channel variation");

    GeneratedMaterialCatalog corrupted = first;
    corrupted.surface.rgba8.pop_back();
    Require(!ValidateMaterialCatalog(corrupted), "truncated texture payload must fail closed");

    corrupted = first;
    corrupted.materials[0].texture_layer = 3;
    Require(!ValidateMaterialCatalog(corrupted), "material-to-layer mismatch must fail closed");

    std::cout << "MARSTHEGAME generated material tests passed\n";
    return 0;
}
