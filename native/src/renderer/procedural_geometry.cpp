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

DirectX::XMFLOAT3 Add(
    const DirectX::XMFLOAT3 first,
    const DirectX::XMFLOAT3 second) noexcept
{
    return {first.x + second.x, first.y + second.y, first.z + second.z};
}

DirectX::XMFLOAT3 Subtract(
    const DirectX::XMFLOAT3 first,
    const DirectX::XMFLOAT3 second) noexcept
{
    return {first.x - second.x, first.y - second.y, first.z - second.z};
}

DirectX::XMFLOAT3 Scale(const DirectX::XMFLOAT3 value, const float scale) noexcept
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

float Dot(const DirectX::XMFLOAT3 first, const DirectX::XMFLOAT3 second) noexcept
{
    return first.x * second.x + first.y * second.y + first.z * second.z;
}

DirectX::XMFLOAT3 Cross(
    const DirectX::XMFLOAT3 first,
    const DirectX::XMFLOAT3 second) noexcept
{
    return {
        first.y * second.z - first.z * second.y,
        first.z * second.x - first.x * second.z,
        first.x * second.y - first.y * second.x,
    };
}

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

std::uint32_t HashCoordinate(
    const std::uint32_t seed,
    const std::uint32_t first,
    const std::uint32_t second) noexcept
{
    std::uint32_t value = seed ^ (first * 0x9E3779B9U) ^ (second * 0x85EBCA6BU);
    value ^= value >> 16U;
    value *= 0x7FEB352DU;
    value ^= value >> 15U;
    value *= 0x846CA68BU;
    value ^= value >> 16U;
    return value;
}

float SignedNoise(
    const std::uint32_t seed,
    const std::uint32_t first,
    const std::uint32_t second) noexcept
{
    constexpr float inverse = 1.0f
        / static_cast<float>((std::numeric_limits<std::uint16_t>::max)());
    return static_cast<float>(HashCoordinate(seed, first, second) & 0xFFFFU)
        * inverse * 2.0f - 1.0f;
}

float TerrainHeight(
    const std::uint32_t seed,
    const float x,
    const float z,
    const float width,
    const float depth,
    const float height_scale) noexcept
{
    const float seed_low = static_cast<float>(seed & 0xFFFFU);
    const float seed_high = static_cast<float>((seed >> 16U) & 0xFFFFU);
    const float phase_a = seed_low * 0.013f + seed_high * 0.031f;
    const float phase_b = seed_low * 0.021f - seed_high * 0.017f;
    const float normalized_x = x / (width * 0.5f);
    const float normalized_z = z / (depth * 0.5f);

    const float macro = std::sin(x * 0.115f + phase_a)
        * std::cos(z * 0.085f + phase_b) * 0.34f;
    const float secondary = std::sin(x * 0.29f + z * 0.17f + phase_b) * 0.12f;
    const float fine = std::sin((x - z) * 0.57f + phase_a * 0.41f) * 0.045f;
    const float side_rise = std::pow(std::abs(normalized_x), 2.35f) * 1.85f;
    const float service_basin = -std::exp(-normalized_x * normalized_x * 7.5f) * 0.22f;
    const float landing_shelf = -std::exp(
        -(normalized_x * normalized_x * 12.0f
          + (normalized_z + 0.42f) * (normalized_z + 0.42f) * 16.0f)) * 0.16f;
    return (macro + secondary + fine + service_basin + landing_shelf + side_rise)
        * height_scale;
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

struct FaceBasis
{
    DirectX::XMFLOAT3 normal{};
    DirectX::XMFLOAT3 axis_u{};
    DirectX::XMFLOAT3 axis_v{};
};

DirectX::XMFLOAT3 RoundedBoxPoint(
    const DirectX::XMFLOAT3 cube_point,
    const float bevel,
    DirectX::XMFLOAT3& normal) noexcept
{
    const float core = 1.0f - bevel;
    const DirectX::XMFLOAT3 nearest{
        (std::clamp)(cube_point.x, -core, core),
        (std::clamp)(cube_point.y, -core, core),
        (std::clamp)(cube_point.z, -core, core),
    };
    normal = Normalize(Subtract(cube_point, nearest));
    return Add(nearest, Scale(normal, bevel));
}

void AppendFlatRockTriangle(
    MeshData& mesh,
    DirectX::XMFLOAT3 first,
    DirectX::XMFLOAT3 second,
    DirectX::XMFLOAT3 third) 
{
    DirectX::XMFLOAT3 normal = Normalize(Cross(Subtract(second, first), Subtract(third, first)));
    const DirectX::XMFLOAT3 centroid = Scale(Add(Add(first, second), third), 1.0f / 3.0f);
    if (Dot(normal, centroid) < 0.0f)
    {
        std::swap(second, third);
        normal = Scale(normal, -1.0f);
    }
    const float height = (std::clamp)((centroid.y + 0.60f) / 1.25f, 0.0f, 1.0f);
    const float upward = (std::clamp)(normal.y * 0.5f + 0.5f, 0.0f, 1.0f);
    const DirectX::XMFLOAT3 color{
        0.30f + height * 0.15f + upward * 0.035f,
        0.205f + height * 0.095f + upward * 0.025f,
        0.155f + height * 0.065f,
    };
    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({first, normal, color});
    mesh.vertices.push_back({second, normal, color});
    mesh.vertices.push_back({third, normal, color});
    mesh.indices.insert(mesh.indices.end(), {base, base + 1U, base + 2U});
}
} // namespace

