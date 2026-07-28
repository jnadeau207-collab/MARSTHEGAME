#include "renderer/generated_materials.h"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

struct FloatColor
{
    float red = 0.0f;
    float green = 0.0f;
    float blue = 0.0f;
};

[[nodiscard]] std::uint32_t HashCoordinate(
    const std::uint32_t x,
    const std::uint32_t y,
    const std::uint32_t seed) noexcept
{
    std::uint32_t value = seed ^ (x * 0x9E3779B9U) ^ (y * 0x85EBCA6BU);
    value ^= value >> 16U;
    value *= 0x7FEB352DU;
    value ^= value >> 15U;
    value *= 0x846CA68BU;
    value ^= value >> 16U;
    return value;
}

[[nodiscard]] float UnitNoise(
    const std::uint32_t x,
    const std::uint32_t y,
    const std::uint32_t seed) noexcept
{
    constexpr float denominator = static_cast<float>((std::numeric_limits<std::uint16_t>::max)());
    return static_cast<float>(HashCoordinate(x, y, seed) & 0xFFFFU) / denominator;
}

[[nodiscard]] float Saturate(const float value) noexcept
{
    return (std::clamp)(value, 0.0f, 1.0f);
}

[[nodiscard]] std::uint8_t EncodeChannel(const float value) noexcept
{
    const float scaled = std::round(Saturate(value) * 255.0f);
    return static_cast<std::uint8_t>(scaled);
}

[[nodiscard]] std::size_t PixelOffset(
    const std::uint32_t layer,
    const std::uint32_t x,
    const std::uint32_t y) noexcept
{
    const std::size_t layer_stride = static_cast<std::size_t>(kGeneratedTextureWidth)
        * static_cast<std::size_t>(kGeneratedTextureHeight) * 4U;
    const std::size_t row_stride = static_cast<std::size_t>(kGeneratedTextureWidth) * 4U;
    return static_cast<std::size_t>(layer) * layer_stride
        + static_cast<std::size_t>(y) * row_stride + static_cast<std::size_t>(x) * 4U;
}

