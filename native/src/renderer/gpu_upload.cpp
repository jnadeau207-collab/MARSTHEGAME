#include "renderer/gpu_upload.h"

#include <algorithm>
#include <cstring>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace mars::renderer
{
namespace
{
using Microsoft::WRL::ComPtr;

[[nodiscard]] std::string FormatHresult(const HRESULT result)
{
    std::ostringstream value;
    value << "0x" << std::hex << static_cast<unsigned long>(result);
    return value.str();
}

[[nodiscard]] D3D12_RESOURCE_BARRIER TransitionBarrier(
    ID3D12Resource* resource,
    const D3D12_RESOURCE_STATES before,
    const D3D12_RESOURCE_STATES after)
{
    D3D12_RESOURCE_BARRIER barrier{};
    barrier.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
    barrier.Flags = D3D12_RESOURCE_BARRIER_FLAG_NONE;
    barrier.Transition.pResource = resource;
    barrier.Transition.StateBefore = before;
    barrier.Transition.StateAfter = after;
    barrier.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
    return barrier;
}
} // namespace

GpuUploadContext::~GpuUploadContext()
{
    try
    {
        Shutdown();
    }
    catch (...)
    {
    }
}

void GpuUploadContext::Initialize(ID3D12Device& device, ID3D12CommandQueue& queue)
{
    if (initialized_)
    {
        throw std::logic_error("GpuUploadContext is already initialized");
    }

    device_ = &device;
    queue_ = &queue;
    initialized_ = true;
    uploaded_bytes_ = 0;
    uploaded_resources_ = 0;
    next_fence_value_ = 1;
    last_submitted_fence_ = 0;

    try
    {
        ThrowIfFailed(
            device_->CreateCommandAllocator(
                D3D12_COMMAND_LIST_TYPE_DIRECT,
                IID_PPV_ARGS(&allocator_)),
            "ID3D12Device::CreateCommandAllocator(upload)");
        NameObject(allocator_.Get(), L"MARSTHEGAME Upload Command Allocator");

        ThrowIfFailed(
            device_->CreateCommandList(
                0,
                D3D12_COMMAND_LIST_TYPE_DIRECT,
                allocator_.Get(),
                nullptr,
                IID_PPV_ARGS(&command_list_)),
            "ID3D12Device::CreateCommandList(upload)");
        NameObject(command_list_.Get(), L"MARSTHEGAME Upload Command List");
        ThrowIfFailed(
            command_list_->Close(),
            "ID3D12GraphicsCommandList::Close(upload initialize)");

        ThrowIfFailed(
            device_->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence_)),
            "ID3D12Device::CreateFence(upload)");
        NameObject(fence_.Get(), L"MARSTHEGAME Upload Fence");

        fence_event_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (fence_event_ == nullptr)
        {
            throw std::runtime_error("CreateEventW failed for the upload fence");
        }
    }
    catch (...)
    {
        Shutdown();
        throw;
    }
}

void GpuUploadContext::Begin()
{
    if (!initialized_)
    {
        throw std::logic_error("GpuUploadContext must be initialized before recording");
    }
    if (recording_)
    {
        throw std::logic_error("GpuUploadContext is already recording");
    }
    if (last_submitted_fence_ != 0 && fence_->GetCompletedValue() < last_submitted_fence_)
    {
        Wait(last_submitted_fence_);
    }
    CollectCompleted();

    ThrowIfFailed(allocator_->Reset(), "ID3D12CommandAllocator::Reset(upload)");
    ThrowIfFailed(
        command_list_->Reset(allocator_.Get(), nullptr),
        "ID3D12GraphicsCommandList::Reset(upload)");
    recording_staging_.clear();
    recording_ = true;
}

ComPtr<ID3D12Resource> GpuUploadContext::UploadBuffer(
    const std::span<const std::byte> data,
    const D3D12_RESOURCE_STATES final_state,
    const std::wstring_view name)
{
    if (!recording_)
    {
        throw std::logic_error("UploadBuffer requires an active upload recording");
    }
    if (data.empty())
    {
        throw std::invalid_argument("UploadBuffer requires non-empty data");
    }

    const std::uint64_t size = static_cast<std::uint64_t>(data.size_bytes());
    Resource destination = CreateCommittedBuffer(
        D3D12_HEAP_TYPE_DEFAULT,
        size,
        D3D12_RESOURCE_STATE_COPY_DEST,
        name);
    Resource staging = CreateCommittedBuffer(
        D3D12_HEAP_TYPE_UPLOAD,
        size,
        D3D12_RESOURCE_STATE_GENERIC_READ,
        std::wstring(name) + L" Staging");

    void* mapped = nullptr;
    const D3D12_RANGE read_range{0, 0};
    ThrowIfFailed(staging->Map(0, &read_range, &mapped), "ID3D12Resource::Map(buffer staging)");
    std::memcpy(mapped, data.data(), data.size_bytes());
    staging->Unmap(0, nullptr);

    command_list_->CopyBufferRegion(destination.Get(), 0, staging.Get(), 0, size);
    if (final_state != D3D12_RESOURCE_STATE_COPY_DEST)
    {
        const D3D12_RESOURCE_BARRIER barrier = TransitionBarrier(
            destination.Get(),
            D3D12_RESOURCE_STATE_COPY_DEST,
            final_state);
        command_list_->ResourceBarrier(1, &barrier);
    }

    recording_staging_.push_back(std::move(staging));
    uploaded_bytes_ += size;
    ++uploaded_resources_;
    return destination;
}

