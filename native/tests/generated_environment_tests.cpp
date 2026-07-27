#include "renderer/generated_environment.h"

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
    const mars::renderer::GeneratedEnvironmentCube first =
        mars::renderer::GenerateAresReachEnvironmentCube();
    const mars::renderer::GeneratedEnvironmentCube repeated =
        mars::renderer::GenerateAresReachEnvironmentCube();
    const mars::renderer::GeneratedEnvironmentCube alternate =
        mars::renderer::GenerateAresReachEnvironmentCube(64, 0x49424C36U);

    Require(mars::renderer::ValidateEnvironmentCube(first),
        "generated environment cube must validate");
    Require(first.face_size == 64U,
        "generated environment cube must use the committed face size");
    Require(first.rgba8.size() == 64U * 64U * 6U * 4U,
        "generated environment cube must contain six complete RGBA8 faces");
    Require(first.content_hash == repeated.content_hash,
        "generated environment cube must be deterministic");
    Require(first.content_hash != alternate.content_hash,
        "generated environment seed must affect content identity");

    mars::renderer::GeneratedEnvironmentCube truncated = first;
    truncated.rgba8.pop_back();
    Require(!mars::renderer::ValidateEnvironmentCube(truncated),
        "environment validation must reject a truncated cube");

    mars::renderer::GeneratedEnvironmentCube corrupted = first;
    corrupted.rgba8[17] ^= 0x5AU;
    Require(!mars::renderer::ValidateEnvironmentCube(corrupted),
        "environment validation must reject content corruption");

    std::cout << "MARSTHEGAME generated environment IBL tests passed\n";
    return 0;
}
