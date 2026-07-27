        TransitionBarrier(
            depth_buffer_.Get(), D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
            D3D12_RESOURCE_STATE_DEPTH_WRITE),
        TransitionBarrier(
            shadow_map_.Get(), D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
            D3D12_RESOURCE_STATE_DEPTH_WRITE),
    }};
    command_list_->ResourceBarrier(
        static_cast<UINT>(restore_depth_resources.size()), restore_depth_resources.data());

    command_list_->EndQuery(timestamp_query_heap_.Get(), D3D12_QUERY_TYPE_TIMESTAMP, query_base + 1U);
    command_list_->ResolveQueryData(
        timestamp_query_heap_.Get(), D3D12_QUERY_TYPE_TIMESTAMP,
        query_base, 2, timestamp_readback_.Get(),
        static_cast<UINT64>(query_base) * sizeof(std::uint64_t));
}

void D3D12Renderer::DrawInstances()
{
    command_list_->SetGraphicsRootSignature(root_signature_.Get());
    command_list_->SetGraphicsRootDescriptorTable(2, SrvHeapStart());
    const D3D12_GPU_VIRTUAL_ADDRESS frame_address =
        frame_constant_buffer_->GetGPUVirtualAddress()
        + static_cast<UINT64>(frame_index_) * sizeof(FrameConstants);
    command_list_->SetGraphicsRootConstantBufferView(1, frame_address);
    command_list_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    command_list_->IASetVertexBuffers(0, 1, &vertex_buffer_view_);
    command_list_->IASetIndexBuffer(&index_buffer_view_);

    const D3D12_GPU_VIRTUAL_ADDRESS object_base = object_constant_buffer_->GetGPUVirtualAddress();
    for (std::uint32_t index = 0; index < instance_count_; ++index)
    {
        const UINT64 constant_index = static_cast<UINT64>(frame_index_) * kMaxInstances + index;
        command_list_->SetGraphicsRootConstantBufferView(
            0, object_base + constant_index * sizeof(ObjectConstants));
        const MeshRange& mesh = mesh_ranges_[static_cast<std::size_t>(instance_meshes_[index])];
        command_list_->DrawIndexedInstanced(
            mesh.index_count, 1, mesh.start_index, mesh.base_vertex, 0);
    }
}

void D3D12Renderer::DrawParticles()
{
    command_list_->SetGraphicsRootSignature(root_signature_.Get());
    command_list_->SetGraphicsRootDescriptorTable(2, SrvHeapStart());
    const D3D12_GPU_VIRTUAL_ADDRESS frame_address =
        frame_constant_buffer_->GetGPUVirtualAddress()
        + static_cast<UINT64>(frame_index_) * sizeof(FrameConstants);
    command_list_->SetGraphicsRootConstantBufferView(1, frame_address);
    command_list_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    command_list_->IASetVertexBuffers(0, 0, nullptr);
    command_list_->IASetIndexBuffer(nullptr);
    command_list_->DrawInstanced(visual_configuration_.particle_count * 3U, 1, 0, 0);
}

void D3D12Renderer::DrawFullscreen(
    ID3D12PipelineState& pipeline,
    const D3D12_CPU_DESCRIPTOR_HANDLE target)
{
    command_list_->RSSetViewports(1, &viewport_);
    command_list_->RSSetScissorRects(1, &scissor_rect_);
    command_list_->OMSetRenderTargets(1, &target, FALSE, nullptr);
    command_list_->SetPipelineState(&pipeline);
    command_list_->SetGraphicsRootSignature(root_signature_.Get());
    command_list_->SetGraphicsRootDescriptorTable(2, SrvHeapStart());
    const D3D12_GPU_VIRTUAL_ADDRESS frame_address =
        frame_constant_buffer_->GetGPUVirtualAddress()
        + static_cast<UINT64>(frame_index_) * sizeof(FrameConstants);
    command_list_->SetGraphicsRootConstantBufferView(1, frame_address);
    command_list_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    command_list_->IASetVertexBuffers(0, 0, nullptr);
    command_list_->IASetIndexBuffer(nullptr);
    command_list_->DrawInstanced(3, 1, 0, 0);
}

void D3D12Renderer::MoveToNextFrame()
{
    const std::uint64_t signal_value = fence_values_[frame_index_];
    ThrowIfDeviceFailed(command_queue_->Signal(fence_.Get(), signal_value),
                        "ID3D12CommandQueue::Signal");
    frame_index_ = swap_chain_->GetCurrentBackBufferIndex();
    if (fence_->GetCompletedValue() < fence_values_[frame_index_])
    {
        ThrowIfDeviceFailed(
            fence_->SetEventOnCompletion(fence_values_[frame_index_], fence_event_),
            "ID3D12Fence::SetEventOnCompletion");
        const DWORD wait_result = WaitForSingleObject(fence_event_, INFINITE);
        if (wait_result != WAIT_OBJECT_0)
        {
            throw std::runtime_error("WaitForSingleObject failed for the frame fence");
        }
    }
    fence_values_[frame_index_] = signal_value + 1U;
}

