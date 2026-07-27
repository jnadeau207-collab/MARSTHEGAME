#include "renderer/procedural_geometry.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <numbers>
#include <vector>

namespace mars::renderer
{
namespace
{
struct RadialProfilePoint
{
    float y = 0.0f;
    float radius_x = 1.0f;
    float radius_z = 1.0f;
};

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

void RecalculateSmoothNormals(MeshData& mesh)
{
    for (MeshVertex& vertex : mesh.vertices)
    {
        vertex.normal = {};
    }
    for (std::size_t index = 0; index + 2U < mesh.indices.size(); index += 3U)
    {
        const std::uint32_t first_index = mesh.indices[index];
        const std::uint32_t second_index = mesh.indices[index + 1U];
        const std::uint32_t third_index = mesh.indices[index + 2U];
        const DirectX::XMFLOAT3 first = mesh.vertices[first_index].position;
        const DirectX::XMFLOAT3 second = mesh.vertices[second_index].position;
        const DirectX::XMFLOAT3 third = mesh.vertices[third_index].position;
        const DirectX::XMFLOAT3 normal = Cross(Subtract(second, first), Subtract(third, first));
        mesh.vertices[first_index].normal = Add(mesh.vertices[first_index].normal, normal);
        mesh.vertices[second_index].normal = Add(mesh.vertices[second_index].normal, normal);
        mesh.vertices[third_index].normal = Add(mesh.vertices[third_index].normal, normal);
    }
    for (MeshVertex& vertex : mesh.vertices)
    {
        vertex.normal = Normalize(vertex.normal);
    }
}

MeshData GenerateProfiledBody(
    const std::span<const RadialProfilePoint> profile,
    const std::uint32_t segments)
{
    if (profile.size() < 3U || segments < 8U)
    {
        return {};
    }

    MeshData mesh;
    const std::uint32_t stride = segments + 1U;
    mesh.vertices.reserve(profile.size() * stride + 2U);
    mesh.indices.reserve((profile.size() - 1U) * segments * 6U + segments * 6U);

    for (const RadialProfilePoint point : profile)
    {
        for (std::uint32_t segment = 0; segment <= segments; ++segment)
        {
            const float angle = static_cast<float>(segment) / static_cast<float>(segments)
                * std::numbers::pi_v<float> * 2.0f;
            const float cosine = std::cos(angle);
            const float sine = std::sin(angle);
            mesh.vertices.push_back({
                .position = {cosine * point.radius_x, point.y, sine * point.radius_z},
                .normal = {},
                .color = {1.0f, 1.0f, 1.0f},
            });
        }
    }

    for (std::uint32_t ring = 0; ring + 1U < profile.size(); ++ring)
    {
        for (std::uint32_t segment = 0; segment < segments; ++segment)
        {
            const std::uint32_t first = ring * stride + segment;
            const std::uint32_t next_ring = first + stride;
            mesh.indices.insert(
                mesh.indices.end(),
                {first, next_ring, first + 1U, next_ring, next_ring + 1U, first + 1U});
        }
    }

    const std::uint32_t bottom_center = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({
        .position = {0.0f, profile.front().y, 0.0f},
        .normal = {},
        .color = {1.0f, 1.0f, 1.0f},
    });
    const std::uint32_t top_center = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({
        .position = {0.0f, profile.back().y, 0.0f},
        .normal = {},
        .color = {1.0f, 1.0f, 1.0f},
    });
    const std::uint32_t top_ring_start = static_cast<std::uint32_t>(
        (profile.size() - 1U) * stride);
    for (std::uint32_t segment = 0; segment < segments; ++segment)
    {
        mesh.indices.insert(mesh.indices.end(), {bottom_center, segment + 1U, segment});
        mesh.indices.insert(
            mesh.indices.end(),
            {top_center, top_ring_start + segment, top_ring_start + segment + 1U});
    }

    RecalculateSmoothNormals(mesh);
    return mesh;
}
} // namespace

MeshData GenerateFieldEngineerTorso(const std::uint32_t segments)
{
    constexpr std::array<RadialProfilePoint, 9> profile = {{
        {-1.00f, 0.34f, 0.32f},
        {-0.84f, 0.57f, 0.45f},
        {-0.52f, 0.66f, 0.49f},
        {-0.18f, 0.70f, 0.52f},
        {0.18f, 0.78f, 0.55f},
        {0.52f, 0.98f, 0.57f},
        {0.72f, 1.00f, 0.54f},
        {0.90f, 0.72f, 0.44f},
        {1.00f, 0.38f, 0.32f},
    }};
    return GenerateProfiledBody(profile, segments);
}

MeshData GenerateFieldEngineerHelmet(
    const std::uint32_t rings,
    const std::uint32_t segments)
{
    if (rings < 4U || segments < 8U)
    {
        return {};
    }

    MeshData mesh;
    const std::uint32_t stride = segments + 1U;
    mesh.vertices.reserve(static_cast<std::size_t>(rings - 1U) * stride + 2U);
    mesh.indices.reserve(static_cast<std::size_t>(rings - 2U) * segments * 6U + segments * 6U);

    const std::uint32_t top_index = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({
        .position = {0.0f, 1.0f, -0.04f},
        .normal = {},
        .color = {1.0f, 1.0f, 1.0f},
    });

    for (std::uint32_t ring = 1; ring < rings; ++ring)
    {
        const float latitude = static_cast<float>(ring) / static_cast<float>(rings)
            * std::numbers::pi_v<float>;
        const float radial = std::sin(latitude);
        const float y = std::cos(latitude);
        for (std::uint32_t segment = 0; segment <= segments; ++segment)
        {
            const float angle = static_cast<float>(segment) / static_cast<float>(segments)
                * std::numbers::pi_v<float> * 2.0f;
            const float raw_z = std::sin(angle) * radial;
            const float front_scale = raw_z > 0.0f ? 1.08f : 0.94f;
            mesh.vertices.push_back({
                .position = {
                    std::cos(angle) * radial * 0.94f,
                    y,
                    raw_z * front_scale - 0.035f,
                },
                .normal = {},
                .color = {1.0f, 1.0f, 1.0f},
            });
        }
    }

    const std::uint32_t bottom_index = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({
        .position = {0.0f, -0.90f, -0.02f},
        .normal = {},
        .color = {1.0f, 1.0f, 1.0f},
    });

    const std::uint32_t first_ring = 1U;
    for (std::uint32_t segment = 0; segment < segments; ++segment)
    {
        mesh.indices.insert(
            mesh.indices.end(),
            {top_index, first_ring + segment, first_ring + segment + 1U});
    }
    for (std::uint32_t ring = 0; ring + 1U < rings - 1U; ++ring)
    {
        const std::uint32_t ring_start = 1U + ring * stride;
        const std::uint32_t next_ring = ring_start + stride;
        for (std::uint32_t segment = 0; segment < segments; ++segment)
        {
            mesh.indices.insert(
                mesh.indices.end(),
                {ring_start + segment, next_ring + segment,
                 ring_start + segment + 1U, next_ring + segment,
                 next_ring + segment + 1U, ring_start + segment + 1U});
        }
    }
    const std::uint32_t last_ring = 1U + (rings - 2U) * stride;
    for (std::uint32_t segment = 0; segment < segments; ++segment)
    {
        mesh.indices.insert(
            mesh.indices.end(),
            {bottom_index, last_ring + segment + 1U, last_ring + segment});
    }

    RecalculateSmoothNormals(mesh);
    return mesh;
}

MeshData GenerateFieldEngineerLimb(
    const std::uint32_t rings,
    const std::uint32_t segments)
{
    if (rings < 5U || segments < 8U)
    {
        return {};
    }

    std::vector<RadialProfilePoint> profile;
    profile.reserve(rings + 1U);
    for (std::uint32_t ring = 0; ring <= rings; ++ring)
    {
        const float normalized = static_cast<float>(ring) / static_cast<float>(rings);
        const float y = -1.0f + normalized * 2.0f;
        const float cap = std::sin(normalized * std::numbers::pi_v<float>);
        const float taper = 0.72f + normalized * 0.16f;
        const float joint_rounding = 0.25f + cap * 0.75f;
        profile.push_back({
            .y = y,
            .radius_x = taper * joint_rounding,
            .radius_z = taper * joint_rounding * 0.92f,
        });
    }
    return GenerateProfiledBody(profile, segments);
}
} // namespace mars::renderer