[[nodiscard]] float HeightAt(
    const GeneratedMaterialSlot material,
    const std::uint32_t x,
    const std::uint32_t y) noexcept
{
    const std::uint32_t wrapped_x = x % kGeneratedTextureWidth;
    const std::uint32_t wrapped_y = y % kGeneratedTextureHeight;
    const float noise_a = UnitNoise(wrapped_x, wrapped_y, 0x4D415253U);
    const float noise_b = UnitNoise(wrapped_x / 4U, wrapped_y / 4U, 0xA51E5U);

    switch (material)
    {
    case GeneratedMaterialSlot::HardSurface:
    {
        const bool seam = (wrapped_x % 32U) == 0U || (wrapped_y % 32U) == 0U;
        const std::uint32_t local_x = wrapped_x % 32U;
        const std::uint32_t local_y = wrapped_y % 32U;
        const bool fastener = (local_x == 4U || local_x == 27U)
            && (local_y == 4U || local_y == 27U);
        return 0.53f - (seam ? 0.11f : 0.0f) + (fastener ? 0.10f : 0.0f)
            + (noise_a - 0.5f) * 0.025f;
    }
    case GeneratedMaterialSlot::MarsRock:
    {
        const float strata = std::abs(std::sin(static_cast<float>(wrapped_y) * 0.31f));
        const float fracture = std::abs(std::sin(
            static_cast<float>(wrapped_x * 3U + wrapped_y) * 0.17f));
        return 0.30f + noise_a * 0.24f + noise_b * 0.11f
            + strata * 0.10f + fracture * 0.055f;
    }
    case GeneratedMaterialSlot::BeaconColumn:
    {
        const bool longitudinal_seam = (wrapped_x % 24U) == 0U;
        const bool service_band = wrapped_y >= 27U && wrapped_y <= 36U;
        return 0.53f - (longitudinal_seam ? 0.10f : 0.0f)
            + (service_band ? 0.045f : 0.0f) + (noise_a - 0.5f) * 0.018f;
    }
    case GeneratedMaterialSlot::Terrain:
    {
        const float broad_ripple = std::abs(std::sin(
            static_cast<float>(wrapped_x) * 0.065f
            + static_cast<float>(wrapped_y) * 0.042f));
        const float compacted = std::abs(std::sin(
            static_cast<float>(wrapped_x + wrapped_y) * 0.19f));
        return 0.27f + noise_a * 0.16f + noise_b * 0.10f
            + broad_ripple * 0.13f + compacted * 0.035f;
    }
    case GeneratedMaterialSlot::SuitFabric:
    {
        const float warp = ((wrapped_x % 4U) == 0U) ? 0.055f : 0.0f;
        const float weft = ((wrapped_y % 4U) == 0U) ? 0.045f : 0.0f;
        return 0.48f + warp + weft + (noise_a - 0.5f) * 0.020f;
    }
    case GeneratedMaterialSlot::SuitAbrasion:
    {
        const bool diagonal = ((wrapped_x + wrapped_y) % 7U) == 0U;
        const bool cross_thread = ((wrapped_x * 2U + wrapped_y) % 11U) == 0U;
        return 0.47f + (diagonal ? 0.070f : 0.0f)
            + (cross_thread ? 0.035f : 0.0f) + (noise_a - 0.5f) * 0.025f;
    }
    case GeneratedMaterialSlot::SuitShell:
    {
        const bool panel_seam = (wrapped_x % 32U) == 0U || (wrapped_y % 32U) == 0U;
        const bool shallow_rib = (wrapped_y % 16U) == 7U;
        return 0.53f - (panel_seam ? 0.075f : 0.0f)
            + (shallow_rib ? 0.025f : 0.0f) + (noise_a - 0.5f) * 0.012f;
    }
    case GeneratedMaterialSlot::SuitMechanism:
    {
        const bool machined_groove = (wrapped_x % 8U) == 0U;
        const bool transverse_ring = (wrapped_y % 24U) == 0U;
        return 0.50f - (machined_groove ? 0.065f : 0.0f)
            - (transverse_ring ? 0.035f : 0.0f) + (noise_a - 0.5f) * 0.012f;
    }
    case GeneratedMaterialSlot::Visor:
    {
        const float broad_curve = std::sin(
            static_cast<float>(wrapped_x) * 0.049f
            + static_cast<float>(wrapped_y) * 0.031f) * 0.012f;
        return 0.50f + broad_curve + (noise_b - 0.5f) * 0.006f;
    }
    case GeneratedMaterialSlot::Count:
        break;
    }
    return 0.5f;
}

