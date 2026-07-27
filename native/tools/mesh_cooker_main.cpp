#include "assets/mesh_asset.h"

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace
{
struct Arguments
{
    std::string mesh_id{};
    std::filesystem::path input{};
    std::filesystem::path output{};
};

Arguments ParseArguments(const int argc, char** argv)
{
    Arguments arguments{};
    for (int index = 1; index < argc; ++index)
    {
        const std::string_view argument(argv[index]);
        if ((argument == "--id" || argument == "--input" || argument == "--output")
            && index + 1 < argc)
        {
            const std::string value(argv[++index]);
            if (argument == "--id")
            {
                arguments.mesh_id = value;
            }
            else if (argument == "--input")
            {
                arguments.input = value;
            }
            else
            {
                arguments.output = value;
            }
        }
        else
        {
            throw std::invalid_argument(
                "Usage: mars_mesh_cooker --id <mesh> --input <gltf> --output <package>");
        }
    }
    if (arguments.mesh_id.empty() || arguments.input.empty() || arguments.output.empty())
    {
        throw std::invalid_argument(
            "Usage: mars_mesh_cooker --id <mesh> --input <gltf> --output <package>");
    }
    return arguments;
}
} // namespace

int main(const int argc, char** argv)
{
    try
    {
        const Arguments arguments = ParseArguments(argc, argv);
        mars::assets::CookGltfMeshFile(
            arguments.mesh_id,
            arguments.input,
            arguments.output);
        const mars::assets::StaticMesh mesh = mars::assets::LoadCookedMesh(arguments.output);
        std::cout << "Cooked mesh " << mesh.id << ": " << mesh.vertices.size()
                  << " vertices, " << mesh.indices.size() / 3U << " triangles, source hash "
                  << mesh.source_hash << '\n';
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Mesh cooker failed: " << error.what() << '\n';
        return 1;
    }
}
