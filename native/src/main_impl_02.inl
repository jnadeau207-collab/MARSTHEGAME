        if (!window.PumpMessages())
        {
            throw std::runtime_error("WARP smoke window closed before rendering");
        }
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
        renderer.Render(game.Scene());
    }

    renderer.Resize(800, 450);
    for (std::uint32_t frame = 0; frame < 6; ++frame)
    {
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
        renderer.Render(game.Scene());
    }
    renderer.RequestFrameCapture();
    game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    renderer.Render(game.Scene());

    const mars::renderer::FrameCaptureEvidence capture = renderer.ConsumeFrameCapture();
    const mars::renderer::FrameStatistics statistics = renderer.Statistics();
    const mars::renderer::VisualSliceConfiguration configuration = renderer.VisualConfiguration();
    LogFrameStatistics(statistics);
    LogFrameCapture(capture);
    renderer.Shutdown();

    if (statistics.presented_frames != 19 || statistics.max_cpu_frame_ms <= 0.0
        || statistics.max_gpu_frame_ms <= 0.0 || statistics.resident_gpu_bytes < 8U * 1024U * 1024U)
    {
        return 3;
    }
    if (!mars::renderer::ValidateVisualSliceConfiguration(configuration)
        || configuration.shadow_resolution < 2'048 || configuration.particle_count < 128)
    {
        return 4;
    }
    if (capture.width != 800 || capture.height != 450 || capture.checksum == 0
        || capture.non_background_pixels < 250'000
        || capture.dark_pixels < 100 || capture.highlight_pixels < 100
        || capture.average_luminance <= 0.12 || capture.average_luminance >= 0.70
        || capture.peak_luminance < 0.68
        || capture.peak_luminance <= capture.average_luminance * 1.75
        || capture.edge_energy <= 0.001)
    {
        return 5;
    }
    const std::filesystem::path capture_path =
        ExecutableDirectory() / L"phase5_visual_slice.bmp";
    if (!std::filesystem::is_regular_file(capture_path)
        || std::filesystem::file_size(capture_path) < 100'000)
    {
        return 6;
    }
    return 0;
}

std::wstring ToWide(const std::string_view text)
{
    if (text.empty())
    {
        return L"Unknown native runtime error";
    }
    const int required = MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        text.data(),
        static_cast<int>(text.size()),
        nullptr,
        0);
    if (required <= 0)
    {
        return L"Native runtime error could not be converted to UTF-16";
    }
    std::wstring result(static_cast<std::size_t>(required), L'\0');
    MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        text.data(),
        static_cast<int>(text.size()),
        result.data(),
        required);
    return result;
}
} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int)
{
    const bool self_test = HasArgument(L"--self-test");
    const bool warp_smoke_test = HasArgument(L"--warp-smoke-test");
    try
    {
        if (self_test)
        {
            return RunSelfTest();
        }
        if (warp_smoke_test)
        {
            return RunWarpSmokeTest(instance);
        }

        mars::platform::Win32Window window;
        window.Create(
            instance,
            1600,
            900,
            L"MARSTHEGAME — Ares Reach Phase 5 visual slice");

        mars::renderer::D3D12Renderer renderer;
        renderer.Initialize(window.Handle(), window.Width(), window.Height());
        window.SetResizeCallback(
            [&renderer](const std::uint32_t width, const std::uint32_t height) {
                renderer.Resize(width, height);
            });

        const mars::assets::SceneDefinition scene = mars::assets::LoadCookedScene(ScenePath());
        const std::filesystem::path save_path = SavePath();
        mars::game::GameState game(scene);
        LoadGame(game, save_path, true);
        const mars::platform::NativeInput native_input;
        const LoopingSoundscape soundscape;
        static_cast<void>(soundscape);

        auto previous = std::chrono::steady_clock::now();
        mars::game::MissionState displayed_state = game.Mission();
        bool saved_checkpoint = game.CheckpointReached();
        KeyLatch save_latch;
        KeyLatch load_latch;
        KeyLatch capture_latch;

        while (window.PumpMessages())
        {
            if (KeyDown(VK_ESCAPE))
            {
                PostMessageW(window.Handle(), WM_CLOSE, 0, 0);
                continue;
            }

            const auto now = std::chrono::steady_clock::now();
            const float delta_seconds = std::chrono::duration<float>(now - previous).count();
            previous = now;

            const mars::game::MissionState mission_before = game.Mission();
            const bool checkpoint_before = game.CheckpointReached();
            game.Update(native_input.Poll(), delta_seconds);

            if (!checkpoint_before && game.CheckpointReached())
            {
                SaveGame(game, save_path, L"checkpoint reached");
                saved_checkpoint = true;
            }
            if (mission_before != mars::game::MissionState::Complete
                && game.Mission() == mars::game::MissionState::Complete)
            {
                SaveGame(game, save_path, L"mission complete");
            }
            if (save_latch.Pressed(VK_F5))
            {
                SaveGame(game, save_path, L"manual F5 save");
            }
            if (load_latch.Pressed(VK_F9))
            {
                LoadGame(game, save_path, false);
                saved_checkpoint = game.CheckpointReached();
            }
            const bool capture_pressed = capture_latch.Pressed(VK_F12);
            if (capture_pressed)
            {
                renderer.RequestFrameCapture();
            }

            renderer.Render(game.Scene());
            if (capture_pressed)
            {
                const mars::renderer::FrameCaptureEvidence capture = renderer.ConsumeFrameCapture();
                LogFrameCapture(capture);
            }

            if (game.Mission() != displayed_state)
            {
                displayed_state = game.Mission();
                const wchar_t* title = displayed_state == mars::game::MissionState::Complete
                    ? L"MARSTHEGAME — Ares Reach Complete — R/Y reset — F12 capture"
                    : L"MARSTHEGAME — WASD/stick — Shift/LT sprint — C/X checkpoint — F12 capture";
                SetWindowTextW(window.Handle(), title);
