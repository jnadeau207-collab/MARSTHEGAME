        D3D12_RESOURCE_STATE_VERTEX_AND_CONSTANT_BUFFER,
        L"MARSTHEGAME Default-Heap Procedural Vertices");
    index_buffer_ = upload_context_.UploadBuffer(
        std::as_bytes(std::span<const std::uint32_t>(indices)),
        D3D12_RESOURCE_STATE_INDEX_BUFFER,
        L"MARSTHEGAME Default-Heap Procedural Indices");
    base_color_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.base_color.rgba8),
        material_catalog.base_color.width,
        material_catalog.base_color.height,
        material_catalog.base_color.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Base Color Array");
    normal_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.normal.rgba8),
        material_catalog.normal.width,
        material_catalog.normal.height,
        material_catalog.normal.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Normal Array");
    surface_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.surface.rgba8),
        material_catalog.surface.width,
        material_catalog.surface.height,
        material_catalog.surface.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Roughness Metallic Mask Array");
    environment_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(environment.rgba8),
        environment.face_size,
        environment.face_size,
        6U,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Martian Environment Cube");
    const std::uint64_t upload_fence = upload_context_.Submit();
    upload_context_.Wait(upload_fence);
    upload_statistics_ = upload_context_.Statistics();
    if (upload_statistics_.pending_staging_batches != 0)
    {
        throw std::runtime_error("Completed startup uploads retained stale staging resources");
    }

    vertex_buffer_view_.BufferLocation = vertex_buffer_->GetGPUVirtualAddress();
    vertex_buffer_view_.StrideInBytes = static_cast<UINT>(sizeof(MeshVertex));
    vertex_buffer_view_.SizeInBytes = CheckedSizeToUint(
        vertices.size() * sizeof(MeshVertex), "procedural vertex atlas");
    index_buffer_view_.BufferLocation = index_buffer_->GetGPUVirtualAddress();
    index_buffer_view_.SizeInBytes = CheckedSizeToUint(
        indices.size() * sizeof(std::uint32_t), "procedural index atlas");
    index_buffer_view_.Format = DXGI_FORMAT_R32_UINT;
    materials_ = material_catalog.materials;
}

void D3D12Renderer::CreateConstantBuffers()
{
    const auto create_upload_buffer = [this](
        const std::uint64_t size,
        ComPtr<ID3D12Resource>& resource,
        const std::wstring_view name) {
        D3D12_HEAP_PROPERTIES heap{};
        heap.Type = D3D12_HEAP_TYPE_UPLOAD;
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
        ThrowIfFailed(
            device_->CreateCommittedResource(
                &heap, D3D12_HEAP_FLAG_NONE, &description,
                D3D12_RESOURCE_STATE_GENERIC_READ, nullptr, IID_PPV_ARGS(&resource)),
            "ID3D12Device::CreateCommittedResource(constants)");
        NameObject(resource.Get(), name);
    };

    create_upload_buffer(
        sizeof(ObjectConstants) * kMaxInstances * kFrameCount,
        object_constant_buffer_,
        L"MARSTHEGAME Object Constants");
    create_upload_buffer(
        sizeof(FrameConstants) * kFrameCount,
        frame_constant_buffer_,
        L"MARSTHEGAME Frame Constants");

    const D3D12_RANGE read_range{0, 0};
    void* object_mapping = nullptr;
    ThrowIfFailed(object_constant_buffer_->Map(0, &read_range, &object_mapping),
                  "ID3D12Resource::Map(object constants)");
    mapped_object_constants_ = static_cast<std::byte*>(object_mapping);
    void* frame_mapping = nullptr;
    ThrowIfFailed(frame_constant_buffer_->Map(0, &read_range, &frame_mapping),
                  "ID3D12Resource::Map(frame constants)");
    mapped_frame_constants_ = static_cast<std::byte*>(frame_mapping);
}

