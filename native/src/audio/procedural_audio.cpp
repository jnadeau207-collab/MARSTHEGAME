#include "audio/procedural_audio.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>

namespace mars::audio
{
namespace
{
constexpr float kPi = 3.14159265358979323846f;
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

std::uint32_t NextNoise(std::uint32_t& state) noexcept
{
    state ^= state << 13U;
    state ^= state >> 17U;
    state ^= state << 5U;
    return state;
}

float NoiseSample(std::uint32_t& state) noexcept
{
    return static_cast<float>(NextNoise(state) & 0x00FFFFFFU)
        / static_cast<float>(0x007FFFFFU) - 1.0f;
}

void HashSample(std::uint64_t& hash, const std::int16_t sample) noexcept
{
    const std::uint16_t word = static_cast<std::uint16_t>(sample);
    hash ^= static_cast<std::uint8_t>(word & 0xFFU);
    hash *= kFnvPrime;
    hash ^= static_cast<std::uint8_t>(word >> 8U);
    hash *= kFnvPrime;
}
} // namespace

SynthesizedSoundscape GenerateAresReachSoundscape(
    const std::uint32_t seed,
    const std::uint32_t duration_seconds)
{
    if (duration_seconds == 0U || duration_seconds > 30U)
    {
        throw std::invalid_argument("Soundscape duration must be between one and thirty seconds");
    }
    SynthesizedSoundscape result{};
    const std::size_t frame_count = static_cast<std::size_t>(result.sample_rate) * duration_seconds;
    if (frame_count > (std::numeric_limits<std::size_t>::max)() / result.channels)
    {
        throw std::overflow_error("Soundscape sample count overflow");
    }
    result.interleaved_samples.resize(frame_count * result.channels);
    std::uint32_t noise_state = seed == 0U ? 1U : seed;
    float filtered_noise = 0.0f;
    double square_sum = 0.0;
    float peak = 0.0f;
    std::uint64_t hash = kFnvOffsetBasis;
    for (std::size_t frame = 0; frame < frame_count; ++frame)
    {
        const float time = static_cast<float>(frame) / static_cast<float>(result.sample_rate);
        filtered_noise = filtered_noise * 0.992f + NoiseSample(noise_state) * 0.008f;
        const float low_drone = std::sin(2.0f * kPi * 41.2f * time) * 0.19f
            + std::sin(2.0f * kPi * 61.8f * time + 0.8f) * 0.11f;
        const float harmonic = std::sin(
            2.0f * kPi * 123.6f * time + std::sin(time * 0.7f) * 0.8f) * 0.055f;
        const float pulse_phase = std::fmod(time, 1.6f) / 1.6f;
        const float pulse = std::exp(-pulse_phase * 11.0f)
            * std::sin(2.0f * kPi * 82.4f * time) * 0.13f;
        const float wind = filtered_noise * (0.10f + 0.04f * std::sin(time * 0.23f));
        const float mono = (std::clamp)(low_drone + harmonic + pulse + wind, -0.92f, 0.92f);
        const float pan = std::sin(time * 0.31f) * 0.16f;
        const std::array<float, 2> channels = {mono * (1.0f - pan), mono * (1.0f + pan)};
        for (std::size_t channel = 0; channel < channels.size(); ++channel)
        {
            const float bounded = (std::clamp)(channels[channel], -1.0f, 1.0f);
            const auto sample = static_cast<std::int16_t>(std::lround(bounded * 32'767.0f));
            result.interleaved_samples[frame * result.channels + channel] = sample;
            HashSample(hash, sample);
            peak = (std::max)(peak, std::abs(bounded));
            square_sum += static_cast<double>(bounded) * static_cast<double>(bounded);
        }
    }
    result.content_hash = hash;
    result.peak_amplitude = peak;
    result.rms_amplitude = static_cast<float>(std::sqrt(
        square_sum / static_cast<double>(result.interleaved_samples.size())));
    return result;
}

bool ValidateSoundscape(const SynthesizedSoundscape& soundscape) noexcept
{
    if (soundscape.sample_rate != 48'000U || soundscape.channels != 2U
        || soundscape.interleaved_samples.empty()
        || soundscape.interleaved_samples.size() % soundscape.channels != 0U
        || soundscape.content_hash == 0U || !std::isfinite(soundscape.peak_amplitude)
        || !std::isfinite(soundscape.rms_amplitude))
    {
        return false;
    }
    return soundscape.peak_amplitude > 0.05f && soundscape.peak_amplitude <= 1.0f
        && soundscape.rms_amplitude > 0.01f && soundscape.rms_amplitude < 0.6f;
}
} // namespace mars::audio
