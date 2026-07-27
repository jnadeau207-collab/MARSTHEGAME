#include "assets/json.h"
#include "assets/mesh_asset.h"

#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

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

template <typename Callable>
void RequireThrows(Callable&& callable, const char* message)
{
    try
    {
        callable();
    }
    catch (const std::exception&)
    {
        return;
    }
    Require(false, message);
}

std::vector<char> ReadBytes(const std::filesystem::path& path)
{
    std::ifstream input(path, std::ios::binary);
    Require(static_cast<bool>(input), "test artifact opens");
    return {
        std::istreambuf_iterator<char>{input},
        std::istreambuf_iterator<char>{},
    };
}
} // namespace

int main(const int argc, char** argv)
{
    Require(argc == 3, "mesh tests require source glTF and cooked package paths");
    const std::filesystem::path source_path(argv[1]);
    const std::filesystem::path cooked_path(argv[2]);

    const std::vector<char> source_bytes = ReadBytes(source_path);
    const std::string source(source_bytes.begin(), source_bytes.end());
    const mars::assets::StaticMesh parsed = mars::assets::ParseGltfStaticMesh("beacon", source);
    const mars::assets::StaticMesh loaded = mars::assets::LoadCookedMesh(cooked_path);

    Require(loaded.id == "beacon", "cooked mesh retains its stable identifier");
    Require(loaded.vertices.size() == 6, "beacon glTF contains six vertices");
    Require(loaded.indices.size() == 24, "beacon glTF contains eight triangles");
    Require(loaded.source_hash == parsed.source_hash, "cooked mesh retains source provenance");
    Require(loaded.bounds_min.y < -1.49f && loaded.bounds_max.y > 1.49f, "mesh bounds are cooked");

    const mars::assets::StaticMesh cube = mars::assets::MakeCubeMesh();
    Require(cube.id == "cube" && cube.vertices.size() == 24 && cube.indices.size() == 36,
        "built-in cube is represented by the same mesh contract");

    RequireThrows(
        []() { static_cast<void>(mars::assets::ParseJson("{\"x\":1,\"x\":2}")); },
        "JSON parser rejects duplicate object keys");
    RequireThrows(
        []() {
            static_cast<void>(mars::assets::ParseGltfStaticMesh(
                "broken",
                "{\"asset\":{\"version\":\"2.0\"},\"buffers\":[],\"bufferViews\":[],\"accessors\":[],\"meshes\":[]}"));
        },
        "glTF loader rejects missing static-mesh data");

    const std::filesystem::path deterministic_path =
        std::filesystem::temp_directory_path() / "marsthegame-beacon-determinism.marsmesh";
    const std::filesystem::path corrupt_path =
        std::filesystem::temp_directory_path() / "marsthegame-beacon-corrupt.marsmesh";
    std::filesystem::remove(deterministic_path);
    std::filesystem::remove(corrupt_path);

    mars::assets::WriteCookedMesh(deterministic_path, parsed);
    Require(ReadBytes(deterministic_path) == ReadBytes(cooked_path),
        "mesh cooking is byte-for-byte deterministic");

    std::filesystem::copy_file(
        cooked_path,
        corrupt_path,
        std::filesystem::copy_options::overwrite_existing);
    {
        std::fstream corrupt(corrupt_path, std::ios::binary | std::ios::in | std::ios::out);
        Require(static_cast<bool>(corrupt), "cooked mesh opens for corruption test");
        corrupt.seekg(-1, std::ios::end);
        char value = 0;
        corrupt.read(&value, 1);
        value = static_cast<char>(static_cast<unsigned char>(value) ^ 0xA5U);
        corrupt.seekp(-1, std::ios::end);
        corrupt.write(&value, 1);
    }
    RequireThrows(
        [&corrupt_path]() { static_cast<void>(mars::assets::LoadCookedMesh(corrupt_path)); },
        "mesh payload corruption is rejected");

    std::filesystem::remove(deterministic_path);
    std::filesystem::remove(deterministic_path.string() + ".bak");
    std::filesystem::remove(deterministic_path.string() + ".tmp");
    std::filesystem::remove(corrupt_path);

    std::cout << "MARSTHEGAME glTF mesh asset tests passed\n";
    return 0;
}
