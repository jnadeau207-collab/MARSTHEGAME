#pragma once

#include <cstdint>
#include <vector>

namespace mars::renderer
{
struct GeneratedEnvironmentCube
{
    std::uint32_t face_size = 0;
    std::vector<std::uint8_t> rgba8{};
    std::uint64_t content_hash = 0;
};

[[nodiscard]] GeneratedEnvironmentCube GenerateAresReachEnvironmentCube(
    std::uint32_t face_size = 64,
    std::uint32_t seed = 0x49424C35U);
[[nodiscard]] bool ValidateEnvironmentCube(const GeneratedEnvironmentCube& environment) noexcept;
[[nodiscard]] std::uint64_t HashEnvironmentCube(const GeneratedEnvironmentCube& environment) noexcept;
} // namespace mars::renderer
