#include "assets/scene_asset.h"
#include "renderer/procedural_catalog.h"

#include <algorithm>
#include <array>
#include <bit>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <system_error>
#include <type_traits>
#include <unordered_set>
#include <utility>
#include <vector>

namespace mars::assets
{
namespace
{
constexpr std::array<char, 8> kMagic = {'M', 'A', 'R', 'S', 'C', 'N', '3', '\0'};
constexpr std::uint32_t kCookedVersion = 3;
constexpr std::uint32_t kMaximumEntities = 512;
constexpr std::uint32_t kMeshFlags = SceneEntityMeshRock | SceneEntityMeshColumn
    | SceneEntityMeshTerrain;
constexpr std::uint32_t kKnownFlags = SceneEntityRender | SceneEntityCollider
    | SceneEntityPlayer | SceneEntityCheckpoint | SceneEntityObjective | kMeshFlags;
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

struct CookedHeader
{
    std::array<char, 8> magic{};
    std::uint32_t version = kCookedVersion;
    std::uint32_t entity_count = 0;
    std::uint64_t source_hash = 0;
    std::uint64_t payload_hash = 0;
    std::uint32_t manifest_schema_version = ContentManifest::kSchemaVersion;
    std::uint32_t reserved = 0;
    std::array<std::uint64_t, ContentManifest::kMeshCount> mesh_hashes{};
    std::uint64_t mesh_catalog_hash = 0;
    std::uint64_t composition_hash = 0;
    std::uint64_t aggregate_hash = 0;
};

struct CookedEntity
{
    std::array<char, 48> id{};
    std::uint32_t flags = SceneEntityNone;
    float position[3]{};
    float scale[3]{};
    float tint[4]{};
};

static_assert(std::is_trivially_copyable_v<CookedHeader>);
static_assert(std::is_trivially_copyable_v<CookedEntity>);
static_assert(sizeof(CookedHeader) == 120);
static_assert(sizeof(CookedEntity) == 92);

void HashAppend(std::uint64_t& hash, const void* data, const std::size_t size) noexcept
{
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::size_t index = 0; index < size; ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
}

std::uint64_t HashBytes(const void* data, const std::size_t size) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    HashAppend(hash, data, size);
    return hash;
}

void HashFloat(std::uint64_t& hash, const float value) noexcept
{
    const std::uint32_t bits = std::bit_cast<std::uint32_t>(value);
    HashAppend(hash, &bits, sizeof(bits));
}

std::uint64_t HashText(const std::string_view source) noexcept
{
    return HashBytes(source.data(), source.size());
}

bool Finite(const DirectX::XMFLOAT3 value) noexcept
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

bool Finite(const DirectX::XMFLOAT4 value) noexcept
{
    return std::isfinite(value.x) && std::isfinite(value.y)
        && std::isfinite(value.z) && std::isfinite(value.w);
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
            return std::islower(character) != 0 || std::isdigit(character) != 0
                || character == static_cast<unsigned char>('_');
        });
}

std::uint32_t FlagForToken(const std::string_view token)
{
    if (token == "render")
    {
        return SceneEntityRender;
    }
    if (token == "collider")
    {
        return SceneEntityCollider;
    }
    if (token == "player")
    {
        return SceneEntityPlayer;
    }
    if (token == "checkpoint")
    {
        return SceneEntityCheckpoint;
    }
    if (token == "objective")
    {
        return SceneEntityObjective;
    }
    if (token == "mesh_rock")
    {
        return SceneEntityMeshRock;
    }
    if (token == "mesh_column")
    {
        return SceneEntityMeshColumn;
    }
    if (token == "mesh_terrain")
    {
        return SceneEntityMeshTerrain;
    }
    throw std::runtime_error("Unknown scene entity flag: " + std::string(token));
}

std::uint32_t ParseFlags(const std::string_view text)
{
    if (text == "none")
    {
        return SceneEntityNone;
    }

    std::uint32_t flags = SceneEntityNone;
    std::size_t start = 0;
    while (start < text.size())
    {
        const std::size_t separator = text.find(',', start);
        const std::string_view token = text.substr(
            start,
            separator == std::string_view::npos ? text.size() - start : separator - start);
        const std::uint32_t flag = FlagForToken(token);
        if ((flags & flag) != 0U)
        {
            throw std::runtime_error("Duplicate scene entity flag: " + std::string(token));
        }
        flags |= flag;
        if (separator == std::string_view::npos)
        {
            break;
        }
        start = separator + 1;
    }
    return flags;
}

