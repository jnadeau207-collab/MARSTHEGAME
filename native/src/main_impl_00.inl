#include "assets/scene_asset.h"
#include "audio/procedural_audio.h"
#include "game/character_rig.h"
#include "game/game_state.h"
#include "game/save_state.h"
#include "platform/native_input.h"
#include "platform/win32_window.h"
#include "renderer/d3d12_renderer.h"
#include "renderer/visual_slice.h"

#include <Windows.h>
#include <ShlObj.h>
#include <mmsystem.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <filesystem>
#include <limits>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace
{
class KeyLatch final
{
public:
    [[nodiscard]] bool Pressed(const int virtual_key)
    {
        const bool down = (GetAsyncKeyState(virtual_key) & 0x8000) != 0;
        const bool pressed = down && !was_down_;
        was_down_ = down;
        return pressed;
    }

private:
    bool was_down_ = false;
};

class LoopingSoundscape final
{
public:
    LoopingSoundscape()
    {
        const mars::audio::SynthesizedSoundscape soundscape =
            mars::audio::GenerateAresReachSoundscape();
        if (!mars::audio::ValidateSoundscape(soundscape))
        {
            throw std::runtime_error("Generated Ares Reach soundscape failed validation");
        }
        wave_bytes_ = BuildWave(soundscape);
        if (!PlaySoundW(
                reinterpret_cast<LPCWSTR>(wave_bytes_.data()),
                nullptr,
                SND_MEMORY | SND_ASYNC | SND_LOOP | SND_NODEFAULT))
        {
            OutputDebugStringW(L"MARSTHEGAME synthesized audio playback was unavailable\n");
        }
    }

    LoopingSoundscape(const LoopingSoundscape&) = delete;
    LoopingSoundscape& operator=(const LoopingSoundscape&) = delete;

    ~LoopingSoundscape()
    {
        PlaySoundW(nullptr, nullptr, 0);
    }

private:
    static void AppendU16(std::vector<std::uint8_t>& bytes, const std::uint16_t value)
    {
        bytes.push_back(static_cast<std::uint8_t>(value & 0xFFU));
        bytes.push_back(static_cast<std::uint8_t>((value >> 8U) & 0xFFU));
    }

    static void AppendU32(std::vector<std::uint8_t>& bytes, const std::uint32_t value)
    {
        for (std::uint32_t shift = 0; shift < 32U; shift += 8U)
        {
            bytes.push_back(static_cast<std::uint8_t>((value >> shift) & 0xFFU));
        }
    }

    static void AppendTag(std::vector<std::uint8_t>& bytes, const char (&tag)[5])
    {
        bytes.insert(bytes.end(), tag, tag + 4);
    }

    [[nodiscard]] static std::vector<std::uint8_t> BuildWave(
        const mars::audio::SynthesizedSoundscape& soundscape)
    {
        const std::size_t sample_bytes = soundscape.interleaved_samples.size() * sizeof(std::int16_t);
        if (sample_bytes > static_cast<std::size_t>((std::numeric_limits<std::uint32_t>::max)()))
        {
            throw std::runtime_error("Synthesized soundscape exceeds the RIFF size limit");
        }
        const std::uint32_t data_size = static_cast<std::uint32_t>(sample_bytes);
        const std::uint16_t block_align = static_cast<std::uint16_t>(
            soundscape.channels * sizeof(std::int16_t));
        const std::uint32_t byte_rate = soundscape.sample_rate * block_align;
        std::vector<std::uint8_t> bytes;
        bytes.reserve(44U + sample_bytes);
        AppendTag(bytes, "RIFF");
        AppendU32(bytes, 36U + data_size);
        AppendTag(bytes, "WAVE");
        AppendTag(bytes, "fmt ");
        AppendU32(bytes, 16U);
        AppendU16(bytes, 1U);
        AppendU16(bytes, soundscape.channels);
        AppendU32(bytes, soundscape.sample_rate);
        AppendU32(bytes, byte_rate);
        AppendU16(bytes, block_align);
        AppendU16(bytes, 16U);
        AppendTag(bytes, "data");
        AppendU32(bytes, data_size);
        const auto* sample_data = reinterpret_cast<const std::uint8_t*>(
            soundscape.interleaved_samples.data());
        bytes.insert(bytes.end(), sample_data, sample_data + sample_bytes);
        return bytes;
    }

    std::vector<std::uint8_t> wave_bytes_{};
};

std::filesystem::path ExecutableDirectory()
{
    std::array<wchar_t, 32'768> path{};
    const DWORD length = GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
    if (length == 0 || length >= path.size())
    {
        throw std::runtime_error("GetModuleFileNameW failed");
    }
    return std::filesystem::path(std::wstring_view(path.data(), length)).parent_path();
}

std::filesystem::path ScenePath()
{
    return ExecutableDirectory() / L"assets" / L"scenes" / L"ares_reach.marscene.bin";
}

std::filesystem::path SavePath()
{
    PWSTR known_folder = nullptr;
    const HRESULT result = SHGetKnownFolderPath(
        FOLDERID_LocalAppData,
        KF_FLAG_CREATE,
        nullptr,
        &known_folder);
    if (FAILED(result) || known_folder == nullptr)
    {
        throw std::runtime_error("SHGetKnownFolderPath(FOLDERID_LocalAppData) failed");
    }
    const std::filesystem::path directory =
        std::filesystem::path(known_folder) / L"MARSTHEGAME";
    CoTaskMemFree(known_folder);
    return directory / L"ares_reach.save";
}

bool HasArgument(const std::wstring_view argument)
{
    const wchar_t* command_line = GetCommandLineW();
    return command_line != nullptr
        && std::wstring_view(command_line).find(argument) != std::wstring_view::npos;
}

bool KeyDown(const int virtual_key)
{
    return (GetAsyncKeyState(virtual_key) & 0x8000) != 0;
}

void LogText(const std::wstring_view text)
{
    const std::wstring owned(text);
