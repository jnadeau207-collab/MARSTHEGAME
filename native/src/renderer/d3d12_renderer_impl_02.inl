    {
        allocator.Reset();
    }
    ReleaseCaptureBuffer();
    shadow_map_.Reset();
    ReleaseVisualTargets();
    ReleaseRenderTargets();
    srv_heap_.Reset();
    dsv_heap_.Reset();
    rtv_heap_.Reset();
    swap_chain_.Reset();
    fence_.Reset();
    command_queue_.Reset();
    device_.Reset();
    factory_.Reset();
    frame_capture_enabled_ = false;
    capture_requested_ = false;
    capture_submitted_ = false;
    history_valid_ = false;
    previous_camera_valid_ = false;
    instance_count_ = 0;
    upload_statistics_ = {};
    frame_statistics_ = {};
}

void D3D12Renderer::RequestFrameCapture()
{
    if (!initialized_)
    {
        throw std::logic_error("Cannot capture a frame before renderer initialization");
    }
    if (!frame_capture_enabled_ || capture_buffer_ == nullptr)
    {
        throw std::logic_error("Frame capture was not enabled for this renderer");
    }
    if (capture_requested_ || capture_submitted_)
    {
        throw std::logic_error("A frame capture is already pending");
    }
    capture_requested_ = true;
}

FrameCaptureEvidence D3D12Renderer::ConsumeFrameCapture()
{
    if (!initialized_ || !capture_submitted_ || capture_buffer_ == nullptr)
    {
        throw std::logic_error("No completed frame capture is available");
    }

    WaitForGpu();
    const D3D12_RANGE read_range{0, static_cast<SIZE_T>(capture_total_bytes_)};
    void* mapped = nullptr;
    ThrowIfFailed(capture_buffer_->Map(0, &read_range, &mapped), "ID3D12Resource::Map(capture)");

    const auto* bytes = static_cast<const std::uint8_t*>(mapped);
    const std::array<std::uint8_t, 4> background = {bytes[0], bytes[1], bytes[2], bytes[3]};
    const std::size_t row_size = static_cast<std::size_t>(capture_row_size_bytes_);
    const std::size_t row_pitch = capture_footprint_.Footprint.RowPitch;
    std::uint64_t checksum = kFnvOffsetBasis;
    std::uint64_t non_background_pixels = 0;
    std::uint64_t dark_pixels = 0;
    std::uint64_t highlight_pixels = 0;
    double luminance_sum = 0.0;
    double peak_luminance = 0.0;
    double edge_energy = 0.0;

    for (std::uint32_t y = 0; y < capture_row_count_; ++y)
    {
        const std::uint8_t* row = bytes + static_cast<std::size_t>(y) * row_pitch;
        for (std::size_t offset = 0; offset < row_size; ++offset)
        {
            checksum ^= row[offset];
            checksum *= kFnvPrime;
        }
        double previous_luminance = 0.0;
        for (std::size_t offset = 0; offset + 3U < row_size; offset += 4U)
        {
            const double red = static_cast<double>(row[offset]) / 255.0;
            const double green = static_cast<double>(row[offset + 1U]) / 255.0;
            const double blue = static_cast<double>(row[offset + 2U]) / 255.0;
            const double luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722;
            luminance_sum += luminance;
            peak_luminance = (std::max)(peak_luminance, luminance);
            if (luminance < 0.075)
            {
                ++dark_pixels;
            }
            if (luminance > 0.82)
            {
                ++highlight_pixels;
            }
            if (offset != 0)
            {
                edge_energy += std::abs(luminance - previous_luminance);
            }
            previous_luminance = luminance;
            const int background_difference =
                std::abs(static_cast<int>(row[offset]) - static_cast<int>(background[0]))
                + std::abs(static_cast<int>(row[offset + 1U]) - static_cast<int>(background[1]))
                + std::abs(static_cast<int>(row[offset + 2U]) - static_cast<int>(background[2]));
            if (background_difference > 7)
            {
                ++non_background_pixels;
            }
        }
    }

    WriteCaptureBitmap(
        ExecutableDirectory() / L"phase5_visual_slice.bmp",
        bytes,
        row_pitch,
        width_,
        height_);

    const D3D12_RANGE written_range{0, 0};
    capture_buffer_->Unmap(0, &written_range);
    capture_submitted_ = false;
    const double pixel_count = static_cast<double>(width_) * static_cast<double>(height_);
    return {
        .checksum = checksum,
        .non_background_pixels = non_background_pixels,
        .dark_pixels = dark_pixels,
        .highlight_pixels = highlight_pixels,
        .average_luminance = pixel_count > 0.0 ? luminance_sum / pixel_count : 0.0,
        .peak_luminance = peak_luminance,
        .edge_energy = pixel_count > 0.0 ? edge_energy / pixel_count : 0.0,
        .width = width_,
        .height = height_,
    };
}

