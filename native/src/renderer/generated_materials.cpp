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
    const float noise_b = UnitNoise(wrapped_x / 2U, wrapped_y / 2U, 0xA51E5U);

    switch (material)
    {
    case GeneratedMaterialSlot::HardSurface:
    {
        const bool seam = (wrapped_x % 16U) == 0U || (wrapped_y % 16U) == 0U;
        const std::uint32_t local_x = wrapped_x % 16U;
        const std::uint32_t local_y = wrapped_y % 16U;
        const bool fastener = (local_x == 3U || local_x == 12U)
            && (local_y == 3U || local_y == 12U);
        return (seam ? 0.20f : 0.58f) + (fastener ? 0.22f : 0.0f) + noise_a * 0.04f;
    }
    case GeneratedMaterialSlot::MarsRock:
    {
        const float vein = std::abs(std::sin(
            static_cast<float>(wrapped_x + wrapped_y * 2U) * 0.22f));
        return 0.25f + noise_a * 0.42f + noise_b * 0.18f + vein * 0.08f;
    }
    case GeneratedMaterialSlot::BeaconColumn:
    {
        const float stripe = ((wrapped_x / 8U) % 2U) == 0U ? 0.62f : 0.38f;
        const float groove = (wrapped_x % 8U) == 0U ? -0.18f : 0.0f;
        return stripe + groove + noise_a * 0.03f;
    }
    case GeneratedMaterialSlot::Terrain:
    {
        const float ridge = std::abs(std::sin(
            static_cast<float>(wrapped_x) * 0.13f + static_cast<float>(wrapped_y) * 0.09f));
        return 0.20f + noise_a * 0.34f + noise_b * 0.24f + ridge * 0.12f;
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
        const bool hazard = ((x / 8U) + (y / 8U)) % 5U == 0U;
        if (hazard)
        {
            return {0.52f + noise * 0.05f, 0.24f + noise * 0.03f, 0.08f};
        }
        return {0.24f + height * 0.12f, 0.27f + height * 0.10f, 0.30f + height * 0.08f};
    }
    case GeneratedMaterialSlot::MarsRock:
        return {0.31f + height * 0.28f, 0.11f + height * 0.12f, 0.055f + height * 0.055f};
    case GeneratedMaterialSlot::BeaconColumn:
    {
        const bool luminous_band = ((x / 8U) % 2U) == 0U;
        if (luminous_band)
        {
            return {0.55f + noise * 0.04f, 0.22f, 0.055f};
        }
        return {0.19f + noise * 0.03f, 0.21f + noise * 0.03f, 0.23f + noise * 0.03f};
    }
    case GeneratedMaterialSlot::Terrain:
        return {0.33f + height * 0.22f, 0.115f + height * 0.10f, 0.052f + height * 0.045f};
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
            .texture_scale = 0.42f,
            .normal_strength = 0.68f,
            .roughness = 0.58f,
            .metallic = 0.46f,
            .mask_strength = 0.72f,
            .base_color_tint = {0.92f, 0.96f, 1.0f},
        },
        {
            .texture_layer = 1,
            .texture_scale = 0.78f,
            .normal_strength = 1.00f,
            .roughness = 0.91f,
            .metallic = 0.0f,
            .mask_strength = 0.42f,
            .base_color_tint = {1.0f, 0.86f, 0.76f},
        },
        {
            .texture_layer = 2,
            .texture_scale = 0.50f,
            .normal_strength = 0.76f,
            .roughness = 0.49f,
            .metallic = 0.64f,
            .mask_strength = 0.88f,
            .base_color_tint = {1.0f, 0.91f, 0.78f},
        },
        {
            .texture_layer = 3,
            .texture_scale = 0.18f,
            .normal_strength = 0.92f,
            .roughness = 0.96f,
            .metallic = 0.0f,
            .mask_strength = 0.35f,
            .base_color_tint = {1.0f, 0.82f, 0.70f},
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
                const float normal_x = -dx * 1.75f;
                const float normal_y = -dy * 1.75f;
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
                const float roughness = Saturate(definition.roughness + micro_noise * 0.20f);
                const float metallic = Saturate(definition.metallic + micro_noise * 0.06f);
                const float mask = Saturate(
                    definition.mask_strength * (0.35f + height * 0.65f));
                const float occlusion = Saturate(0.72f + height * 0.28f);
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
        if (material.texture_layer != static_cast<std::uint32_t>(index) || !std::isfinite(material.texture_scale)
            || material.texture_scale <= 0.0f || !IsFiniteUnit(material.normal_strength)
            || !IsFiniteUnit(material.roughness) || !IsFiniteUnit(material.metallic)
            || !IsFiniteUnit(material.mask_strength))
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
