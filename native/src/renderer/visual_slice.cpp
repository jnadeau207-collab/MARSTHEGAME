#include "renderer/visual_slice.h"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstddef>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

float RadicalInverse(std::uint64_t index, const std::uint32_t base) noexcept
{
    float result = 0.0f;
    float fraction = 1.0f / static_cast<float>(base);
    while (index != 0)
    {
        result += static_cast<float>(index % base) * fraction;
        index /= base;
        fraction /= static_cast<float>(base);
    }
    return result;
}

float ToneMapChannel(const float value) noexcept
{
    constexpr float a = 2.51f;
    constexpr float b = 0.03f;
    constexpr float c = 2.43f;
    constexpr float d = 0.59f;
    constexpr float e = 0.14f;
    return (std::clamp)((value * (a * value + b)) / (value * (c * value + d) + e), 0.0f, 1.0f);
}

void HashWord(std::uint64_t& hash, const std::uint32_t word) noexcept
{
    for (std::uint32_t shift = 0; shift < 32; shift += 8)
    {
        hash ^= static_cast<std::uint8_t>(word >> shift);
        hash *= kFnvPrime;
    }
}
} // namespace

VisualSliceConfiguration DefaultVisualSliceConfiguration() noexcept
{
    return {};
}

bool ValidateVisualSliceConfiguration(const VisualSliceConfiguration& configuration) noexcept
{
    const bool finite = std::isfinite(configuration.minimum_exposure)
        && std::isfinite(configuration.maximum_exposure)
        && std::isfinite(configuration.exposure_adaptation_rate)
        && std::isfinite(configuration.temporal_history_weight)
        && std::isfinite(configuration.fog_density)
        && std::isfinite(configuration.bloom_threshold)
        && std::isfinite(configuration.motion_blur_strength)
        && std::isfinite(configuration.focus_distance)
        && std::isfinite(configuration.focus_range);
    return finite && configuration.minimum_exposure > 0.0f
        && configuration.maximum_exposure >= configuration.minimum_exposure
        && configuration.maximum_exposure <= 16.0f
        && configuration.exposure_adaptation_rate > 0.0f
        && configuration.temporal_history_weight >= 0.0f
        && configuration.temporal_history_weight < 1.0f
        && configuration.fog_density >= 0.0f && configuration.fog_density <= 0.25f
        && configuration.bloom_threshold >= 0.0f
        && configuration.motion_blur_strength >= 0.0f
        && configuration.motion_blur_strength <= 2.0f
        && configuration.focus_distance > 0.0f && configuration.focus_range > 0.0f
        && configuration.shadow_resolution >= 512
        && configuration.shadow_resolution <= 8192
        && (configuration.shadow_resolution & (configuration.shadow_resolution - 1U)) == 0U
        && configuration.particle_count >= 64 && configuration.particle_count <= 65'536;
}

TemporalJitter ComputeTemporalJitter(
    const std::uint64_t frame_index,
    const std::uint32_t width,
    const std::uint32_t height) noexcept
{
    if (width == 0 || height == 0)
    {
        return {};
    }
    const std::uint64_t sequence_index = frame_index % 1'024U + 1U;
    const float sample_x = RadicalInverse(sequence_index, 2U) - 0.5f;
    const float sample_y = RadicalInverse(sequence_index, 3U) - 0.5f;
    return {
        .x = sample_x * 2.0f / static_cast<float>(width),
        .y = sample_y * 2.0f / static_cast<float>(height),
    };
}

float AdaptExposure(
    const float current_exposure,
    const float target_exposure,
    const float delta_seconds,
    const float adaptation_rate) noexcept
{
    if (!std::isfinite(current_exposure) || !std::isfinite(target_exposure)
        || !std::isfinite(delta_seconds) || !std::isfinite(adaptation_rate))
    {
        return 1.0f;
    }
    const float bounded_delta = (std::clamp)(delta_seconds, 0.0f, 1.0f);
    const float bounded_rate = (std::max)(adaptation_rate, 0.0f);
    const float blend = 1.0f - std::exp(-bounded_rate * bounded_delta);
    return current_exposure + (target_exposure - current_exposure) * blend;
}

std::array<float, 3> AcesToneMapReference(
    const std::array<float, 3>& linear_color,
    const float exposure) noexcept
{
    const float bounded_exposure = std::isfinite(exposure) ? (std::max)(exposure, 0.0f) : 1.0f;
    return {
        ToneMapChannel((std::max)(linear_color[0], 0.0f) * bounded_exposure),
        ToneMapChannel((std::max)(linear_color[1], 0.0f) * bounded_exposure),
        ToneMapChannel((std::max)(linear_color[2], 0.0f) * bounded_exposure),
    };
}

std::uint64_t HashVisualSliceConfiguration(
    const VisualSliceConfiguration& configuration) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    const std::array<float, 9> values = {
        configuration.minimum_exposure,
        configuration.maximum_exposure,
        configuration.exposure_adaptation_rate,
        configuration.temporal_history_weight,
        configuration.fog_density,
        configuration.bloom_threshold,
        configuration.motion_blur_strength,
        configuration.focus_distance,
        configuration.focus_range,
    };
    for (const float value : values)
    {
        HashWord(hash, std::bit_cast<std::uint32_t>(value));
    }
    HashWord(hash, configuration.shadow_resolution);
    HashWord(hash, configuration.particle_count);
    return hash;
}
} // namespace mars::renderer