void ValidateDefinition(const SceneDefinition& scene)
{
    if (scene.schema_version != SceneDefinition::kSchemaVersion)
    {
        throw std::runtime_error("Unsupported scene schema version");
    }
    if (scene.entities.empty() || scene.entities.size() > kMaximumEntities)
    {
        throw std::runtime_error("Scene entity count is outside supported bounds");
    }

    std::unordered_set<std::string> ids;
    std::uint32_t players = 0;
    std::uint32_t checkpoints = 0;
    std::uint32_t objectives = 0;
    for (const SceneEntity& entity : scene.entities)
    {
        if (!ValidIdentifier(entity.id) || !ids.insert(entity.id).second)
        {
            throw std::runtime_error("Scene contains an invalid or duplicate entity id");
        }
        if ((entity.flags & ~kKnownFlags) != 0U)
        {
            throw std::runtime_error("Scene contains unknown entity flags");
        }
        const std::uint32_t mesh_flags = entity.flags & kMeshFlags;
        if (mesh_flags != 0U && (mesh_flags & (mesh_flags - 1U)) != 0U)
        {
            throw std::runtime_error("Scene entity selects multiple generated mesh kinds");
        }
        if (mesh_flags != 0U && (entity.flags & SceneEntityRender) == 0U)
        {
            throw std::runtime_error("Generated mesh selection requires a renderable entity");
        }
        if (!Finite(entity.position) || !Finite(entity.scale) || !Finite(entity.tint))
        {
            throw std::runtime_error("Scene contains non-finite transform or tint values");
        }
        if ((entity.flags & (SceneEntityRender | SceneEntityCollider)) != 0U
            && (entity.scale.x <= 0.0f || entity.scale.y <= 0.0f || entity.scale.z <= 0.0f))
        {
            throw std::runtime_error("Renderable and collidable entities require positive scale");
        }
        if ((entity.flags & SceneEntityCollider) != 0U
            && (entity.flags & SceneEntityRender) == 0U)
        {
            throw std::runtime_error("Current scene colliders must have visible geometry");
        }
        players += (entity.flags & SceneEntityPlayer) != 0U ? 1U : 0U;
        checkpoints += (entity.flags & SceneEntityCheckpoint) != 0U ? 1U : 0U;
        objectives += (entity.flags & SceneEntityObjective) != 0U ? 1U : 0U;
    }
    if (players != 1U || checkpoints != 1U || objectives != 1U)
    {
        throw std::runtime_error("Scene requires exactly one player, checkpoint, and objective entity");
    }
}

std::uint64_t HashComposition(const SceneDefinition& scene) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    HashAppend(hash, &scene.schema_version, sizeof(scene.schema_version));
    HashAppend(hash, &scene.source_hash, sizeof(scene.source_hash));
    const std::uint64_t entity_count = static_cast<std::uint64_t>(scene.entities.size());
    HashAppend(hash, &entity_count, sizeof(entity_count));
    for (const SceneEntity& entity : scene.entities)
    {
        const std::uint64_t id_size = static_cast<std::uint64_t>(entity.id.size());
        HashAppend(hash, &id_size, sizeof(id_size));
        HashAppend(hash, entity.id.data(), entity.id.size());
        HashAppend(hash, &entity.flags, sizeof(entity.flags));
        HashFloat(hash, entity.position.x);
        HashFloat(hash, entity.position.y);
        HashFloat(hash, entity.position.z);
        HashFloat(hash, entity.scale.x);
        HashFloat(hash, entity.scale.y);
        HashFloat(hash, entity.scale.z);
        HashFloat(hash, entity.tint.x);
        HashFloat(hash, entity.tint.y);
        HashFloat(hash, entity.tint.z);
        HashFloat(hash, entity.tint.w);
    }
    return hash;
}

CookedEntity ToCooked(const SceneEntity& entity)
{
    CookedEntity record{};
    std::memcpy(record.id.data(), entity.id.data(), entity.id.size());
    record.flags = entity.flags;
    record.position[0] = entity.position.x;
    record.position[1] = entity.position.y;
    record.position[2] = entity.position.z;
    record.scale[0] = entity.scale.x;
    record.scale[1] = entity.scale.y;
    record.scale[2] = entity.scale.z;
    record.tint[0] = entity.tint.x;
    record.tint[1] = entity.tint.y;
    record.tint[2] = entity.tint.z;
    record.tint[3] = entity.tint.w;
    return record;
}

SceneEntity FromCooked(const CookedEntity& record)
{
    const auto terminator = std::find(record.id.begin(), record.id.end(), '\0');
    if (terminator == record.id.end() || terminator == record.id.begin())
    {
        throw std::runtime_error("Cooked scene contains an invalid entity id");
    }
    return {
        .id = std::string(record.id.begin(), terminator),
        .flags = record.flags,
        .position = {record.position[0], record.position[1], record.position[2]},
        .scale = {record.scale[0], record.scale[1], record.scale[2]},
        .tint = {record.tint[0], record.tint[1], record.tint[2], record.tint[3]},
    };
}
} // namespace