void D3D12Renderer::CreateTimingResources()
{
    ThrowIfFailed(command_queue_->GetTimestampFrequency(&timestamp_frequency_),
                  "ID3D12CommandQueue::GetTimestampFrequency");
    D3D12_QUERY_HEAP_DESC heap_description{};
    heap_description.Type = D3D12_QUERY_HEAP_TYPE_TIMESTAMP;
    heap_description.Count = kFrameCount * 2U;
    ThrowIfFailed(device_->CreateQueryHeap(&heap_description, IID_PPV_ARGS(&timestamp_query_heap_)),
                  "ID3D12Device::CreateQueryHeap(timestamp)");

    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = D3D12_HEAP_TYPE_READBACK;
    heap.CreationNodeMask = 1;
    heap.VisibleNodeMask = 1;
    D3D12_RESOURCE_DESC description{};
    description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    description.Width = sizeof(std::uint64_t) * kFrameCount * 2U;
    description.Height = 1;
    description.DepthOrArraySize = 1;
    description.MipLevels = 1;
    description.SampleDesc.Count = 1;
    description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
    ThrowIfFailed(
        device_->CreateCommittedResource(
            &heap, D3D12_HEAP_FLAG_NONE, &description,
            D3D12_RESOURCE_STATE_COPY_DEST, nullptr, IID_PPV_ARGS(&timestamp_readback_)),
        "ID3D12Device::CreateCommittedResource(timestamp readback)");
    NameObject(timestamp_query_heap_.Get(), L"MARSTHEGAME GPU Timestamp Heap");
    NameObject(timestamp_readback_.Get(), L"MARSTHEGAME GPU Timestamp Readback");
}

void D3D12Renderer::WriteShaderResourceViews()
{
    D3D12_CPU_DESCRIPTOR_HANDLE descriptor = srv_heap_->GetCPUDescriptorHandleForHeapStart();
    const auto advance = [this, &descriptor]() { descriptor.ptr += srv_descriptor_size_; };

    D3D12_SHADER_RESOURCE_VIEW_DESC material_view{};
    material_view.Shader4ComponentMapping = D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
    material_view.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    material_view.ViewDimension = D3D12_SRV_DIMENSION_TEXTURE2DARRAY;
    material_view.Texture2DArray.MostDetailedMip = 0;
    material_view.Texture2DArray.MipLevels = 1;
    material_view.Texture2DArray.FirstArraySlice = 0;
    material_view.Texture2DArray.ArraySize = static_cast<UINT>(kGeneratedMaterialCount);
    material_view.Texture2DArray.ResourceMinLODClamp = 0.0f;
    device_->CreateShaderResourceView(base_color_texture_.Get(), &material_view, descriptor);
    advance();
    device_->CreateShaderResourceView(normal_texture_.Get(), &material_view, descriptor);
    advance();
    device_->CreateShaderResourceView(surface_texture_.Get(), &material_view, descriptor);
    advance();

    D3D12_SHADER_RESOURCE_VIEW_DESC scalar_view{};
    scalar_view.Shader4ComponentMapping = D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
    scalar_view.Format = DXGI_FORMAT_R32_FLOAT;
    scalar_view.ViewDimension = D3D12_SRV_DIMENSION_TEXTURE2D;
    scalar_view.Texture2D.MostDetailedMip = 0;
    scalar_view.Texture2D.MipLevels = 1;
    scalar_view.Texture2D.ResourceMinLODClamp = 0.0f;
    device_->CreateShaderResourceView(shadow_map_.Get(), &scalar_view, descriptor);
    advance();

    D3D12_SHADER_RESOURCE_VIEW_DESC hdr_view{};
    hdr_view.Shader4ComponentMapping = D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
    hdr_view.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
    hdr_view.ViewDimension = D3D12_SRV_DIMENSION_TEXTURE2D;
    hdr_view.Texture2D.MostDetailedMip = 0;
    hdr_view.Texture2D.MipLevels = 1;
    hdr_view.Texture2D.ResourceMinLODClamp = 0.0f;
    device_->CreateShaderResourceView(hdr_color_.Get(), &hdr_view, descriptor);
    advance();
    device_->CreateShaderResourceView(history_targets_[0].Get(), &hdr_view, descriptor);
    advance();
    device_->CreateShaderResourceView(history_targets_[1].Get(), &hdr_view, descriptor);
    advance();
    device_->CreateShaderResourceView(depth_buffer_.Get(), &scalar_view, descriptor);
    advance();

    D3D12_SHADER_RESOURCE_VIEW_DESC environment_view{};
    environment_view.Shader4ComponentMapping = D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
    environment_view.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    environment_view.ViewDimension = D3D12_SRV_DIMENSION_TEXTURECUBE;
    environment_view.TextureCube.MostDetailedMip = 0;
    environment_view.TextureCube.MipLevels = 1;
    environment_view.TextureCube.ResourceMinLODClamp = 0.0f;
    device_->CreateShaderResourceView(environment_texture_.Get(), &environment_view, descriptor);
}