[[nodiscard]] FloatColor BaseColorAt(
    const GeneratedMaterialSlot material,
    const std::uint32_t x,
    const std::uint32_t y,
    const float height) noexcept
{
    const float noise = UnitNoise(x, y, 0xC001D00DU) - 0.5f;
    switch (material)
    {
    case GeneratedMaterialSlot::HardSurface:
    {
        const bool service_mark = y >= 29U && y <= 34U && x >= 4U && x <= 18U;
        if (service_mark)
        {
            return {0.48f + noise * 0.025f, 0.30f + noise * 0.018f, 0.11f};
        }
        return {
            0.205f + height * 0.095f + noise * 0.018f,
            0.225f + height * 0.090f + noise * 0.018f,
            0.235f + height * 0.085f + noise * 0.016f,
        };
    }
    case GeneratedMaterialSlot::MarsRock:
        return {
            0.205f + height * 0.205f + noise * 0.018f,
            0.135f + height * 0.135f + noise * 0.012f,
            0.095f + height * 0.090f,
        };
    case GeneratedMaterialSlot::BeaconColumn:
    {
        const bool service_band = y >= 27U && y <= 36U;
        if (service_band)
        {
            return {0.43f + noise * 0.018f, 0.31f + noise * 0.014f, 0.15f};
        }
        return {
            0.235f + height * 0.085f + noise * 0.012f,
            0.255f + height * 0.080f + noise * 0.012f,
            0.265f + height * 0.075f + noise * 0.012f,
        };
    }
    case GeneratedMaterialSlot::Terrain:
        return {
            0.265f + height * 0.185f + noise * 0.020f,
            0.165f + height * 0.135f + noise * 0.014f,
            0.105f + height * 0.095f,
        };
    case GeneratedMaterialSlot::SuitFabric:
    {
        const float thread = ((x + y) % 4U) == 0U ? 0.018f : 0.0f;
        return {
            0.54f + height * 0.065f + thread + noise * 0.012f,
            0.515f + height * 0.060f + thread + noise * 0.011f,
            0.455f + height * 0.055f + thread + noise * 0.010f,
        };
    }
    case GeneratedMaterialSlot::SuitAbrasion:
        return {
            0.245f + height * 0.075f + noise * 0.010f,
            0.255f + height * 0.072f + noise * 0.010f,
            0.250f + height * 0.068f + noise * 0.010f,
        };
    case GeneratedMaterialSlot::SuitShell:
    {
        const bool safety_insert = y >= 8U && y <= 13U && x >= 41U && x <= 58U;
        if (safety_insert)
        {
            return {0.56f + noise * 0.012f, 0.31f + noise * 0.009f, 0.075f};
        }
        return {
            0.55f + height * 0.105f + noise * 0.008f,
            0.47f + height * 0.095f + noise * 0.008f,
            0.285f + height * 0.065f + noise * 0.006f,
        };
    }
    case GeneratedMaterialSlot::SuitMechanism:
        return {
            0.095f + height * 0.070f + noise * 0.006f,
            0.105f + height * 0.072f + noise * 0.006f,
            0.110f + height * 0.075f + noise * 0.006f,
        };
    case GeneratedMaterialSlot::Visor:
    {
        const float vertical = static_cast<float>(y) / static_cast<float>(kGeneratedTextureHeight - 1U);
        return {
            0.018f + height * 0.020f,
            0.052f + height * 0.055f + vertical * 0.015f,
            0.070f + height * 0.075f + vertical * 0.025f,
        };
    }
    case GeneratedMaterialSlot::Count:
        break;
    }
    return {1.0f, 0.0f, 1.0f};
}

void WritePixel(
    GeneratedTextureArray& texture,
    const std::uint32_t layer,
    const std::uint32_t x,
    const std::uint32_t y,
    const FloatColor color,
    const float alpha) noexcept
{
    const std::size_t offset = PixelOffset(layer, x, y);
    texture.rgba8[offset] = EncodeChannel(color.red);
    texture.rgba8[offset + 1U] = EncodeChannel(color.green);
    texture.rgba8[offset + 2U] = EncodeChannel(color.blue);
    texture.rgba8[offset + 3U] = EncodeChannel(alpha);
}

void HashBytes(std::uint64_t& hash, const void* data, const std::size_t size) noexcept
{
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::size_t index = 0; index < size; ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
}

template <typename T>
void HashValue(std::uint64_t& hash, const T& value) noexcept
{
    HashBytes(hash, &value, sizeof(value));
}

[[nodiscard]] bool IsFiniteUnit(const float value) noexcept
{
    return std::isfinite(value) && value >= 0.0f && value <= 1.0f;
}

[[nodiscard]] bool ValidateTexture(const GeneratedTextureArray& texture) noexcept
{
    if (texture.width != kGeneratedTextureWidth || texture.height != kGeneratedTextureHeight
        || texture.layers != static_cast<std::uint32_t>(kGeneratedMaterialCount))
    {
        return false;
    }
    const std::size_t expected = static_cast<std::size_t>(texture.width)
        * static_cast<std::size_t>(texture.height) * static_cast<std::size_t>(texture.layers) * 4U;
    return texture.rgba8.size() == expected;
}
} // namespace

