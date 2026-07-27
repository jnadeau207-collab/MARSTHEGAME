    OutputDebugStringW(owned.c_str());
    OutputDebugStringW(L"\n");
}

void LogError(const std::string_view prefix, const std::exception& error)
{
    const std::string message = std::string(prefix) + ": " + error.what() + "\n";
    OutputDebugStringA(message.c_str());
}

void QuarantineCorruptSave(const std::filesystem::path& save_path)
{
    if (!std::filesystem::exists(save_path))
    {
        return;
    }
    const std::filesystem::path corrupt_path = save_path.string() + ".corrupt";
    std::error_code error;
    std::filesystem::remove(corrupt_path, error);
    error.clear();
    std::filesystem::rename(save_path, corrupt_path, error);
    if (error)
    {
        LogText(L"Failed to quarantine corrupt save; leaving it in place");
    }
    else
    {
        LogText(L"Corrupt save quarantined as ares_reach.save.corrupt");
    }
}

bool LoadGame(
    mars::game::GameState& game,
    const std::filesystem::path& save_path,
    const bool quarantine_on_failure)
{
    try
    {
        const std::optional<mars::game::GameSnapshot> snapshot =
            mars::game::SaveRepository::Load(save_path);
        if (!snapshot.has_value())
        {
            return false;
        }
        game.Restore(*snapshot);
        LogText(L"Native save loaded");
        return true;
    }
    catch (const std::exception& error)
    {
        LogError("Native save load failed", error);
        if (quarantine_on_failure)
        {
            QuarantineCorruptSave(save_path);
        }
        return false;
    }
}

void SaveGame(
    const mars::game::GameState& game,
    const std::filesystem::path& save_path,
    const std::wstring_view reason)
{
    mars::game::SaveRepository::Write(save_path, game.Snapshot());
    LogText(std::wstring(L"Native save committed: ") + std::wstring(reason));
}

int RunSelfTest()
{
    const std::filesystem::path shader_directory = ExecutableDirectory() / L"shaders";
    const std::array<std::filesystem::path, 8> shader_paths = {
        shader_directory / L"shadow.vs.dxil",
        shader_directory / L"scene.vs.dxil",
        shader_directory / L"scene.ps.dxil",
        shader_directory / L"particle.vs.dxil",
        shader_directory / L"particle.ps.dxil",
        shader_directory / L"fullscreen.vs.dxil",
        shader_directory / L"temporal.ps.dxil",
        shader_directory / L"final.ps.dxil",
    };
    for (const std::filesystem::path& shader_path : shader_paths)
    {
        if (!std::filesystem::is_regular_file(shader_path)
            || std::filesystem::file_size(shader_path) == 0)
        {
            return 2;
        }
    }

    const mars::renderer::VisualSliceConfiguration visual =
        mars::renderer::DefaultVisualSliceConfiguration();
    if (!mars::renderer::ValidateVisualSliceConfiguration(visual)
        || mars::renderer::HashVisualSliceConfiguration(visual) == 0)
    {
        return 3;
    }
    const mars::game::CharacterPose pose =
        mars::game::EvaluateCharacterPose(1.25f, 5.0f, false);
    if (!mars::game::ValidateCharacterPose(pose)
        || mars::game::HashCharacterPose(pose) == 0)
    {
        return 4;
    }
    const mars::audio::SynthesizedSoundscape soundscape =
        mars::audio::GenerateAresReachSoundscape();
    if (!mars::audio::ValidateSoundscape(soundscape) || soundscape.content_hash == 0)
    {
        return 5;
    }
    const mars::assets::SceneDefinition scene = mars::assets::LoadCookedScene(ScenePath());
    return scene.entities.size() == 37 ? 0 : 6;
}

void LogFrameStatistics(const mars::renderer::FrameStatistics statistics)
{
    std::array<wchar_t, 512> message{};
    const int written = swprintf_s(
        message.data(),
        message.size(),
        L"MARSTHEGAME frames=%llu cpu_ms=%.3f cpu_max=%.3f gpu_ms=%.3f gpu_max=%.3f hitches=%llu resident_mb=%.2f\n",
        static_cast<unsigned long long>(statistics.presented_frames),
        statistics.last_cpu_frame_ms,
        statistics.max_cpu_frame_ms,
        statistics.last_gpu_frame_ms,
        statistics.max_gpu_frame_ms,
        static_cast<unsigned long long>(statistics.hitch_count),
        static_cast<double>(statistics.resident_gpu_bytes) / (1024.0 * 1024.0));
    if (written > 0)
    {
        OutputDebugStringW(message.data());
    }
}

void LogFrameCapture(const mars::renderer::FrameCaptureEvidence capture)
{
    std::array<wchar_t, 512> message{};
    const int written = swprintf_s(
        message.data(),
        message.size(),
        L"MARSTHEGAME capture width=%u height=%u checksum=%llu non_background=%llu dark=%llu highlights=%llu avg_luma=%.5f peak_luma=%.5f edge=%.6f\n",
        capture.width,
        capture.height,
        static_cast<unsigned long long>(capture.checksum),
        static_cast<unsigned long long>(capture.non_background_pixels),
        static_cast<unsigned long long>(capture.dark_pixels),
        static_cast<unsigned long long>(capture.highlight_pixels),
        capture.average_luminance,
        capture.peak_luminance,
        capture.edge_energy);
    if (written > 0)
    {
        OutputDebugStringW(message.data());
    }
}

int RunWarpSmokeTest(const HINSTANCE instance)
{
    mars::platform::Win32Window window;
    window.Create(instance, 640, 360, L"MARSTHEGAME Phase 5 WARP Test", false);

    mars::renderer::D3D12Renderer renderer;
    renderer.Initialize(
        window.Handle(),
        window.Width(),
        window.Height(),
        mars::renderer::AdapterPreference::Warp,
        true);
    window.SetResizeCallback(
        [&renderer](const std::uint32_t width, const std::uint32_t height) {
            renderer.Resize(width, height);
        });

    const mars::assets::SceneDefinition scene = mars::assets::LoadCookedScene(ScenePath());
    mars::game::GameState game(scene);
    mars::game::InputState forward{};
    forward.move_z = 1.0f;
    forward.sprint = true;
    for (std::uint32_t frame = 0; frame < 12; ++frame)
    {
