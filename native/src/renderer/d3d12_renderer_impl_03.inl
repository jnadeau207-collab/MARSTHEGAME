    ThrowIfFailed(command_list_->Close(), "ID3D12GraphicsCommandList::Close");

    ThrowIfFailed(device_->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence_)),
                  "ID3D12Device::CreateFence");
    NameObject(fence_.Get(), L"MARSTHEGAME Frame Fence");
    fence_event_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    if (fence_event_ == nullptr)
    {
        throw std::runtime_error("CreateEventW failed for the D3D12 frame fence");
    }
}

void D3D12Renderer::CreateSwapChain(const HWND window)
{
    DXGI_SWAP_CHAIN_DESC1 description{};
    description.Width = width_;
    description.Height = height_;
    description.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    description.SampleDesc.Count = 1;
    description.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    description.BufferCount = kFrameCount;
    description.Scaling = DXGI_SCALING_STRETCH;
    description.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
    description.AlphaMode = DXGI_ALPHA_MODE_UNSPECIFIED;

    ComPtr<IDXGISwapChain1> swap_chain;
    ThrowIfFailed(
        factory_->CreateSwapChainForHwnd(
            command_queue_.Get(), window, &description, nullptr, nullptr, &swap_chain),
        "IDXGIFactory::CreateSwapChainForHwnd");
    ThrowIfFailed(factory_->MakeWindowAssociation(window, DXGI_MWA_NO_ALT_ENTER),
                  "IDXGIFactory::MakeWindowAssociation");
    ThrowIfFailed(swap_chain.As(&swap_chain_), "IDXGISwapChain::QueryInterface");
    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    fence_values_.fill(0);
    fence_values_[frame_index_] = 1;
}

void D3D12Renderer::CreateDescriptorHeaps()
{
    D3D12_DESCRIPTOR_HEAP_DESC rtv_description{};
    rtv_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
    rtv_description.NumDescriptors = kRtvDescriptorCount;
    ThrowIfFailed(device_->CreateDescriptorHeap(&rtv_description, IID_PPV_ARGS(&rtv_heap_)),
                  "ID3D12Device::CreateDescriptorHeap(RTV)");
    rtv_descriptor_size_ = device_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);

    D3D12_DESCRIPTOR_HEAP_DESC dsv_description{};
    dsv_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_DSV;
    dsv_description.NumDescriptors = kDsvDescriptorCount;
    ThrowIfFailed(device_->CreateDescriptorHeap(&dsv_description, IID_PPV_ARGS(&dsv_heap_)),
                  "ID3D12Device::CreateDescriptorHeap(DSV)");
    dsv_descriptor_size_ = device_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_DSV);

    D3D12_DESCRIPTOR_HEAP_DESC srv_description{};
    srv_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV;
    srv_description.NumDescriptors = kSrvDescriptorCount;
    srv_description.Flags = D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE;
    ThrowIfFailed(device_->CreateDescriptorHeap(&srv_description, IID_PPV_ARGS(&srv_heap_)),
                  "ID3D12Device::CreateDescriptorHeap(SRV)");
    srv_descriptor_size_ =
        device_->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);
    NameObject(rtv_heap_.Get(), L"MARSTHEGAME Phase 5 RTV Heap");
    NameObject(dsv_heap_.Get(), L"MARSTHEGAME Phase 5 DSV Heap");
    NameObject(srv_heap_.Get(), L"MARSTHEGAME Phase 5 SRV Heap");
}

void D3D12Renderer::CreateRenderTargetViews()
{
    for (std::uint32_t index = 0; index < kFrameCount; ++index)
    {
        ThrowIfFailed(swap_chain_->GetBuffer(index, IID_PPV_ARGS(&render_targets_[index])),
                      "IDXGISwapChain::GetBuffer");
        device_->CreateRenderTargetView(render_targets_[index].Get(), nullptr, RtvHandle(index));
        NameObject(render_targets_[index].Get(), L"MARSTHEGAME Phase 5 Back Buffer");
    }
}