MeshData GenerateUnitCube()
{
    constexpr std::uint32_t subdivisions = 4U;
    constexpr float bevel = 0.14f;
    constexpr std::array<FaceBasis, 6> faces = {{
        {{1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 0.0f, 1.0f}},
        {{-1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 0.0f, -1.0f}},
        {{0.0f, 1.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {0.0f, 0.0f, -1.0f}},
        {{0.0f, -1.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.0f}},
        {{0.0f, 0.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}},
        {{0.0f, 0.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}},
    }};

    MeshData mesh;
    const std::uint32_t stride = subdivisions + 1U;
    mesh.vertices.reserve(faces.size() * static_cast<std::size_t>(stride) * stride);
    mesh.indices.reserve(faces.size() * static_cast<std::size_t>(subdivisions) * subdivisions * 6U);

    for (const FaceBasis& face : faces)
    {
        const std::uint32_t face_start = static_cast<std::uint32_t>(mesh.vertices.size());
        for (std::uint32_t v_index = 0; v_index <= subdivisions; ++v_index)
        {
            const float v = -1.0f + 2.0f * static_cast<float>(v_index)
                / static_cast<float>(subdivisions);
            for (std::uint32_t u_index = 0; u_index <= subdivisions; ++u_index)
            {
                const float u = -1.0f + 2.0f * static_cast<float>(u_index)
                    / static_cast<float>(subdivisions);
                const DirectX::XMFLOAT3 cube_point = Add(
                    face.normal,
                    Add(Scale(face.axis_u, u), Scale(face.axis_v, v)));
                DirectX::XMFLOAT3 normal{};
                const DirectX::XMFLOAT3 position = RoundedBoxPoint(cube_point, bevel, normal);
                mesh.vertices.push_back({position, normal, {1.0f, 1.0f, 1.0f}});
            }
        }
        for (std::uint32_t v_index = 0; v_index < subdivisions; ++v_index)
        {
            for (std::uint32_t u_index = 0; u_index < subdivisions; ++u_index)
            {
                const std::uint32_t first = face_start + v_index * stride + u_index;
                const std::uint32_t right = first + 1U;
                const std::uint32_t upper = first + stride;
                const std::uint32_t upper_right = upper + 1U;
                mesh.indices.insert(
                    mesh.indices.end(),
                    {first, right, upper, right, upper_right, upper});
            }
        }
    }
    return mesh;
}

MeshData GenerateMarsRock(
    const std::uint32_t seed,
    const std::uint32_t rings,
    const std::uint32_t segments,
    const float radial_variation)
{
    if (rings < 3U || segments < 3U || radial_variation < 0.0f || radial_variation > 0.8f)
    {
        return {};
    }

    const std::uint32_t stride = segments + 1U;
    std::vector<DirectX::XMFLOAT3> positions;
    positions.reserve(static_cast<std::size_t>(rings + 1U) * stride);
    const float phase = static_cast<float>(seed & 0xFFFFU) * 0.00037f;

    for (std::uint32_t ring = 0; ring <= rings; ++ring)
    {
        const float latitude = static_cast<float>(ring) / static_cast<float>(rings)
            * std::numbers::pi_v<float>;
        const float sin_latitude = std::sin(latitude);
        const float cos_latitude = std::cos(latitude);
        for (std::uint32_t segment = 0; segment <= segments; ++segment)
        {
            const std::uint32_t wrapped_segment = segment % segments;
            const float longitude = static_cast<float>(segment) / static_cast<float>(segments)
                * std::numbers::pi_v<float> * 2.0f;
            const float low_frequency = std::sin(longitude * 2.0f + phase) * 0.12f
                + std::sin(longitude * 5.0f - latitude * 2.0f + phase * 0.7f) * 0.055f;
            const float seeded = SignedNoise(seed, ring, wrapped_segment)
                * radial_variation * 0.33f;
            const float radius = 1.0f + (low_frequency + seeded) * sin_latitude;
            const float stratum = 1.0f + std::sin(cos_latitude * 26.0f + phase) * 0.035f;
            float y = cos_latitude * radius * 0.72f;
            if (y < -0.54f)
            {
                y = -0.54f + (y + 0.54f) * 0.10f;
            }
            if (y > 0.58f)
            {
                y = 0.58f + (y - 0.58f) * 0.18f;
            }
            positions.push_back({
                sin_latitude * std::cos(longitude) * radius * 1.08f * stratum,
                y,
                sin_latitude * std::sin(longitude) * radius * 0.86f * stratum,
            });
        }
    }

    MeshData mesh;
    mesh.vertices.reserve(static_cast<std::size_t>(rings) * segments * 6U);
    mesh.indices.reserve(static_cast<std::size_t>(rings) * segments * 6U);
    for (std::uint32_t ring = 0; ring < rings; ++ring)
    {
        for (std::uint32_t segment = 0; segment < segments; ++segment)
        {
            const std::uint32_t first = ring * stride + segment;
            const std::uint32_t second = first + stride;
            AppendFlatRockTriangle(mesh, positions[first], positions[second], positions[first + 1U]);
            AppendFlatRockTriangle(
                mesh,
                positions[second],
                positions[second + 1U],
                positions[first + 1U]);
        }
    }
    return mesh;
}

MeshData GenerateBeaconColumn(const std::uint32_t segments)
{
    if (segments < 3U)
    {
        return {};
    }

    constexpr std::uint32_t vertical_segments = 12U;
    constexpr float body_half_height = 0.64f;
    constexpr float cap_height = 1.0f - body_half_height;
    const std::uint32_t stride = segments + 1U;
    MeshData mesh;
    mesh.vertices.reserve(static_cast<std::size_t>(vertical_segments + 1U) * stride);
    mesh.indices.reserve(static_cast<std::size_t>(vertical_segments) * segments * 6U);

    for (std::uint32_t vertical = 0; vertical <= vertical_segments; ++vertical)
    {
        const float y = -1.0f + 2.0f * static_cast<float>(vertical)
            / static_cast<float>(vertical_segments);
        float radius = 1.0f;
        float normal_y = 0.0f;
        if (y < -body_half_height)
        {
            normal_y = (y + body_half_height) / cap_height;
            radius = std::sqrt((std::max)(0.0f, 1.0f - normal_y * normal_y));
        }
        else if (y > body_half_height)
        {
            normal_y = (y - body_half_height) / cap_height;
            radius = std::sqrt((std::max)(0.0f, 1.0f - normal_y * normal_y));
        }

        for (std::uint32_t segment = 0; segment <= segments; ++segment)
        {
            const float angle = static_cast<float>(segment) / static_cast<float>(segments)
                * std::numbers::pi_v<float> * 2.0f;
            const float x = std::cos(angle);
            const float z = std::sin(angle);
            const DirectX::XMFLOAT3 normal = Normalize({x, normal_y * 1.45f, z});
            mesh.vertices.push_back({
                {x * radius, y, z * radius},
                normal,
                {1.0f, 1.0f, 1.0f},
            });
        }
    }

    for (std::uint32_t vertical = 0; vertical < vertical_segments; ++vertical)
    {
        for (std::uint32_t segment = 0; segment < segments; ++segment)
        {
            const std::uint32_t first = vertical * stride + segment;
            const std::uint32_t second = first + stride;
            mesh.indices.insert(
                mesh.indices.end(),
                {first, second, first + 1U, second, second + 1U, first + 1U});
        }
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
    if (cells_x < 2U || cells_z < 2U || width <= 0.0f || depth <= 0.0f || height_scale < 0.0f)
    {
        return {};
    }

    MeshData mesh;
    const std::uint32_t vertices_x = cells_x + 1U;
    const std::uint32_t vertices_z = cells_z + 1U;
    mesh.vertices.reserve(static_cast<std::size_t>(vertices_x) * vertices_z);
    mesh.indices.reserve(static_cast<std::size_t>(cells_x) * cells_z * 6U);

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
            const float height = TerrainHeight(seed, x, z, width, depth, height_scale);
            const float left = TerrainHeight(seed, x - step_x, z, width, depth, height_scale);
            const float right = TerrainHeight(seed, x + step_x, z, width, depth, height_scale);
            const float back = TerrainHeight(seed, x, z - step_z, width, depth, height_scale);
            const float front = TerrainHeight(seed, x, z + step_z, width, depth, height_scale);
            const DirectX::XMFLOAT3 normal = Normalize({left - right, step_x + step_z, back - front});
            const float height_mix = (std::clamp)((height + 0.35f) / 2.0f, 0.0f, 1.0f);
            const float grain = SignedNoise(seed, x_index, z_index) * 0.018f;
            mesh.vertices.push_back({
                .position = {x, height, z},
                .normal = normal,
                .color = {
                    0.39f + height_mix * 0.11f + grain,
                    0.245f + height_mix * 0.095f + grain * 0.6f,
                    0.155f + height_mix * 0.070f,
                },
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
                {first, second, first + 1U, second, second + 1U, first + 1U});
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
    if (mesh.vertices.empty() || mesh.indices.empty() || mesh.indices.size() % 3U != 0U)
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
