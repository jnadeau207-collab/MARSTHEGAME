    XMFLOAT3 right_values{};
    XMFLOAT3 up_values{};
    XMStoreFloat3(&right_values, right);
    XMStoreFloat3(&up_values, camera_up);

    XMFLOAT3 camera_motion{};
    if (previous_camera_valid_)
    {
        camera_motion = {
            scene.camera_eye.x - previous_camera_eye_.x,
            scene.camera_eye.y - previous_camera_eye_.y,
            scene.camera_eye.z - previous_camera_eye_.z,
        };
    }

    FrameConstants frame{};
    XMStoreFloat4x4(&frame.view_projection, view_projection);
    XMStoreFloat4x4(&frame.previous_view_projection, previous_view_projection);
    XMStoreFloat4x4(&frame.light_view_projection, light_view_projection);
    frame.camera_position_time = {
        scene.camera_eye.x, scene.camera_eye.y, scene.camera_eye.z, scene.elapsed_seconds};
    frame.sun_direction_exposure = {0.28f, -0.74f, -0.61f, current_exposure_};
    frame.sun_color_intensity = {1.0f, 0.60f, 0.36f, 7.2f};
    frame.fog_color_density = scene.mission_complete
        ? XMFLOAT4{0.055f, 0.14f, 0.11f, visual_configuration_.fog_density * 0.72f}
        : XMFLOAT4{0.12f, 0.034f, 0.018f, visual_configuration_.fog_density};
    frame.sky_zenith_history = {
        0.015f, 0.025f, 0.065f,
        history_valid_ ? visual_configuration_.temporal_history_weight : 0.0f};
    frame.horizon_color_bloom = {
        scene.mission_complete ? 0.08f : 0.22f,
        scene.mission_complete ? 0.19f : 0.055f,
        scene.mission_complete ? 0.13f : 0.025f,
        visual_configuration_.bloom_threshold};
    frame.post_parameters = {
        visual_configuration_.motion_blur_strength,
        0.24f,
        static_cast<float>(history_read_index_),
        static_cast<float>(active_history_write_index_)};
    frame.focus_parameters = {
        visual_configuration_.focus_distance,
        visual_configuration_.focus_range,
        kNearPlane,
        kFarPlane};
    frame.camera_motion_jitter = {
        camera_motion.x * 0.003f,
        -camera_motion.z * 0.003f,
        jitter.x,
        jitter.y};
    frame.particle_emitter_count = {
        scene.particle_emitter.x,
        scene.particle_emitter.y,
        scene.particle_emitter.z,
        static_cast<float>(visual_configuration_.particle_count)};
    frame.camera_right = {right_values.x, right_values.y, right_values.z, 0.0f};
    frame.camera_up = {up_values.x, up_values.y, up_values.z, 0.0f};
    for (std::size_t light_index = 0; light_index < scene.point_lights.size(); ++light_index)
    {
        const PointLight& light = scene.point_lights[light_index];
        DirectX::XMFLOAT3 position = light.position;
        float radius = light.radius;
        float intensity = light.intensity;
        if (light_index == 2U)
        {
            position.x = scene.camera_eye.x * 0.35f + position.x * 0.65f;
            position.y += 0.9f;
            position.z -= 2.2f;
            radius = 7.0f;
            intensity *= 3.2f;
        }
        frame.local_light_position_radius[light_index] = {
            position.x, position.y, position.z, radius};
        frame.local_light_color_intensity[light_index] = {
            light.color.x, light.color.y, light.color.z, intensity};
    }
    std::byte* frame_destination = mapped_frame_constants_
        + static_cast<std::size_t>(frame_index_) * sizeof(FrameConstants);
    std::memcpy(frame_destination, &frame, sizeof(frame));

    std::uint32_t destination_index = 0;
    const auto write_instance = [&](const RenderInstance& instance) {
        const std::size_t mesh_index = static_cast<std::size_t>(instance.mesh);
        if (mesh_index >= mesh_ranges_.size())
        {
            throw std::invalid_argument("RenderScene contains an invalid generated mesh kind");
        }
        instance_meshes_[destination_index] = instance.mesh;
        const XMMATRIX world =
            XMMatrixScaling(instance.scale.x, instance.scale.y, instance.scale.z)
            * XMMatrixRotationRollPitchYaw(
                instance.rotation_radians.x,
                instance.rotation_radians.y,
                instance.rotation_radians.z)
            * XMMatrixTranslation(instance.position.x, instance.position.y, instance.position.z);
        const XMMATRIX inverse_transpose = XMMatrixTranspose(XMMatrixInverse(nullptr, world));
        const GeneratedMaterial& material = materials_[mesh_index];
        ObjectConstants object{};
        XMStoreFloat4x4(&object.world, world);
        XMStoreFloat4x4(&object.world_inverse_transpose, inverse_transpose);
        XMStoreFloat4x4(&object.world_view_projection, world * view_projection);
        XMStoreFloat4x4(&object.previous_world_view_projection, world * previous_view_projection);
        XMStoreFloat4x4(&object.world_light_view_projection, world * light_view_projection);
        object.tint = instance.tint;
        object.material_parameters = {
            material.texture_scale,
            material.normal_strength,
            material.roughness,
            material.metallic};
        object.material_layer_mask = {
            static_cast<float>(material.texture_layer),
            material.mask_strength,
            0.0f,
            0.0f};
        const std::size_t constant_index =
            static_cast<std::size_t>(frame_index_) * kMaxInstances + destination_index;
        std::byte* destination = mapped_object_constants_ + constant_index * sizeof(ObjectConstants);
        std::memcpy(destination, &object, sizeof(object));
        ++destination_index;
    };

    for (const RenderInstance& instance : scene.instances)
    {
        write_instance(instance);
    }
    for (std::uint32_t index = 0; index < scene.supplemental_character_count; ++index)
    {
        write_instance(scene.supplemental_character_instances[index]);
    }

    XMStoreFloat4x4(&previous_view_projection_, view_projection);
    previous_camera_eye_ = scene.camera_eye;
    previous_camera_valid_ = true;
    previous_scene_time_ = scene.elapsed_seconds;
}