bool HasFlag(const SceneEntity& entity, const SceneEntityFlag flag) noexcept
{
    return (entity.flags & static_cast<std::uint32_t>(flag)) != 0U;
}

SceneMeshKind MeshKindForEntity(const SceneEntity& entity) noexcept
{
    if (HasFlag(entity, SceneEntityMeshTerrain))
    {
        return SceneMeshKind::TerrainPatch;
    }
    if (HasFlag(entity, SceneEntityMeshRock))
    {
        return SceneMeshKind::MarsRock;
    }
    if (HasFlag(entity, SceneEntityMeshColumn))
    {
        return SceneMeshKind::BeaconColumn;
    }
    return SceneMeshKind::Cube;
}

ContentManifest BuildContentManifest(const SceneDefinition& scene)
{
    ValidateDefinition(scene);
    static_assert(ContentManifest::kMeshCount == renderer::kProceduralMeshCount);
    static_assert(static_cast<std::size_t>(SceneMeshKind::Cube)
        == static_cast<std::size_t>(renderer::ProceduralMeshSlot::Cube));
    static_assert(static_cast<std::size_t>(SceneMeshKind::MarsRock)
        == static_cast<std::size_t>(renderer::ProceduralMeshSlot::MarsRock));
    static_assert(static_cast<std::size_t>(SceneMeshKind::BeaconColumn)
        == static_cast<std::size_t>(renderer::ProceduralMeshSlot::BeaconColumn));
    static_assert(static_cast<std::size_t>(SceneMeshKind::TerrainPatch)
        == static_cast<std::size_t>(renderer::ProceduralMeshSlot::TerrainPatch));

    const renderer::ProceduralMeshCatalog catalog = renderer::GenerateProceduralMeshCatalog();
    ContentManifest manifest{};
    manifest.scene_source_hash = scene.source_hash;
    manifest.mesh_hashes = catalog.mesh_hashes;
    manifest.mesh_catalog_hash = catalog.aggregate_hash;
    manifest.composition_hash = HashComposition(scene);

    std::uint64_t aggregate = kFnvOffsetBasis;
    HashAppend(aggregate, &manifest.schema_version, sizeof(manifest.schema_version));
    HashAppend(aggregate, &manifest.scene_source_hash, sizeof(manifest.scene_source_hash));
    HashAppend(
        aggregate,
        manifest.mesh_hashes.data(),
        manifest.mesh_hashes.size() * sizeof(manifest.mesh_hashes.front()));
    HashAppend(aggregate, &manifest.mesh_catalog_hash, sizeof(manifest.mesh_catalog_hash));
    HashAppend(aggregate, &manifest.composition_hash, sizeof(manifest.composition_hash));
    manifest.aggregate_hash = aggregate;
    return manifest;
}

SceneDefinition ParseSceneSource(const std::string_view source)
{
    SceneDefinition scene{};
    scene.source_hash = HashText(source);

    bool header_seen = false;
    std::istringstream input{std::string(source)};
    std::string line;
    std::uint32_t line_number = 0;
    while (std::getline(input, line))
    {
        ++line_number;
        const std::size_t comment = line.find('#');
        if (comment != std::string::npos)
        {
            line.erase(comment);
        }
        std::istringstream tokens(line);
        std::string command;
        if (!(tokens >> command))
        {
            continue;
        }

        if (command == "mars_scene")
        {
            if (header_seen || !scene.entities.empty())
            {
                throw std::runtime_error("Scene header must appear exactly once before entities");
            }
            std::uint32_t version = 0;
            std::string trailing;
            if (!(tokens >> version) || (tokens >> trailing))
            {
                throw std::runtime_error("Malformed scene header at line " + std::to_string(line_number));
            }
            if (version != SceneDefinition::kSchemaVersion)
            {
                throw std::runtime_error("Unsupported source scene schema");
            }
            scene.schema_version = version;
            header_seen = true;
            continue;
        }

        if (command != "entity" || !header_seen)
        {
            throw std::runtime_error("Unexpected scene command at line " + std::to_string(line_number));
        }

        SceneEntity entity{};
        std::string flags;
        std::string trailing;
        if (!(tokens >> entity.id >> flags
              >> entity.position.x >> entity.position.y >> entity.position.z
              >> entity.scale.x >> entity.scale.y >> entity.scale.z
              >> entity.tint.x >> entity.tint.y >> entity.tint.z >> entity.tint.w)
            || (tokens >> trailing))
        {
            throw std::runtime_error("Malformed scene entity at line " + std::to_string(line_number));
        }
        entity.flags = ParseFlags(flags);
        scene.entities.push_back(std::move(entity));
    }

    if (!header_seen)
    {
        throw std::runtime_error("Scene source is missing its schema header");
    }
    std::sort(
        scene.entities.begin(),
        scene.entities.end(),
        [](const SceneEntity& left, const SceneEntity& right) { return left.id < right.id; });
    ValidateDefinition(scene);
    scene.content_manifest = BuildContentManifest(scene);
    return scene;
}

