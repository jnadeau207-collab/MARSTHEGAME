#include "assets/mesh_asset.h"

#include "assets/json.h"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <system_error>
#include <type_traits>
#include <utility>
#include <vector>

namespace mars::assets
{
namespace
{
constexpr std::array<char, 8> kMagic = {'M', 'A', 'R', 'S', 'M', 'H', '1', '\0'};
constexpr std::uint32_t kCookedVersion = 1;
constexpr std::uint32_t kMaximumVertices = 1'000'000;
constexpr std::uint32_t kMaximumIndices = 3'000'000;
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;
constexpr std::string_view kDataPrefix = "data:application/octet-stream;base64,";
constexpr std::string_view kGltfDataPrefix = "data:application/gltf-buffer;base64,";

static_assert(std::endian::native == std::endian::little);

struct CookedMeshHeader
{
    std::array<char, 8> magic{};
    std::uint32_t version = kCookedVersion;
    std::uint32_t vertex_count = 0;
    std::uint32_t index_count = 0;
    std::uint32_t reserved = 0;
    std::array<char, 48> id{};
    std::uint64_t source_hash = 0;
    std::uint64_t payload_hash = 0;
    float bounds_min[3]{};
    float bounds_max[3]{};
};

static_assert(std::is_trivially_copyable_v<CookedMeshHeader>);
static_assert(std::is_trivially_copyable_v<MeshVertex>);
static_assert(sizeof(CookedMeshHeader) == 112);

struct BufferView
{
    std::size_t offset = 0;
    std::size_t length = 0;
    std::size_t stride = 0;
};

struct Accessor
{
    std::uint32_t buffer_view = 0;
    std::uint32_t component_type = 0;
    std::uint32_t count = 0;
    std::size_t byte_offset = 0;
    std::string type{};
};

std::uint64_t HashAppend(
    std::uint64_t hash,
    const void* data,
    const std::size_t size) noexcept
{
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::size_t index = 0; index < size; ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
    return hash;
}

std::uint64_t HashBytes(const void* data, const std::size_t size) noexcept
{
    return HashAppend(kFnvOffsetBasis, data, size);
}

std::uint64_t HashText(const std::string_view source) noexcept
{
    return HashBytes(source.data(), source.size());
}

bool ValidIdentifier(const std::string_view id) noexcept
{
    if (id.empty() || id.size() >= 48)
    {
        return false;
    }
    return std::all_of(
        id.begin(),
        id.end(),
        [](const char value) {
            const unsigned char character = static_cast<unsigned char>(value);
            return (character >= static_cast<unsigned char>('a')
                    && character <= static_cast<unsigned char>('z'))
                || (character >= static_cast<unsigned char>('0')
                    && character <= static_cast<unsigned char>('9'))
                || character == static_cast<unsigned char>('_');
        });
}

bool Finite(const DirectX::XMFLOAT3 value) noexcept
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

std::size_t CheckedAdd(const std::size_t left, const std::size_t right)
{
    if (right > (std::numeric_limits<std::size_t>::max)() - left)
    {
        throw std::runtime_error("glTF byte range overflows addressable memory");
    }
    return left + right;
}

std::size_t CheckedMultiply(const std::size_t left, const std::size_t right)
{
    if (left != 0 && right > (std::numeric_limits<std::size_t>::max)() / left)
    {
        throw std::runtime_error("glTF byte range overflows addressable memory");
    }
    return left * right;
}

std::uint32_t JsonUnsigned(const JsonValue& value, const std::string_view label)
{
    const double number = value.AsNumber();
    if (number < 0.0 || number > static_cast<double>((std::numeric_limits<std::uint32_t>::max)())
        || std::floor(number) != number)
    {
        throw std::runtime_error(std::string(label) + " must be an unsigned integer");
    }
    return static_cast<std::uint32_t>(number);
}

std::size_t OptionalSize(
    const JsonValue::Object& object,
    const std::string_view name,
    const std::size_t fallback)
{
    const JsonValue* value = FindJsonMember(object, name);
    if (value == nullptr)
    {
        return fallback;
    }
    const std::uint32_t parsed = JsonUnsigned(*value, name);
    return static_cast<std::size_t>(parsed);
}

bool OptionalBoolean(
    const JsonValue::Object& object,
    const std::string_view name,
    const bool fallback)
{
    const JsonValue* value = FindJsonMember(object, name);
    return value == nullptr ? fallback : value->AsBoolean();
}

int Base64Value(const char value) noexcept
{
    if (value >= 'A' && value <= 'Z')
    {
        return value - 'A';
    }
    if (value >= 'a' && value <= 'z')
    {
        return value - 'a' + 26;
    }
    if (value >= '0' && value <= '9')
    {
        return value - '0' + 52;
    }
    if (value == '+')
    {
        return 62;
    }
    if (value == '/')
    {
        return 63;
    }
    return -1;
}

std::vector<std::uint8_t> DecodeBase64(const std::string_view encoded)
{
    if (encoded.empty() || encoded.size() % 4U != 0U)
    {
        throw std::runtime_error("glTF base64 buffer length is invalid");
    }

    std::vector<std::uint8_t> output;
    output.reserve(encoded.size() / 4U * 3U);
    for (std::size_t offset = 0; offset < encoded.size(); offset += 4U)
    {
        const char first_char = encoded[offset];
        const char second_char = encoded[offset + 1U];
        const char third_char = encoded[offset + 2U];
        const char fourth_char = encoded[offset + 3U];
        const int first = Base64Value(first_char);
        const int second = Base64Value(second_char);
        const bool third_padding = third_char == '=';
        const bool fourth_padding = fourth_char == '=';
        const int third = third_padding ? 0 : Base64Value(third_char);
        const int fourth = fourth_padding ? 0 : Base64Value(fourth_char);

        if (first < 0 || second < 0 || third < 0 || fourth < 0
            || (third_padding && !fourth_padding)
            || ((third_padding || fourth_padding) && offset + 4U != encoded.size()))
        {
            throw std::runtime_error("glTF base64 buffer contains invalid padding or characters");
        }

        const std::uint32_t packed =
            (static_cast<std::uint32_t>(first) << 18U)
            | (static_cast<std::uint32_t>(second) << 12U)
            | (static_cast<std::uint32_t>(third) << 6U)
            | static_cast<std::uint32_t>(fourth);
        output.push_back(static_cast<std::uint8_t>((packed >> 16U) & 0xFFU));
        if (!third_padding)
        {
            output.push_back(static_cast<std::uint8_t>((packed >> 8U) & 0xFFU));
        }
        if (!fourth_padding)
        {
            output.push_back(static_cast<std::uint8_t>(packed & 0xFFU));
        }
    }
    return output;
}

std::vector<std::uint8_t> DecodeDataUri(const std::string_view uri)
{
    if (uri.starts_with(kDataPrefix))
    {
        return DecodeBase64(uri.substr(kDataPrefix.size()));
    }
    if (uri.starts_with(kGltfDataPrefix))
    {
        return DecodeBase64(uri.substr(kGltfDataPrefix.size()));
    }
    throw std::runtime_error(
        "This glTF tranche supports embedded base64 application/octet-stream buffers only");
}

std::vector<BufferView> ParseBufferViews(
    const JsonValue::Object& root,
    const std::size_t buffer_size)
{
    const JsonValue::Array& source = RequireJsonMember(root, "bufferViews").AsArray();
    if (source.empty() || source.size() > 1'024U)
    {
        throw std::runtime_error("glTF bufferView count is outside supported bounds");
    }

    std::vector<BufferView> views;
    views.reserve(source.size());
    for (const JsonValue& value : source)
    {
        const JsonValue::Object& object = value.AsObject();
        if (JsonUnsigned(RequireJsonMember(object, "buffer"), "bufferView.buffer") != 0U)
        {
            throw std::runtime_error("glTF bufferView references an unsupported buffer");
        }
        const std::size_t offset = OptionalSize(object, "byteOffset", 0);
        const std::size_t length = static_cast<std::size_t>(
            JsonUnsigned(RequireJsonMember(object, "byteLength"), "bufferView.byteLength"));
        const std::size_t stride = OptionalSize(object, "byteStride", 0);
        if (length == 0 || CheckedAdd(offset, length) > buffer_size)
        {
            throw std::runtime_error("glTF bufferView range is outside the embedded buffer");
        }
        if (stride != 0 && (stride < 4 || stride > 252 || stride % 4U != 0U))
        {
            throw std::runtime_error("glTF bufferView byteStride is unsupported");
        }
        views.push_back({.offset = offset, .length = length, .stride = stride});
    }
    return views;
}

std::vector<Accessor> ParseAccessors(const JsonValue::Object& root)
{
    const JsonValue::Array& source = RequireJsonMember(root, "accessors").AsArray();
    if (source.empty() || source.size() > 2'048U)
    {
        throw std::runtime_error("glTF accessor count is outside supported bounds");
    }

    std::vector<Accessor> accessors;
    accessors.reserve(source.size());
    for (const JsonValue& value : source)
    {
        const JsonValue::Object& object = value.AsObject();
        if (FindJsonMember(object, "sparse") != nullptr)
        {
            throw std::runtime_error("Sparse glTF accessors are not supported yet");
        }
        if (OptionalBoolean(object, "normalized", false))
        {
            throw std::runtime_error("Normalized glTF accessors are not supported in static meshes");
        }
        accessors.push_back({
            .buffer_view = JsonUnsigned(
                RequireJsonMember(object, "bufferView"),
                "accessor.bufferView"),
            .component_type = JsonUnsigned(
                RequireJsonMember(object, "componentType"),
                "accessor.componentType"),
            .count = JsonUnsigned(RequireJsonMember(object, "count"), "accessor.count"),
            .byte_offset = OptionalSize(object, "byteOffset", 0),
            .type = RequireJsonMember(object, "type").AsString(),
        });
        if (accessors.back().count == 0U)
        {
            throw std::runtime_error("glTF accessors cannot be empty");
        }
    }
    return accessors;
}

const Accessor& CheckedAccessor(
    const std::vector<Accessor>& accessors,
    const std::uint32_t index)
{
    if (index >= accessors.size())
    {
        throw std::runtime_error("glTF primitive references an invalid accessor");
    }
    return accessors[index];
}

const BufferView& CheckedView(
    const std::vector<BufferView>& views,
    const std::uint32_t index)
{
    if (index >= views.size())
    {
        throw std::runtime_error("glTF accessor references an invalid bufferView");
    }
    return views[index];
}

std::size_t CheckedElementEnd(
    const Accessor& accessor,
    const std::size_t element_size,
    const std::size_t stride)
{
    if (stride < element_size)
    {
        throw std::runtime_error("glTF accessor stride is smaller than its element");
    }
    const std::size_t last_offset = accessor.count == 0U
        ? 0
        : CheckedMultiply(static_cast<std::size_t>(accessor.count - 1U), stride);
    return CheckedAdd(CheckedAdd(accessor.byte_offset, last_offset), element_size);
}

float ReadFloat(const std::uint8_t* bytes)
{
    float value = 0.0f;
    std::memcpy(&value, bytes, sizeof(value));
    if (!std::isfinite(value))
    {
        throw std::runtime_error("glTF mesh contains a non-finite float");
    }
    return value;
}

std::vector<DirectX::XMFLOAT3> ReadFloatVec3(
    const std::vector<std::uint8_t>& buffer,
    const std::vector<BufferView>& views,
    const Accessor& accessor,
    const std::string_view semantic)
{
    if (accessor.component_type != 5126U || accessor.type != "VEC3")
    {
        throw std::runtime_error(std::string(semantic) + " must be a FLOAT VEC3 accessor");
    }
    const BufferView& view = CheckedView(views, accessor.buffer_view);
    constexpr std::size_t element_size = sizeof(float) * 3U;
    const std::size_t stride = view.stride == 0 ? element_size : view.stride;
    if (CheckedElementEnd(accessor, element_size, stride) > view.length)
    {
        throw std::runtime_error(std::string(semantic) + " accessor exceeds its bufferView");
    }

    std::vector<DirectX::XMFLOAT3> values;
    values.reserve(accessor.count);
    const std::size_t first = CheckedAdd(view.offset, accessor.byte_offset);
    for (std::uint32_t index = 0; index < accessor.count; ++index)
    {
        const std::size_t offset = CheckedAdd(first, CheckedMultiply(index, stride));
        values.push_back({
            ReadFloat(buffer.data() + offset),
            ReadFloat(buffer.data() + offset + sizeof(float)),
            ReadFloat(buffer.data() + offset + sizeof(float) * 2U),
        });
    }
    return values;
}

std::vector<std::uint32_t> ReadIndices(
    const std::vector<std::uint8_t>& buffer,
    const std::vector<BufferView>& views,
    const Accessor& accessor)
{
    if (accessor.type != "SCALAR")
    {
        throw std::runtime_error("glTF indices must use a SCALAR accessor");
    }
    std::size_t element_size = 0;
    if (accessor.component_type == 5121U)
    {
        element_size = 1;
    }
    else if (accessor.component_type == 5123U)
    {
        element_size = 2;
    }
    else if (accessor.component_type == 5125U)
    {
        element_size = 4;
    }
    else
    {
        throw std::runtime_error("glTF indices must use UNSIGNED_BYTE, UNSIGNED_SHORT, or UNSIGNED_INT");
    }

    const BufferView& view = CheckedView(views, accessor.buffer_view);
    const std::size_t stride = view.stride == 0 ? element_size : view.stride;
    if (CheckedElementEnd(accessor, element_size, stride) > view.length)
    {
        throw std::runtime_error("glTF index accessor exceeds its bufferView");
    }

    std::vector<std::uint32_t> indices;
    indices.reserve(accessor.count);
    const std::size_t first = CheckedAdd(view.offset, accessor.byte_offset);
    for (std::uint32_t index = 0; index < accessor.count; ++index)
    {
        const std::size_t offset = CheckedAdd(first, CheckedMultiply(index, stride));
        std::uint32_t value = 0;
        if (element_size == 1)
        {
            value = buffer[offset];
        }
        else if (element_size == 2)
        {
            std::uint16_t decoded = 0;
            std::memcpy(&decoded, buffer.data() + offset, sizeof(decoded));
            value = decoded;
        }
        else
        {
            std::memcpy(&value, buffer.data() + offset, sizeof(value));
        }
        indices.push_back(value);
    }
    return indices;
}

void ComputeBounds(StaticMesh& mesh)
{
    if (mesh.vertices.empty())
    {
        throw std::runtime_error("Static meshes cannot be empty");
    }
    DirectX::XMFLOAT3 minimum = mesh.vertices.front().position;
    DirectX::XMFLOAT3 maximum = mesh.vertices.front().position;
    for (const MeshVertex& vertex : mesh.vertices)
    {
        minimum.x = (std::min)(minimum.x, vertex.position.x);
        minimum.y = (std::min)(minimum.y, vertex.position.y);
        minimum.z = (std::min)(minimum.z, vertex.position.z);
        maximum.x = (std::max)(maximum.x, vertex.position.x);
        maximum.y = (std::max)(maximum.y, vertex.position.y);
        maximum.z = (std::max)(maximum.z, vertex.position.z);
    }
    mesh.bounds_min = minimum;
    mesh.bounds_max = maximum;
}

void ValidateMesh(const StaticMesh& mesh)
{
    if (!ValidIdentifier(mesh.id))
    {
        throw std::runtime_error("Static mesh identifier is invalid");
    }
    if (mesh.vertices.empty() || mesh.vertices.size() > kMaximumVertices)
    {
        throw std::runtime_error("Static mesh vertex count is outside supported bounds");
    }
    if (mesh.indices.empty() || mesh.indices.size() > kMaximumIndices
        || mesh.indices.size() % 3U != 0U)
    {
        throw std::runtime_error("Static mesh indices must contain bounded triangle lists");
    }
    if (!Finite(mesh.bounds_min) || !Finite(mesh.bounds_max)
        || mesh.bounds_min.x > mesh.bounds_max.x
        || mesh.bounds_min.y > mesh.bounds_max.y
        || mesh.bounds_min.z > mesh.bounds_max.z)
    {
        throw std::runtime_error("Static mesh bounds are invalid");
    }
    for (const MeshVertex& vertex : mesh.vertices)
    {
        if (!Finite(vertex.position) || !Finite(vertex.normal) || !Finite(vertex.color))
        {
            throw std::runtime_error("Static mesh contains non-finite vertex data");
        }
        const float normal_length_squared = vertex.normal.x * vertex.normal.x
            + vertex.normal.y * vertex.normal.y + vertex.normal.z * vertex.normal.z;
        if (normal_length_squared < 0.25f || normal_length_squared > 1.75f)
        {
            throw std::runtime_error("Static mesh contains an invalid normal");
        }
    }
    for (std::size_t index = 0; index < mesh.indices.size(); index += 3U)
    {
        const std::uint32_t first = mesh.indices[index];
        const std::uint32_t second = mesh.indices[index + 1U];
        const std::uint32_t third = mesh.indices[index + 2U];
        if (first >= mesh.vertices.size() || second >= mesh.vertices.size()
            || third >= mesh.vertices.size())
        {
            throw std::runtime_error("Static mesh index is outside the vertex buffer");
        }
        if (first == second || second == third || first == third)
        {
            throw std::runtime_error("Static mesh contains a degenerate indexed triangle");
        }
    }
}

std::uint64_t MeshPayloadHash(const StaticMesh& mesh) noexcept
{
    std::uint64_t hash = HashAppend(
        kFnvOffsetBasis,
        mesh.vertices.data(),
        mesh.vertices.size() * sizeof(MeshVertex));
    return HashAppend(
        hash,
        mesh.indices.data(),
        mesh.indices.size() * sizeof(std::uint32_t));
}

std::filesystem::path AppendedPath(
    const std::filesystem::path& path,
    const wchar_t* suffix)
{
    std::filesystem::path result = path;
    result += suffix;
    return result;
}
} // namespace

StaticMesh ParseGltfStaticMesh(
    const std::string_view mesh_id,
    const std::string_view source)
{
    if (!ValidIdentifier(mesh_id))
    {
        throw std::invalid_argument("glTF mesh identifier is invalid");
    }
    const JsonValue::Object& root = ParseJson(source).AsObject();
    const JsonValue::Object& asset = RequireJsonMember(root, "asset").AsObject();
    if (RequireJsonMember(asset, "version").AsString() != "2.0")
    {
        throw std::runtime_error("Only glTF 2.0 static meshes are supported");
    }

    const JsonValue::Array& buffers = RequireJsonMember(root, "buffers").AsArray();
    if (buffers.size() != 1U)
    {
        throw std::runtime_error("This glTF tranche requires exactly one embedded buffer");
    }
    const JsonValue::Object& buffer_object = buffers.front().AsObject();
    const std::uint32_t declared_length = JsonUnsigned(
        RequireJsonMember(buffer_object, "byteLength"),
        "buffer.byteLength");
    const std::vector<std::uint8_t> buffer = DecodeDataUri(
        RequireJsonMember(buffer_object, "uri").AsString());
    if (buffer.size() != declared_length)
    {
        throw std::runtime_error("glTF embedded buffer length does not match byteLength");
    }

    const std::vector<BufferView> views = ParseBufferViews(root, buffer.size());
    const std::vector<Accessor> accessors = ParseAccessors(root);
    const JsonValue::Array& meshes = RequireJsonMember(root, "meshes").AsArray();
    if (meshes.size() != 1U)
    {
        throw std::runtime_error("This glTF tranche requires exactly one mesh");
    }
    const JsonValue::Array& primitives = RequireJsonMember(
        meshes.front().AsObject(),
        "primitives").AsArray();
    if (primitives.size() != 1U)
    {
        throw std::runtime_error("This glTF tranche requires exactly one mesh primitive");
    }
    const JsonValue::Object& primitive = primitives.front().AsObject();
    const JsonValue* mode = FindJsonMember(primitive, "mode");
    if (mode != nullptr && JsonUnsigned(*mode, "primitive.mode") != 4U)
    {
        throw std::runtime_error("glTF static meshes must use TRIANGLES mode");
    }
    if (FindJsonMember(primitive, "targets") != nullptr)
    {
        throw std::runtime_error("glTF morph targets are not supported in static meshes");
    }

    const JsonValue::Object& attributes = RequireJsonMember(primitive, "attributes").AsObject();
    const std::uint32_t position_index = JsonUnsigned(
        RequireJsonMember(attributes, "POSITION"),
        "primitive.attributes.POSITION");
    const std::uint32_t normal_index = JsonUnsigned(
        RequireJsonMember(attributes, "NORMAL"),
        "primitive.attributes.NORMAL");
    const std::uint32_t index_index = JsonUnsigned(
        RequireJsonMember(primitive, "indices"),
        "primitive.indices");

    const Accessor& position_accessor = CheckedAccessor(accessors, position_index);
    const Accessor& normal_accessor = CheckedAccessor(accessors, normal_index);
    const Accessor& index_accessor = CheckedAccessor(accessors, index_index);
    if (position_accessor.count != normal_accessor.count
        || position_accessor.count > kMaximumVertices
        || index_accessor.count > kMaximumIndices)
    {
        throw std::runtime_error("glTF static mesh accessor counts are inconsistent or excessive");
    }

    const std::vector<DirectX::XMFLOAT3> positions = ReadFloatVec3(
        buffer,
        views,
        position_accessor,
        "POSITION");
    std::vector<DirectX::XMFLOAT3> normals = ReadFloatVec3(
        buffer,
        views,
        normal_accessor,
        "NORMAL");
    std::vector<std::uint32_t> indices = ReadIndices(buffer, views, index_accessor);

    StaticMesh mesh{};
    mesh.id = std::string(mesh_id);
    mesh.source_hash = HashText(source);
    mesh.vertices.reserve(positions.size());
    for (std::size_t index = 0; index < positions.size(); ++index)
    {
        DirectX::XMFLOAT3 normal = normals[index];
        const float length_squared = normal.x * normal.x + normal.y * normal.y + normal.z * normal.z;
        if (!std::isfinite(length_squared) || length_squared <= 1.0e-8f)
        {
            throw std::runtime_error("glTF NORMAL accessor contains a zero or invalid normal");
        }
        const float inverse_length = 1.0f / std::sqrt(length_squared);
        normal.x *= inverse_length;
        normal.y *= inverse_length;
        normal.z *= inverse_length;
        mesh.vertices.push_back({
            .position = positions[index],
            .normal = normal,
            .color = {1.0f, 1.0f, 1.0f},
        });
    }
    mesh.indices = std::move(indices);
    ComputeBounds(mesh);
    ValidateMesh(mesh);
    return mesh;
}

void WriteCookedMesh(const std::filesystem::path& path, const StaticMesh& mesh)
{
    ValidateMesh(mesh);
    if (path.empty())
    {
        throw std::invalid_argument("Cooked mesh path cannot be empty");
    }
    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path());
    }

