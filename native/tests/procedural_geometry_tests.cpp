#include "renderer/procedural_geometry.h"

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

    const MeshData cube = GenerateUnitCube();
    Require(ValidateMesh(cube), "generated beveled hard-surface mesh must be valid");
    Require(cube.vertices.size() == 150,
        "beveled hard-surface mesh must provide rounded face edge and corner normals");
    Require(cube.indices.size() == 576,
        "beveled hard-surface mesh must contain the deterministic subdivided topology");
    bool found_beveled_normal = false;
    for (const MeshVertex& vertex : cube.vertices)
    {
        const int non_zero_axes = static_cast<int>(std::abs(vertex.normal.x) > 0.05f)
            + static_cast<int>(std::abs(vertex.normal.y) > 0.05f)
            + static_cast<int>(std::abs(vertex.normal.z) > 0.05f);
        found_beveled_normal = found_beveled_normal || non_zero_axes >= 2;
    }
    Require(found_beveled_normal,
        "hard-surface mesh must expose beveled edge normals rather than a six-plane box");

    const MeshData rock_a = GenerateMarsRock(0xA51E5U);
    const MeshData rock_b = GenerateMarsRock(0xA51E5U);
    const MeshData rock_c = GenerateMarsRock(0xA51E6U);
    Require(ValidateMesh(rock_a), "generated faceted Mars outcrop must be valid");
    Require(HashMesh(rock_a) == HashMesh(rock_b), "same rock seed must be deterministic");
    Require(HashMesh(rock_a) != HashMesh(rock_c), "different rock seed must change geometry");
    Require(rock_a.vertices.size() == 960,
        "faceted outcrop must retain independent triangle normals and authored density");
    bool found_flat_stratum = false;
    for (const MeshVertex& vertex : rock_a.vertices)
    {
        found_flat_stratum = found_flat_stratum
            || (vertex.position.y < -0.53f && vertex.position.y > -0.58f);
    }
    Require(found_flat_stratum,
        "faceted outcrop must include a grounded weathered base rather than a floating sphere");

    const MeshData beacon = GenerateBeaconColumn();
    Require(ValidateMesh(beacon), "generated rounded structural column must be valid");
    Require(beacon.vertices.size() == 13U * 25U,
        "rounded structural column must preserve body and cap rings");
    Require(beacon.indices.size() == 12U * 24U * 6U,
        "rounded structural column must provide a smooth radial silhouette");

    const MeshData terrain_a = GenerateTerrainPatch(0x4D415253U);
    const MeshData terrain_b = GenerateTerrainPatch(0x4D415253U);
    const MeshData terrain_c = GenerateTerrainPatch(0x4D415254U);
    Require(ValidateMesh(terrain_a), "generated authored-basin terrain must be valid");
    Require(HashMesh(terrain_a) == HashMesh(terrain_b), "terrain seed must be deterministic");
    Require(HashMesh(terrain_a) != HashMesh(terrain_c), "terrain seed must affect topology");
    Require(terrain_a.vertices.size() == 33U * 49U, "terrain grid dimensions must be exact");
    Require(terrain_a.indices.size() == 32U * 48U * 6U, "terrain triangle count must be exact");

    float minimum_height = terrain_a.vertices.front().position.y;
    float maximum_height = minimum_height;
    float center_height = 0.0f;
    float edge_height = 0.0f;
    for (const MeshVertex& vertex : terrain_a.vertices)
    {
        minimum_height = (std::min)(minimum_height, vertex.position.y);
        maximum_height = (std::max)(maximum_height, vertex.position.y);
        if (std::abs(vertex.position.x) < 0.01f && std::abs(vertex.position.z) < 0.01f)
        {
            center_height = vertex.position.y;
        }
        if (std::abs(vertex.position.x - 12.0f) < 0.01f
            && std::abs(vertex.position.z) < 0.01f)
        {
            edge_height = vertex.position.y;
        }
    }
    Require(maximum_height - minimum_height > 1.0f,
        "authored-basin terrain must contain meaningful macro elevation");
    Require(edge_height > center_height + 0.6f,
        "authored-basin terrain must rise toward geological edges instead of remaining a flat carpet");

    std::cout << "MARSTHEGAME Phase 5 recovery procedural geometry tests passed\n";
    return 0;
}
