#pragma once

#include <DirectXMath.h>

#include <span>

namespace mars::game
{
struct CollisionBox
{
    float min_x = 0.0f;
    float max_x = 0.0f;
    float min_z = 0.0f;
    float max_z = 0.0f;
};

[[nodiscard]] bool CircleIntersectsBox(
    float center_x,
    float center_z,
    float radius,
    const CollisionBox& box) noexcept;

[[nodiscard]] DirectX::XMFLOAT2 ResolvePlanarMovement(
    DirectX::XMFLOAT2 position,
    DirectX::XMFLOAT2 desired_delta,
    float radius,
    std::span<const CollisionBox> boxes) noexcept;
} // namespace mars::game
