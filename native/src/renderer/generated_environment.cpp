#include "renderer/generated_environment.h"

#include <algorithm>
#include <cmath>
#include <cstddef>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

struct Vec3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

[[nodiscard]] Vec3 Normalize(const Vec3 value) noexcept
{
    const float length_squared = value.x * value.x + value.y * value.y + value.z * value.z;
    if (!(length_squared > 0.0f) || !std::isfinite(length_squared))
    {
        return {0.0f, 1.0f, 0.0f};
    }
    const float inverse_length = 1.0f / std::sqrt(length_squared);
    return {value.x * inverse_length, value.y * inverse_length, value.z * inverse_length};
}

[[nodiscard]] float Dot(const Vec3 first, const Vec3 second) noexcept
{
    return first.x * second.x + first.y * second.y + first.z * second.z;
}

[[nodiscard]] Vec3 CubeDirection(
    const std::uint32_t face,
    const float u,
    const float v) noexcept
{
    switch (face)
    {
    case 0U: return Normalize({1.0f, -v, -u});
    case 1U: return Normalize({-1.0f, -v, u});
    case 2U: return Normalize({u, 1.0f, v});
    case 3U: return Normalize({u, -1.0f, -v});
    case 4U: return Normalize({u, -v, 1.0f});
    default: return Normalize({-u, -v, -1.0f});
    }
}

[[nodiscard]] std::uint32_t HashNoise(std::uint32_t value) noexcept
{
    value ^= value >> 16U;
    value *= 0x7FEB352DU;
    value ^= value >> 15U;
    value *= 0x846CA68BU;
    value ^= value >> 16U;
    return value;
}

[[nodiscard]] float Noise01(const std::uint32_t value) noexcept
{
    return static_cast<float>(HashNoise(value) & 0x00FFFFFFU) / 16'777'215.0f;
}

[[nodiscard]] std::uint8_t Encode(const float linear) noexcept
{
    const float bounded = (std::clamp)(linear, 0.0f, 1.0f);
    const float gamma = std::pow(bounded, 1.0f / 2.2f);
    return static_cast<std::uint8_t>((std::clamp)(gamma * 255.0f + 0.5f, 0.0f, 255.0f));
}

void HashByte(std::uint64_t& hash, const std::uint8_t value) noexcept
{
    hash ^= value;
    hash *= kFnvPrime;
}

void HashWord(std::uint64_t& hash, const std::uint32_t value) noexcept
{
    for (std::uint32_t shift = 0; shift < 32U; shift += 8U)
    {
        HashByte(hash, static_cast<std::uint8_t>(value >> shift));
    }
}
} // namespace

GeneratedEnvironmentCube GenerateAresReachEnvironmentCube(
    const std::uint32_t face_size,
    const std::uint32_t seed)
{
    if (face_size < 8U || face_size > 1'024U)
    {
        return {};
    }

    GeneratedEnvironmentCube environment{};
    environment.face_size = face_size;
    const std::size_t texel_count = static_cast<std::size_t>(face_size)
        * static_cast<std::size_t>(face_size) * 6U;
    environment.rgba8.resize(texel_count * 4U);
    const Vec3 sun_direction = Normalize({-0.28f, 0.74f, 0.61f});

    for (std::uint32_t face = 0; face < 6U; ++face)
    {
        for (std::uint32_t y = 0; y < face_size; ++y)
        {
            for (std::uint32_t x = 0; x < face_size; ++x)
            {
                const float u = ((static_cast<float>(x) + 0.5f)
                    / static_cast<float>(face_size)) * 2.0f - 1.0f;
                const float v = ((static_cast<float>(y) + 0.5f)
                    / static_cast<float>(face_size)) * 2.0f - 1.0f;
                const Vec3 direction = CubeDirection(face, u, v);
                const float height = (std::clamp)(direction.y * 0.5f + 0.5f, 0.0f, 1.0f);
                const float horizon_band = std::exp(-std::abs(direction.y) * 7.0f);
                const float sun_alignment = (std::max)(Dot(direction, sun_direction), 0.0f);
                const float sun_disc = std::pow(sun_alignment, 900.0f) * 0.9f;
                const float sun_halo = std::pow(sun_alignment, 20.0f) * 0.38f;
                const float variation = (Noise01(
                    seed ^ (face * 0x9E3779B9U) ^ (y * face_size + x)) - 0.5f) * 0.025f;

                const float blend = std::pow(height, 0.68f);
                float red = 0.43f + (0.018f - 0.43f) * blend;
                float green = 0.105f + (0.028f - 0.105f) * blend;
                float blue = 0.045f + (0.075f - 0.045f) * blend;
                red += 0.43f * horizon_band * 0.20f;
                green += 0.105f * horizon_band * 0.16f;
                blue += 0.045f * horizon_band * 0.12f;
                red += sun_disc + sun_halo;
                green += sun_disc * 0.72f + sun_halo * 0.42f;
                blue += sun_disc * 0.34f + sun_halo * 0.12f;
                red *= 1.0f + variation;
                green *= 1.0f + variation;
                blue *= 1.0f + variation;

                const std::size_t texel = (static_cast<std::size_t>(face)
                    * face_size * face_size + static_cast<std::size_t>(y) * face_size + x) * 4U;
                environment.rgba8[texel] = Encode(red);
                environment.rgba8[texel + 1U] = Encode(green);
                environment.rgba8[texel + 2U] = Encode(blue);
                environment.rgba8[texel + 3U] = 255U;
            }
        }
    }
    environment.content_hash = HashEnvironmentCube(environment);
    return environment;
}

bool ValidateEnvironmentCube(const GeneratedEnvironmentCube& environment) noexcept
{
    if (environment.face_size < 8U || environment.face_size > 1'024U)
    {
        return false;
    }
    const std::size_t expected_size = static_cast<std::size_t>(environment.face_size)
        * static_cast<std::size_t>(environment.face_size) * 6U * 4U;
    return environment.rgba8.size() == expected_size
        && environment.content_hash != 0U
        && environment.content_hash == HashEnvironmentCube(environment);
}

std::uint64_t HashEnvironmentCube(const GeneratedEnvironmentCube& environment) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    HashWord(hash, environment.face_size);
    for (const std::uint8_t value : environment.rgba8)
    {
        HashByte(hash, value);
    }
    return hash;
}
} // namespace mars::renderer
