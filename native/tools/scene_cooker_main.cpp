#include "assets/scene_asset.h"

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace
{
struct Arguments
{
    std::filesystem::path input{};
    std::filesystem::path output{};
};

Arguments ParseArguments(const int argc, char** argv)
{
    Arguments arguments{};
    for (int index = 1; index < argc; ++index)
    {
        const std::string_view argument(argv[index]);
        if ((argument == "--input" || argument == "--output") && index + 1 < argc)
        {
            const std::filesystem::path value(argv[++index]);
            if (argument == "--input")
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
            throw std::invalid_argument("Usage: mars_scene_cooker --input <scene> --output <package>");
        }
    }
    if (arguments.input.empty() || arguments.output.empty())
    {
        throw std::invalid_argument("Usage: mars_scene_cooker --input <scene> --output <package>");
    }
    return arguments;
}
} // namespace

int main(const int argc, char** argv)
{
    try
    {
        const Arguments arguments = ParseArguments(argc, argv);
        mars::assets::CookSceneFile(arguments.input, arguments.output);
        const mars::assets::SceneDefinition scene = mars::assets::LoadCookedScene(arguments.output);
        std::cout << "Cooked " << scene.entities.size() << " entities; source hash "
                  << scene.source_hash << '\n';
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Scene cooker failed: " << error.what() << '\n';
        return 1;
    }
}
