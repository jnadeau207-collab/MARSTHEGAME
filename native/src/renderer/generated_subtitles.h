#pragma once

#include <cstdint>
#include <vector>

namespace mars::renderer
{
struct GeneratedSubtitleAtlas
{
    std::uint32_t width = 0;
    std::uint32_t height = 0;
    std::uint32_t layers = 0;
    std::vector<std::uint8_t> rgba8{};
    std::uint64_t content_hash = 0;
};

[[nodiscard]] GeneratedSubtitleAtlas GenerateSubtitleAtlas();
[[nodiscard]] bool ValidateSubtitleAtlas(const GeneratedSubtitleAtlas& atlas) noexcept;
[[nodiscard]] std::uint64_t HashSubtitleAtlas(const GeneratedSubtitleAtlas& atlas) noexcept;
} // namespace mars::renderer