    CookedMeshHeader header{};
    header.magic = kMagic;
    header.vertex_count = static_cast<std::uint32_t>(mesh.vertices.size());
    header.index_count = static_cast<std::uint32_t>(mesh.indices.size());
    std::memcpy(header.id.data(), mesh.id.data(), mesh.id.size());
    header.source_hash = mesh.source_hash;
    header.payload_hash = MeshPayloadHash(mesh);
    header.bounds_min[0] = mesh.bounds_min.x;
    header.bounds_min[1] = mesh.bounds_min.y;
    header.bounds_min[2] = mesh.bounds_min.z;
    header.bounds_max[0] = mesh.bounds_max.x;
    header.bounds_max[1] = mesh.bounds_max.y;
    header.bounds_max[2] = mesh.bounds_max.z;

    const std::filesystem::path temporary = AppendedPath(path, L".tmp");
    const std::filesystem::path backup = AppendedPath(path, L".bak");
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output)
        {
            throw std::runtime_error("Could not create cooked mesh temporary file");
        }
        output.write(reinterpret_cast<const char*>(&header), sizeof(header));
        output.write(
            reinterpret_cast<const char*>(mesh.vertices.data()),
            static_cast<std::streamsize>(mesh.vertices.size() * sizeof(MeshVertex)));
        output.write(
            reinterpret_cast<const char*>(mesh.indices.data()),
            static_cast<std::streamsize>(mesh.indices.size() * sizeof(std::uint32_t)));
        output.flush();
        if (!output)
        {
            throw std::runtime_error("Could not write cooked mesh package");
        }
    }

    std::error_code error;
    std::filesystem::remove(backup, error);
    error.clear();
    if (std::filesystem::exists(path))
    {
        std::filesystem::rename(path, backup, error);
        if (error)
        {
            std::filesystem::remove(temporary);
            throw std::runtime_error("Could not rotate cooked mesh backup");
        }
    }
    std::filesystem::rename(temporary, path, error);
    if (error)
    {
        if (std::filesystem::exists(backup))
        {
            std::error_code restore_error;
            std::filesystem::rename(backup, path, restore_error);
        }
        std::filesystem::remove(temporary);
        throw std::runtime_error("Could not commit cooked mesh package");
    }
}

