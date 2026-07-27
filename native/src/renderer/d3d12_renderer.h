#pragma once

#include "renderer/generated_environment.h"
#include "renderer/generated_materials.h"
#include "renderer/gpu_upload.h"
#include "renderer/render_scene.h"
#include "renderer/visual_slice.h"

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
    double last_gpu_frame_ms = 0.0;
    double max_gpu_frame_ms = 0.0;
    std::uint64_t hitch_count = 0;
    std::uint64_t resident_gpu_bytes = 0;
};

struct FrameCaptureEvidence
{
    std::uint64_t checksum = 0;
    std::uint64_t non_background_pixels = 0;
    std::uint64_t dark_pixels = 0;
    std::uint64_t highlight_pixels = 0;
    double average_luminance = 0.0;
    double peak_luminance = 0.0;
    double edge_energy = 0.0;
    std::uint32_t width = 0;
    std::uint32_t height = 0;
};

class D3D12Renderer final
{
public:
    static constexpr std::uint32_t kFrameCount = 2;
    static constexpr std::uint32_t kMaxInstances = 96;

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
    [[nodiscard]] VisualSliceConfiguration VisualConfiguration() const noexcept;

private:
    struct ObjectConstants
    {
        DirectX::XMFLOAT4X4 world{};
        DirectX::XMFLOAT4X4 world_inverse_transpose{};
        DirectX::XMFLOAT4X4 world_view_projection{};
        DirectX::XMFLOAT4X4 previous_world_view_projection{};
        DirectX::XMFLOAT4X4 world_light_view_projection{};
        DirectX::XMFLOAT4 tint{};
        DirectX::XMFLOAT4 material_parameters{};
        DirectX::XMFLOAT4 material_layer_mask{};
        std::array<float, 36> padding{};
    };

    struct FrameConstants
    {
        DirectX::XMFLOAT4X4 view_projection{};
        DirectX::XMFLOAT4X4 previous_view_projection{};
        DirectX::XMFLOAT4X4 light_view_projection{};
        DirectX::XMFLOAT4 camera_position_time{};
        DirectX::XMFLOAT4 sun_direction_exposure{};
        DirectX::XMFLOAT4 sun_color_intensity{};
        DirectX::XMFLOAT4 fog_color_density{};
        DirectX::XMFLOAT4 sky_zenith_history{};
        DirectX::XMFLOAT4 horizon_color_bloom{};
        DirectX::XMFLOAT4 post_parameters{};
        DirectX::XMFLOAT4 focus_parameters{};
        DirectX::XMFLOAT4 camera_motion_jitter{};
        DirectX::XMFLOAT4 particle_emitter_count{};
        DirectX::XMFLOAT4 camera_right{};
        DirectX::XMFLOAT4 camera_up{};
        std::array<DirectX::XMFLOAT4, 4> local_light_position_radius{};
        std::array<DirectX::XMFLOAT4, 4> local_light_color_intensity{};
    };

    struct MeshRange
    {
        std::uint32_t index_count = 0;
        std::uint32_t start_index = 0;
        std::int32_t base_vertex = 0;
    };

    static_assert(sizeof(ObjectConstants) == 512);
    static_assert(sizeof(FrameConstants) == 512);

    void EnableDebugLayer();
    void CreateFactoryAndDevice(AdapterPreference adapter_preference);
    void CreateCommandObjects();
    void CreateSwapChain(HWND window);
    void CreateDescriptorHeaps();
    void CreateRenderTargetViews();
    void CreateVisualTargets();
    void CreateShadowMap();
    void CreateCaptureBuffer();
    void CreatePipelines();
    void CreateStaticResources();
    void CreateConstantBuffers();
    void CreateTimingResources();
    void WriteShaderResourceViews();
    void UpdateConstants(const RenderScene& scene);
    void PopulateCommandList();
    void DrawInstances();
    void DrawParticles();
    void DrawFullscreen(ID3D12PipelineState& pipeline, D3D12_CPU_DESCRIPTOR_HANDLE target);
    void MoveToNextFrame();
    void WaitForGpu();
    void CollectGpuTiming(std::uint32_t frame_index);
    void ReleaseRenderTargets();
    void ReleaseVisualTargets();
    void ReleaseCaptureBuffer();
    void UpdateViewportAndScissor();
    void UpdateResidentMemoryEstimate();
    void ThrowIfDeviceFailed(HRESULT result, std::string_view operation) const;

