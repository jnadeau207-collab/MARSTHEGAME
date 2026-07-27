#pragma once

#include "renderer/generated_materials.h"
#include "renderer/gpu_upload.h"
#include "renderer/render_scene.h"

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

struct FrameCaptureEvidence
{
    std::uint64_t checksum = 0;
    std::uint64_t non_background_pixels = 0;
    std::uint32_t width = 0;
    std::uint32_t height = 0;
};

class D3D12Renderer final
{
public:
    static constexpr std::uint32_t kFrameCount = 2;
    static constexpr std::uint32_t kMaxInstances = 64;

    D3D12Renderer() = default;
    D3D12Renderer(const D3D12Renderer&) = delete;
    D3D12Renderer& operator=(const D3D12Renderer&) = delete;
    ~D3D12Renderer();

    void Initialize(
        HWND window,
        std::uint32_t width,
        std::uint32_t height,
        AdapterPreference adapter_preference = AdapterPreference::Hardware,
        bool enable_frame_capture = false);
    void Render(const RenderScene& scene);
    void Resize(std::uint32_t width, std::uint32_t height);
    void Shutdown();
    void RequestFrameCapture();
    [[nodiscard]] FrameCaptureEvidence ConsumeFrameCapture();

    [[nodiscard]] bool IsInitialized() const noexcept;
    [[nodiscard]] std::uint64_t PresentedFrameCount() const noexcept;
    [[nodiscard]] FrameStatistics Statistics() const noexcept;
    [[nodiscard]] GpuUploadStatistics UploadStatistics() const noexcept;

private:
    struct SceneConstants
    {
        DirectX::XMFLOAT4X4 world{};
        DirectX::XMFLOAT4X4 world_view_projection{};
        DirectX::XMFLOAT4 light_direction{};
        DirectX::XMFLOAT4 tint{};
        DirectX::XMFLOAT4 material_parameters{};
        DirectX::XMFLOAT4 material_layer_mask{};
        std::array<float, 16> padding{};
    };

    struct MeshRange
    {
        std::uint32_t index_count = 0;
        std::uint32_t start_index = 0;
        std::int32_t base_vertex = 0;
    };

    static_assert(sizeof(SceneConstants) == 256);

    void EnableDebugLayer();
    void CreateFactoryAndDevice(AdapterPreference adapter_preference);
    void CreateCommandObjects();
    void CreateSwapChain(HWND window);
    void CreateRenderTargetViews();
    void CreateDepthBuffer();
    void CreateCaptureBuffer();
    void CreatePipeline();
    void CreateStaticResources();
    void CreateSceneConstants();
    void UpdateSceneConstants(const RenderScene& scene);
    void PopulateCommandList();
    void MoveToNextFrame();
    void WaitForGpu();
    void ReleaseRenderTargets();
    void ReleaseDepthBuffer();
    void ReleaseCaptureBuffer();
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
    Microsoft::WRL::ComPtr<ID3D12DescriptorHeap> srv_heap_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12Resource>, kFrameCount> render_targets_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> depth_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> capture_buffer_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12CommandAllocator>, kFrameCount>
        command_allocators_{};
    Microsoft::WRL::ComPtr<ID3D12GraphicsCommandList> command_list_{};
    Microsoft::WRL::ComPtr<ID3D12RootSignature> root_signature_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> pipeline_state_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> vertex_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> index_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> base_color_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> normal_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> surface_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> scene_constant_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Fence> fence_{};
    GpuUploadContext upload_context_{};

    D3D12_VERTEX_BUFFER_VIEW vertex_buffer_view_{};
    D3D12_INDEX_BUFFER_VIEW index_buffer_view_{};
    D3D12_CPU_DESCRIPTOR_HANDLE dsv_handle_{};
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT capture_footprint_{};
    D3D12_VIEWPORT viewport_{};
    D3D12_RECT scissor_rect_{};
    std::array<MeshRange, static_cast<std::size_t>(MeshKind::Count)> mesh_ranges_{};
    std::array<MeshKind, kMaxInstances> instance_meshes_{};
    std::array<GeneratedMaterial, kGeneratedMaterialCount> materials_{};
    std::array<float, 4> clear_color_{0.018f, 0.022f, 0.035f, 1.0f};
    GpuUploadStatistics upload_statistics_{};
    std::byte* mapped_scene_constants_ = nullptr;
    HANDLE fence_event_ = nullptr;
    std::array<std::uint64_t, kFrameCount> fence_values_{};
    std::uint64_t capture_total_bytes_ = 0;
    std::uint64_t capture_row_size_bytes_ = 0;
    std::uint32_t capture_row_count_ = 0;
    std::uint32_t frame_index_ = 0;
    std::uint32_t rtv_descriptor_size_ = 0;
    std::uint32_t width_ = 0;
    std::uint32_t height_ = 0;
    std::uint32_t instance_count_ = 0;
    std::uint64_t presented_frames_ = 0;
    double last_cpu_frame_ms_ = 0.0;
    double max_cpu_frame_ms_ = 0.0;
    bool frame_capture_enabled_ = false;
    bool capture_requested_ = false;
    bool capture_submitted_ = false;
    bool initialized_ = false;
};
} // namespace mars::renderer
