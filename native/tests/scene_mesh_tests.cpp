#include "assets/scene_asset.h"
#include "game/game_state.h"

#include <array>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
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
    const std::filesystem::path cooked_path(argv[1]);
    const mars::assets::SceneDefinition definition =
        mars::assets::LoadCookedScene(cooked_path);

    const mars::assets::ContentManifest rebuilt_manifest =
        mars::assets::BuildContentManifest(definition);
    Require(definition.content_manifest == rebuilt_manifest,
        "cooked scene must expose its verified aggregate content manifest");
    Require(rebuilt_manifest.scene_source_hash == definition.source_hash,
        "content manifest must bind the authored scene source hash");
    Require(rebuilt_manifest.mesh_catalog_hash != 0 && rebuilt_manifest.composition_hash != 0
            && rebuilt_manifest.aggregate_hash != 0,
        "content manifest hashes must be non-zero");
    for (const std::uint64_t mesh_hash : rebuilt_manifest.mesh_hashes)
    {
        Require(mesh_hash != 0, "content manifest must bind every canonical generated mesh");
    }

    mars::assets::SceneDefinition changed_definition = definition;
    changed_definition.entities.front().position.x += 0.125f;
    const mars::assets::ContentManifest changed_manifest =
        mars::assets::BuildContentManifest(changed_definition);
    Require(changed_manifest.mesh_hashes == rebuilt_manifest.mesh_hashes,
        "scene composition changes must not alter canonical mesh identity");
    Require(changed_manifest.composition_hash != rebuilt_manifest.composition_hash,
        "scene composition changes must alter the composition hash");
    Require(changed_manifest.aggregate_hash != rebuilt_manifest.aggregate_hash,
        "scene composition changes must alter the aggregate content hash");

    const std::filesystem::path corrupt_path = cooked_path.parent_path()
        / "ares_reach.manifest-corrupt-test.bin";
    std::filesystem::copy_file(
        cooked_path,
        corrupt_path,
        std::filesystem::copy_options::overwrite_existing);
    {
        std::fstream corrupt(corrupt_path, std::ios::binary | std::ios::in | std::ios::out);
        Require(static_cast<bool>(corrupt), "manifest corruption fixture must open");
        corrupt.seekg(95, std::ios::beg);
        char byte = 0;
        corrupt.read(&byte, 1);
        Require(static_cast<bool>(corrupt), "manifest corruption fixture must read header byte");
        byte = static_cast<char>(static_cast<unsigned char>(byte) ^ 0x5AU);
        corrupt.seekp(95, std::ios::beg);
        corrupt.write(&byte, 1);
        Require(static_cast<bool>(corrupt), "manifest corruption fixture must write header byte");
    }
    RequireThrows(
        [&corrupt_path]() {
            static_cast<void>(mars::assets::LoadCookedScene(corrupt_path));
        },
        "runtime must reject a cooked package with a corrupted aggregate manifest");
    std::filesystem::remove(corrupt_path);

    std::array<std::size_t, 4> authored_counts{};
    bool found_featureless_wall = false;
    bool found_relay_coupling = false;
    for (const mars::assets::SceneEntity& entity : definition.entities)
    {
        ++authored_counts[static_cast<std::size_t>(mars::assets::MeshKindForEntity(entity))];
        found_featureless_wall = found_featureless_wall
            || entity.id == "west_wall" || entity.id == "east_wall";
        if (entity.id == "objective_coupling")
        {
            found_relay_coupling = true;
            Require(entity.scale.y <= 0.35f,
                "relay objective must remain a human-scale coupling rather than a giant pillar");
        }
    }
    Require(!found_featureless_wall,
        "Phase 5 recovery scene must not restore the featureless perimeter walls");
    Require(found_relay_coupling,
        "Phase 5 recovery scene must contain the Relay 03 physical coupling objective");
    Require(authored_counts[0] == 15, "recovery scene must contain fifteen hard-surface cube entities");
    Require(authored_counts[1] == 12, "recovery scene must contain twelve geological rock entities");
    Require(authored_counts[2] == 9, "recovery scene must contain nine structural column entities");
    Require(authored_counts[3] == 1, "recovery scene must contain one generated terrain entity");

    const mars::game::GameState game(definition);
    const mars::renderer::RenderScene scene = game.Scene();
    Require(scene.instances.size() == definition.entities.size(),
        "runtime scene must preserve all thirty-seven authored instance slots");
    Require(scene.supplemental_character_count == 8,
        "runtime scene must expose eight supplemental generated character parts");

    std::array<std::size_t, static_cast<std::size_t>(mars::renderer::MeshKind::Count)> authored_runtime_counts{};
    for (const mars::renderer::RenderInstance& instance : scene.instances)
    {
        const std::size_t mesh_index = static_cast<std::size_t>(instance.mesh);
        Require(mesh_index < authored_runtime_counts.size(),
            "runtime scene must reject invalid authored mesh kinds");
        ++authored_runtime_counts[mesh_index];
    }
    Require(authored_runtime_counts[static_cast<std::size_t>(mars::renderer::MeshKind::Cube)] == 16,
        "runtime scene must replace the authored player column with the generated torso cube");
    Require(authored_runtime_counts[static_cast<std::size_t>(mars::renderer::MeshKind::MarsRock)] == 12,
        "runtime scene must preserve twelve authored geological rock instances");
    Require(authored_runtime_counts[static_cast<std::size_t>(mars::renderer::MeshKind::BeaconColumn)] == 8,
        "runtime scene must preserve eight non-player authored structural columns");
    Require(authored_runtime_counts[static_cast<std::size_t>(mars::renderer::MeshKind::TerrainPatch)] == 1,
        "runtime scene must preserve one authored generated terrain instance");

    std::array<std::size_t, static_cast<std::size_t>(mars::renderer::MeshKind::Count)> supplemental_counts{};
    for (std::uint32_t index = 0; index < scene.supplemental_character_count; ++index)
    {
        const mars::renderer::RenderInstance& instance = scene.supplemental_character_instances[index];
        const std::size_t mesh_index = static_cast<std::size_t>(instance.mesh);
        Require(mesh_index < supplemental_counts.size(),
            "supplemental character must reject invalid generated mesh kinds");
        ++supplemental_counts[mesh_index];
    }
    Require(supplemental_counts[static_cast<std::size_t>(mars::renderer::MeshKind::Cube)] == 3,
        "supplemental character must contain pelvis backpack and visor cube parts");
    Require(supplemental_counts[static_cast<std::size_t>(mars::renderer::MeshKind::MarsRock)] == 0,
        "field-engineer previsualization must not use a generated rock as the helmet");
    Require(supplemental_counts[static_cast<std::size_t>(mars::renderer::MeshKind::BeaconColumn)] == 5,
        "supplemental character must contain a cylindrical helmet and four limb parts");
    Require(supplemental_counts[static_cast<std::size_t>(mars::renderer::MeshKind::TerrainPatch)] == 0,
        "supplemental character must not misuse terrain geometry");

    RequireThrows(
        []() {
            static_cast<void>(mars::assets::ParseSceneSource(
                "mars_scene 1\n"
                "entity checkpoint render,checkpoint 0 0 5 1 1 1 1 1 1 1\n"
                "entity objective render,objective 0 0 10 1 1 1 1 1 1 1\n"
                "entity player render,player,mesh_rock,mesh_column 0 0 0 1 1 1 1 1 1 1\n"));
        },
        "scene parser must reject multiple generated mesh selections");

    std::cout << "MARSTHEGAME Relay 03 previsualization mesh contract tests passed\n";
    return 0;
}
