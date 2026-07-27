#include "renderer/d3d12_renderer.h"

#include <d3d12sdklayers.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#ifndef MARS_ENABLE_D3D12_VALIDATION
#define MARS_ENABLE_D3D12_VALIDATION 0
#endif

namespace mars::renderer
{
namespace
{
using Microsoft::WRL::ComPtr;

std::string FormatHresult(const HRESULT result)
{
    std::ostringstream value;
    value << "0x" << std::hex << static_cast<unsigned long>(result);
    return value.str();
}

void ThrowIfFailed(const HRESULT result, const std::string_view operation)
{
    if (SUCCEEDED(result))
    {
        return;
    }
    throw std::runtime_error(std::string(operation) + " failed with HRESULT " + FormatHresult(result));
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

    const std::streampos end = stream.tellg();
    if (end <= 0)
    {
        throw std::runtime_error("Shader is empty: " + path.string());
    }
    const auto size = static_cast<std::size_t>(end);
    stream.seekg(0, std::ios::beg);

    std::vector<std::uint8_t> bytes(size);
    if (!stream.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(size)))
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
    const std::uint32_t height,
    const AdapterPreference adapter_preference)
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
    presented_frames_ = 0;
    last_cpu_frame_ms_ = 0.0;
    max_cpu_frame_ms_ = 0.0;
    initialized_ = true;

    try
    {
        EnableDebugLayer();
        CreateFactoryAndDevice(adapter_preference);
        CreateCommandObjects();
        CreateSwapChain(window);
        CreateRenderTargetViews();
        CreateDepthBuffer();
        CreatePipeline();
        CreateGeometry();
        CreateSceneConstants();
        UpdateViewportAndScissor();
    }
    catch (...)
    {
        Shutdown();
        throw;
    }
}

void D3D12Renderer::Render()
{
    if (!initialized_ || width_ == 0 || height_ == 0)
    {
        return;
    }

    const auto started = std::chrono::steady_clock::now();
    ThrowIfFailed(
        command_allocators_[frame_index_]->Reset(),
        "ID3D12CommandAllocator::Reset");
    ThrowIfFailed(
        command_list_->Reset(command_allocators_[frame_index_].Get(), pipeline_state_.Get()),
        "ID3D12GraphicsCommandList::Reset");

    UpdateSceneConstants();
    PopulateCommandList();
    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close");

    ID3D12CommandList* command_lists[] = {command_list_.Get()};
    command_queue_->ExecuteCommandLists(1, command_lists);
    ThrowIfDeviceFailed(swap_chain_->Present(1, 0), "IDXGISwapChain::Present");
    ++presented_frames_;
    MoveToNextFrame();

    const auto elapsed = std::chrono::steady_clock::now() - started;
    last_cpu_frame_ms_ = std::chrono::duration<double, std::milli>(elapsed).count();
    max_cpu_frame_ms_ = (std::max)(max_cpu_frame_ms_, last_cpu_frame_ms_);
}

