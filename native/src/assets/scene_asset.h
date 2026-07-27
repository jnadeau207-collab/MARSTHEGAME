#pragma once

#include <DirectXMath.h>

#include <cstdint>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

namespace mars::assets
{
enum SceneEntityFlag : std::uint32_t
{
    SceneEntityNone = 0,
    SceneEntityRender = 1U << 0U,
    SceneEntityCollider = 1U << 1U,
    SceneEntityPlayer = 1U << 2U,
    SceneEntityCheckpoint = 1U << 3U,
    SceneEntityObjective = 1U << 4U,
};

struct SceneEntity
{
    std::string id{};
    std::uint32_t flags = SceneEntityNone;
    DirectX::XMFLOAT3 position{};
    DirectX::XMFLOAT3 scale{1.0f, 1.0f, 1.0f};
    DirectX::XMFLOAT4 tint{1.0f, 1.0f, 1.0f, 1.0f};
};

struct SceneDefinition
{
    static constexpr std::uint32_t kSchemaVersion = 1;

    std::uint32_t schema_version = kSchemaVersion;
    std::uint64_t source_hash = 0;
    std::vector<SceneEntity> entities{};
};

[[nodiscard]] bool HasFlag(const SceneEntity& entity, SceneEntityFlag flag) noexcept;
[[nodiscard]] SceneDefinition ParseSceneSource(std::string_view source);
void WriteCookedScene(const std::filesystem::path& path, const SceneDefinition& scene);
[[nodiscard]] SceneDefinition LoadCookedScene(const std::filesystem::path& path);
void CookSceneFile(
    const std::filesystem::path& source_path,
    const std::filesystem::path& output_path);
} // namespace mars::assets
