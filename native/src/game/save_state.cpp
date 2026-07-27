#include "game/save_state.h"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <system_error>
#include <vector>

namespace mars::game
{
namespace
{
constexpr std::array<char, 8> kMagic = {'M', 'A', 'R', 'S', 'A', 'V', 'E', '1'};
constexpr std::uint32_t kEnvelopeVersion = 1;
constexpr std::uint64_t kFnvOffsetBasis = 1'469'598'103'934'665'603ULL;
constexpr std::uint64_t kFnvPrime = 1'099'511'628'211ULL;

struct SavePayload
{
    std::uint32_t snapshot_version = 1;
    float player_x = 0.0f;
    float player_y = 0.0f;
    float player_z = 0.0f;
    float velocity_x = 0.0f;
    float velocity_y = 0.0f;
    float velocity_z = 0.0f;
    float elapsed_seconds = 0.0f;
    std::uint32_t mission_state = 0;
    std::uint32_t checkpoint_reached = 0;
};

struct SaveEnvelope
{
    std::array<char, 8> magic{};
    std::uint32_t envelope_version = kEnvelopeVersion;
    std::uint32_t payload_size = sizeof(SavePayload);
    std::uint64_t checksum = 0;
    SavePayload payload{};
};

static_assert(std::is_trivially_copyable_v<SavePayload>);
static_assert(std::is_trivially_copyable_v<SaveEnvelope>);

std::uint64_t Checksum(const SavePayload& payload) noexcept
{
    std::uint64_t hash = kFnvOffsetBasis;
    const auto* bytes = reinterpret_cast<const std::uint8_t*>(&payload);
    for (std::size_t index = 0; index < sizeof(payload); ++index)
    {
        hash ^= bytes[index];
        hash *= kFnvPrime;
    }
    return hash;
}

SavePayload ToPayload(const GameSnapshot& snapshot)
{
    return {
        .snapshot_version = snapshot.schema_version,
        .player_x = snapshot.player_position.x,
        .player_y = snapshot.player_position.y,
        .player_z = snapshot.player_position.z,
        .velocity_x = snapshot.player_velocity.x,
        .velocity_y = snapshot.player_velocity.y,
        .velocity_z = snapshot.player_velocity.z,
        .elapsed_seconds = snapshot.elapsed_seconds,
        .mission_state = static_cast<std::uint32_t>(snapshot.mission_state),
        .checkpoint_reached = snapshot.checkpoint_reached ? 1U : 0U,
    };
}

GameSnapshot FromPayload(const SavePayload& payload)
{
    if (payload.snapshot_version != GameSnapshot::kSchemaVersion)
    {
        throw std::runtime_error("Unsupported native save schema");
    }
    if (!std::isfinite(payload.player_x) || !std::isfinite(payload.player_y)
        || !std::isfinite(payload.player_z) || !std::isfinite(payload.velocity_x)
        || !std::isfinite(payload.velocity_y) || !std::isfinite(payload.velocity_z)
        || !std::isfinite(payload.elapsed_seconds))
    {
        throw std::runtime_error("Native save contains non-finite values");
    }
    if (payload.mission_state > static_cast<std::uint32_t>(MissionState::Complete)
        || payload.checkpoint_reached > 1U)
    {
        throw std::runtime_error("Native save contains invalid enum state");
    }
    return {
        .schema_version = payload.snapshot_version,
        .player_position = {payload.player_x, payload.player_y, payload.player_z},
        .player_velocity = {payload.velocity_x, payload.velocity_y, payload.velocity_z},
        .elapsed_seconds = payload.elapsed_seconds,
        .mission_state = static_cast<MissionState>(payload.mission_state),
        .checkpoint_reached = payload.checkpoint_reached == 1U,
    };
}
} // namespace

void SaveRepository::Write(const std::filesystem::path& path, const GameSnapshot& snapshot)
{
    if (path.empty())
    {
        throw std::invalid_argument("Native save path cannot be empty");
    }
    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path());
    }

    SaveEnvelope envelope{};
    envelope.magic = kMagic;
    envelope.payload = ToPayload(snapshot);
    envelope.checksum = Checksum(envelope.payload);

    const std::filesystem::path temporary = path.string() + ".tmp";
    const std::filesystem::path backup = path.string() + ".bak";
    {
        std::ofstream stream(temporary, std::ios::binary | std::ios::trunc);
        if (!stream)
        {
            throw std::runtime_error("Could not create native save temporary file");
        }
        stream.write(reinterpret_cast<const char*>(&envelope), sizeof(envelope));
        stream.flush();
        if (!stream)
        {
            throw std::runtime_error("Could not write native save temporary file");
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
            throw std::runtime_error("Could not rotate native save backup");
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
        throw std::runtime_error("Could not commit native save transaction");
    }
}

std::optional<GameSnapshot> SaveRepository::Load(const std::filesystem::path& path)
{
    if (!std::filesystem::exists(path))
    {
        return std::nullopt;
    }

    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    if (!stream)
    {
        throw std::runtime_error("Could not open native save");
    }
    const std::streamoff size = stream.tellg();
    if (size != static_cast<std::streamoff>(sizeof(SaveEnvelope)))
    {
        throw std::runtime_error("Native save size is invalid");
    }
    stream.seekg(0, std::ios::beg);

    SaveEnvelope envelope{};
    stream.read(reinterpret_cast<char*>(&envelope), sizeof(envelope));
    if (!stream)
    {
        throw std::runtime_error("Could not read native save");
    }
    if (envelope.magic != kMagic || envelope.envelope_version != kEnvelopeVersion
        || envelope.payload_size != sizeof(SavePayload))
    {
        throw std::runtime_error("Native save envelope is invalid");
    }
    if (envelope.checksum != Checksum(envelope.payload))
    {
        throw std::runtime_error("Native save checksum mismatch");
    }
    return FromPayload(envelope.payload);
}
} // namespace mars::game
