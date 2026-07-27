#include "platform/win32_window.h"
#include "renderer/d3d12_renderer.h"

#include <Windows.h>

#include <array>
#include <cstdint>
#include <cwchar>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <string_view>

namespace
{
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

bool HasArgument(const std::wstring_view argument)
{
    const wchar_t* command_line = GetCommandLineW();
    return command_line != nullptr
        && std::wstring_view(command_line).find(argument) != std::wstring_view::npos;
}

int RunSelfTest()
{
    const std::filesystem::path shader_directory = ExecutableDirectory() / L"shaders";
    const bool vertex_shader_exists =
        std::filesystem::is_regular_file(shader_directory / L"triangle.vs.dxil");
    const bool pixel_shader_exists =
        std::filesystem::is_regular_file(shader_directory / L"triangle.ps.dxil");
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
    window.Create(instance, 640, 360, L"MARSTHEGAME WARP Smoke Test", false);

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

    for (std::uint32_t frame = 0; frame < 3; ++frame)
    {
        if (!window.PumpMessages())
        {
            throw std::runtime_error("WARP smoke window closed before the first render sequence");
        }
        renderer.Render();
    }

    renderer.Resize(800, 450);
    for (std::uint32_t frame = 0; frame < 2; ++frame)
    {
        if (!window.PumpMessages())
        {
            throw std::runtime_error("WARP smoke window closed before the resize render sequence");
        }
        renderer.Render();
    }

    renderer.RequestFrameCapture();
    renderer.Render();
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
        || capture.non_background_pixels < 1'000)
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
        window.Create(instance, 1600, 900, L"MARSTHEGAME — Native Renderer Foundation");

        mars::renderer::D3D12Renderer renderer;
        renderer.Initialize(window.Handle(), window.Width(), window.Height());
        window.SetResizeCallback(
            [&renderer](const std::uint32_t width, const std::uint32_t height) {
                renderer.Resize(width, height);
            });

        while (window.PumpMessages())
        {
            renderer.Render();
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
