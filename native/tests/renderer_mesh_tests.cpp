#include "assets/mesh_asset.h"
#include "platform/win32_window.h"
#include "renderer/d3d12_renderer.h"

#include <Windows.h>

#include <array>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <span>
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

mars::renderer::FrameCaptureEvidence CaptureMesh(
    mars::platform::Win32Window& window,
    mars::renderer::D3D12Renderer& renderer,
    const std::uint32_t mesh_index)
{
    Require(window.PumpMessages(), "renderer mesh test window remains alive");
    const std::array<mars::renderer::RenderInstance, 1> instances = {{
        {
            .position = {0.0f, 0.0f, 0.0f},
            .scale = {1.4f, 1.4f, 1.4f},
            .tint = {0.95f, 0.66f, 0.12f, 1.0f},
            .mesh_index = mesh_index,
        },
    }};
    const mars::renderer::RenderScene scene = {
        .camera_eye = {0.0f, 0.0f, -6.0f},
        .camera_target = {0.0f, 0.0f, 0.0f},
        .clear_color = {0.015f, 0.018f, 0.025f, 1.0f},
        .instances = std::span<const mars::renderer::RenderInstance>(instances),
    };
    renderer.RequestFrameCapture();
    renderer.Render(scene);
    return renderer.ConsumeFrameCapture();
}
} // namespace

int main(const int argc, char** argv)
{
    Require(argc == 2, "renderer mesh test requires the cooked beacon path");
    std::vector<mars::assets::StaticMesh> meshes;
    meshes.push_back(mars::assets::MakeCubeMesh());
    meshes.push_back(mars::assets::LoadCookedMesh(std::filesystem::path(argv[1])));
    const std::size_t cube_index = mars::assets::FindMeshIndex(meshes, "cube");
    const std::size_t beacon_index = mars::assets::FindMeshIndex(meshes, "beacon");
    Require(cube_index <= UINT32_MAX && beacon_index <= UINT32_MAX, "mesh indices fit renderer contract");

    mars::platform::Win32Window window;
    window.Create(
        GetModuleHandleW(nullptr),
        640,
        360,
        L"MARSTHEGAME Mesh Selection Test",
        false);

    mars::renderer::D3D12Renderer renderer;
    renderer.Initialize(
        window.Handle(),
        window.Width(),
        window.Height(),
        meshes,
        mars::renderer::AdapterPreference::Warp,
        true);
    window.SetResizeCallback(
        [&renderer](const std::uint32_t width, const std::uint32_t height) {
            renderer.Resize(width, height);
        });

    const mars::renderer::FrameCaptureEvidence cube = CaptureMesh(
        window,
        renderer,
        static_cast<std::uint32_t>(cube_index));
    const mars::renderer::FrameCaptureEvidence beacon = CaptureMesh(
        window,
        renderer,
        static_cast<std::uint32_t>(beacon_index));
    renderer.Shutdown();

    Require(cube.checksum != 0 && beacon.checksum != 0, "both mesh captures produce checksums");
    Require(
        cube.non_background_pixels > 1'000 && beacon.non_background_pixels > 500,
        "both mesh captures contain substantial rendered geometry");
    Require(cube.checksum != beacon.checksum, "cube and glTF beacon produce distinct GPU frames");
    Require(
        cube.non_background_pixels != beacon.non_background_pixels,
        "cube and glTF beacon produce distinct silhouettes");

    std::cout << "MARSTHEGAME D3D12 mesh selection test passed\n";
    return 0;
}
