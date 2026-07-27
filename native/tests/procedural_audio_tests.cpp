#include "audio/procedural_audio.h"

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
    using namespace mars::audio;
    const SynthesizedSoundscape first = GenerateAresReachSoundscape(0x41524553U, 2U);
    const SynthesizedSoundscape repeat = GenerateAresReachSoundscape(0x41524553U, 2U);
    const SynthesizedSoundscape changed = GenerateAresReachSoundscape(0x41524554U, 2U);
    Require(ValidateSoundscape(first), "generated soundscape must validate");
    Require(first.content_hash == repeat.content_hash, "soundscape generation must be deterministic");
    Require(first.content_hash != changed.content_hash, "soundscape seed must affect content");
    Require(first.interleaved_samples.size() == 48'000U * 2U * 2U, "sample count must be exact");
    std::cout << "MARSTHEGAME procedural audio tests passed\n";
    return 0;
}
