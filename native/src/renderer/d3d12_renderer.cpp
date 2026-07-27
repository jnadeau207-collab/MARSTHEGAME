#include "renderer/d3d12_renderer.h"

#include <d3d12sdklayers.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace mars::renderer
{
namespace
{
using Microsoft::WRL::ComPtr;

void ThrowIfFailed(const HRESULT result, const std::string_view operation)
{
    if (SUCCEEDED(result))
    {
        return;
    }

    std::ostringstream message;
    message << operation << " failed with HRESULT 0x" << std::hex
            << static_cast<unsigned long>(result);
    throw std::runtime_error(message.str());
}

void NameObject(ID3D12Object* object, const std::wstring_view name)
{
    if (object == nullptr)
    {
        return;
    }
    const std::wstring owned_name(name);
    ThrowIfFailed(object->SetName(owned_name.c_str()), "ID3D12Object::SetName");
}

std::vector<std::uint8_t> ReadBinaryFile(const std::filesystem::path& path)
{
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    if (!stream)
    {
        throw std::runtime_error("Could not open shader: " + path.string());
    }

    const std::streamsize size = stream.tellg();
    if (size <= 0)
    {
        throw std::runtime_error("Shader is empty: " + path.string());
    }
    stream.seekg(0, std::ios::beg);

    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    if (!stream.read(reinterpret_cast<char*>(bytes.data()), size))
    {
        throw std::runtime_error("Could not read shader: " + path.string());
    }
    return bytes;
}

D3D12_RESOURCE_BARRIER TransitionBarrier(
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

D3D12Renderer::~D3D12Renderer()
{
    try
    {
        Shutdown();
    }
    catch (...)
    {
    }
}

void D3D12Renderer::Initialize(
    const HWND window,
    const std::uint32_t width,
    const std::uint32_t height)
{
    if (initialized_)
    {
        throw std::logic_error("D3D12Renderer is already initialized");
    }
    if (window == nullptr || width == 0 || height == 0)
    {
        throw std::invalid_argument("D3D12Renderer requires a valid window and non-zero size");
    }

    width_ = width;
    height_ = height;

    EnableDebugLayer();
    CreateFactoryAndDevice();
    CreateCommandObjects();
    CreateSwapChain(window);
    CreateRenderTargetViews();
    CreatePipeline();
    CreateGeometry();
    UpdateViewportAndScissor();

    initialized_ = true;
}

void D3D12Renderer::Render()
{
    if (!initialized_ || width_ == 0 || height_ == 0)
    {
        return;
    }

    ThrowIfFailed(
        command_allocators_[frame_index_]->Reset(),
        "ID3D12CommandAllocator::Reset");
    ThrowIfFailed(
        command_list_->Reset(command_allocators_[frame_index_].Get(), pipeline_state_.Get()),
        "ID3D12GraphicsCommandList::Reset");

    PopulateCommandList();
    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close");

    ID3D12CommandList* command_lists[] = {command_list_.Get()};
    command_queue_->ExecuteCommandLists(1, command_lists);
    ThrowIfFailed(swap_chain_->Present(1, 0), "IDXGISwapChain::Present");
    ++presented_frames_;
    MoveToNextFrame();
}

void D3D12Renderer::Resize(const std::uint32_t width, const std::uint32_t height)
{
    if (!initialized_ || width == 0 || height == 0 || (width == width_ && height == height_))
    {
        return;
    }

    WaitForGpu();
    ReleaseRenderTargets();

    DXGI_SWAP_CHAIN_DESC description{};
    ThrowIfFailed(swap_chain_->GetDesc(&description), "IDXGISwapChain::GetDesc");
    ThrowIfFailed(
        swap_chain_->ResizeBuffers(
            kFrameCount,
            width,
            height,
            description.BufferDesc.Format,
            description.Flags),
        "IDXGISwapChain::ResizeBuffers");

    width_ = width;
    height_ = height;
    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    const std::uint64_t next_fence_value = fence_->GetCompletedValue() + 1;
    fence_values_.fill(next_fence_value);
    CreateRenderTargetViews();
    UpdateViewportAndScissor();
}

void D3D12Renderer::Shutdown()
{
    if (!initialized_)
    {
        return;
    }

    WaitForGpu();
    initialized_ = false;

    if (fence_event_ != nullptr)
    {
        CloseHandle(fence_event_);
        fence_event_ = nullptr;
    }

    index_buffer_.Reset();
    vertex_buffer_.Reset();
    pipeline_state_.Reset();
    root_signature_.Reset();
    command_list_.Reset();
    for (auto& allocator : command_allocators_)
    {
        allocator.Reset();
    }
    ReleaseRenderTargets();
    rtv_heap_.Reset();
    swap_chain_.Reset();
    command_queue_.Reset();
    fence_.Reset();
    device_.Reset();
    factory_.Reset();
}

bool D3D12Renderer::IsInitialized() const noexcept
{
    return initialized_;
}

std::uint64_t D3D12Renderer::PresentedFrameCount() const noexcept
{
    return presented_frames_;
}

void D3D12Renderer::EnableDebugLayer()
{
#if defined(_DEBUG)
    ComPtr<ID3D12Debug> debug_controller;
    if (SUCCEEDED(D3D12GetDebugInterface(IID_PPV_ARGS(&debug_controller))))
    {
        debug_controller->EnableDebugLayer();
    }
#endif
}

void D3D12Renderer::CreateFactoryAndDevice()
{
    UINT factory_flags = 0;
#if defined(_DEBUG)
    factory_flags |= DXGI_CREATE_FACTORY_DEBUG;
#endif
    ThrowIfFailed(
        CreateDXGIFactory2(factory_flags, IID_PPV_ARGS(&factory_)),
        "CreateDXGIFactory2");

    const ComPtr<IDXGIAdapter1> adapter = ChooseAdapter(*factory_.Get());
    ThrowIfFailed(
        D3D12CreateDevice(
            adapter.Get(),
            D3D_FEATURE_LEVEL_12_0,
            IID_PPV_ARGS(&device_)),
        "D3D12CreateDevice");
    NameObject(device_.Get(), L"MARSTHEGAME D3D12 Device");

#if defined(_DEBUG)
    ComPtr<ID3D12InfoQueue> info_queue;
    if (SUCCEEDED(device_.As(&info_queue)))
    {
        info_queue->SetBreakOnSeverity(D3D12_MESSAGE_SEVERITY_CORRUPTION, TRUE);
        info_queue->SetBreakOnSeverity(D3D12_MESSAGE_SEVERITY_ERROR, TRUE);
    }
#endif
}

void D3D12Renderer::CreateCommandObjects()
{
    D3D12_COMMAND_QUEUE_DESC queue_description{};
    queue_description.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
    queue_description.Priority = D3D12_COMMAND_QUEUE_PRIORITY_NORMAL;
    queue_description.Flags = D3D12_COMMAND_QUEUE_FLAG_NONE;
    queue_description.NodeMask = 0;
    ThrowIfFailed(
        device_->CreateCommandQueue(&queue_description, IID_PPV_ARGS(&command_queue_)),
        "ID3D12Device::CreateCommandQueue");
    NameObject(command_queue_.Get(), L"MARSTHEGAME Direct Command Queue");

    for (std::uint32_t index = 0; index < kFrameCount; ++index)
    {
        ThrowIfFailed(
            device_->CreateCommandAllocator(
                D3D12_COMMAND_LIST_TYPE_DIRECT,
                IID_PPV_ARGS(&command_allocators_[index])),
            "ID3D12Device::CreateCommandAllocator");
        NameObject(
            command_allocators_[index].Get(),
            L"MARSTHEGAME Frame Command Allocator");
    }

    ThrowIfFailed(
        device_->CreateCommandList(
            0,
            D3D12_COMMAND_LIST_TYPE_DIRECT,
            command_allocators_[0].Get(),
            nullptr,
            IID_PPV_ARGS(&command_list_)),
        "ID3D12Device::CreateCommandList");
    NameObject(command_list_.Get(), L"MARSTHEGAME Graphics Command List");
    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close");

    ThrowIfFailed(
        device_->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence_)),
        "ID3D12Device::CreateFence");
    NameObject(fence_.Get(), L"MARSTHEGAME Frame Fence");

    fence_event_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    if (fence_event_ == nullptr)
    {
        throw std::runtime_error("CreateEventW failed for the D3D12 fence");
    }
}

void D3D12Renderer::CreateSwapChain(const HWND window)
{
    DXGI_SWAP_CHAIN_DESC1 description{};
    description.Width = width_;
    description.Height = height_;
    description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    description.Stereo = FALSE;
    description.SampleDesc.Count = 1;
    description.SampleDesc.Quality = 0;
    description.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    description.BufferCount = kFrameCount;
    description.Scaling = DXGI_SCALING_STRETCH;
    description.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
    description.AlphaMode = DXGI_ALPHA_MODE_UNSPECIFIED;
    description.Flags = 0;

    ComPtr<IDXGISwapChain1> swap_chain;
    ThrowIfFailed(
        factory_->CreateSwapChainForHwnd(
            command_queue_.Get(),
            window,
            &description,
            nullptr,
            nullptr,
            &swap_chain),
        "IDXGIFactory::CreateSwapChainForHwnd");
    ThrowIfFailed(
        factory_->MakeWindowAssociation(window, DXGI_MWA_NO_ALT_ENTER),
        "IDXGIFactory::MakeWindowAssociation");
    ThrowIfFailed(swap_chain.As(&swap_chain_), "IDXGISwapChain::QueryInterface");

    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    fence_values_.fill(0);
    fence_values_[frame_index_] = 1;
}

void D3D12Renderer::CreateRenderTargetViews()
{
    if (rtv_heap_ == nullptr)
    {
        D3D12_DESCRIPTOR_HEAP_DESC heap_description{};
        heap_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
        heap_description.NumDescriptors = kFrameCount;
        heap_description.Flags = D3D12_DESCRIPTOR_HEAP_FLAG_NONE;
        heap_description.NodeMask = 0;
        ThrowIfFailed(
            device_->CreateDescriptorHeap(&heap_description, IID_PPV_ARGS(&rtv_heap_)),
            "ID3D12Device::CreateDescriptorHeap(RTV)");
        NameObject(rtv_heap_.Get(), L"MARSTHEGAME RTV Heap");
        rtv_descriptor_size_ =
            device_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
    }

    D3D12_CPU_DESCRIPTOR_HANDLE handle = rtv_heap_->GetCPUDescriptorHandleForHeapStart();
    for (std::uint32_t index = 0; index < kFrameCount; ++index)
    {
        ThrowIfFailed(
            swap_chain_->GetBuffer(index, IID_PPV_ARGS(&render_targets_[index])),
            "IDXGISwapChain::GetBuffer");
        device_->CreateRenderTargetView(render_targets_[index].Get(), nullptr, handle);
        NameObject(render_targets_[index].Get(), L"MARSTHEGAME Back Buffer");
        handle.ptr += rtv_descriptor_size_;
    }
}

void D3D12Renderer::CreatePipeline()
{
    const std::filesystem::path shader_directory = ExecutableDirectory() / L"shaders";
    const std::vector<std::uint8_t> vertex_shader =
        ReadBinaryFile(shader_directory / L"triangle.vs.dxil");
    const std::vector<std::uint8_t> pixel_shader =
        ReadBinaryFile(shader_directory / L"triangle.ps.dxil");

    D3D12_ROOT_SIGNATURE_DESC root_description{};
    root_description.NumParameters = 0;
    root_description.pParameters = nullptr;
    root_description.NumStaticSamplers = 0;
    root_description.pStaticSamplers = nullptr;
    root_description.Flags = D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT;

    ComPtr<ID3DBlob> serialized_root_signature;
    ComPtr<ID3DBlob> root_error;
    const HRESULT serialization_result = D3D12SerializeRootSignature(
        &root_description,
        D3D_ROOT_SIGNATURE_VERSION_1,
        &serialized_root_signature,
        &root_error);
    if (FAILED(serialization_result))
    {
        const char* error_text = root_error != nullptr
            ? static_cast<const char*>(root_error->GetBufferPointer())
            : "unknown root-signature error";
        throw std::runtime_error(std::string("Root signature serialization failed: ") + error_text);
    }
    ThrowIfFailed(
        device_->CreateRootSignature(
            0,
            serialized_root_signature->GetBufferPointer(),
            serialized_root_signature->GetBufferSize(),
            IID_PPV_ARGS(&root_signature_)),
        "ID3D12Device::CreateRootSignature");
    NameObject(root_signature_.Get(), L"MARSTHEGAME Root Signature");

    const std::array<D3D12_INPUT_ELEMENT_DESC, 2> input_layout = {{
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"COLOR", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    }};

    D3D12_RASTERIZER_DESC rasterizer{};
    rasterizer.FillMode = D3D12_FILL_MODE_SOLID;
    rasterizer.CullMode = D3D12_CULL_MODE_BACK;
    rasterizer.FrontCounterClockwise = FALSE;
    rasterizer.DepthBias = D3D12_DEFAULT_DEPTH_BIAS;
    rasterizer.DepthBiasClamp = D3D12_DEFAULT_DEPTH_BIAS_CLAMP;
    rasterizer.SlopeScaledDepthBias = D3D12_DEFAULT_SLOPE_SCALED_DEPTH_BIAS;
    rasterizer.DepthClipEnable = TRUE;
    rasterizer.MultisampleEnable = FALSE;
    rasterizer.AntialiasedLineEnable = FALSE;
    rasterizer.ForcedSampleCount = 0;
    rasterizer.ConservativeRaster = D3D12_CONSERVATIVE_RASTERIZATION_MODE_OFF;

    D3D12_BLEND_DESC blend{};
    blend.AlphaToCoverageEnable = FALSE;
    blend.IndependentBlendEnable = FALSE;
    D3D12_RENDER_TARGET_BLEND_DESC& target_blend = blend.RenderTarget[0];
    target_blend.BlendEnable = FALSE;
    target_blend.LogicOpEnable = FALSE;
    target_blend.SrcBlend = D3D12_BLEND_ONE;
    target_blend.DestBlend = D3D12_BLEND_ZERO;
    target_blend.BlendOp = D3D12_BLEND_OP_ADD;
    target_blend.SrcBlendAlpha = D3D12_BLEND_ONE;
    target_blend.DestBlendAlpha = D3D12_BLEND_ZERO;
    target_blend.BlendOpAlpha = D3D12_BLEND_OP_ADD;
    target_blend.LogicOp = D3D12_LOGIC_OP_NOOP;
    target_blend.RenderTargetWriteMask = D3D12_COLOR_WRITE_ENABLE_ALL;

    D3D12_DEPTH_STENCIL_DESC depth_stencil{};
    depth_stencil.DepthEnable = FALSE;
    depth_stencil.DepthWriteMask = D3D12_DEPTH_WRITE_MASK_ZERO;
    depth_stencil.DepthFunc = D3D12_COMPARISON_FUNC_ALWAYS;
    depth_stencil.StencilEnable = FALSE;

    D3D12_GRAPHICS_PIPELINE_STATE_DESC pipeline_description{};
    pipeline_description.pRootSignature = root_signature_.Get();
    pipeline_description.VS = {vertex_shader.data(), vertex_shader.size()};
    pipeline_description.PS = {pixel_shader.data(), pixel_shader.size()};
    pipeline_description.BlendState = blend;
    pipeline_description.SampleMask = std::numeric_limits<UINT>::max();
    pipeline_description.RasterizerState = rasterizer;
    pipeline_description.DepthStencilState = depth_stencil;
    pipeline_description.InputLayout = {input_layout.data(), static_cast<UINT>(input_layout.size())};
    pipeline_description.IBStripCutValue = D3D12_INDEX_BUFFER_STRIP_CUT_VALUE_DISABLED;
    pipeline_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    pipeline_description.NumRenderTargets = 1;
    pipeline_description.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
    pipeline_description.DSVFormat = DXGI_FORMAT_UNKNOWN;
    pipeline_description.SampleDesc.Count = 1;
    pipeline_description.SampleDesc.Quality = 0;
    pipeline_description.NodeMask = 0;
    pipeline_description.CachedPSO = {};
    pipeline_description.Flags = D3D12_PIPELINE_STATE_FLAG_NONE;

    ThrowIfFailed(
        device_->CreateGraphicsPipelineState(
            &pipeline_description,
            IID_PPV_ARGS(&pipeline_state_)),
        "ID3D12Device::CreateGraphicsPipelineState");
    NameObject(pipeline_state_.Get(), L"MARSTHEGAME Triangle Pipeline");
}

void D3D12Renderer::CreateGeometry()
{
    constexpr std::array<Vertex, 3> vertices = {{
        {{0.0f, 0.65f, 0.0f}, {0.92f, 0.31f, 0.16f}},
        {{0.62f, -0.55f, 0.0f}, {0.95f, 0.74f, 0.20f}},
        {{-0.62f, -0.55f, 0.0f}, {0.20f, 0.48f, 0.95f}},
    }};
    constexpr std::array<std::uint16_t, 3> indices = {0, 1, 2};

    const auto create_upload_buffer = [this](
                                          const void* source,
                                          const std::size_t size,
                                          ComPtr<ID3D12Resource>& resource,
                                          const std::wstring_view name) {
        D3D12_HEAP_PROPERTIES heap{};
        heap.Type = D3D12_HEAP_TYPE_UPLOAD;
        heap.CPUPageProperty = D3D12_CPU_PAGE_PROPERTY_UNKNOWN;
        heap.MemoryPoolPreference = D3D12_MEMORY_POOL_UNKNOWN;
        heap.CreationNodeMask = 1;
        heap.VisibleNodeMask = 1;

        D3D12_RESOURCE_DESC description{};
        description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
        description.Alignment = 0;
        description.Width = size;
        description.Height = 1;
        description.DepthOrArraySize = 1;
        description.MipLevels = 1;
        description.Format = DXGI_FORMAT_UNKNOWN;
        description.SampleDesc.Count = 1;
        description.SampleDesc.Quality = 0;
        description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
        description.Flags = D3D12_RESOURCE_FLAG_NONE;

        ThrowIfFailed(
            device_->CreateCommittedResource(
                &heap,
                D3D12_HEAP_FLAG_NONE,
                &description,
                D3D12_RESOURCE_STATE_GENERIC_READ,
                nullptr,
                IID_PPV_ARGS(&resource)),
            "ID3D12Device::CreateCommittedResource(upload)");
        NameObject(resource.Get(), name);

        void* mapped = nullptr;
        const D3D12_RANGE read_range{0, 0};
        ThrowIfFailed(resource->Map(0, &read_range, &mapped), "ID3D12Resource::Map");
        std::memcpy(mapped, source, size);
        resource->Unmap(0, nullptr);
    };

    create_upload_buffer(
        vertices.data(),
        sizeof(vertices),
        vertex_buffer_,
        L"MARSTHEGAME Triangle Vertex Buffer");
    vertex_buffer_view_.BufferLocation = vertex_buffer_->GetGPUVirtualAddress();
    vertex_buffer_view_.StrideInBytes = sizeof(Vertex);
    vertex_buffer_view_.SizeInBytes = sizeof(vertices);

    create_upload_buffer(
        indices.data(),
        sizeof(indices),
        index_buffer_,
        L"MARSTHEGAME Triangle Index Buffer");
    index_buffer_view_.BufferLocation = index_buffer_->GetGPUVirtualAddress();
    index_buffer_view_.SizeInBytes = sizeof(indices);
    index_buffer_view_.Format = DXGI_FORMAT_R16_UINT;
}

void D3D12Renderer::PopulateCommandList()
{
    const D3D12_RESOURCE_BARRIER to_render_target = TransitionBarrier(
        render_targets_[frame_index_].Get(),
        D3D12_RESOURCE_STATE_PRESENT,
        D3D12_RESOURCE_STATE_RENDER_TARGET);
    command_list_->ResourceBarrier(1, &to_render_target);

    D3D12_CPU_DESCRIPTOR_HANDLE target = rtv_heap_->GetCPUDescriptorHandleForHeapStart();
    target.ptr += static_cast<SIZE_T>(frame_index_) * rtv_descriptor_size_;

    constexpr float clear_color[4] = {0.018f, 0.022f, 0.035f, 1.0f};
    command_list_->RSSetViewports(1, &viewport_);
    command_list_->RSSetScissorRects(1, &scissor_rect_);
    command_list_->OMSetRenderTargets(1, &target, FALSE, nullptr);
    command_list_->ClearRenderTargetView(target, clear_color, 0, nullptr);
    command_list_->SetGraphicsRootSignature(root_signature_.Get());
    command_list_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    command_list_->IASetVertexBuffers(0, 1, &vertex_buffer_view_);
    command_list_->IASetIndexBuffer(&index_buffer_view_);
    command_list_->DrawIndexedInstanced(3, 1, 0, 0, 0);

    const D3D12_RESOURCE_BARRIER to_present = TransitionBarrier(
        render_targets_[frame_index_].Get(),
        D3D12_RESOURCE_STATE_RENDER_TARGET,
        D3D12_RESOURCE_STATE_PRESENT);
    command_list_->ResourceBarrier(1, &to_present);
}

void D3D12Renderer::MoveToNextFrame()
{
    const std::uint64_t signal_value = fence_values_[frame_index_];
    ThrowIfFailed(
        command_queue_->Signal(fence_.Get(), signal_value),
        "ID3D12CommandQueue::Signal");

    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    if (fence_->GetCompletedValue() < fence_values_[frame_index_])
    {
        ThrowIfFailed(
            fence_->SetEventOnCompletion(fence_values_[frame_index_], fence_event_),
            "ID3D12Fence::SetEventOnCompletion");
        WaitForSingleObject(fence_event_, INFINITE);
    }
    fence_values_[frame_index_] = signal_value + 1;
}

void D3D12Renderer::WaitForGpu()
{
    if (command_queue_ == nullptr || fence_ == nullptr || fence_event_ == nullptr)
    {
        return;
    }

    const std::uint64_t signal_value = fence_values_[frame_index_];
    ThrowIfFailed(
        command_queue_->Signal(fence_.Get(), signal_value),
        "ID3D12CommandQueue::Signal(wait)");
    ThrowIfFailed(
        fence_->SetEventOnCompletion(signal_value, fence_event_),
        "ID3D12Fence::SetEventOnCompletion(wait)");
    WaitForSingleObject(fence_event_, INFINITE);
    fence_values_[frame_index_] = signal_value + 1;
}

void D3D12Renderer::ReleaseRenderTargets()
{
    for (auto& target : render_targets_)
    {
        target.Reset();
    }
}

void D3D12Renderer::UpdateViewportAndScissor()
{
    viewport_.TopLeftX = 0.0f;
    viewport_.TopLeftY = 0.0f;
    viewport_.Width = static_cast<float>(width_);
    viewport_.Height = static_cast<float>(height_);
    viewport_.MinDepth = 0.0f;
    viewport_.MaxDepth = 1.0f;

    scissor_rect_.left = 0;
    scissor_rect_.top = 0;
    scissor_rect_.right = static_cast<LONG>(width_);
    scissor_rect_.bottom = static_cast<LONG>(height_);
}

std::filesystem::path D3D12Renderer::ExecutableDirectory() const
{
    std::array<wchar_t, 32'768> path{};
    const DWORD length = GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
    if (length == 0 || length >= path.size())
    {
        throw std::runtime_error("GetModuleFileNameW failed");
    }
    return std::filesystem::path(std::wstring_view(path.data(), length)).parent_path();
}

ComPtr<IDXGIAdapter1> D3D12Renderer::ChooseAdapter(IDXGIFactory6& factory)
{
    for (UINT index = 0;; ++index)
    {
        ComPtr<IDXGIAdapter1> adapter;
        const HRESULT result = factory.EnumAdapterByGpuPreference(
            index,
            DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE,
            IID_PPV_ARGS(&adapter));
        if (result == DXGI_ERROR_NOT_FOUND)
        {
            break;
        }
        ThrowIfFailed(result, "IDXGIFactory6::EnumAdapterByGpuPreference");

        DXGI_ADAPTER_DESC1 description{};
        ThrowIfFailed(adapter->GetDesc1(&description), "IDXGIAdapter1::GetDesc1");
        if ((description.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) != 0)
        {
            continue;
        }
        if (SUCCEEDED(D3D12CreateDevice(
                adapter.Get(),
                D3D_FEATURE_LEVEL_12_0,
                __uuidof(ID3D12Device),
                nullptr)))
        {
            return adapter;
        }
    }
    throw std::runtime_error("No Direct3D 12 feature-level 12_0 hardware adapter was found");
}
} // namespace mars::renderer
