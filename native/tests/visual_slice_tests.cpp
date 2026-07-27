#include "renderer/visual_slice.h"

#include <cmath>
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
    using namespace mars::renderer;
    const VisualSliceConfiguration configuration = DefaultVisualSliceConfiguration();
    Require(ValidateVisualSliceConfiguration(configuration), "default visual slice config must validate");
    Require(HashVisualSliceConfiguration(configuration) == HashVisualSliceConfiguration(configuration),
        "visual slice config hash must be deterministic");
    const TemporalJitter first = ComputeTemporalJitter(0, 1920, 1080);
    const TemporalJitter second = ComputeTemporalJitter(1, 1920, 1080);
    Require(first.x != second.x || first.y != second.y, "temporal jitter must advance");
    Require(std::abs(first.x) <= 1.0f / 1920.0f && std::abs(first.y) <= 1.0f / 1080.0f,
        "temporal jitter must stay within one pixel");
    const float adapted = AdaptExposure(0.5f, 2.0f, 1.0f / 60.0f, 2.0f);
    Require(adapted > 0.5f && adapted < 2.0f, "exposure adaptation must approach without overshoot");
    const auto mapped = AcesToneMapReference({0.2f, 1.0f, 8.0f}, 1.0f);
    Require(mapped[0] < mapped[1] && mapped[1] < mapped[2] && mapped[2] <= 1.0f,
        "tone map must preserve ordering and bound highlights");
    VisualSliceConfiguration invalid = configuration;
    invalid.shadow_resolution = 1536;
    Require(!ValidateVisualSliceConfiguration(invalid), "non-power-of-two shadow resolution must fail");
    std::cout << "MARSTHEGAME Phase 5 visual slice contract tests passed\n";
    return 0;
}