    [[nodiscard]] std::filesystem::path ExecutableDirectory() const;
    [[nodiscard]] D3D12_CPU_DESCRIPTOR_HANDLE RtvHandle(std::uint32_t index) const noexcept;
    [[nodiscard]] D3D12_CPU_DESCRIPTOR_HANDLE DsvHandle(std::uint32_t index) const noexcept;
    [[nodiscard]] D3D12_GPU_DESCRIPTOR_HANDLE SrvHeapStart() const noexcept;
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
    Microsoft::WRL::ComPtr<ID3D12Resource> hdr_color_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12Resource>, 2> history_targets_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> depth_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> shadow_map_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> capture_buffer_{};
    std::array<Microsoft::WRL::ComPtr<ID3D12CommandAllocator>, kFrameCount> command_allocators_{};
    Microsoft::WRL::ComPtr<ID3D12GraphicsCommandList> command_list_{};
    Microsoft::WRL::ComPtr<ID3D12RootSignature> root_signature_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> shadow_pipeline_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> scene_pipeline_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> particle_pipeline_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> temporal_pipeline_{};
    Microsoft::WRL::ComPtr<ID3D12PipelineState> final_pipeline_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> vertex_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> index_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> base_color_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> normal_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> surface_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> environment_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> subtitle_texture_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> object_constant_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> frame_constant_buffer_{};
    Microsoft::WRL::ComPtr<ID3D12QueryHeap> timestamp_query_heap_{};
    Microsoft::WRL::ComPtr<ID3D12Resource> timestamp_readback_{};
    Microsoft::WRL::ComPtr<ID3D12Fence> fence_{};
    GpuUploadContext upload_context_{};

    D3D12_VERTEX_BUFFER_VIEW vertex_buffer_view_{};
    D3D12_INDEX_BUFFER_VIEW index_buffer_view_{};
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT capture_footprint_{};
    D3D12_VIEWPORT viewport_{};
    D3D12_RECT scissor_rect_{};
    D3D12_VIEWPORT shadow_viewport_{};
    D3D12_RECT shadow_scissor_{};
    std::array<MeshRange, static_cast<std::size_t>(MeshKind::Count)> mesh_ranges_{};
    std::array<MeshKind, kMaxInstances> instance_meshes_{};
    std::array<GeneratedMaterial, kGeneratedMaterialCount> materials_{};
    std::array<float, 4> clear_color_{0.018f, 0.022f, 0.035f, 1.0f};
    VisualSliceConfiguration visual_configuration_{};
    GpuUploadStatistics upload_statistics_{};
    FrameStatistics frame_statistics_{};
    DirectX::XMFLOAT4X4 previous_view_projection_{};
    DirectX::XMFLOAT3 previous_camera_eye_{};
    std::byte* mapped_object_constants_ = nullptr;
    std::byte* mapped_frame_constants_ = nullptr;
    HANDLE fence_event_ = nullptr;
    std::array<std::uint64_t, kFrameCount> fence_values_{};
    std::array<bool, kFrameCount> timestamp_valid_{};
    std::uint64_t timestamp_frequency_ = 0;
    std::uint64_t capture_total_bytes_ = 0;
    std::uint64_t capture_row_size_bytes_ = 0;
    std::uint64_t visual_target_bytes_ = 0;
    std::uint32_t capture_row_count_ = 0;
    std::uint32_t frame_index_ = 0;
    std::uint32_t rtv_descriptor_size_ = 0;
    std::uint32_t dsv_descriptor_size_ = 0;
    std::uint32_t srv_descriptor_size_ = 0;
    std::uint32_t width_ = 0;
    std::uint32_t height_ = 0;
    std::uint32_t instance_count_ = 0;
    std::uint32_t history_read_index_ = 0;
    std::uint32_t active_history_write_index_ = 1;
    float current_exposure_ = 1.0f;
    float previous_scene_time_ = 0.0f;
    bool frame_capture_enabled_ = false;
    bool capture_requested_ = false;
    bool capture_submitted_ = false;
    bool history_valid_ = false;
    bool previous_camera_valid_ = false;
    bool initialized_ = false;
};
} // namespace mars::renderer
