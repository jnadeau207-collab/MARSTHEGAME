#include "renderer/d3d12_renderer.h"

#include "renderer/procedural_catalog.h"
#include "renderer/procedural_geometry.h"

#include <d3d12sdklayers.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cfloat>
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
#include <span>
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

constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;
constexpr UINT kRtvDescriptorCount = D3D12Renderer::kFrameCount + 3U;
constexpr UINT kDsvDescriptorCount = 2U;
constexpr UINT kSrvDescriptorCount = 9U;
constexpr UINT kHdrRtvIndex = D3D12Renderer::kFrameCount;
constexpr UINT kHistory0RtvIndex = kHdrRtvIndex + 1U;
constexpr UINT kHistory1RtvIndex = kHdrRtvIndex + 2U;
constexpr UINT kSceneDepthDsvIndex = 0U;
constexpr UINT kShadowDsvIndex = 1U;
constexpr float kNearPlane = 0.1f;
constexpr float kFarPlane = 250.0f;

[[nodiscard]] std::string FormatHresult(const HRESULT result)
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

[[nodiscard]] std::vector<std::uint8_t> ReadBinaryFile(const std::filesystem::path& path)
{
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    if (!stream)
    {
        throw std::runtime_error("Could not open shader: " + path.string());
    }
    const std::streamoff end = stream.tellg();
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

[[nodiscard]] UINT CheckedSizeToUint(const std::size_t size, const std::string_view label)
{
    if (size > static_cast<std::size_t>((std::numeric_limits<UINT>::max)()))
    {
        throw std::runtime_error(std::string(label) + " exceeds the D3D12 UINT size limit");
    }
    return static_cast<UINT>(size);
}

[[nodiscard]] D3D12_RASTERIZER_DESC RasterizerDescription() noexcept
{
    D3D12_RASTERIZER_DESC description{};
    description.FillMode = D3D12_FILL_MODE_SOLID;
    description.CullMode = D3D12_CULL_MODE_NONE;
    description.FrontCounterClockwise = FALSE;
    description.DepthBias = D3D12_DEFAULT_DEPTH_BIAS;
    description.DepthBiasClamp = D3D12_DEFAULT_DEPTH_BIAS_CLAMP;
    description.SlopeScaledDepthBias = D3D12_DEFAULT_SLOPE_SCALED_DEPTH_BIAS;
    description.DepthClipEnable = TRUE;
    description.MultisampleEnable = FALSE;
    description.AntialiasedLineEnable = FALSE;
    description.ForcedSampleCount = 0;
    description.ConservativeRaster = D3D12_CONSERVATIVE_RASTERIZATION_MODE_OFF;
    return description;
}

[[nodiscard]] D3D12_BLEND_DESC OpaqueBlendDescription() noexcept
{
    D3D12_BLEND_DESC description{};
    description.AlphaToCoverageEnable = FALSE;
    description.IndependentBlendEnable = FALSE;
    D3D12_RENDER_TARGET_BLEND_DESC& target = description.RenderTarget[0];
    target.BlendEnable = FALSE;
    target.LogicOpEnable = FALSE;
    target.SrcBlend = D3D12_BLEND_ONE;
    target.DestBlend = D3D12_BLEND_ZERO;
    target.BlendOp = D3D12_BLEND_OP_ADD;
    target.SrcBlendAlpha = D3D12_BLEND_ONE;
    target.DestBlendAlpha = D3D12_BLEND_ZERO;
    target.BlendOpAlpha = D3D12_BLEND_OP_ADD;
    target.LogicOp = D3D12_LOGIC_OP_NOOP;
    target.RenderTargetWriteMask = D3D12_COLOR_WRITE_ENABLE_ALL;
    return description;
}

[[nodiscard]] D3D12_DEPTH_STENCIL_DESC DepthDescription(
    const bool enabled,
    const bool write_enabled) noexcept
{
    D3D12_DEPTH_STENCIL_DESC description{};
    description.DepthEnable = enabled ? TRUE : FALSE;
    description.DepthWriteMask = write_enabled
        ? D3D12_DEPTH_WRITE_MASK_ALL
        : D3D12_DEPTH_WRITE_MASK_ZERO;
    description.DepthFunc = D3D12_COMPARISON_FUNC_LESS_EQUAL;
    description.StencilEnable = FALSE;
    description.StencilReadMask = D3D12_DEFAULT_STENCIL_READ_MASK;
    description.StencilWriteMask = D3D12_DEFAULT_STENCIL_WRITE_MASK;
    return description;
}

void WriteCaptureBitmap(
    const std::filesystem::path& path,
    const std::uint8_t* source,
    const std::size_t source_row_pitch,
    const std::uint32_t width,
    const std::uint32_t height)
{
    const std::size_t destination_row_pitch = static_cast<std::size_t>(width) * 4U;
    std::vector<std::uint8_t> bgra(destination_row_pitch * static_cast<std::size_t>(height));
    for (std::uint32_t y = 0; y < height; ++y)
    {
        const std::uint8_t* source_row = source + static_cast<std::size_t>(y) * source_row_pitch;
        std::uint8_t* destination_row = bgra.data() + static_cast<std::size_t>(y) * destination_row_pitch;
        for (std::uint32_t x = 0; x < width; ++x)
        {
            const std::size_t offset = static_cast<std::size_t>(x) * 4U;
            destination_row[offset] = source_row[offset + 2U];
            destination_row[offset + 1U] = source_row[offset + 1U];
            destination_row[offset + 2U] = source_row[offset];
            destination_row[offset + 3U] = source_row[offset + 3U];
        }
    }

    BITMAPFILEHEADER file_header{};
    BITMAPINFOHEADER info_header{};
    info_header.biSize = sizeof(BITMAPINFOHEADER);
    info_header.biWidth = static_cast<LONG>(width);
    info_header.biHeight = -static_cast<LONG>(height);
    info_header.biPlanes = 1;
    info_header.biBitCount = 32;
    info_header.biCompression = BI_RGB;
    info_header.biSizeImage = CheckedSizeToUint(bgra.size(), "capture bitmap");
    file_header.bfType = 0x4D42U;
    file_header.bfOffBits = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);
    file_header.bfSize = file_header.bfOffBits + info_header.biSizeImage;

    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    if (!output)
    {
        throw std::runtime_error("Could not create Phase 5 frame capture: " + path.string());
    }
    output.write(reinterpret_cast<const char*>(&file_header), sizeof(file_header));
    output.write(reinterpret_cast<const char*>(&info_header), sizeof(info_header));
    output.write(reinterpret_cast<const char*>(bgra.data()), static_cast<std::streamsize>(bgra.size()));
    if (!output)
    {
        throw std::runtime_error("Could not write Phase 5 frame capture: " + path.string());
    }
}
} // namespace