void D3D12Renderer::CreateVisualTargets()
{
    ReleaseVisualTargets();
    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_DEFAULT;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC color_description{};
    color_description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    color_description.Width = width_;
    color_description.Height = height_;
    color_description.DepthOrArraySize = 1;
    color_description.MipLevels = 1;
    color_description.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
    color_description.SampleDesc.Count = 1;
    color_description.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;
    color_description.Flags = D3D12_RESOURCE_FLAG_ALLOW_RENDER_TARGET;
    D3D12_CLEAR_VALUE color_clear{};
    color_clear.Format = color_description.Format;

    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap, D3D12_HEAP_FLAG_NONE, &color_description,
            D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE, &color_clear,
            IID_PPV_ARGS(&hdr_color_)),
        "ID3D12Device::CreateCommittedResource(HDR color)");
    NameObject(hdr_color_.Get(), L"MARSTHEGAME HDR Scene Color");
    device_->CreateRenderTargetView(hdr_color_.Get(), nullptr, RtvHandle(kHdrRtvIndex));

    for (std::size_t index = 0; index < history_targets_.size(); ++index)
    {
        ThrowIfFailed(
            device_->CreateCommittedResource(
                &heap, D3D12_HEAP_FLAG_NONE, &color_description,
                D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE, &color_clear,
                IID_PPV_ARGS(&history_targets_[index])),
            "ID3D12Device::CreateCommittedResource(temporal history)");
        NameObject(history_targets_[index].Get(), L"MARSTHEGAME Temporal History");
        device_->CreateRenderTargetView(
            history_targets_[index].Get(), nullptr,
            RtvHandle(index == 0 ? kHistory0RtvIndex : kHistory1RtvIndex));
    }

    D3D12_RESOURCE_DESC depth_description{};
    depth_description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    depth_description.Width = width_;
    depth_description.Height = height_;
    depth_description.DepthOrArraySize = 1;
    depth_description.MipLevels = 1;
    depth_description.Format = DXGI_FORMAT_R32_TYPELESS;
    depth_description.SampleDesc.Count = 1;
    depth_description.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;
    depth_description.Flags = D3D12_RESOURCE_FLAG_ALLOW_DEPTH_STENCIL;
    D3D12_CLEAR_VALUE depth_clear{};
    depth_clear.Format = DXGI_FORMAT_D32_FLOAT;
    depth_clear.DepthStencil.Depth = 1.0f;

    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap, D3D12_HEAP_FLAG_NONE, &depth_description,
            D3D12_RESOURCE_STATE_DEPTH_WRITE, &depth_clear,
            IID_PPV_ARGS(&depth_buffer_)),
        "ID3D12Device::CreateCommittedResource(scene depth)");
    NameObject(depth_buffer_.Get(), L"MARSTHEGAME Sampleable Scene Depth");
    D3D12_DEPTH_STENCIL_VIEW_DESC dsv{};
    dsv.Format = DXGI_FORMAT_D32_FLOAT;
    dsv.ViewDimension = D3D12_DSV_DIMENSION_TEXTURE2D;
    device_->CreateDepthStencilView(depth_buffer_.Get(), &dsv, DsvHandle(kSceneDepthDsvIndex));

    history_valid_ = false;
}

void D3D12Renderer::CreateShadowMap()
{
    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_DEFAULT;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;

    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
    description.Width = visual_configuration_.shadow_resolution;
    description.Height = visual_configuration_.shadow_resolution;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.Format = DXGI_FORMAT_R32_TYPELESS;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_UNKNOWN;
    description.Flags = D3D12_RESOURCE_FLAG_ALLOW_DEPTH_STENCIL;
    D3D12_CLEAR_VALUE clear_value{};
    clear_value.Format = DXGI_FORMAT_D32_FLOAT;
    clear_value.DepthStencil.Depth = 1.0f;

    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap, D3D12_HEAP_FLAG_NONE, &description,
            D3D12_RESOURCE_STATE_DEPTH_WRITE, &clear_value,
            IID_PPV_ARGS(&shadow_map_)),
        "ID3D12Device::CreateCommittedResource(shadow map)");
    NameObject(shadow_map_.Get(), L"MARSTHEGAME 2048 Shadow Map");
    D3D12_DEPTH_STENCIL_VIEW_DESC dsv{};
    dsv.Format = DXGI_FORMAT_D32_FLOAT;
    dsv.ViewDimension = D3D12_DSV_DIMENSION_TEXTURE2D;
    device_->CreateDepthStencilView(shadow_map_.Get(), &dsv, DsvHandle(kShadowDsvIndex));
}

void D3D12Renderer::CreateCaptureBuffer()
{
    ReleaseCaptureBuffer();
    if (!frame_capture_enabled_ || render_targets_[0] == nullptr)
    {
        return;
    }
    const D3D12_RESOURCE_DESC source_description = render_targets_[0]->GetDesc();
    UINT row_count = 0;
    UINT64 row_size = 0;
    UINT64 total_bytes = 0;
    device_->GetCopyableFootprints(
        &source_description, 0, 1, 0, &capture_footprint_, &row_count, &row_size, &total_bytes);
    capture_row_count_ = row_count;
    capture_row_size_bytes_ = row_size;
    capture_total_bytes_ = total_bytes;

    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_READBACK;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;
    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    description.Width = capture_total_bytes_;
    description.Height = 1;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap, D3D12_HEAP_FLAG_NONE, &description,
            D3D12_RESOURCE_STATE_COPY_DEST, nullptr, IID_PPV_ARGS(&capture_buffer_)),
        "ID3D12Device::CreateCommittedResource(capture)");
    NameObject(capture_buffer_.Get(), L"MARSTHEGAME Phase 5 Capture Readback");
