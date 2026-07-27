#include "renderer/fence_retirement.h"

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace
{
void Require(const bool condition, const char* message)
{
    if (!condition)
    {
        std::cerr << "FAILED: " << message << '\n';
        std::exit(1);
    }
}
} // namespace

int main()
{
    using mars::renderer::FenceRetirementQueue;

    int destroyed = 0;
    const auto make_batch = [&destroyed](const int count) {
        std::vector<std::shared_ptr<int>> resources;
        for (int index = 0; index < count; ++index)
        {
            resources.push_back(std::shared_ptr<int>(
                new int(index),
                [&destroyed](int* value) {
                    delete value;
                    ++destroyed;
                }));
        }
        return resources;
    };

    FenceRetirementQueue<std::vector<std::shared_ptr<int>>> queue;
    queue.Retire(3, make_batch(2));
    queue.Retire(5, make_batch(3));
    Require(queue.PendingBatchCount() == 2, "two upload batches must remain retained");
    Require(queue.Collect(2) == 0, "resources must not release before their fence");
    Require(destroyed == 0, "pre-fence collection must preserve every resource");
    Require(queue.Collect(3) == 1, "first batch must release at its fence");
    Require(destroyed == 2, "first batch resources must be destroyed together");
    Require(queue.Collect(4) == 0, "later batch must remain retained");
    Require(queue.Collect(5) == 1, "second batch must release at its fence");
    Require(destroyed == 5, "all resources must release after completed fences");
    Require(queue.Empty(), "retirement queue must be empty after collection");

    bool rejected_regression = false;
    queue.Retire(9, make_batch(1));
    try
    {
        queue.Retire(8, make_batch(1));
    }
    catch (const std::invalid_argument&)
    {
        rejected_regression = true;
    }
    Require(rejected_regression, "decreasing fence values must fail closed");
    queue.Clear();
    Require(destroyed == 7, "clear must release retained resources");

    std::cout << "MARSTHEGAME fence retirement tests passed\n";
    return 0;
}