void WriteCookedScene(const std::filesystem::path& path, const SceneDefinition& scene)
{
    ValidateDefinition(scene);
    const ContentManifest manifest = BuildContentManifest(scene);
    if (path.empty())
    {
        throw std::invalid_argument("Cooked scene path cannot be empty");
    }
    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path());
    }

    std::vector<CookedEntity> records;
    records.reserve(scene.entities.size());
    for (const SceneEntity& entity : scene.entities)
    {
        records.push_back(ToCooked(entity));
    }

    CookedHeader header{};
    header.magic = kMagic;
    header.entity_count = static_cast<std::uint32_t>(records.size());
    header.source_hash = scene.source_hash;
    header.payload_hash = HashBytes(records.data(), records.size() * sizeof(CookedEntity));
    header.manifest_schema_version = manifest.schema_version;
    header.mesh_hashes = manifest.mesh_hashes;
    header.mesh_catalog_hash = manifest.mesh_catalog_hash;
    header.composition_hash = manifest.composition_hash;
    header.aggregate_hash = manifest.aggregate_hash;

    const std::filesystem::path temporary = path.string() + ".tmp";
    const std::filesystem::path backup = path.string() + ".bak";
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output)
        {
            throw std::runtime_error("Could not create cooked scene temporary file");
        }
        output.write(reinterpret_cast<const char*>(&header), sizeof(header));
        output.write(
            reinterpret_cast<const char*>(records.data()),
            static_cast<std::streamsize>(records.size() * sizeof(CookedEntity)));
        output.flush();
        if (!output)
        {
            throw std::runtime_error("Could not write cooked scene package");
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
            throw std::runtime_error("Could not rotate cooked scene backup");
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
        throw std::runtime_error("Could not commit cooked scene package");
    }
}

SceneDefinition LoadCookedScene(const std::filesystem::path& path)
{
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input)
    {
        throw std::runtime_error("Could not open cooked scene: " + path.string());
    }
    const std::streamoff file_size = input.tellg();
    if (file_size < static_cast<std::streamoff>(sizeof(CookedHeader)))
    {
        throw std::runtime_error("Cooked scene is truncated");
    }
    input.seekg(0, std::ios::beg);

    CookedHeader header{};
    input.read(reinterpret_cast<char*>(&header), sizeof(header));
    if (!input || header.magic != kMagic || header.version != kCookedVersion
        || header.entity_count == 0U || header.entity_count > kMaximumEntities
        || header.reserved != 0U)
    {
        throw std::runtime_error("Cooked scene header is invalid");
    }
    const std::uint64_t expected_size = sizeof(CookedHeader)
        + static_cast<std::uint64_t>(header.entity_count) * sizeof(CookedEntity);
    if (file_size != static_cast<std::streamoff>(expected_size))
    {
        throw std::runtime_error("Cooked scene size does not match its header");
    }

    std::vector<CookedEntity> records(header.entity_count);
    input.read(
        reinterpret_cast<char*>(records.data()),
        static_cast<std::streamsize>(records.size() * sizeof(CookedEntity)));
    if (!input)
    {
        throw std::runtime_error("Could not read cooked scene payload");
    }
    if (header.payload_hash != HashBytes(records.data(), records.size() * sizeof(CookedEntity)))
    {
        throw std::runtime_error("Cooked scene payload checksum mismatch");
    }

    SceneDefinition scene{};
    scene.source_hash = header.source_hash;
    scene.entities.reserve(records.size());
    for (const CookedEntity& record : records)
    {
        scene.entities.push_back(FromCooked(record));
    }
    ValidateDefinition(scene);
    const ContentManifest expected_manifest = BuildContentManifest(scene);
    if (header.manifest_schema_version != expected_manifest.schema_version
        || header.mesh_hashes != expected_manifest.mesh_hashes
        || header.mesh_catalog_hash != expected_manifest.mesh_catalog_hash
        || header.composition_hash != expected_manifest.composition_hash
        || header.aggregate_hash != expected_manifest.aggregate_hash)
    {
        throw std::runtime_error("Cooked scene content manifest mismatch");
    }
    scene.content_manifest = expected_manifest;
    return scene;
}

void CookSceneFile(
    const std::filesystem::path& source_path,
    const std::filesystem::path& output_path)
{
    std::ifstream input(source_path, std::ios::binary);
    if (!input)
    {
        throw std::runtime_error("Could not open source scene: " + source_path.string());
    }
    const std::string source{
        std::istreambuf_iterator<char>{input},
        std::istreambuf_iterator<char>{}};
    WriteCookedScene(output_path, ParseSceneSource(source));
}
} // namespace mars::assets
