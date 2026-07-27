#include "game/collision.h"
#include "game/game_state.h"
#include "game/replay.h"
#include "game/save_state.h"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

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

template <typename Callable>
void RequireThrows(Callable&& callable, const char* message)
{
    try
    {
        callable();
    }
    catch (const std::exception&)
    {
        return;
    }
    Require(false, message);
}

void Advance(
    mars::game::GameState& game,
    const mars::game::InputState& input,
    const int ticks)
{
    for (int tick = 0; tick < ticks; ++tick)
    {
        game.Update(input, mars::game::GameState::kFixedStepSeconds);
    }
}

bool Near(const float first, const float second, const float tolerance = 0.001f)
{
    return std::abs(first - second) <= tolerance;
}
} // namespace

int main()
{
    using mars::game::GameState;
    using mars::game::InputState;
    using mars::game::MissionState;

    {
        const mars::game::CollisionBox box{-1.0f, 1.0f, -1.0f, 1.0f};
        Require(
            mars::game::CircleIntersectsBox(0.0f, 0.0f, 0.4f, box),
            "circle-box collision detects overlap");
        Require(
            !mars::game::CircleIntersectsBox(-2.0f, 0.0f, 0.4f, box),
            "circle-box collision rejects separation");
        const DirectX::XMFLOAT2 blocked = mars::game::ResolvePlanarMovement(
            {-2.0f, 0.0f},
            {2.0f, 0.0f},
            0.4f,
            std::span<const mars::game::CollisionBox>(&box, 1));
        Require(Near(blocked.x, -2.0f), "collision resolution blocks penetration");
    }

    GameState game;
    Require(game.Mission() == MissionState::Traverse, "mission starts in traverse state");
    Require(!game.CheckpointReached(), "checkpoint starts unreached");

    const auto start = game.PlayerPosition();
    InputState forward{};
    forward.move_z = 1.0f;
    Advance(game, forward, 60);
    const auto advanced = game.PlayerPosition();
    Require(advanced.z > start.z + 3.0f, "forward input advances deterministically");

    Advance(game, forward, 180);
    Require(game.CheckpointReached(), "crossing the relay line records checkpoint progress");
    const mars::game::GameSnapshot checkpoint_snapshot = game.Snapshot();
    Require(checkpoint_snapshot.checkpoint_reached, "checkpoint persists in snapshots");

    game.Reset();
    Require(!game.CheckpointReached(), "full reset clears checkpoint progress");
    game.Restore(checkpoint_snapshot);
    Require(game.CheckpointReached(), "snapshot restore recovers checkpoint progress");
    Require(
        Near(game.PlayerPosition().z, checkpoint_snapshot.player_position.z),
        "snapshot restore recovers player position");

    InputState checkpoint_restore{};
    checkpoint_restore.restore_checkpoint = true;
    game.Update(checkpoint_restore, GameState::kFixedStepSeconds);
    Require(
        Near(game.PlayerPosition().z, 5.0f),
        "checkpoint restore returns to the native relay position");

    Advance(game, forward, 300);
    Require(game.Mission() == MissionState::Complete, "objective beacon completes the mission");
    const auto completed = game.PlayerPosition();
    Advance(game, forward, 60);
    const auto stopped = game.PlayerPosition();
    Require(
        std::abs(stopped.z - completed.z) < 0.75f,
        "completion arrests player movement");

    {
        mars::game::ReplayTape tape;
        InputState sprint_forward{};
        sprint_forward.move_z = 1.0f;
        sprint_forward.sprint = true;
        tape.Append(sprint_forward, 240);
        Require(tape.Hash() != 0, "native replay produces a stable non-zero hash");

        GameState first;
        GameState second;
        tape.Play(first);
        tape.Play(second);
        const auto first_snapshot = first.Snapshot();
        const auto second_snapshot = second.Snapshot();
        Require(
            Near(first_snapshot.player_position.x, second_snapshot.player_position.x)
                && Near(first_snapshot.player_position.z, second_snapshot.player_position.z)
                && first_snapshot.mission_state == second_snapshot.mission_state
                && first_snapshot.checkpoint_reached == second_snapshot.checkpoint_reached,
            "native replay produces identical state on repeated playback");
    }

    {
        const std::filesystem::path save_path =
            std::filesystem::temp_directory_path() / "marsthegame-native-save-test.bin";
        const std::filesystem::path backup_path = save_path.string() + ".bak";
        const std::filesystem::path temporary_path = save_path.string() + ".tmp";
        std::filesystem::remove(save_path);
        std::filesystem::remove(backup_path);
        std::filesystem::remove(temporary_path);

        mars::game::SaveRepository::Write(save_path, checkpoint_snapshot);
        const auto loaded = mars::game::SaveRepository::Load(save_path);
        Require(loaded.has_value(), "transactional native save round-trips");
        Require(
            Near(loaded->player_position.z, checkpoint_snapshot.player_position.z)
                && loaded->checkpoint_reached,
            "loaded native save preserves checkpoint state");

        mars::game::SaveRepository::Write(save_path, game.Snapshot());
        Require(std::filesystem::exists(backup_path), "second save rotates a backup");
        Require(!std::filesystem::exists(temporary_path), "committed save leaves no temporary file");

        {
            std::fstream corrupt(save_path, std::ios::binary | std::ios::in | std::ios::out);
            Require(static_cast<bool>(corrupt), "save opens for corruption regression test");
            corrupt.seekg(40, std::ios::beg);
            char value = 0;
            corrupt.read(&value, 1);
            value = static_cast<char>(static_cast<unsigned char>(value) ^ 0x5AU);
            corrupt.seekp(40, std::ios::beg);
            corrupt.write(&value, 1);
        }
        RequireThrows(
            [&save_path]() { static_cast<void>(mars::game::SaveRepository::Load(save_path)); },
            "checksum corruption is rejected");

        std::filesystem::remove(save_path);
        std::filesystem::remove(backup_path);
        std::filesystem::remove(temporary_path);
    }

    InputState reset{};
    reset.reset = true;
    game.Update(reset, GameState::kFixedStepSeconds);
    Require(game.Mission() == MissionState::Traverse, "reset restores active mission state");
    Require(game.PlayerPosition().z < -7.5f, "reset restores landing position");

    const auto scene = game.Scene();
    Require(scene.instances.size() == 18, "native graybox exposes the complete scene instance set");
    std::cout << "MARSTHEGAME native collision, save, and replay tests passed\n";
    return 0;
}