GeneratedMaterialCatalog GenerateMaterialCatalog()
{
    GeneratedMaterialCatalog catalog{};
    catalog.materials = {{
        {
            .texture_layer = 0,
            .texture_scale = 0.30f,
            .normal_strength = 0.38f,
            .roughness = 0.62f,
            .metallic = 0.38f,
            .mask_strength = 0.36f,
            .base_color_tint = {0.92f, 0.95f, 0.97f},
        },
        {
            .texture_layer = 1,
            .texture_scale = 0.54f,
            .normal_strength = 0.58f,
            .roughness = 0.93f,
            .metallic = 0.0f,
            .mask_strength = 0.32f,
            .base_color_tint = {0.91f, 0.84f, 0.77f},
        },
        {
            .texture_layer = 2,
            .texture_scale = 0.34f,
            .normal_strength = 0.30f,
            .roughness = 0.50f,
            .metallic = 0.56f,
            .mask_strength = 0.44f,
            .base_color_tint = {0.90f, 0.93f, 0.95f},
        },
        {
            .texture_layer = 3,
            .texture_scale = 0.12f,
            .normal_strength = 0.46f,
            .roughness = 0.96f,
            .metallic = 0.0f,
            .mask_strength = 0.25f,
            .base_color_tint = {0.96f, 0.88f, 0.78f},
        },
        {
            .texture_layer = 4,
            .texture_scale = 0.75f,
            .normal_strength = 0.32f,
            .roughness = 0.88f,
            .metallic = 0.0f,
            .mask_strength = 0.18f,
            .base_color_tint = {0.96f, 0.94f, 0.88f},
        },
        {
            .texture_layer = 5,
            .texture_scale = 0.65f,
            .normal_strength = 0.42f,
            .roughness = 0.92f,
            .metallic = 0.0f,
            .mask_strength = 0.25f,
            .base_color_tint = {0.75f, 0.78f, 0.76f},
        },
        {
            .texture_layer = 6,
            .texture_scale = 0.38f,
            .normal_strength = 0.24f,
            .roughness = 0.46f,
            .metallic = 0.08f,
            .mask_strength = 0.30f,
            .base_color_tint = {1.0f, 0.94f, 0.72f},
        },
        {
            .texture_layer = 7,
            .texture_scale = 0.42f,
            .normal_strength = 0.28f,
            .roughness = 0.34f,
            .metallic = 0.72f,
            .mask_strength = 0.25f,
            .base_color_tint = {0.52f, 0.56f, 0.58f},
        },
        {
            .texture_layer = 8,
            .texture_scale = 0.20f,
            .normal_strength = 0.08f,
            .roughness = 0.16f,
            .metallic = 0.12f,
            .mask_strength = 0.10f,
            .base_color_tint = {0.20f, 0.48f, 0.58f},
        },
    }};

    const std::size_t texture_size = static_cast<std::size_t>(kGeneratedTextureWidth)
        * static_cast<std::size_t>(kGeneratedTextureHeight) * kGeneratedMaterialCount * 4U;
    catalog.base_color = {
        .width = kGeneratedTextureWidth,
        .height = kGeneratedTextureHeight,
        .layers = static_cast<std::uint32_t>(kGeneratedMaterialCount),
        .rgba8 = std::vector<std::uint8_t>(texture_size),
    };
    catalog.normal = catalog.base_color;
    catalog.surface = catalog.base_color;

    for (std::uint32_t layer = 0; layer < static_cast<std::uint32_t>(kGeneratedMaterialCount); ++layer)
    {
        const auto material = static_cast<GeneratedMaterialSlot>(layer);
        for (std::uint32_t y = 0; y < kGeneratedTextureHeight; ++y)
        {
            for (std::uint32_t x = 0; x < kGeneratedTextureWidth; ++x)
            {
                const float height = Saturate(HeightAt(material, x, y));
                WritePixel(catalog.base_color, layer, x, y, BaseColorAt(material, x, y, height), 1.0f);

                const std::uint32_t left_x = (x + kGeneratedTextureWidth - 1U) % kGeneratedTextureWidth;
                const std::uint32_t right_x = (x + 1U) % kGeneratedTextureWidth;
                const std::uint32_t down_y = (y + kGeneratedTextureHeight - 1U) % kGeneratedTextureHeight;
                const std::uint32_t up_y = (y + 1U) % kGeneratedTextureHeight;
                const float dx = HeightAt(material, right_x, y) - HeightAt(material, left_x, y);
                const float dy = HeightAt(material, x, up_y) - HeightAt(material, x, down_y);
                const float normal_x = -dx * 1.25f;
                const float normal_y = -dy * 1.25f;
                const float normal_z = 1.0f;
                const float inverse_length = 1.0f / std::sqrt(
                    normal_x * normal_x + normal_y * normal_y + normal_z * normal_z);
                WritePixel(
                    catalog.normal,
                    layer,
                    x,
                    y,
                    {
                        normal_x * inverse_length * 0.5f + 0.5f,
                        normal_y * inverse_length * 0.5f + 0.5f,
                        normal_z * inverse_length * 0.5f + 0.5f,
                    },
                    height);

                const GeneratedMaterial& definition = catalog.materials[layer];
                const float micro_noise = UnitNoise(x, y, 0x5EEDFACEU) - 0.5f;
                const float roughness = Saturate(definition.roughness + micro_noise * 0.10f);
                const float metallic = Saturate(definition.metallic + micro_noise * 0.03f);
                const float mask = Saturate(
                    definition.mask_strength * (0.45f + height * 0.55f));
                const float occlusion = Saturate(0.79f + height * 0.21f);
                WritePixel(
                    catalog.surface,
                    layer,
                    x,
                    y,
                    {roughness, metallic, mask},
                    occlusion);
            }
        }
    }

    catalog.aggregate_hash = HashMaterialCatalog(catalog);
    return catalog;
}