StaticMesh LoadCookedMesh(const std::filesystem::path& path)
{
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input)
    {
        throw std::runtime_error("Could not open cooked mesh: " + path.string());
    }
    const std::streamoff file_size = input.tellg();
    if (file_size < static_cast<std::streamoff>(sizeof(CookedMeshHeader)))
    {
        throw std::runtime_error("Cooked mesh is truncated");
    }
    input.seekg(0, std::ios::beg);

    CookedMeshHeader header{};
    input.read(reinterpret_cast<char*>(&header), sizeof(header));
    if (!input || header.magic != kMagic || header.version != kCookedVersion
        || header.reserved != 0U || header.vertex_count == 0U
        || header.vertex_count > kMaximumVertices || header.index_count == 0U
        || header.index_count > kMaximumIndices || header.index_count % 3U != 0U)
    {
        throw std::runtime_error("Cooked mesh header is invalid");
    }

    const std::uint64_t vertex_bytes =
        static_cast<std::uint64_t>(header.vertex_count) * sizeof(MeshVertex);
    const std::uint64_t index_bytes =
        static_cast<std::uint64_t>(header.index_count) * sizeof(std::uint32_t);
    const std::uint64_t expected_size = sizeof(CookedMeshHeader) + vertex_bytes + index_bytes;
    if (file_size != static_cast<std::streamoff>(expected_size))
    {
        throw std::runtime_error("Cooked mesh size does not match its header");
    }

    const auto terminator = std::find(header.id.begin(), header.id.end(), '\0');
    if (terminator == header.id.end() || terminator == header.id.begin())
    {
        throw std::runtime_error("Cooked mesh identifier is invalid");
    }

    StaticMesh mesh{};
    mesh.id = std::string(header.id.begin(), terminator);
    mesh.source_hash = header.source_hash;
    mesh.bounds_min = {header.bounds_min[0], header.bounds_min[1], header.bounds_min[2]};
    mesh.bounds_max = {header.bounds_max[0], header.bounds_max[1], header.bounds_max[2]};
    mesh.vertices.resize(header.vertex_count);
    mesh.indices.resize(header.index_count);
    input.read(
        reinterpret_cast<char*>(mesh.vertices.data()),
        static_cast<std::streamsize>(vertex_bytes));
    input.read(
        reinterpret_cast<char*>(mesh.indices.data()),
        static_cast<std::streamsize>(index_bytes));
    if (!input)
    {
        throw std::runtime_error("Could not read cooked mesh payload");
    }
    if (header.payload_hash != MeshPayloadHash(mesh))
    {
        throw std::runtime_error("Cooked mesh payload checksum mismatch");
    }
    ValidateMesh(mesh);
    return mesh;
}

