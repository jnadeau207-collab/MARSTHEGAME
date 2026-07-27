#include "platform/win32_window.h"

#include <stdexcept>
#include <string>

namespace mars::platform
{
namespace
{
constexpr wchar_t kWindowClassName[] = L"MARSTHEGAME.Native.Window";
}

Win32Window::~Win32Window()
{
    if (window_ != nullptr)
    {
        DestroyWindow(window_);
        window_ = nullptr;
    }
    if (instance_ != nullptr)
    {
        UnregisterClassW(kWindowClassName, instance_);
    }
}

void Win32Window::Create(
    HINSTANCE instance,
    const std::uint32_t width,
    const std::uint32_t height,
    const std::wstring_view title)
{
    if (instance == nullptr || width == 0 || height == 0)
    {
        throw std::invalid_argument("Win32Window requires a valid instance and non-zero size");
    }

    instance_ = instance;
    width_ = width;
    height_ = height;

    WNDCLASSEXW window_class{};
    window_class.cbSize = sizeof(window_class);
    window_class.style = CS_HREDRAW | CS_VREDRAW;
    window_class.lpfnWndProc = &Win32Window::WindowProc;
    window_class.hInstance = instance_;
    window_class.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    window_class.lpszClassName = kWindowClassName;

    if (RegisterClassExW(&window_class) == 0)
    {
        throw std::runtime_error("RegisterClassExW failed");
    }

    RECT client_rect{0, 0, static_cast<LONG>(width), static_cast<LONG>(height)};
    if (AdjustWindowRect(&client_rect, WS_OVERLAPPEDWINDOW, FALSE) == FALSE)
    {
        throw std::runtime_error("AdjustWindowRect failed");
    }

    const std::wstring owned_title(title);
    window_ = CreateWindowExW(
        0,
        kWindowClassName,
        owned_title.c_str(),
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        client_rect.right - client_rect.left,
        client_rect.bottom - client_rect.top,
        nullptr,
        nullptr,
        instance_,
        this);

    if (window_ == nullptr)
    {
        throw std::runtime_error("CreateWindowExW failed");
    }

    running_ = true;
    ShowWindow(window_, SW_SHOWDEFAULT);
    UpdateWindow(window_);
}

bool Win32Window::PumpMessages()
{
    MSG message{};
    while (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE) != FALSE)
    {
        if (message.message == WM_QUIT)
        {
            running_ = false;
            return false;
        }
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    return running_;
}

HWND Win32Window::Handle() const noexcept
{
    return window_;
}

std::uint32_t Win32Window::Width() const noexcept
{
    return width_;
}

std::uint32_t Win32Window::Height() const noexcept
{
    return height_;
}

void Win32Window::SetResizeCallback(ResizeCallback callback)
{
    resize_callback_ = std::move(callback);
}

LRESULT CALLBACK Win32Window::WindowProc(
    const HWND window,
    const UINT message,
    const WPARAM wparam,
    const LPARAM lparam)
{
    Win32Window* self = nullptr;
    if (message == WM_NCCREATE)
    {
        const auto* create = reinterpret_cast<const CREATESTRUCTW*>(lparam);
        self = static_cast<Win32Window*>(create->lpCreateParams);
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(self));
    }
    else
    {
        self = reinterpret_cast<Win32Window*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    }

    if (self != nullptr)
    {
        return self->HandleMessage(window, message, wparam, lparam);
    }
    return DefWindowProcW(window, message, wparam, lparam);
}

LRESULT Win32Window::HandleMessage(
    const HWND window,
    const UINT message,
    const WPARAM wparam,
    const LPARAM lparam)
{
    switch (message)
    {
    case WM_SIZE:
        if (wparam != SIZE_MINIMIZED)
        {
            width_ = static_cast<std::uint32_t>(LOWORD(lparam));
            height_ = static_cast<std::uint32_t>(HIWORD(lparam));
            if (width_ > 0 && height_ > 0 && resize_callback_)
            {
                resize_callback_(width_, height_);
            }
        }
        return 0;
    case WM_CLOSE:
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        window_ = nullptr;
        running_ = false;
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(window, message, wparam, lparam);
    }
}
} // namespace mars::platform