ComPtr<ID3D12Resource> GpuUploadContext::UploadTexture2DArrayRgba8(
    const std::span<const std::uint8_t> rgba8,
    const std::uint32_t width,
    const std::uint32_t height,
    const std::uint32_t layers,
    const D3D12_RESOURCE_STATES final_state,
    const std::wstring_view name)
{
    if (!recording_)
    {
        throw std::logic_error("UploadTexture2DArrayRgba8 requires an active upload recording");
    }
    if (width == 0 || height == 0 || layers == 0)
    {
        throw std::invalid_argument("Texture dimensions and layer count must be non-zero");
    }
    const std::size_t expected_size = static_cast<std::size_t>(width)
        * static_cast<std::size_t>(height) * static_cast<std::size_t>(layers) * 4U;
    if (rgba8.size() != expected_size)
    {
        throw std::invalid_argument("RGBA8 texture payload size does not match its dimensions");
    }
    if (layers > static_cast<std::uint32_t>((std::numeric_limits<std::uint16_t>::max)()))
    {
        throw std::invalid_argument("Texture array exceeds the D3D12 layer limit");
    }

    D3D12_HEAP_PROPERTIES default_heap{};
    default_heap.Type = D3D12_HEAP_TYPE_DEFAULT;
    default_heap.CreationNodeMask = 1;
    default_heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    description.Width = width;
    description.Height = height;
    description.DepthOrArraySize = static_cast<UINT16>(layers);
    description.MipLevels = 1;
    description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;

    Resource destination;
    ThrowIfFailed(
        device_->CreateCommittedResource(
            &default_heap,
            D3D12_HEAP_FLAG_NONE,
            &description,
            D3D12_RESOURCE_STATE_COPY_DEST,
            nullptr,
            IID_PPV_ARGS(&destination)),
        "ID3D12Device::CreateCommittedResource(default texture)");
    NameObject(destination.Get(), name);

    std::vector<D3D12_PLACED_SUBRESOURCE_FOOTPRINT> footprints(layers);
    std::vector<UINT> row_counts(layers);
    std::vector<UINT64> row_sizes(layers);
    UINT64 total_bytes = 0;
    device_->GetCopyableFootprints(
        &description,
        0,
        layers,
        0,
        footprints.data(),
        row_counts.data(),
        row_sizes.data(),
        &total_bytes);

    Resource staging = CreateCommittedBuffer(
        D3D12_HEAP_TYPE_UPLOAD,
        total_bytes,
        D3D12_RESOURCE_STATE_GENERIC_READ,
        std::wstring(name) + L" Staging");

    void* mapped = nullptr;
    const D3D12_RANGE read_range{0, 0};
    ThrowIfFailed(staging->Map(0, &read_range, &mapped), "ID3D12Resource::Map(texture staging)");
    auto* destination_bytes = static_cast<std::uint8_t*>(mapped);
    const std::size_t source_row_pitch = static_cast<std::size_t>(width) * 4U;
    const std::size_t source_layer_pitch = source_row_pitch * static_cast<std::size_t>(height);

    for (std::uint32_t layer = 0; layer < layers; ++layer)
    {
        const D3D12_PLACED_SUBRESOURCE_FOOTPRINT& footprint = footprints[layer];
        const std::uint8_t* source_layer = rgba8.data()
            + static_cast<std::size_t>(layer) * source_layer_pitch;
        std::uint8_t* destination_layer = destination_bytes
            + static_cast<std::size_t>(footprint.Offset);
        for (std::uint32_t row = 0; row < height; ++row)
        {
            std::memcpy(
                destination_layer
                    + static_cast<std::size_t>(row) * footprint.Footprint.RowPitch,
                source_layer + static_cast<std::size_t>(row) * source_row_pitch,
                source_row_pitch);
        }

        D3D12_TEXTURE_COPY_LOCATION destination_location{};
        destination_location.pResource = destination.Get();
        destination_location.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        destination_location.SubresourceIndex = layer;

        D3D12_TEXTURE_COPY_LOCATION source_location{};
        source_location.pResource = staging.Get();
        source_location.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
        source_location.PlacedFootprint = footprint;
        command_list_->CopyTextureRegion(
            &destination_location,
            0,
            0,
            0,
            &source_location,
            nullptr);
    }
    staging->Unmap(0, nullptr);

    if (final_state != D3D12_RESOURCE_STATE_COPY_DEST)
    {
        const D3D12_RESOURCE_BARRIER barrier = TransitionBarrier(
            destination.Get(),
            D3D12_RESOURCE_STATE_COPY_DEST,
            final_state);
        command_list_->ResourceBarrier(1, &barrier);
    }

    recording_staging_.push_back(std::move(staging));
    uploaded_bytes_ += static_cast<std::uint64_t>(rgba8.size());
    ++uploaded_resources_;
    return destination;
}