bool D3D12Renderer::IsInitialized() const noexcept
{
    return initialized_;
}

std::uint64_t D3D12Renderer::PresentedFrameCount() const noexcept
{
    return frame_statistics_.presented_frames;
}

FrameStatistics D3D12Renderer::Statistics() const noexcept
{
    return frame_statistics_;
}

GpuUploadStatistics D3D12Renderer::UploadStatistics() const noexcept
{
    return upload_statistics_;
}

VisualSliceConfiguration D3D12Renderer::VisualConfiguration() const noexcept
{
    return visual_configuration_;
}

void D3D12Renderer::EnableDebugLayer()
{
#if MARS_ENABLE_D3D12_VALIDATION
    ComPtr<ID3D12Debug> debug_controller;
    ThrowIfFailed(D3D12GetDebugInterface(IID_PPV_ARGS(&debug_controller)), "D3D12GetDebugInterface");
    debug_controller->EnableDebugLayer();
#endif
}

void D3D12Renderer::CreateFactoryAndDevice(const AdapterPreference adapter_preference)
{
    UINT factory_flags = 0;
#if MARS_ENABLE_D3D12_VALIDATION
    factory_flags |= DXGI_CREATE_FACTORY_DEBUG;
#endif
    ThrowIfFailed(CreateDXGIFactory2(factory_flags, IID_PPV_ARGS(&factory_)), "CreateDXGIFactory2");
    const ComPtr<IDXGIAdapter1> adapter = ChooseAdapter(*factory_.Get(), adapter_preference);
    ThrowIfFailed(
        D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&device_)),
        "D3D12CreateDevice");
    NameObject(device_.Get(), L"MARSTHEGAME Phase 5 D3D12 Device");

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
    ThrowIfFailed(
        device_->CreateCommandQueue(&queue_description, IID_PPV_ARGS(&command_queue_)),
        "ID3D12Device::CreateCommandQueue");
    NameObject(command_queue_.Get(), L"MARSTHEGAME Phase 5 Direct Queue");

    for (std::uint32_t index = 0; index < kFrameCount; ++index)
    {
        ThrowIfFailed(
            device_->CreateCommandAllocator(
                D3D12_COMMAND_LIST_TYPE_DIRECT,
                IID_PPV_ARGS(&command_allocators_[index])),
            "ID3D12Device::CreateCommandAllocator");
        NameObject(command_allocators_[index].Get(), L"MARSTHEGAME Phase 5 Frame Allocator");
    }

    ThrowIfFailed(
        device_->CreateCommandList(
            0,
            D3D12_COMMAND_LIST_TYPE_DIRECT,
            command_allocators_[0].Get(),
            nullptr,
            IID_PPV_ARGS(&command_list_)),
        "ID3D12Device::CreateCommandList");
    NameObject(command_list_.Get(), L"MARSTHEGAME Phase 5 Graphics Command List");
