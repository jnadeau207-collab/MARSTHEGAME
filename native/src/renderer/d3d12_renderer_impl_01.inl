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
    const AdapterPreference adapter_preference,
    const bool enable_frame_capture)
{
    if (initialized_)
    {
        throw std::logic_error("D3D12Renderer is already initialized");
    }
    if (window == nullptr || width == 0 || height == 0)
    {
        throw std::invalid_argument("D3D12Renderer requires a valid window and non-zero size");
    }

    visual_configuration_ = DefaultVisualSliceConfiguration();
    if (!ValidateVisualSliceConfiguration(visual_configuration_))
    {
        throw std::runtime_error("Default Phase 5 visual configuration failed validation");
    }
    width_ = width;
    height_ = height;
    frame_capture_enabled_ = enable_frame_capture;
    current_exposure_ = 1.0f;
    history_read_index_ = 0;
    active_history_write_index_ = 1;
    initialized_ = true;

    try
    {
        EnableDebugLayer();
        CreateFactoryAndDevice(adapter_preference);
        CreateCommandObjects();
        CreateSwapChain(window);
        CreateDescriptorHeaps();
        CreateRenderTargetViews();
        CreateVisualTargets();
        CreateShadowMap();
        if (frame_capture_enabled_)
        {
            CreateCaptureBuffer();
        }
        CreatePipelines();
        CreateStaticResources();
        CreateConstantBuffers();
        CreateTimingResources();
        WriteShaderResourceViews();
        UpdateViewportAndScissor();
        UpdateResidentMemoryEstimate();
    }
    catch (...)
    {
        Shutdown();
        throw;
    }
}

void D3D12Renderer::Render(const RenderScene& scene)
{
    if (!initialized_ || width_ == 0 || height_ == 0)
    {
        return;
    }
    if (scene.instances.empty())
    {
        throw std::invalid_argument("RenderScene must contain at least one authored instance");
    }
    if (static_cast<std::size_t>(scene.supplemental_character_count) > scene.supplemental_character_instances.size())
    {
        throw std::invalid_argument("RenderScene supplemental character count exceeds its fixed storage");
    }
    const std::size_t total_instances = scene.instances.size() + scene.supplemental_character_count;
    if (total_instances > kMaxInstances)
    {
        throw std::invalid_argument("RenderScene exceeds the Phase 5 native instance limit");
    }

    CollectGpuTiming(frame_index_);
    const auto started = std::chrono::steady_clock::now();
    const std::uint32_t recording_frame = frame_index_;
    const bool capture_this_frame = capture_requested_;

    ThrowIfFailed(command_allocators_[recording_frame]->Reset(), "ID3D12CommandAllocator::Reset");
    ThrowIfFailed(
        command_list_->Reset(command_allocators_[recording_frame].Get(), nullptr),
        "ID3D12GraphicsCommandList::Reset");

    UpdateConstants(scene);
    PopulateCommandList();
    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close");

    ID3D12CommandList* command_lists[] = {command_list_.Get()};
    command_queue_->ExecuteCommandLists(1, command_lists);
    ThrowIfDeviceFailed(swap_chain_->Present(1, 0), "IDXGISwapChain::Present");
    timestamp_valid_[recording_frame] = true;
    history_read_index_ = active_history_write_index_;
    history_valid_ = true;
    ++frame_statistics_.presented_frames;
    MoveToNextFrame();

    if (capture_this_frame)
    {
        capture_requested_ = false;
        capture_submitted_ = true;
    }

    const auto elapsed = std::chrono::steady_clock::now() - started;
    frame_statistics_.last_cpu_frame_ms = std::chrono::duration<double, std::milli>(elapsed).count();
    frame_statistics_.max_cpu_frame_ms =
        (std::max)(frame_statistics_.max_cpu_frame_ms, frame_statistics_.last_cpu_frame_ms);
    if (frame_statistics_.last_cpu_frame_ms > 33.333)
    {
        ++frame_statistics_.hitch_count;
    }
}

void D3D12Renderer::Resize(const std::uint32_t width, const std::uint32_t height)
{
    if (!initialized_ || width == 0 || height == 0 || (width == width_ && height == height_))
    {
        return;
    }
    if (capture_requested_ || capture_submitted_)
    {
        throw std::logic_error("Cannot resize while a frame capture is pending");
    }

    WaitForGpu();
    ReleaseCaptureBuffer();
    ReleaseVisualTargets();
    ReleaseRenderTargets();

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
    const std::uint64_t next_fence_value = fence_->GetCompletedValue() + 1U;
    fence_values_.fill(next_fence_value);
    timestamp_valid_.fill(false);
    history_read_index_ = 0;
    active_history_write_index_ = 1;
    history_valid_ = false;
    previous_camera_valid_ = false;
    CreateRenderTargetViews();
    CreateVisualTargets();
    if (frame_capture_enabled_)
    {
        CreateCaptureBuffer();
    }
    WriteShaderResourceViews();
    UpdateViewportAndScissor();
    UpdateResidentMemoryEstimate();
}

void D3D12Renderer::Shutdown()
{
    if (!initialized_)
    {
        return;
    }

    WaitForGpu();
    upload_context_.Shutdown();
    initialized_ = false;

    if (object_constant_buffer_ != nullptr && mapped_object_constants_ != nullptr)
    {
        object_constant_buffer_->Unmap(0, nullptr);
        mapped_object_constants_ = nullptr;
    }
    if (frame_constant_buffer_ != nullptr && mapped_frame_constants_ != nullptr)
    {
        frame_constant_buffer_->Unmap(0, nullptr);
        mapped_frame_constants_ = nullptr;
    }
    if (fence_event_ != nullptr)
    {
        CloseHandle(fence_event_);
        fence_event_ = nullptr;
    }

    timestamp_readback_.Reset();
    timestamp_query_heap_.Reset();
    frame_constant_buffer_.Reset();
    object_constant_buffer_.Reset();
    surface_texture_.Reset();
    normal_texture_.Reset();
    base_color_texture_.Reset();
    index_buffer_.Reset();
    vertex_buffer_.Reset();
    final_pipeline_.Reset();
    temporal_pipeline_.Reset();
    particle_pipeline_.Reset();
    scene_pipeline_.Reset();
    shadow_pipeline_.Reset();
    root_signature_.Reset();
    command_list_.Reset();
    for (auto& allocator : command_allocators_)
