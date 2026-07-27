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
    Require(ValidateMesh(cube), "generated cube must be valid");
    Require(cube.vertices.size() == 24, "cube must preserve hard face normals");
    Require(cube.indices.size() == 36, "cube must contain twelve triangles");

    const MeshData rock_a = GenerateMarsRock(0xA51E5U);
    const MeshData rock_b = GenerateMarsRock(0xA51E5U);
    const MeshData rock_c = GenerateMarsRock(0xA51E6U);
    Require(ValidateMesh(rock_a), "generated Mars rock must be valid");
    Require(HashMesh(rock_a) == HashMesh(rock_b), "same rock seed must be deterministic");
    Require(HashMesh(rock_a) != HashMesh(rock_c), "different rock seed must change geometry");
    Require(rock_a.vertices.size() > 150, "rock must exceed placeholder geometry density");

    const MeshData beacon = GenerateBeaconColumn();
    Require(ValidateMesh(beacon), "generated beacon column must be valid");
    Require(beacon.indices.size() >= 240, "beacon must have a smooth radial silhouette");

    const MeshData terrain_a = GenerateTerrainPatch(0x4D415253U);
    const MeshData terrain_b = GenerateTerrainPatch(0x4D415253U);
    const MeshData terrain_c = GenerateTerrainPatch(0x4D415254U);
    Require(ValidateMesh(terrain_a), "generated terrain must be valid");
    Require(HashMesh(terrain_a) == HashMesh(terrain_b), "terrain seed must be deterministic");
    Require(HashMesh(terrain_a) != HashMesh(terrain_c), "terrain seed must affect topology");
    Require(terrain_a.vertices.size() == 33U * 49U, "terrain grid dimensions must be exact");
    Require(terrain_a.indices.size() == 32U * 48U * 6U, "terrain triangle count must be exact");

    float minimum_height = terrain_a.vertices.front().position.y;
    float maximum_height = minimum_height;
    for (const MeshVertex& vertex : terrain_a.vertices)
    {
        minimum_height = (std::min)(minimum_height, vertex.position.y);
        maximum_height = (std::max)(maximum_height, vertex.position.y);
    }
    Require(maximum_height - minimum_height > 0.5f, "terrain must contain meaningful elevation");

    std::cout << "MARSTHEGAME procedural geometry tests passed\n";
    return 0;
}
