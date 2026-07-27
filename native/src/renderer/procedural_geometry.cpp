#include "renderer/procedural_geometry.h"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numbers>

namespace mars::renderer
{
namespace
{
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

class DeterministicRandom final
{
public:
    explicit DeterministicRandom(const std::uint32_t seed) noexcept
        : state_(seed == 0 ? 0x9E3779B9U : seed)
    {
    }

    [[nodiscard]] std::uint32_t Next() noexcept
    {
        std::uint32_t value = state_;
        value ^= value << 13U;
        value ^= value >> 17U;
        value ^= value << 5U;
        state_ = value;
        return value;
    }

    [[nodiscard]] float SignedUnit() noexcept
    {
        constexpr float inverse = 1.0f / static_cast<float>(std::numeric_limits<std::uint32_t>::max());
        return static_cast<float>(Next()) * inverse * 2.0f - 1.0f;
    }

private:
    std::uint32_t state_;
};

DirectX::XMFLOAT3 Normalize(const DirectX::XMFLOAT3 value) noexcept
{
    const float length_squared = value.x * value.x + value.y * value.y + value.z * value.z;
    if (length_squared <= 1.0e-12f)
    {
        return {0.0f, 1.0f, 0.0f};
    }
    const float inverse_length = 1.0f / std::sqrt(length_squared);
    return {value.x * inverse_length, value.y * inverse_length, value.z * inverse_length};
}

float TerrainNoise(const std::uint32_t seed, const float x, const float z) noexcept
{
    const float seed_low = static_cast<float>(seed & 0xFFFFU);
    const float seed_high = static_cast<float>((seed >> 16U) & 0xFFFFU);
    const float phase_a = seed_low * 0.017f + seed_high * 0.071f;
    const float phase_b = seed_low * 0.043f - seed_high * 0.029f;
    const float ridge = std::sin(x * 0.31f + phase_a)
        * std::cos(z * 0.27f + phase_b);
    const float detail = std::sin((x + z) * 0.83f + phase_a * 0.37f + phase_b * 0.19f) * 0.35f;
    const float basin = -std::exp(-(x * x + z * z) * 0.015f) * 0.55f;
    return ridge * 0.62f + detail + basin;
}

void HashBytes(std::uint64_t& hash, const void* data, const std::size_t size) noexcept
{
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::size_t index = 0; index < size; ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
}
} // namespace

MeshData GenerateUnitCube()
{
    constexpr std::array<MeshVertex, 24> vertices = {{
        {{-1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
    }};
    constexpr std::array<std::uint32_t, 36> indices = {
        0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11,
        12, 13, 14, 12, 14, 15, 16, 17, 18, 16, 18, 19, 20, 21, 22, 20, 22, 23,
    };
    return {
        .vertices = {vertices.begin(), vertices.end()},
        .indices = {indices.begin(), indices.end()},
    };
}

MeshData GenerateMarsRock(
    const std::uint32_t seed,
    const std::uint32_t rings,
    const std::uint32_t segments,
    const float radial_variation)
{
    if (rings < 3 || segments < 3 || radial_variation < 0.0f || radial_variation > 0.8f)
    {
        return {};
    }

    MeshData mesh;
    mesh.vertices.reserve(static_cast<std::size_t>(rings + 1) * (segments + 1));
    mesh.indices.reserve(static_cast<std::size_t>(rings) * segments * 6);
    DeterministicRandom random(seed);

    for (std::uint32_t ring = 0; ring <= rings; ++ring)
    {
        const float v = static_cast<float>(ring) / static_cast<float>(rings);
        const float latitude = v * std::numbers::pi_v<float>;
        const float sin_latitude = std::sin(latitude);
        const float cos_latitude = std::cos(latitude);
        for (std::uint32_t segment = 0; segment <= segments; ++segment)
        {
            const float u = static_cast<float>(segment) / static_cast<float>(segments);
            const float longitude = u * std::numbers::pi_v<float> * 2.0f;
            const DirectX::XMFLOAT3 direction = {
                sin_latitude * std::cos(longitude),
                cos_latitude,
                sin_latitude * std::sin(longitude),
            };
            const float layered = std::sin(longitude * 3.0f + latitude * 2.0f) * 0.08f;
            const float radius = 1.0f + layered + random.SignedUnit() * radial_variation;
            const float vertical_compression = 0.72f + random.SignedUnit() * 0.035f;
            mesh.vertices.push_back({
                .position = {
                    direction.x * radius,
                    direction.y * radius * vertical_compression,
                    direction.z * radius,
                },
                .normal = Normalize(direction),
                .color = {0.46f, 0.23f, 0.13f},
            });
        }
    }

    const std::uint32_t stride = segments + 1;
    for (std::uint32_t ring = 0; ring < rings; ++ring)
    {
        for (std::uint32_t segment = 0; segment < segments; ++segment)
        {
            const std::uint32_t first = ring * stride + segment;
            const std::uint32_t second = first + stride;
            mesh.indices.insert(
                mesh.indices.end(),
                {first, second, first + 1, second, second + 1, first + 1});
        }
    }
    return mesh;
}

MeshData GenerateBeaconColumn(const std::uint32_t segments)
{
    if (segments < 3)
    {
        return {};
    }

    MeshData mesh;
    mesh.vertices.reserve(static_cast<std::size_t>(segments + 1) * 2 + 2);
    mesh.indices.reserve(static_cast<std::size_t>(segments) * 12);
    for (std::uint32_t segment = 0; segment <= segments; ++segment)
    {
        const float angle = static_cast<float>(segment) / static_cast<float>(segments)
            * std::numbers::pi_v<float> * 2.0f;
        const float x = std::cos(angle);
        const float z = std::sin(angle);
        mesh.vertices.push_back({{x, -1.0f, z}, {x, 0.0f, z}, {1.0f, 1.0f, 1.0f}});
        mesh.vertices.push_back({{x, 1.0f, z}, {x, 0.0f, z}, {1.0f, 1.0f, 1.0f}});
    }
    const std::uint32_t bottom_center = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({{0.0f, -1.0f, 0.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}});
    const std::uint32_t top_center = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({{0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}});

    for (std::uint32_t segment = 0; segment < segments; ++segment)
    {
        const std::uint32_t lower = segment * 2;
        const std::uint32_t upper = lower + 1;
        const std::uint32_t next_lower = lower + 2;
        const std::uint32_t next_upper = upper + 2;
        mesh.indices.insert(
            mesh.indices.end(),
            {lower, upper, next_lower, upper, next_upper, next_lower,
             bottom_center, next_lower, lower, top_center, upper, next_upper});
    }
    return mesh;
}

MeshData GenerateTerrainPatch(
    const std::uint32_t seed,
    const std::uint32_t cells_x,
    const std::uint32_t cells_z,
    const float width,
    const float depth,
    const float height_scale)
{
    if (cells_x < 2 || cells_z < 2 || width <= 0.0f || depth <= 0.0f || height_scale < 0.0f)
    {
        return {};
    }

    MeshData mesh;
    const std::uint32_t vertices_x = cells_x + 1;
    const std::uint32_t vertices_z = cells_z + 1;
    mesh.vertices.reserve(static_cast<std::size_t>(vertices_x) * vertices_z);
    mesh.indices.reserve(static_cast<std::size_t>(cells_x) * cells_z * 6);

    const float step_x = width / static_cast<float>(cells_x);
    const float step_z = depth / static_cast<float>(cells_z);
    const float origin_x = -width * 0.5f;
    const float origin_z = -depth * 0.5f;

    for (std::uint32_t z_index = 0; z_index < vertices_z; ++z_index)
    {
        for (std::uint32_t x_index = 0; x_index < vertices_x; ++x_index)
        {
            const float x = origin_x + static_cast<float>(x_index) * step_x;
            const float z = origin_z + static_cast<float>(z_index) * step_z;
            const float height = TerrainNoise(seed, x, z) * height_scale;
            const float left = TerrainNoise(seed, x - step_x, z) * height_scale;
            const float right = TerrainNoise(seed, x + step_x, z) * height_scale;
            const float back = TerrainNoise(seed, x, z - step_z) * height_scale;
            const float front = TerrainNoise(seed, x, z + step_z) * height_scale;
            const DirectX::XMFLOAT3 normal = Normalize({left - right, step_x + step_z, back - front});
            const float color_variation = (std::clamp)(height * 0.08f, -0.08f, 0.08f);
            mesh.vertices.push_back({
                .position = {x, height, z},
                .normal = normal,
                .color = {0.48f + color_variation, 0.19f, 0.085f},
            });
        }
    }

    for (std::uint32_t z_index = 0; z_index < cells_z; ++z_index)
    {
        for (std::uint32_t x_index = 0; x_index < cells_x; ++x_index)
        {
            const std::uint32_t first = z_index * vertices_x + x_index;
            const std::uint32_t second = first + vertices_x;
            mesh.indices.insert(
                mesh.indices.end(),
                {first, second, first + 1, second, second + 1, first + 1});
        }
    }
    return mesh;
}

std::uint64_t HashMesh(const MeshData& mesh) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    const std::uint64_t vertex_count = mesh.vertices.size();
    const std::uint64_t index_count = mesh.indices.size();
    HashBytes(hash, &vertex_count, sizeof(vertex_count));
    HashBytes(hash, &index_count, sizeof(index_count));
    for (const MeshVertex& vertex : mesh.vertices)
    {
        HashBytes(hash, &vertex, sizeof(vertex));
    }
    if (!mesh.indices.empty())
    {
        HashBytes(hash, mesh.indices.data(), mesh.indices.size() * sizeof(std::uint32_t));
    }
    return hash;
}

bool ValidateMesh(const MeshData& mesh) noexcept
{
    if (mesh.vertices.empty() || mesh.indices.empty() || mesh.indices.size() % 3 != 0)
    {
        return false;
    }
    for (const MeshVertex& vertex : mesh.vertices)
    {
        const auto finite = [](const float value) { return std::isfinite(value); };
        if (!finite(vertex.position.x) || !finite(vertex.position.y) || !finite(vertex.position.z)
            || !finite(vertex.normal.x) || !finite(vertex.normal.y) || !finite(vertex.normal.z))
        {
            return false;
        }
        const float normal_length = std::sqrt(
            vertex.normal.x * vertex.normal.x + vertex.normal.y * vertex.normal.y
            + vertex.normal.z * vertex.normal.z);
        if (normal_length < 0.85f || normal_length > 1.15f)
        {
            return false;
        }
    }
    return std::ranges::all_of(mesh.indices, [&mesh](const std::uint32_t index) {
        return index < mesh.vertices.size();
    });
}
} // namespace mars::renderer