void D3D12Renderer::PopulateCommandList()
{
    const UINT query_base = frame_index_ * 2U;
    command_list_->EndQuery(timestamp_query_heap_.Get(), D3D12_QUERY_TYPE_TIMESTAMP, query_base);
    ID3D12DescriptorHeap* descriptor_heaps[] = {srv_heap_.Get()};
    command_list_->SetDescriptorHeaps(1, descriptor_heaps);

    command_list_->RSSetViewports(1, &shadow_viewport_);
    command_list_->RSSetScissorRects(1, &shadow_scissor_);
    const D3D12_CPU_DESCRIPTOR_HANDLE shadow_dsv = DsvHandle(kShadowDsvIndex);
    command_list_->OMSetRenderTargets(0, nullptr, FALSE, &shadow_dsv);
    command_list_->ClearDepthStencilView(
        shadow_dsv, D3D12_CLEAR_FLAG_DEPTH, 1.0f, 0, 0, nullptr);
    command_list_->SetPipelineState(shadow_pipeline_.Get());
    DrawInstances();

    const D3D12_RESOURCE_BARRIER shadow_to_read = TransitionBarrier(
        shadow_map_.Get(), D3D12_RESOURCE_STATE_DEPTH_WRITE,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE);
    command_list_->ResourceBarrier(1, &shadow_to_read);

    const D3D12_RESOURCE_BARRIER hdr_to_target = TransitionBarrier(
        hdr_color_.Get(), D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        D3D12_RESOURCE_STATE_RENDER_TARGET);
    command_list_->ResourceBarrier(1, &hdr_to_target);
    command_list_->RSSetViewports(1, &viewport_);
    command_list_->RSSetScissorRects(1, &scissor_rect_);
    const D3D12_CPU_DESCRIPTOR_HANDLE hdr_rtv = RtvHandle(kHdrRtvIndex);
    const D3D12_CPU_DESCRIPTOR_HANDLE scene_dsv = DsvHandle(kSceneDepthDsvIndex);
    command_list_->OMSetRenderTargets(1, &hdr_rtv, FALSE, &scene_dsv);
    command_list_->ClearRenderTargetView(hdr_rtv, clear_color_.data(), 0, nullptr);
    command_list_->ClearDepthStencilView(
        scene_dsv, D3D12_CLEAR_FLAG_DEPTH, 1.0f, 0, 0, nullptr);
    command_list_->SetPipelineState(scene_pipeline_.Get());
    DrawInstances();
    command_list_->SetPipelineState(particle_pipeline_.Get());
    DrawParticles();

    const D3D12_RESOURCE_BARRIER hdr_to_read = TransitionBarrier(
        hdr_color_.Get(), D3D12_RESOURCE_STATE_RENDER_TARGET,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE);
    command_list_->ResourceBarrier(1, &hdr_to_read);
    const D3D12_RESOURCE_BARRIER depth_to_read = TransitionBarrier(
        depth_buffer_.Get(), D3D12_RESOURCE_STATE_DEPTH_WRITE,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE);
    command_list_->ResourceBarrier(1, &depth_to_read);

    ID3D12Resource* history_write = history_targets_[active_history_write_index_].Get();
    const D3D12_RESOURCE_BARRIER history_to_target = TransitionBarrier(
        history_write, D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        D3D12_RESOURCE_STATE_RENDER_TARGET);
    command_list_->ResourceBarrier(1, &history_to_target);
    const D3D12_CPU_DESCRIPTOR_HANDLE history_rtv = RtvHandle(
        active_history_write_index_ == 0 ? kHistory0RtvIndex : kHistory1RtvIndex);
    DrawFullscreen(*temporal_pipeline_.Get(), history_rtv);
    const D3D12_RESOURCE_BARRIER history_to_read = TransitionBarrier(
        history_write, D3D12_RESOURCE_STATE_RENDER_TARGET,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE);
    command_list_->ResourceBarrier(1, &history_to_read);

    const D3D12_RESOURCE_BARRIER back_buffer_to_target = TransitionBarrier(
        render_targets_[frame_index_].Get(), D3D12_RESOURCE_STATE_PRESENT,
        D3D12_RESOURCE_STATE_RENDER_TARGET);
    command_list_->ResourceBarrier(1, &back_buffer_to_target);
    const D3D12_CPU_DESCRIPTOR_HANDLE back_buffer_rtv = RtvHandle(frame_index_);
    DrawFullscreen(*final_pipeline_.Get(), back_buffer_rtv);

    if (capture_requested_)
    {
        const D3D12_RESOURCE_BARRIER target_to_copy = TransitionBarrier(
            render_targets_[frame_index_].Get(), D3D12_RESOURCE_STATE_RENDER_TARGET,
            D3D12_RESOURCE_STATE_COPY_SOURCE);
        command_list_->ResourceBarrier(1, &target_to_copy);
        D3D12_TEXTURE_COPY_LOCATION destination{};
        destination.pResource = capture_buffer_.Get();
        destination.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
        destination.PlacedFootprint = capture_footprint_;
        D3D12_TEXTURE_COPY_LOCATION source{};
        source.pResource = render_targets_[frame_index_].Get();
        source.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        source.SubresourceIndex = 0;
        command_list_->CopyTextureRegion(&destination, 0, 0, 0, &source, nullptr);
        const D3D12_RESOURCE_BARRIER copy_to_present = TransitionBarrier(
            render_targets_[frame_index_].Get(), D3D12_RESOURCE_STATE_COPY_SOURCE,
            D3D12_RESOURCE_STATE_PRESENT);
        command_list_->ResourceBarrier(1, &copy_to_present);
    }
    else
    {
        const D3D12_RESOURCE_BARRIER target_to_present = TransitionBarrier(
            render_targets_[frame_index_].Get(), D3D12_RESOURCE_STATE_RENDER_TARGET,
            D3D12_RESOURCE_STATE_PRESENT);
        command_list_->ResourceBarrier(1, &target_to_present);
    }

    const std::array<D3D12_RESOURCE_BARRIER, 2> restore_depth_resources = {{