bool ValidateMaterialCatalog(const GeneratedMaterialCatalog& catalog) noexcept
{
    if (!ValidateTexture(catalog.base_color) || !ValidateTexture(catalog.normal)
        || !ValidateTexture(catalog.surface))
    {
        return false;
    }

    for (std::size_t index = 0; index < catalog.materials.size(); ++index)
    {
        const GeneratedMaterial& material = catalog.materials[index];
        if (material.texture_layer != static_cast<std::uint32_t>(index)
            || !std::isfinite(material.texture_scale) || material.texture_scale <= 0.0f
            || !IsFiniteUnit(material.normal_strength) || !IsFiniteUnit(material.roughness)
            || !IsFiniteUnit(material.metallic) || !IsFiniteUnit(material.mask_strength))
        {
            return false;
        }
        for (const float component : material.base_color_tint)
        {
            if (!IsFiniteUnit(component))
            {
                return false;
            }
        }
    }

    return catalog.aggregate_hash == HashMaterialCatalog(catalog);
}

std::uint64_t HashMaterialCatalog(const GeneratedMaterialCatalog& catalog) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    for (const GeneratedMaterial& material : catalog.materials)
    {
        HashValue(hash, material.texture_layer);
        HashValue(hash, std::bit_cast<std::uint32_t>(material.texture_scale));
        HashValue(hash, std::bit_cast<std::uint32_t>(material.normal_strength));
        HashValue(hash, std::bit_cast<std::uint32_t>(material.roughness));
        HashValue(hash, std::bit_cast<std::uint32_t>(material.metallic));
        HashValue(hash, std::bit_cast<std::uint32_t>(material.mask_strength));
        for (const float component : material.base_color_tint)
        {
            HashValue(hash, std::bit_cast<std::uint32_t>(component));
        }
    }

    const auto hash_texture = [&hash](const GeneratedTextureArray& texture) {
        HashValue(hash, texture.width);
        HashValue(hash, texture.height);
        HashValue(hash, texture.layers);
        if (!texture.rgba8.empty())
        {
            HashBytes(hash, texture.rgba8.data(), texture.rgba8.size());
        }
    };
    hash_texture(catalog.base_color);
    hash_texture(catalog.normal);
    hash_texture(catalog.surface);
    return hash;
}
} // namespace mars::renderer
