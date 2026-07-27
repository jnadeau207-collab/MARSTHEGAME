#include "renderer/generated_subtitles.h"

#include <array>
#include <cmath>
#include <cstddef>
#include <string_view>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;
using Glyph = std::array<std::uint8_t, 7>;

[[nodiscard]] Glyph GlyphFor(const char character) noexcept
{
    switch (character)
    {
    case 'A': return {14, 17, 17, 31, 17, 17, 17};
    case 'B': return {30, 17, 17, 30, 17, 17, 30};
    case 'C': return {14, 17, 16, 16, 16, 17, 14};
    case 'D': return {30, 17, 17, 17, 17, 17, 30};
    case 'E': return {31, 16, 16, 30, 16, 16, 31};
    case 'G': return {14, 17, 16, 23, 17, 17, 15};
    case 'H': return {17, 17, 17, 31, 17, 17, 17};
    case 'I': return {31, 4, 4, 4, 4, 4, 31};
    case 'K': return {17, 18, 20, 24, 20, 18, 17};
    case 'L': return {16, 16, 16, 16, 16, 16, 31};
    case 'N': return {17, 25, 21, 19, 17, 17, 17};
    case 'O': return {14, 17, 17, 17, 17, 17, 14};
    case 'R': return {30, 17, 17, 30, 20, 18, 17};
    case 'S': return {15, 16, 16, 14, 1, 1, 30};
    case 'T': return {31, 4, 4, 4, 4, 4, 4};
    default: return {};
    }
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

void SetPixel(
    GeneratedSubtitleAtlas& atlas,
    const std::uint32_t layer,
    const std::uint32_t x,
    const std::uint32_t y,
    const std::array<std::uint8_t, 4> color) noexcept
{
    if (x >= atlas.width || y >= atlas.height || layer >= atlas.layers)
    {
        return;
    }
    const std::size_t index = (static_cast<std::size_t>(layer) * atlas.width * atlas.height
        + static_cast<std::size_t>(y) * atlas.width + x) * 4U;
    for (std::size_t channel = 0; channel < color.size(); ++channel)
    {
        atlas.rgba8[index + channel] = color[channel];
    }
}

void DrawLayer(
    GeneratedSubtitleAtlas& atlas,
    const std::uint32_t layer,
    const std::string_view text,
    const std::array<std::uint8_t, 3> accent)
{
    for (std::uint32_t y = 0; y < atlas.height; ++y)
    {
        for (std::uint32_t x = 0; x < atlas.width; ++x)
        {
            const float normalized_x = static_cast<float>(x) / static_cast<float>(atlas.width - 1U);
            const float center_weight = 1.0f - 2.0f * std::abs(normalized_x - 0.5f);
            const std::uint8_t alpha = y >= 8U && y < atlas.height - 8U
                ? static_cast<std::uint8_t>(118.0f + 40.0f * center_weight)
                : 0U;
            SetPixel(atlas, layer, x, y, {6U, 8U, 12U, alpha});
        }
    }
    for (std::uint32_t x = 32U; x < atlas.width - 32U; ++x)
    {
        SetPixel(atlas, layer, x, 8U, {accent[0], accent[1], accent[2], 210U});
        SetPixel(atlas, layer, x, atlas.height - 9U, {accent[0], accent[1], accent[2], 120U});
    }

    constexpr std::uint32_t scale = 4U;
    constexpr std::uint32_t advance = 24U;
    const std::uint32_t total_width = static_cast<std::uint32_t>(text.size()) * advance;
    const std::uint32_t origin_x = (atlas.width - total_width) / 2U;
    constexpr std::uint32_t origin_y = 18U;
    for (std::uint32_t character_index = 0; character_index < text.size(); ++character_index)
    {
        const Glyph glyph = GlyphFor(text[character_index]);
        for (std::uint32_t row = 0; row < glyph.size(); ++row)
        {
            for (std::uint32_t column = 0; column < 5U; ++column)
            {
                if ((glyph[row] & (1U << (4U - column))) == 0U)
                {
                    continue;
                }
                for (std::uint32_t sub_y = 0; sub_y < scale; ++sub_y)
                {
                    for (std::uint32_t sub_x = 0; sub_x < scale; ++sub_x)
                    {
                        SetPixel(
                            atlas,
                            layer,
                            origin_x + character_index * advance + column * scale + sub_x,
                            origin_y + row * scale + sub_y,
                            {235U, 241U, 246U, 255U});
                    }
                }
            }
        }
    }
}
} // namespace

GeneratedSubtitleAtlas GenerateSubtitleAtlas()
{
    GeneratedSubtitleAtlas atlas{};
    atlas.width = 512U;
    atlas.height = 64U;
    atlas.layers = 2U;
    atlas.rgba8.assign(static_cast<std::size_t>(atlas.width) * atlas.height * atlas.layers * 4U, 0U);
    DrawLayer(atlas, 0U, "REACH THE BEACON", {235U, 104U, 34U});
    DrawLayer(atlas, 1U, "SIGNAL LOCKED", {48U, 232U, 140U});
    atlas.content_hash = HashSubtitleAtlas(atlas);
    return atlas;
}

bool ValidateSubtitleAtlas(const GeneratedSubtitleAtlas& atlas) noexcept
{
    return atlas.width == 512U && atlas.height == 64U && atlas.layers == 2U
        && atlas.rgba8.size() == static_cast<std::size_t>(atlas.width) * atlas.height * atlas.layers * 4U
        && atlas.content_hash != 0U
        && atlas.content_hash == HashSubtitleAtlas(atlas);
}

std::uint64_t HashSubtitleAtlas(const GeneratedSubtitleAtlas& atlas) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    HashWord(hash, atlas.width);
    HashWord(hash, atlas.height);
    HashWord(hash, atlas.layers);
    for (const std::uint8_t value : atlas.rgba8)
    {
        HashByte(hash, value);
    }
    return hash;
}
} // namespace mars::renderer
