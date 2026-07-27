#pragma once

#include <cstdint>
#include <vector>

namespace mars::audio
{
struct SynthesizedSoundscape
{
    std::uint32_t sample_rate = 48'000;
    std::uint16_t channels = 2;
    std::vector<std::int16_t> interleaved_samples{};
    std::uint64_t content_hash = 0;
    float peak_amplitude = 0.0f;
    float rms_amplitude = 0.0f;
};

[[nodiscard]] SynthesizedSoundscape GenerateAresReachSoundscape(
    std::uint32_t seed = 0x41524553U,
    std::uint32_t duration_seconds = 4U);
[[nodiscard]] bool ValidateSoundscape(const SynthesizedSoundscape& soundscape) noexcept;
} // namespace mars::audio