void D3D12Renderer::Resize(const std::uint32_t width, const std::uint32_t height)
{
    if (!initialized_ || width == 0 || height == 0 || (width == width_ && height == height_))
    {
        return;
    }

    WaitForGpu();
    ReleaseRenderTargets();
    ReleaseDepthBuffer();

    DXGI_SWAP_CHAIN_DESC description{};
    ThrowIfFailed(swap_chain_->GetDesc(&description), "IDXGISwapChain::GetDesc");
    ThrowIfDeviceFailed(
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
    CreateDepthBuffer();
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

    if (scene_constant_buffer_ != nullptr && mapped_scene_constants_ != nullptr)
    {
        scene_constant_buffer_->Unmap(0, nullptr);
        mapped_scene_constants_ = nullptr;
    }

    if (fence_event_ != nullptr)
    {
        CloseHandle(fence_event_);
        fence_event_ = nullptr;
    }

    scene_constant_buffer_.Reset();
    index_buffer_.Reset();
    vertex_buffer_.Reset();
    pipeline_state_.Reset();
    root_signature_.Reset();
    command_list_.Reset();
    for (auto& allocator : command_allocators_)
    {
        allocator.Reset();
    }
    ReleaseDepthBuffer();
    ReleaseRenderTargets();
    dsv_heap_.Reset();
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

FrameStatistics D3D12Renderer::Statistics() const noexcept
{
    return {
        .presented_frames = presented_frames_,
        .last_cpu_frame_ms = last_cpu_frame_ms_,
        .max_cpu_frame_ms = max_cpu_frame_ms_,
    };
}

void D3D12Renderer::EnableDebugLayer()
{
#if MARS_ENABLE_D3D12_VALIDATION
    ComPtr<ID3D12Debug> debug_controller;
    ThrowIfFailed(
        D3D12GetDebugInterface(IID_PPV_ARGS(&debug_controller)),
        "D3D12GetDebugInterface");
    debug_controller->EnableDebugLayer();
#endif
}

void D3D12Renderer::CreateFactoryAndDevice(const AdapterPreference adapter_preference)
{
    UINT factory_flags = 0;
#if MARS_ENABLE_D3D12_VALIDATION
    factory_flags |= DXGI_CREATE_FACTORY_DEBUG;
#endif
    ThrowIfFailed(
        CreateDXGIFactory2(factory_flags, IID_PPV_ARGS(&factory_)),
        "CreateDXGIFactory2");

    const ComPtr<IDXGIAdapter1> adapter = ChooseAdapter(*factory_.Get(), adapter_preference);
    ThrowIfFailed(
        D3D12CreateDevice(
            adapter.Get(),
            D3D_FEATURE_LEVEL_12_0,
            IID_PPV_ARGS(&device_)),
        "D3D12CreateDevice");
    NameObject(device_.Get(), L"MARSTHEGAME D3D12 Device");

#if MARS_ENABLE_D3D12_VALIDATION
    ComPtr<ID3D12InfoQueue> info_queue;
    ThrowIfFailed(device_.As(&info_queue), "ID3D12Device::QueryInterface(ID3D12InfoQueue)");
    ThrowIfFailed(
        info_queue->SetBreakOnSeverity(D3D12_MESSAGE_SEVERITY_CORRUPTION, TRUE),
        "ID3D12InfoQueue::SetBreakOnSeverity(corruption)");
    ThrowIfFailed(
        info_queue->SetBreakOnSeverity(D3D12_MESSAGE_SEVERITY_ERROR, TRUE),
        "ID3D12InfoQueue::SetBreakOnSeverity(error)");
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

void D3D12Renderer::CreateDepthBuffer()
{
    if (dsv_heap_ == nullptr)
    {
        D3D12_DESCRIPTOR_HEAP_DESC heap_description{};
        heap_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_DSV;
        heap_description.NumDescriptors = 1;
        heap_description.Flags = D3D12_DESCRIPTOR_HEAP_FLAG_NONE;
        ThrowIfFailed(
            device_->CreateDescriptorHeap(&heap_description, IID_PPV_ARGS(&dsv_heap_)),
            "ID3D12Device::CreateDescriptorHeap(DSV)");
        NameObject(dsv_heap_.Get(), L"MARSTHEGAME DSV Heap");
        dsv_handle_ = dsv_heap_->GetCPUDescriptorHandleForHeapStart();
    }

    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_DEFAULT;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    description.Width = width_;
    description.Height = height_;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.Format = DXGI_FORMAT_D32_FLOAT;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;
    description.Flags = D3D12_RESOURCE_FLAG_ALLOW_DEPTH_STENCIL;

    D3D12_CLEAR_VALUE clear_value{};
    clear_value.Format = DXGI_FORMAT_D32_FLOAT;
    clear_value.DepthStencil.Depth = 1.0f;
    clear_value.DepthStencil.Stencil = 0;

    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap,
            D3D12_HEAP_FLAG_NONE,
            &description,
            D3D12_RESOURCE_STATE_DEPTH_WRITE,
            &clear_value,
            IID_PPV_ARGS(&depth_buffer_)),
        "ID3D12Device::CreateCommittedResource(depth)");
    NameObject(depth_buffer_.Get(), L"MARSTHEGAME Depth Buffer");

    D3D12_DEPTH_STENCIL_VIEW_DESC view{};
    view.Format = DXGI_FORMAT_D32_FLOAT;
    view.ViewDimension = D3D12_DSV_DIMENSION_TEXTURE2D;
    view.Flags = D3D12_DSV_FLAG_NONE;
    device_->CreateDepthStencilView(depth_buffer_.Get(), &view, dsv_handle_);
}

void D3D12Renderer::CreatePipeline()
{
    const std::filesystem::path shader_directory = ExecutableDirectory() / L"shaders";
    const std::vector<std::uint8_t> vertex_shader =
        ReadBinaryFile(shader_directory / L"triangle.vs.dxil");
    const std::vector<std::uint8_t> pixel_shader =
        ReadBinaryFile(shader_directory / L"triangle.ps.dxil");

    D3D12_ROOT_PARAMETER root_parameter{};
    root_parameter.ParameterType = D3D12_ROOT_PARAMETER_TYPE_CBV;
    root_parameter.Descriptor.ShaderRegister = 0;
    root_parameter.Descriptor.RegisterSpace = 0;
    root_parameter.ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;

    D3D12_ROOT_SIGNATURE_DESC root_description{};
    root_description.NumParameters = 1;
    root_description.pParameters = &root_parameter;
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
        const std::string error_text = root_error != nullptr
            ? std::string(
                  static_cast<const char*>(root_error->GetBufferPointer()),
                  root_error->GetBufferSize())
            : "unknown root-signature error";
        throw std::runtime_error("Root signature serialization failed: " + error_text);
    }
    ThrowIfFailed(
        device_->CreateRootSignature(
            0,
            serialized_root_signature->GetBufferPointer(),
            serialized_root_signature->GetBufferSize(),
            IID_PPV_ARGS(&root_signature_)),
        "ID3D12Device::CreateRootSignature");
    NameObject(root_signature_.Get(), L"MARSTHEGAME Root Signature");

    const std::array<D3D12_INPUT_ELEMENT_DESC, 3> input_layout = {{
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"NORMAL", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"COLOR", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 24,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    }};

    D3D12_RASTERIZER_DESC rasterizer{};
    rasterizer.FillMode = D3D12_FILL_MODE_SOLID;
    rasterizer.CullMode = D3D12_CULL_MODE_NONE;
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
    depth_stencil.DepthEnable = TRUE;
    depth_stencil.DepthWriteMask = D3D12_DEPTH_WRITE_MASK_ALL;
    depth_stencil.DepthFunc = D3D12_COMPARISON_FUNC_LESS;
    depth_stencil.StencilEnable = FALSE;

    D3D12_GRAPHICS_PIPELINE_STATE_DESC pipeline_description{};
    pipeline_description.pRootSignature = root_signature_.Get();
    pipeline_description.VS = {vertex_shader.data(), vertex_shader.size()};
    pipeline_description.PS = {pixel_shader.data(), pixel_shader.size()};
    pipeline_description.BlendState = blend;
    pipeline_description.SampleMask = (std::numeric_limits<UINT>::max)();
    pipeline_description.RasterizerState = rasterizer;
    pipeline_description.DepthStencilState = depth_stencil;
    pipeline_description.InputLayout = {
        input_layout.data(),
        static_cast<UINT>(input_layout.size()),
    };
    pipeline_description.IBStripCutValue = D3D12_INDEX_BUFFER_STRIP_CUT_VALUE_DISABLED;
    pipeline_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    pipeline_description.NumRenderTargets = 1;
    pipeline_description.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
    pipeline_description.DSVFormat = DXGI_FORMAT_D32_FLOAT;
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
    NameObject(pipeline_state_.Get(), L"MARSTHEGAME Lit 3D Pipeline");
}