std::uint64_t GpuUploadContext::Submit()
{
    if (!recording_)
    {
        throw std::logic_error("Submit requires an active upload recording");
    }
    if (recording_staging_.empty())
    {
        throw std::logic_error("Submit requires at least one staged resource");
    }

    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close(upload)");
    ID3D12CommandList* lists[] = {command_list_.Get()};
    queue_->ExecuteCommandLists(1, lists);

    const std::uint64_t fence_value = next_fence_value_++;
    ThrowIfFailed(queue_->Signal(fence_.Get(), fence_value), "ID3D12CommandQueue::Signal(upload)");
    retirement_queue_.Retire(fence_value, std::move(recording_staging_));
    recording_staging_.clear();
    last_submitted_fence_ = fence_value;
    recording_ = false;
    return fence_value;
}

void GpuUploadContext::Wait(const std::uint64_t fence_value)
{
    if (!initialized_ || fence_value == 0)
    {
        return;
    }
    if (fence_->GetCompletedValue() < fence_value)
    {
        ThrowIfFailed(
            fence_->SetEventOnCompletion(fence_value, fence_event_),
            "ID3D12Fence::SetEventOnCompletion(upload)");
        const DWORD wait_result = WaitForSingleObject(fence_event_, INFINITE);
        if (wait_result != WAIT_OBJECT_0)
        {
            throw std::runtime_error("WaitForSingleObject failed for the upload fence");
        }
    }
    CollectCompleted();
}

void GpuUploadContext::CollectCompleted()
{
    if (fence_ != nullptr)
    {
        static_cast<void>(retirement_queue_.Collect(fence_->GetCompletedValue()));
    }
}

void GpuUploadContext::Shutdown()
{
    if (!initialized_)
    {
        return;
    }
    if (recording_)
    {
        recording_staging_.clear();
        recording_ = false;
    }
    if (last_submitted_fence_ != 0)
    {
        Wait(last_submitted_fence_);
    }
    retirement_queue_.Clear();
    recording_staging_.clear();

    if (fence_event_ != nullptr)
    {
        CloseHandle(fence_event_);
        fence_event_ = nullptr;
    }
    command_list_.Reset();
    allocator_.Reset();
    fence_.Reset();
    queue_ = nullptr;
    device_ = nullptr;
    initialized_ = false;
}

bool GpuUploadContext::IsInitialized() const noexcept
{
    return initialized_;
}

GpuUploadStatistics GpuUploadContext::Statistics() const noexcept
{
    return {
        .uploaded_bytes = uploaded_bytes_,
        .uploaded_resources = uploaded_resources_,
        .last_submitted_fence = last_submitted_fence_,
        .pending_staging_batches = retirement_queue_.PendingBatchCount(),
    };
}

GpuUploadContext::Resource GpuUploadContext::CreateCommittedBuffer(
    const D3D12_HEAP_TYPE heap_type,
    const std::uint64_t size,
    const D3D12_RESOURCE_STATES initial_state,
    const std::wstring_view name) const
{
    if (size == 0)
    {
        throw std::invalid_argument("Committed buffer size must be non-zero");
    }

    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = heap_type;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    description.Width = size;
    description.Height = 1;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;

    Resource resource;
    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap,
            D3D12_HEAP_FLAG_NONE,
            &description,
            initial_state,
            nullptr,
            IID_PPV_ARGS(&resource)),
        "ID3D12Device::CreateCommittedResource(buffer)");
    NameObject(resource.Get(), name);
    return resource;
}

void GpuUploadContext::ThrowIfFailed(
    const HRESULT result,
    const std::string_view operation)
{
    if (FAILED(result))
    {
        throw std::runtime_error(
            std::string(operation) + " failed with HRESULT " + FormatHresult(result));
    }
}

void GpuUploadContext::NameObject(ID3D12Object* object, const std::wstring_view name)
{
    if (object == nullptr)
    {
        return;
    }
    const std::wstring owned_name(name);
    ThrowIfFailed(object->SetName(owned_name.c_str()), "ID3D12Object::SetName(upload)");
}
} // namespace mars::renderer