void D3D12Renderer::WaitForGpu()
{
    if (command_queue_ == nullptr || fence_ == nullptr || fence_event_ == nullptr)
    {
        return;
    }
    const std::uint64_t signal_value = fence_values_[frame_index_];
    ThrowIfDeviceFailed(command_queue_->Signal(fence_.Get(), signal_value),
                        "ID3D12CommandQueue::Signal(wait)");
    ThrowIfDeviceFailed(fence_->SetEventOnCompletion(signal_value, fence_event_),
                        "ID3D12Fence::SetEventOnCompletion(wait)");
    const DWORD wait_result = WaitForSingleObject(fence_event_, INFINITE);
    if (wait_result != WAIT_OBJECT_0)
    {
        throw std::runtime_error("WaitForSingleObject failed while draining the GPU");
    }
    fence_values_[frame_index_] = signal_value + 1U;
    for (std::uint32_t index = 0; index < kFrameCount; ++index)
    {
        CollectGpuTiming(index);
    }
}

void D3D12Renderer::CollectGpuTiming(const std::uint32_t frame_index)
{
    if (!timestamp_valid_[frame_index] || timestamp_readback_ == nullptr || timestamp_frequency_ == 0)
    {
        return;
    }
    const SIZE_T offset = static_cast<SIZE_T>(frame_index) * 2U * sizeof(std::uint64_t);
    const D3D12_RANGE read_range{offset, offset + 2U * sizeof(std::uint64_t)};
    void* mapped = nullptr;
    ThrowIfFailed(timestamp_readback_->Map(0, &read_range, &mapped),
                  "ID3D12Resource::Map(timestamp readback)");
    const auto* values = reinterpret_cast<const std::uint64_t*>(
        static_cast<const std::byte*>(mapped) + offset);
    const std::uint64_t start = values[0];
    const std::uint64_t end = values[1];
    const D3D12_RANGE written_range{0, 0};
    timestamp_readback_->Unmap(0, &written_range);
    timestamp_valid_[frame_index] = false;
    if (end > start)
    {
        frame_statistics_.last_gpu_frame_ms =
            static_cast<double>(end - start) * 1'000.0 / static_cast<double>(timestamp_frequency_);
        frame_statistics_.max_gpu_frame_ms =
            (std::max)(frame_statistics_.max_gpu_frame_ms, frame_statistics_.last_gpu_frame_ms);
    }
}

void D3D12Renderer::ReleaseRenderTargets()
{
    for (auto& target : render_targets_)
    {
        target.Reset();
    }
}

void D3D12Renderer::ReleaseVisualTargets()
{
    depth_buffer_.Reset();
    for (auto& target : history_targets_)
    {
        target.Reset();
    }
    hdr_color_.Reset();
    history_valid_ = false;
}

void D3D12Renderer::ReleaseCaptureBuffer()
{
    capture_buffer_.Reset();
    capture_footprint_ = {};
    capture_total_bytes_ = 0;
    capture_row_size_bytes_ = 0;
    capture_row_count_ = 0;
    capture_requested_ = false;
    capture_submitted_ = false;
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

    shadow_viewport_.TopLeftX = 0.0f;
    shadow_viewport_.TopLeftY = 0.0f;
    shadow_viewport_.Width = static_cast<float>(visual_configuration_.shadow_resolution);
    shadow_viewport_.Height = static_cast<float>(visual_configuration_.shadow_resolution);
    shadow_viewport_.MinDepth = 0.0f;
    shadow_viewport_.MaxDepth = 1.0f;
    shadow_scissor_.left = 0;
    shadow_scissor_.top = 0;
    shadow_scissor_.right = static_cast<LONG>(visual_configuration_.shadow_resolution);
    shadow_scissor_.bottom = static_cast<LONG>(visual_configuration_.shadow_resolution);
}

void D3D12Renderer::UpdateResidentMemoryEstimate()
{
    const std::uint64_t pixels = static_cast<std::uint64_t>(width_) * height_;
    const std::uint64_t shadow_pixels =
        static_cast<std::uint64_t>(visual_configuration_.shadow_resolution)
        * visual_configuration_.shadow_resolution;
    visual_target_bytes_ = pixels * (8U * 3U + 4U + 4U * kFrameCount)
        + shadow_pixels * 4U;
    frame_statistics_.resident_gpu_bytes = visual_target_bytes_
        + upload_statistics_.uploaded_bytes
        + sizeof(ObjectConstants) * kMaxInstances * kFrameCount
        + sizeof(FrameConstants) * kFrameCount
        + sizeof(std::uint64_t) * kFrameCount * 2U;
}

void D3D12Renderer::ThrowIfDeviceFailed(
    const HRESULT result,
    const std::string_view operation) const
{
    if (SUCCEEDED(result))