void D3D12Renderer::CreateGeometry()
{
    constexpr std::array<Vertex, 24> vertices = {{
        {{-1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {0.90f, 0.28f, 0.14f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {0.90f, 0.28f, 0.14f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {0.90f, 0.28f, 0.14f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {0.90f, 0.28f, 0.14f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {0.95f, 0.68f, 0.18f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {0.95f, 0.68f, 0.18f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {0.95f, 0.68f, 0.18f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {0.95f, 0.68f, 0.18f}},
        {{-1.0f, -1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {0.20f, 0.45f, 0.92f}},
        {{-1.0f, 1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {0.20f, 0.45f, 0.92f}},
        {{-1.0f, 1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {0.20f, 0.45f, 0.92f}},
        {{-1.0f, -1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {0.20f, 0.45f, 0.92f}},
        {{1.0f, -1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {0.35f, 0.76f, 0.46f}},
        {{1.0f, 1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {0.35f, 0.76f, 0.46f}},
        {{1.0f, 1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {0.35f, 0.76f, 0.46f}},
        {{1.0f, -1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {0.35f, 0.76f, 0.46f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {0.76f, 0.34f, 0.86f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {0.76f, 0.34f, 0.86f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {0.76f, 0.34f, 0.86f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {0.76f, 0.34f, 0.86f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {0.18f, 0.74f, 0.82f}},
        {{-1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {0.18f, 0.74f, 0.82f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {0.18f, 0.74f, 0.82f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {0.18f, 0.74f, 0.82f}},
    }};
    constexpr std::array<std::uint16_t, 36> indices = {
        0, 1, 2, 0, 2, 3,
        4, 5, 6, 4, 6, 7,
        8, 9, 10, 8, 10, 11,
        12, 13, 14, 12, 14, 15,
        16, 17, 18, 16, 18, 19,
        20, 21, 22, 20, 22, 23,
    };

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
        description.Width = static_cast<UINT64>(size);
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
        L"MARSTHEGAME Cube Vertex Buffer");
    vertex_buffer_view_.BufferLocation = vertex_buffer_->GetGPUVirtualAddress();
    vertex_buffer_view_.StrideInBytes = static_cast<UINT>(sizeof(Vertex));
    vertex_buffer_view_.SizeInBytes = static_cast<UINT>(sizeof(vertices));

    create_upload_buffer(
        indices.data(),
        sizeof(indices),
        index_buffer_,
        L"MARSTHEGAME Cube Index Buffer");
    index_buffer_view_.BufferLocation = index_buffer_->GetGPUVirtualAddress();
    index_buffer_view_.SizeInBytes = static_cast<UINT>(sizeof(indices));
    index_buffer_view_.Format = DXGI_FORMAT_R16_UINT;
    index_count_ = static_cast<std::uint32_t>(indices.size());
}

void D3D12Renderer::CreateSceneConstants()
{
    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_UPLOAD;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    description.Width = sizeof(SceneConstants) * kFrameCount;
    description.Height = 1;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.Format = DXGI_FORMAT_UNKNOWN;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;

    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap,
            D3D12_HEAP_FLAG_NONE,
            &description,
            D3D12_RESOURCE_STATE_GENERIC_READ,
            nullptr,
            IID_PPV_ARGS(&scene_constant_buffer_)),
        "ID3D12Device::CreateCommittedResource(scene constants)");
    NameObject(scene_constant_buffer_.Get(), L"MARSTHEGAME Scene Constant Buffer");

    const D3D12_RANGE read_range{0, 0};
    void* mapped = nullptr;
    ThrowIfFailed(
        scene_constant_buffer_->Map(0, &read_range, &mapped),
        "ID3D12Resource::Map(scene constants)");
    mapped_scene_constants_ = static_cast<std::byte*>(mapped);
}

void D3D12Renderer::UpdateSceneConstants()
{
    using namespace DirectX;

    const float angle = static_cast<float>(presented_frames_) * 0.0125f;
    const float aspect = static_cast<float>(width_) / static_cast<float>(height_);
    const XMMATRIX world = XMMatrixRotationY(angle) * XMMatrixRotationX(angle * 0.47f);
    const XMMATRIX view = XMMatrixLookAtLH(
        XMVectorSet(0.0f, 1.3f, -5.2f, 1.0f),
        XMVectorZero(),
        XMVectorSet(0.0f, 1.0f, 0.0f, 0.0f));
    const XMMATRIX projection = XMMatrixPerspectiveFovLH(
        XMConvertToRadians(58.0f),
        aspect,
        0.1f,
        100.0f);

    SceneConstants constants{};
    XMStoreFloat4x4(&constants.world, world);
    XMStoreFloat4x4(&constants.world_view_projection, world * view * projection);
    constants.light_direction = {-0.35f, -0.78f, -0.52f, 0.0f};

    std::byte* destination =
        mapped_scene_constants_ + static_cast<std::size_t>(frame_index_) * sizeof(SceneConstants);
    std::memcpy(destination, &constants, sizeof(constants));
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
    command_list_->OMSetRenderTargets(1, &target, FALSE, &dsv_handle_);
    command_list_->ClearRenderTargetView(target, clear_color, 0, nullptr);
    command_list_->ClearDepthStencilView(
        dsv_handle_,
        D3D12_CLEAR_FLAG_DEPTH,
        1.0f,
        0,
        0,
        nullptr);
    command_list_->SetGraphicsRootSignature(root_signature_.Get());
    command_list_->SetGraphicsRootConstantBufferView(
        0,
        scene_constant_buffer_->GetGPUVirtualAddress()
            + static_cast<UINT64>(frame_index_) * sizeof(SceneConstants));
    command_list_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    command_list_->IASetVertexBuffers(0, 1, &vertex_buffer_view_);
    command_list_->IASetIndexBuffer(&index_buffer_view_);
    command_list_->DrawIndexedInstanced(index_count_, 1, 0, 0, 0);

    const D3D12_RESOURCE_BARRIER to_present = TransitionBarrier(
        render_targets_[frame_index_].Get(),
        D3D12_RESOURCE_STATE_RENDER_TARGET,
        D3D12_RESOURCE_STATE_PRESENT);
    command_list_->ResourceBarrier(1, &to_present);
}

void D3D12Renderer::MoveToNextFrame()
{
    const std::uint64_t signal_value = fence_values_[frame_index_];
    ThrowIfDeviceFailed(
        command_queue_->Signal(fence_.Get(), signal_value),
        "ID3D12CommandQueue::Signal");

    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    if (fence_->GetCompletedValue() < fence_values_[frame_index_])
    {
        ThrowIfDeviceFailed(
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
    ThrowIfDeviceFailed(
        command_queue_->Signal(fence_.Get(), signal_value),
        "ID3D12CommandQueue::Signal(wait)");
    ThrowIfDeviceFailed(
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

void D3D12Renderer::ReleaseDepthBuffer()
{
    depth_buffer_.Reset();
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

void D3D12Renderer::ThrowIfDeviceFailed(
    const HRESULT result,
    const std::string_view operation) const
{
    if (SUCCEEDED(result))
    {
        return;
    }

    std::string message =
        std::string(operation) + " failed with HRESULT " + FormatHresult(result);
    if (device_ != nullptr
        && (result == DXGI_ERROR_DEVICE_HUNG || result == DXGI_ERROR_DEVICE_REMOVED
            || result == DXGI_ERROR_DEVICE_RESET))
    {
        message += "; device removal reason " + FormatHresult(device_->GetDeviceRemovedReason());
    }
    throw std::runtime_error(message);
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

ComPtr<IDXGIAdapter1> D3D12Renderer::ChooseAdapter(
    IDXGIFactory6& factory,
    const AdapterPreference adapter_preference)
{
    if (adapter_preference == AdapterPreference::Warp)
    {
        ComPtr<IDXGIAdapter1> warp_adapter;
        ThrowIfFailed(
            factory.EnumWarpAdapter(IID_PPV_ARGS(&warp_adapter)),
            "IDXGIFactory::EnumWarpAdapter");
        return warp_adapter;
    }

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
