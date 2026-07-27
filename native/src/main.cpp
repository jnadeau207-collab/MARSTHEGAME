#include "game/game_state.h"
#include "game/save_state.h"
#include "platform/native_input.h"
#include "platform/win32_window.h"
#include "renderer/d3d12_renderer.h"

#include <Windows.h>
#include <ShlObj.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <cwchar>
#include <filesystem>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>

namespace
{
class KeyLatch final
{
public:
    [[nodiscard]] bool Pressed(const int virtual_key)
    {
        const bool down = (GetAsyncKeyState(virtual_key) & 0x8000) != 0;
        const bool pressed = down && !was_down_;
        was_down_ = down;
        return pressed;
    }

private:
    bool was_down_ = false;
};

std::filesystem::path ExecutableDirectory()
{
    std::array<wchar_t, 32'768> path{};
    const DWORD length = GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
    if (length == 0 || length >= path.size())
    {
        throw std::runtime_error("GetModuleFileNameW failed");
    }
    return std::filesystem::path(std::wstring_view(path.data(), length)).parent_path();
}

std::filesystem::path SavePath()
{
    PWSTR known_folder = nullptr;
    const HRESULT result = SHGetKnownFolderPath(
        FOLDERID_LocalAppData,
        KF_FLAG_CREATE,
        nullptr,
        &known_folder);
    if (FAILED(result) || known_folder == nullptr)
    {
        throw std::runtime_error("SHGetKnownFolderPath(FOLDERID_LocalAppData) failed");
    }

    const std::filesystem::path directory =
        std::filesystem::path(known_folder) / L"MARSTHEGAME";
    CoTaskMemFree(known_folder);
    return directory / L"ares_reach.save";
}

bool HasArgument(const std::wstring_view argument)
{
    const wchar_t* command_line = GetCommandLineW();
    return command_line != nullptr
        && std::wstring_view(command_line).find(argument) != std::wstring_view::npos;
}

bool KeyDown(const int virtual_key)
{
    return (GetAsyncKeyState(virtual_key) & 0x8000) != 0;
}

void LogText(const std::wstring_view text)
{
    const std::wstring owned(text);
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
    const bool vertex_shader_exists =
        std::filesystem::is_regular_file(shader_directory / L"scene.vs.dxil");
    const bool pixel_shader_exists =
        std::filesystem::is_regular_file(shader_directory / L"scene.ps.dxil");
    return vertex_shader_exists && pixel_shader_exists ? 0 : 2;
}

void LogFrameStatistics(const mars::renderer::FrameStatistics statistics)
{
    std::array<wchar_t, 256> message{};
    const int written = swprintf_s(
        message.data(),
        message.size(),
        L"MARSTHEGAME native frames=%llu last_cpu_ms=%.3f max_cpu_ms=%.3f\n",
        static_cast<unsigned long long>(statistics.presented_frames),
        statistics.last_cpu_frame_ms,
        statistics.max_cpu_frame_ms);
    if (written > 0)
    {
        OutputDebugStringW(message.data());
    }
}

void LogFrameCapture(const mars::renderer::FrameCaptureEvidence capture)
{
    std::array<wchar_t, 256> message{};
    const int written = swprintf_s(
        message.data(),
        message.size(),
        L"MARSTHEGAME capture width=%u height=%u checksum=%llu non_background=%llu\n",
        capture.width,
        capture.height,
        static_cast<unsigned long long>(capture.checksum),
        static_cast<unsigned long long>(capture.non_background_pixels));
    if (written > 0)
    {
        OutputDebugStringW(message.data());
    }
}

int RunWarpSmokeTest(const HINSTANCE instance)
{
    mars::platform::Win32Window window;
    window.Create(instance, 640, 360, L"MARSTHEGAME Native WARP Test", false);

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

    mars::game::GameState game;
    mars::game::InputState forward{};
    forward.move_z = 1.0f;
    for (std::uint32_t frame = 0; frame < 4; ++frame)
    {
        if (!window.PumpMessages())
        {
            throw std::runtime_error("WARP smoke window closed before rendering");
        }
        game.Update(forward, mars::game::GameState::kFixedStepSeconds);
        renderer.Render(game.Scene());
    }

    renderer.Resize(800, 450);
    game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    renderer.Render(game.Scene());
    renderer.RequestFrameCapture();
    game.Update(forward, mars::game::GameState::kFixedStepSeconds);
    renderer.Render(game.Scene());

    const mars::renderer::FrameCaptureEvidence capture = renderer.ConsumeFrameCapture();
    const mars::renderer::FrameStatistics statistics = renderer.Statistics();
    LogFrameStatistics(statistics);
    LogFrameCapture(capture);
    renderer.Shutdown();

    if (statistics.presented_frames != 6 || statistics.max_cpu_frame_ms <= 0.0)
    {
        return 3;
    }
    if (capture.width != 800 || capture.height != 450 || capture.checksum == 0
        || capture.non_background_pixels < 12'000)
    {
        return 4;
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
            L"MARSTHEGAME — Reach the beacon — keyboard or controller");

        mars::renderer::D3D12Renderer renderer;
        renderer.Initialize(window.Handle(), window.Width(), window.Height());
        window.SetResizeCallback(
            [&renderer](const std::uint32_t width, const std::uint32_t height) {
                renderer.Resize(width, height);
            });

        const std::filesystem::path save_path = SavePath();
        mars::game::GameState game;
        LoadGame(game, save_path, true);
        const mars::platform::NativeInput native_input;

        auto previous = std::chrono::steady_clock::now();
        mars::game::MissionState displayed_state = game.Mission();
        bool saved_checkpoint = game.CheckpointReached();
        KeyLatch save_latch;
        KeyLatch load_latch;

        while (window.PumpMessages())
        {
            if (KeyDown(VK_ESCAPE))
            {
                PostMessageW(window.Handle(), WM_CLOSE, 0, 0);
                continue;
            }

            const auto now = std::chrono::steady_clock::now();
            const float delta_seconds =
                std::chrono::duration<float>(now - previous).count();
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

            renderer.Render(game.Scene());

            if (game.Mission() != displayed_state)
            {
                displayed_state = game.Mission();
                const wchar_t* title = displayed_state == mars::game::MissionState::Complete
                    ? L"MARSTHEGAME — Ares Reach Complete — R/Y reset"
                    : L"MARSTHEGAME — WASD or left stick — Shift/LT sprint — C/X checkpoint";
                SetWindowTextW(window.Handle(), title);
            }
            if (saved_checkpoint && !game.CheckpointReached())
            {
                saved_checkpoint = false;
            }
            if (renderer.PresentedFrameCount() % 120 == 0)
            {
                LogFrameStatistics(renderer.Statistics());
            }
        }
        renderer.Shutdown();
        return 0;
    }
    catch (const std::exception& error)
    {
        const std::wstring message = ToWide(error.what());
        OutputDebugStringW(message.c_str());
        if (!self_test && !warp_smoke_test)
        {
            MessageBoxW(nullptr, message.c_str(), L"MARSTHEGAME native failure", MB_OK | MB_ICONERROR);
        }
        return 1;
    }
}