void CookGltfMeshFile(
    const std::string_view mesh_id,
    const std::filesystem::path& source_path,
    const std::filesystem::path& output_path)
{
    std::ifstream input(source_path, std::ios::binary);
    if (!input)
    {
        throw std::runtime_error("Could not open glTF mesh source: " + source_path.string());
    }
    const std::string source{
        std::istreambuf_iterator<char>{input},
        std::istreambuf_iterator<char>{}};
    WriteCookedMesh(output_path, ParseGltfStaticMesh(mesh_id, source));
}

StaticMesh MakeCubeMesh()
{
    const std::array<MeshVertex, 24> vertices = {{
        {{-1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, -1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, 0.0f, 1.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, -1.0f}, {-1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, 1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{-1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, -1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
        {{1.0f, -1.0f, 1.0f}, {0.0f, -1.0f, 0.0f}, {1.0f, 1.0f, 1.0f}},
    }};
    constexpr std::array<std::uint32_t, 36> indices = {
        0, 1, 2, 0, 2, 3,
        4, 5, 6, 4, 6, 7,
        8, 9, 10, 8, 10, 11,
        12, 13, 14, 12, 14, 15,
        16, 17, 18, 16, 18, 19,
        20, 21, 22, 20, 22, 23,
    };

    StaticMesh mesh{};
    mesh.id = "cube";
    mesh.source_hash = HashText("builtin:cube:v1");
    mesh.vertices.assign(vertices.begin(), vertices.end());
    mesh.indices.assign(indices.begin(), indices.end());
    ComputeBounds(mesh);
    ValidateMesh(mesh);
    return mesh;
}

std::size_t FindMeshIndex(
    const std::span<const StaticMesh> meshes,
    const std::string_view mesh_id)
{
    std::size_t found = meshes.size();
    for (std::size_t index = 0; index < meshes.size(); ++index)
    {
        if (meshes[index].id == mesh_id)
        {
            if (found != meshes.size())
            {
                throw std::runtime_error("Mesh catalog contains a duplicate identifier");
            }
            found = index;
        }
    }
    if (found == meshes.size())
    {
        throw std::runtime_error("Scene references an unavailable mesh: " + std::string(mesh_id));
    }
    return found;
}
} // namespace mars::assets
