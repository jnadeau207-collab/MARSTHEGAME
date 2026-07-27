    {
        return;
    }
    std::string message = std::string(operation) + " failed with HRESULT " + FormatHresult(result);
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

D3D12_CPU_DESCRIPTOR_HANDLE D3D12Renderer::RtvHandle(const std::uint32_t index) const noexcept
{
    D3D12_CPU_DESCRIPTOR_HANDLE handle = rtv_heap_->GetCPUDescriptorHandleForHeapStart();
    handle.ptr += static_cast<SIZE_T>(index) * rtv_descriptor_size_;
    return handle;
}

D3D12_CPU_DESCRIPTOR_HANDLE D3D12Renderer::DsvHandle(const std::uint32_t index) const noexcept
{
    D3D12_CPU_DESCRIPTOR_HANDLE handle = dsv_heap_->GetCPUDescriptorHandleForHeapStart();
    handle.ptr += static_cast<SIZE_T>(index) * dsv_descriptor_size_;
    return handle;
}

D3D12_GPU_DESCRIPTOR_HANDLE D3D12Renderer::SrvHeapStart() const noexcept
{
    return srv_heap_->GetGPUDescriptorHandleForHeapStart();
}

ComPtr<IDXGIAdapter1> D3D12Renderer::ChooseAdapter(
    IDXGIFactory6& factory,
    const AdapterPreference adapter_preference)
{
    if (adapter_preference == AdapterPreference::Warp)
    {
        ComPtr<IDXGIAdapter1> warp_adapter;
        ThrowIfFailed(factory.EnumWarpAdapter(IID_PPV_ARGS(&warp_adapter)),
                      "IDXGIFactory::EnumWarpAdapter");
        return warp_adapter;
    }
    for (UINT index = 0;; ++index)
    {
        ComPtr<IDXGIAdapter1> adapter;
        const HRESULT result = factory.EnumAdapterByGpuPreference(
            index, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE, IID_PPV_ARGS(&adapter));
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
                adapter.Get(), D3D_FEATURE_LEVEL_12_0, __uuidof(ID3D12Device), nullptr)))
        {
            return adapter;
        }
    }
    throw std::runtime_error("No Direct3D 12 feature-level 12_0 hardware adapter was found");
}
} // namespace mars::renderer
