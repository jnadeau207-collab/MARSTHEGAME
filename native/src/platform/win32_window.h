#pragma once

#include <Windows.h>

#include <cstdint>
#include <functional>
#include <string_view>

namespace mars::platform
{
class Win32Window final
{
public:
    using ResizeCallback = std::function<void(std::uint32_t, std::uint32_t)>;

    Win32Window() = default;
    Win32Window(const Win32Window&) = delete;
    Win32Window& operator=(const Win32Window&) = delete;
    ~Win32Window();

    void Create(HINSTANCE instance, std::uint32_t width, std::uint32_t height, std::wstring_view title);
    [[nodiscard]] bool PumpMessages();
    [[nodiscard]] HWND Handle() const noexcept;
    [[nodiscard]] std::uint32_t Width() const noexcept;
    [[nodiscard]] std::uint32_t Height() const noexcept;
    void SetResizeCallback(ResizeCallback callback);

private:
    static LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wparam, LPARAM lparam);
    LRESULT HandleMessage(HWND window, UINT message, WPARAM wparam, LPARAM lparam);

    HINSTANCE instance_ = nullptr;
    HWND window_ = nullptr;
    std::uint32_t width_ = 0;
    std::uint32_t height_ = 0;
    bool running_ = false;
    ResizeCallback resize_callback_{};
};
} // namespace mars::platform
