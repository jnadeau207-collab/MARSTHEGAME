#pragma once

#include <array>
#include <cstdint>

namespace mars::renderer
{
struct VisualSliceConfiguration
{
    float minimum_exposure = 0.55f;
    float maximum_exposure = 2.8f;
    float exposure_adaptation_rate = 2.2f;
    float temporal_history_weight = 0.86f;
    float fog_density = 0.019f;
    float bloom_threshold = 0.78f;
    float motion_blur_strength = 0.26f;
    float focus_distance = 8.5f;
    float focus_range = 10.0f;
    std::uint32_t shadow_resolution = 2048;
    std::uint32_t particle_count = 256;
};

struct TemporalJitter
{
    float x = 0.0f;
    float y = 0.0f;
};

[[nodiscard]] VisualSliceConfiguration DefaultVisualSliceConfiguration() noexcept;
[[nodiscard]] bool ValidateVisualSliceConfiguration(
    const VisualSliceConfiguration& configuration) noexcept;
[[nodiscard]] TemporalJitter ComputeTemporalJitter(
    std::uint64_t frame_index,
    std::uint32_t width,
    std::uint32_t height) noexcept;
[[nodiscard]] float AdaptExposure(
    float current_exposure,
    float target_exposure,
    float delta_seconds,
    float adaptation_rate) noexcept;
[[nodiscard]] std::array<float, 3> AcesToneMapReference(
    const std::array<float, 3>& linear_color,
    float exposure) noexcept;
[[nodiscard]] std::uint64_t HashVisualSliceConfiguration(
    const VisualSliceConfiguration& configuration) noexcept;
} // namespace mars::renderer
