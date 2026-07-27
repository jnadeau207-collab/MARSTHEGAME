#pragma once

#include "renderer/fence_retirement.h"

#include <Windows.h>
#include <d3d12.h>
#include <wrl/client.h>

#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace mars::renderer
{
struct GpuUploadStatistics
{
    std::uint64_t uploaded_bytes = 0;
    std::uint32_t uploaded_resources = 0;
    std::uint64_t last_submitted_fence = 0;
    std::size_t pending_staging_batches = 0;
};

class GpuUploadContext final
{
public:
    GpuUploadContext() = default;
    GpuUploadContext(const GpuUploadContext&) = delete;
    GpuUploadContext& operator=(const GpuUploadContext&) = delete;
    ~GpuUploadContext();

    void Initialize(ID3D12Device& device, ID3D12CommandQueue& queue);
    void Begin();
    [[nodiscard]] Microsoft::WRL::ComPtr<ID3D12Resource> UploadBuffer(
        std::span<const std::byte> data,
        D3D12_RESOURCE_STATES final_state,
        std::wstring_view name);
    [[nodiscard]] Microsoft::WRL::ComPtr<ID3D12Resource> UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t> rgba8,
        std::uint32_t width,
        std::uint32_t height,
        std::uint32_t layers,
        D3D12_RESOURCE_STATES final_state,
        std::wstring_view name);
    [[nodiscard]] std::uint64_t Submit();
    void Wait(std::uint64_t fence_value);
    void CollectCompleted();
    void Shutdown();

    [[nodiscard]] bool IsInitialized() const noexcept;
    [[nodiscard]] GpuUploadStatistics Statistics() const noexcept;

private:
    using Resource = Microsoft::WRL::ComPtr<ID3D12Resource>;
    using StagingBatch = std::vector<Resource>;

    [[nodiscard]] Resource CreateCommittedBuffer(
        D3D12_HEAP_TYPE heap_type,
        std::uint64_t size,
        D3D12_RESOURCE_STATES initial_state,
        std::wstring_view name) const;
    static void ThrowIfFailed(HRESULT result, std::string_view operation);
    static void NameObject(ID3D12Object* object, std::wstring_view name);

    ID3D12Device* device_ = nullptr;
    ID3D12CommandQueue* queue_ = nullptr;
    Microsoft::WRL::ComPtr<ID3D12CommandAllocator> allocator_{};
    Microsoft::WRL::ComPtr<ID3D12GraphicsCommandList> command_list_{};
    Microsoft::WRL::ComPtr<ID3D12Fence> fence_{};
    HANDLE fence_event_ = nullptr;
    FenceRetirementQueue<StagingBatch> retirement_queue_{};
    StagingBatch recording_staging_{};
    std::uint64_t next_fence_value_ = 1;
    std::uint64_t last_submitted_fence_ = 0;
    std::uint64_t uploaded_bytes_ = 0;
    std::uint32_t uploaded_resources_ = 0;
    bool recording_ = false;
    bool initialized_ = false;
};
} // namespace mars::renderer
