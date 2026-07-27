#pragma once

#include <Windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>

#include <array>
#include <cstdint>
#include <filesystem>

namespace mars::renderer
{
class D3D12Renderer final
{
public:
    static constexpr std::uint32_t kFrameCount = 2;

    D3D12Renderer() = default;
    D3D12Renderer(const D3D12Renderer&) = delete;
    D3D12Renderer& operator=(const D3D12Renderer&) = delete;
    ~D3D12Renderer();

    void Initialize(HWND window, std::uint32_t width, std::uint32_t height);
    void Render();
    void Resize(std::uint32_t width, std::uint32_t height);
    void Shutdown();

    [[nodiscard]] bool IsInitialized() const noexcept;
    [[nodiscard]] std::uint64_t PresentedFrameCount() const noexcept;

private:
    struct Vertex
    {
        float position[3];
        float color[3];
    };

    void EnableDebugLayer();
    void CreateFactoryAndDevice();
    void CreateCommandObjects();
    void CreateSwapChain(HWND window);
    void CreateRenderTargetViews();
    void CreatePipeline();
    void CreateGeometry();
    void PopulateCommandList();
    void MoveToNextFrame();
    void WaitForGpu();
    void ReleaseRenderTargets();
    void UpdateViewportAndScissor();

    [[nodiscard]] std::filesystem::path ExecutableDirectory() const;
    [[nodiscard]] static Microsoft::WRL::ComPtr<IDXGIAdapter1> ChooseAdapter(
        IDXGIFactory6& factory);

    Microsoft::WRL::ComPtr<IDXGIFactory6> factory_{};
    Microsoft::WRL::ComPtr<ID3D12Device> device_{};
    Microsoft::WRL::ComPtr<ID3D12CommandQueue> command_queue_{};
    Microsoft::WRL::ComPtr<IDXGISwapChain3> swap_chain_{};
    Microsoft::WRL::ComPtr<ID3D12DescriptorHeap> rtv_heap_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12Resource>, kFrameCount> render_targets_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12CommandAllocator>, kFrameCount>
        command_allocators_{};
    Microsoft::WRL::ComPtr<ID3D12GraphicsCommandList> command_list_{};
    Microsoft::WRL::ComPtr<ID3D12RootSignature> root_signature_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> pipeline_state_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> vertex_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> index_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Fence> fence_{};

    D3D12_VERTEX_BUFFER_VIEW vertex_buffer_view_{};
    D3D12_INDEX_BUFFER_VIEW index_buffer_view_{};
    D3D12_VIEWPORT viewport_{};
    D3D12_RECT scissor_rect_{};
    HANDLE fence_event_ = nullptr;
    std::array<std::uint64_t, kFrameCount> fence_values_{};
    std::uint32_t frame_index_ = 0;
    std::uint32_t rtv_descriptor_size_ = 0;
    std::uint32_t width_ = 0;
    std::uint32_t height_ = 0;
    std::uint64_t presented_frames_ = 0;
    bool initialized_ = false;
};
} // namespace mars::renderer
