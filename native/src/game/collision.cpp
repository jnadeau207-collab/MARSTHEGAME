#include "game/collision.h"

#include <algorithm>

namespace mars::game
{
bool CircleIntersectsBox(
    const float center_x,
    const float center_z,
    const float radius,
    const CollisionBox& box) noexcept
{
    const float nearest_x = (std::clamp)(center_x, box.min_x, box.max_x);
    const float nearest_z = (std::clamp)(center_z, box.min_z, box.max_z);
    const float delta_x = center_x - nearest_x;
    const float delta_z = center_z - nearest_z;
    return delta_x * delta_x + delta_z * delta_z < radius * radius;
}

DirectX::XMFLOAT2 ResolvePlanarMovement(
    const DirectX::XMFLOAT2 position,
    const DirectX::XMFLOAT2 desired_delta,
    const float radius,
    const std::span<const CollisionBox> boxes) noexcept
{
    DirectX::XMFLOAT2 result = position;

    const float candidate_x = position.x + desired_delta.x;
    bool x_blocked = false;
    for (const CollisionBox& box : boxes)
    {
        if (CircleIntersectsBox(candidate_x, result.y, radius, box))
        {
            x_blocked = true;
            break;
        }
    }
    if (!x_blocked)
    {
        result.x = candidate_x;
    }

    const float candidate_z = position.y + desired_delta.y;
    bool z_blocked = false;
    for (const CollisionBox& box : boxes)
    {
        if (CircleIntersectsBox(result.x, candidate_z, radius, box))
        {
            z_blocked = true;
            break;
        }
    }
    if (!z_blocked)
    {
        result.y = candidate_z;
    }

    return result;
}
} // namespace mars::game
