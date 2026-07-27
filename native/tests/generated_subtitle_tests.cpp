#include "renderer/generated_subtitles.h"

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
} // namespace

int main()
{
    const mars::renderer::GeneratedSubtitleAtlas first =
        mars::renderer::GenerateSubtitleAtlas();
    const mars::renderer::GeneratedSubtitleAtlas repeated =
        mars::renderer::GenerateSubtitleAtlas();
    Require(mars::renderer::ValidateSubtitleAtlas(first),
        "generated subtitle atlas must validate");
    Require(first.content_hash == repeated.content_hash,
        "generated subtitle atlas must be deterministic");
    Require(first.rgba8.size() == 512U * 64U * 2U * 4U,
        "generated subtitle atlas must contain two complete presentation layers");

    mars::renderer::GeneratedSubtitleAtlas corrupted = first;
    corrupted.rgba8[1'024] ^= 0x5AU;
    Require(!mars::renderer::ValidateSubtitleAtlas(corrupted),
        "subtitle validation must reject content corruption");

    mars::renderer::GeneratedSubtitleAtlas truncated = first;
    truncated.rgba8.pop_back();
    Require(!mars::renderer::ValidateSubtitleAtlas(truncated),
        "subtitle validation must reject truncation");

    std::cout << "MARSTHEGAME generated subtitle tests passed\n";
    return 0;
}
