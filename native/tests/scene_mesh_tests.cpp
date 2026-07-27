#include "assets/scene_asset.h"
#include "game/game_state.h"

#include <array>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <stdexcept>

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
} // namespace

int main(const int argc, char** argv)
{
    Require(argc == 2, "scene mesh tests require the cooked Ares Reach scene path");
    const mars::assets::SceneDefinition definition =
        mars::assets::LoadCookedScene(std::filesystem::path(argv[1]));

    std::array<std::size_t, 4> authored_counts{};
    for (const mars::assets::SceneEntity& entity : definition.entities)
    {
        ++authored_counts[static_cast<std::size_t>(mars::assets::MeshKindForEntity(entity))];
    }
    Require(authored_counts[0] == 5, "cooked scene must contain five cube entities");
    Require(authored_counts[1] == 6, "cooked scene must contain six generated rock entities");
    Require(authored_counts[2] == 6, "cooked scene must contain six generated column entities");
    Require(authored_counts[3] == 1, "cooked scene must contain one generated terrain entity");

    const mars::game::GameState game(definition);
    const mars::renderer::RenderScene scene = game.Scene();
    std::array<std::size_t, static_cast<std::size_t>(mars::renderer::MeshKind::Count)> render_counts{};
    for (const mars::renderer::RenderInstance& instance : scene.instances)
    {
        const std::size_t mesh_index = static_cast<std::size_t>(instance.mesh);
        Require(mesh_index < render_counts.size(), "runtime scene must reject invalid mesh kinds");
        ++render_counts[mesh_index];
    }
    Require(render_counts[static_cast<std::size_t>(mars::renderer::MeshKind::Cube)] == 5,
        "runtime scene must preserve five cube instances");
    Require(render_counts[static_cast<std::size_t>(mars::renderer::MeshKind::MarsRock)] == 6,
        "runtime scene must preserve six generated rock instances");
    Require(render_counts[static_cast<std::size_t>(mars::renderer::MeshKind::BeaconColumn)] == 6,
        "runtime scene must preserve six generated column instances");
    Require(render_counts[static_cast<std::size_t>(mars::renderer::MeshKind::TerrainPatch)] == 1,
        "runtime scene must preserve one generated terrain instance");

    RequireThrows(
        []() {
            static_cast<void>(mars::assets::ParseSceneSource(
                "mars_scene 1\n"
                "entity checkpoint render,checkpoint 0 0 5 1 1 1 1 1 1 1\n"
                "entity objective render,objective 0 0 10 1 1 1 1 1 1 1\n"
                "entity player render,player,mesh_rock,mesh_column 0 0 0 1 1 1 1 1 1 1\n"));
        },
        "scene parser must reject multiple generated mesh selections");

    std::cout << "MARSTHEGAME cooked procedural mesh contract tests passed\n";
    return 0;
}