void D3D12Renderer::UpdateConstants(const RenderScene& scene)
{
    using namespace DirectX;

    instance_count_ = static_cast<std::uint32_t>(scene.instances.size() + scene.supplemental_character_count);
    clear_color_ = {scene.clear_color.x, scene.clear_color.y, scene.clear_color.z, scene.clear_color.w};
    active_history_write_index_ = 1U - history_read_index_;

    const XMFLOAT3 cinematic_eye_values{
        scene.camera_eye.x - 2.6f,
        scene.camera_eye.y - 2.15f,
        scene.camera_eye.z + 3.0f,
    };
    const XMFLOAT3 cinematic_target_values{
        scene.camera_target.x + 0.45f,
        scene.camera_target.y + 0.15f,
        scene.camera_target.z + 1.1f,
    };
    const XMVECTOR eye = XMLoadFloat3(&cinematic_eye_values);
    const XMVECTOR target = XMLoadFloat3(&cinematic_target_values);
    const XMVECTOR up_axis = XMVectorSet(0.0f, 1.0f, 0.0f, 0.0f);
    const XMMATRIX view = XMMatrixLookAtLH(eye, target, up_axis);
    XMMATRIX projection = XMMatrixPerspectiveFovLH(
        XMConvertToRadians(58.0f),
        static_cast<float>(width_) / static_cast<float>(height_),
        kNearPlane,
        kFarPlane);
    const TemporalJitter jitter = ComputeTemporalJitter(
        frame_statistics_.presented_frames, width_, height_);
    XMFLOAT4X4 projection_values{};
    XMStoreFloat4x4(&projection_values, projection);
    projection_values._31 += jitter.x;
    projection_values._32 += jitter.y;
    projection = XMLoadFloat4x4(&projection_values);
    const XMMATRIX view_projection = view * projection;

    const XMVECTOR light_eye = XMVectorSet(22.0f, 34.0f, -24.0f, 1.0f);
    const XMVECTOR light_target = XMVectorSet(0.0f, 0.0f, 7.0f, 1.0f);
    const XMMATRIX light_view = XMMatrixLookAtLH(light_eye, light_target, up_axis);
    const XMMATRIX light_projection = XMMatrixOrthographicLH(54.0f, 70.0f, 1.0f, 120.0f);
    const XMMATRIX light_view_projection = light_view * light_projection;

    XMMATRIX previous_view_projection = view_projection;
    if (previous_camera_valid_)
    {
        previous_view_projection = XMLoadFloat4x4(&previous_view_projection_);
    }

    const float scene_delta = (std::clamp)(scene.elapsed_seconds - previous_scene_time_, 0.0f, 0.25f);
    const float target_exposure = (std::clamp)(
        scene.target_exposure * 1.22f,
        visual_configuration_.minimum_exposure,
        visual_configuration_.maximum_exposure);
    current_exposure_ = AdaptExposure(
        current_exposure_, target_exposure, scene_delta,
        visual_configuration_.exposure_adaptation_rate);

    const XMVECTOR forward = XMVector3Normalize(XMVectorSubtract(target, eye));
    const XMVECTOR right = XMVector3Normalize(XMVector3Cross(up_axis, forward));
    const XMVECTOR camera_up = XMVector3Normalize(XMVector3Cross(forward, right));
