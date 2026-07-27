#pragma once

#include <Windows.h>
#include <DirectXMath.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string_view>

namespace mars::renderer
{
enum class AdapterPreference
{
    Hardware,
    Warp,
};

struct FrameStatistics
{
    std::uint64_t presented_frames = 0;
    double last_cpu_frame_ms = 0.0;
    double max_cpu_frame_ms = 0.0;
};

class D3D12Renderer final
{
public:
    static constexpr std::uint32_t kFrameCount = 2;

    D3D12Renderer() = default;
    D3D12Renderer(const D3D12Renderer&) = delete;
    D3D12Renderer& operator=(const D3D12Renderer&) = delete;
    ~D3D12Renderer();

    void Initialize(
        HWND window,
        std::uint32_t width,
        std::uint32_t height,
        AdapterPreference adapter_preference = AdapterPreference::Hardware);
    void Render();
    void Resize(std::uint32_t width, std::uint32_t height);
    void Shutdown();

    [[nodiscard]] bool IsInitialized() const noexcept;
    [[nodiscard]] std::uint64_t PresentedFrameCount() const noexcept;
    [[nodiscard]] FrameStatistics Statistics() const noexcept;

private:
    struct Vertex
    {
        float position[3];
        float normal[3];
        float color[3];
    };

    struct alignas(256) SceneConstants
    {
        DirectX::XMFLOAT4X4 world{};
        DirectX::XMFLOAT4X4 world_view_projection{};
        DirectX::XMFLOAT4 light_direction{};
    };

    static_assert(sizeof(SceneConstants) == 256);

    void EnableDebugLayer();
    void CreateFactoryAndDevice(AdapterPreference adapter_preference);
    void CreateCommandObjects();
    void CreateSwapChain(HWND window);
    void CreateRenderTargetViews();
    void CreateDepthBuffer();
    void CreatePipeline();
    void CreateGeometry();
    void CreateSceneConstants();
    void UpdateSceneConstants();
    void PopulateCommandList();
    void MoveToNextFrame();
    void WaitForGpu();
    void ReleaseRenderTargets();
    void ReleaseDepthBuffer();
    void UpdateViewportAndScissor();
    void ThrowIfDeviceFailed(HRESULT result, std::string_view operation) const;

    [[nodiscard]] std::filesystem::path ExecutableDirectory() const;
    [[nodiscard]] static Microsoft::WRL::ComPtr<IDXGIAdapter1> ChooseAdapter(
        IDXGIFactory6& factory,
        AdapterPreference adapter_preference);

    Microsoft::WRL::ComPtr<IDXGIFactory6> factory_{};
    Microsoft::WRL::ComPtr<ID3D12Device> device_{};
    Microsoft::WRL::ComPtr<ID3D12CommandQueue> command_queue_{};
    Microsoft::WRL::ComPtr<IDXGISwapChain3> swap_chain_{};
    Microsoft::WRL::ComPtr<ID3D12DescriptorHeap> rtv_heap_{};
    Microsoft::WRL::ComPtr<ID3D12DescriptorHeap> dsv_heap_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12Resource>, kFrameCount> render_targets_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> depth_buffer_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12CommandAllocator>, kFrameCount>
        command_allocators_{};
    Microsoft::WRL::ComPtr<ID3D12GraphicsCommandList> command_list_{};
    Microsoft::WRL::ComPtr<ID3D12RootSignature> root_signature_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> pipeline_state_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> vertex_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> index_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> scene_constant_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Fence> fence_{};

    D3D12_VERTEX_BUFFER_VIEW vertex_buffer_view_{};
    D3D12_INDEX_BUFFER_VIEW index_buffer_view_{};
    D3D12_CPU_DESCRIPTOR_HANDLE dsv_handle_{};
    D3D12_VIEWPORT viewport_{};
    D3D12_RECT scissor_rect_{};
    std::byte* mapped_scene_constants_ = nullptr;
    HANDLE fence_event_ = nullptr;
    std::array<std::uint64_t, kFrameCount> fence_values_{};
    std::uint32_t frame_index_ = 0;
    std::uint32_t rtv_descriptor_size_ = 0;
    std::uint32_t width_ = 0;
    std::uint32_t height_ = 0;
    std::uint32_t index_count_ = 0;
    std::uint64_t presented_frames_ = 0;
    double last_cpu_frame_ms_ = 0.0;
    double max_cpu_frame_ms_ = 0.0;
    bool initialized_ = false;
};
} // namespace mars::renderer
