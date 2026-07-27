#include "platform/win32_window.h"
#include "renderer/d3d12_renderer.h"

#include <Windows.h>

#include <array>
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

bool IsSelfTestRequested()
{
    const wchar_t* command_line = GetCommandLineW();
    return command_line != nullptr
        && std::wstring_view(command_line).find(L"--self-test") != std::wstring_view::npos;
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
    try
    {
        if (IsSelfTestRequested())
        {
            return RunSelfTest();
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
        }
        renderer.Shutdown();
        return 0;
    }
    catch (const std::exception& error)
    {
        const std::wstring message = ToWide(error.what());
        OutputDebugStringW(message.c_str());
        MessageBoxW(nullptr, message.c_str(), L"MARSTHEGAME native failure", MB_OK | MB_ICONERROR);
        return 1;
    }
}
