cmake_minimum_required(VERSION 3.25)

project(MARSTHEGAME_Native LANGUAGES CXX)

if(NOT WIN32)
  message(FATAL_ERROR "MARSTHEGAME currently targets Windows and Direct3D 12.")
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

enable_testing()

option(
  MARS_ENABLE_D3D12_VALIDATION
  "Enable the Direct3D 12 debug layer and validation failures"
  ON
)

set(WINDOWS_SDK_DIR "$ENV{WindowsSdkDir}")
set(WINDOWS_SDK_VERSION "$ENV{WindowsSDKVersion}")
string(REGEX REPLACE "[/\\\\]+$" "" WINDOWS_SDK_DIR "${WINDOWS_SDK_DIR}")
string(REGEX REPLACE "[/\\\\]+$" "" WINDOWS_SDK_VERSION "${WINDOWS_SDK_VERSION}")
file(TO_CMAKE_PATH "${WINDOWS_SDK_DIR}" WINDOWS_SDK_DIR)

find_program(
  DXC_EXECUTABLE
  NAMES dxc.exe dxc
  HINTS
    "${WINDOWS_SDK_DIR}/bin/${WINDOWS_SDK_VERSION}/x64"
    "${WINDOWS_SDK_DIR}/bin/x64"
)

if(NOT DXC_EXECUTABLE)
  message(FATAL_ERROR "DXC was not found. Install a Windows SDK containing dxc.exe.")
endif()

function(mars_strict_warnings target)
  target_compile_options(
    ${target}
    PRIVATE
      /W4
      /WX
      /permissive-
      /EHsc
      /Zc:__cplusplus
      /utf-8
  )
endfunction()

set(SHADER_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/shaders/scene.hlsl")
set(SHADER_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/shaders")
set(SHADOW_VERTEX_SHADER "${SHADER_OUTPUT_DIR}/shadow.vs.dxil")
set(SCENE_VERTEX_SHADER "${SHADER_OUTPUT_DIR}/scene.vs.dxil")
set(SCENE_PIXEL_SHADER "${SHADER_OUTPUT_DIR}/scene.ps.dxil")
set(PARTICLE_VERTEX_SHADER "${SHADER_OUTPUT_DIR}/particle.vs.dxil")
set(PARTICLE_PIXEL_SHADER "${SHADER_OUTPUT_DIR}/particle.ps.dxil")
set(FULLSCREEN_VERTEX_SHADER "${SHADER_OUTPUT_DIR}/fullscreen.vs.dxil")
set(TEMPORAL_PIXEL_SHADER "${SHADER_OUTPUT_DIR}/temporal.ps.dxil")
set(FINAL_PIXEL_SHADER "${SHADER_OUTPUT_DIR}/final.ps.dxil")
set(MARS_SHADER_OUTPUTS
  "${SHADOW_VERTEX_SHADER}"
  "${SCENE_VERTEX_SHADER}"
  "${SCENE_PIXEL_SHADER}"
  "${PARTICLE_VERTEX_SHADER}"
  "${PARTICLE_PIXEL_SHADER}"
  "${FULLSCREEN_VERTEX_SHADER}"
  "${TEMPORAL_PIXEL_SHADER}"
  "${FINAL_PIXEL_SHADER}"
)

function(mars_compile_shader output profile entry)
  add_custom_command(
    OUTPUT "${output}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${SHADER_OUTPUT_DIR}"
    COMMAND "${DXC_EXECUTABLE}" -nologo -Ges -O3 -T "${profile}" -E "${entry}"
            -Fo "${output}" "${SHADER_SOURCE}"
    DEPENDS
      "${SHADER_SOURCE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/shaders/scene_impl_00.hlsli"
      "${CMAKE_CURRENT_SOURCE_DIR}/shaders/scene_impl_01.hlsli"
      "${CMAKE_CURRENT_SOURCE_DIR}/shaders/scene_impl_02.hlsli"
    VERBATIM
  )
endfunction()

mars_compile_shader("${SHADOW_VERTEX_SHADER}" vs_6_0 ShadowVS)
mars_compile_shader("${SCENE_VERTEX_SHADER}" vs_6_0 SceneVS)
mars_compile_shader("${SCENE_PIXEL_SHADER}" ps_6_0 ScenePS)
mars_compile_shader("${PARTICLE_VERTEX_SHADER}" vs_6_0 ParticleVS)
mars_compile_shader("${PARTICLE_PIXEL_SHADER}" ps_6_0 ParticlePS)
mars_compile_shader("${FULLSCREEN_VERTEX_SHADER}" vs_6_0 FullscreenVS)
mars_compile_shader("${TEMPORAL_PIXEL_SHADER}" ps_6_0 TemporalPS)
mars_compile_shader("${FINAL_PIXEL_SHADER}" ps_6_0 FinalPS)
add_custom_target(mars_shaders DEPENDS ${MARS_SHADER_OUTPUTS})

set(MARS_PROCEDURAL_CONTENT_SOURCES
  src/renderer/procedural_catalog.cpp
  src/renderer/procedural_catalog.h
  src/renderer/procedural_geometry.cpp
  src/renderer/procedural_geometry.h
)

set(MARS_GENERATED_MATERIAL_SOURCES
  src/renderer/generated_materials.cpp
  src/renderer/generated_materials.h
)

set(MARS_VISUAL_SLICE_SOURCES
  src/renderer/generated_environment.cpp
  src/renderer/generated_environment.h
  src/renderer/visual_slice.cpp
  src/renderer/visual_slice.h
)

set(MARS_CHARACTER_SOURCES
  src/game/character_rig.cpp
  src/game/character_rig.h
)

set(MARS_AUDIO_SOURCES
  src/audio/procedural_audio.cpp
  src/audio/procedural_audio.h
)

set(MARS_SCENE_ASSET_SOURCES
  src/assets/scene_asset.cpp
  src/assets/scene_asset.h
)

add_executable(
  mars_scene_cooker
  tools/scene_cooker_main.cpp
  ${MARS_SCENE_ASSET_SOURCES}
  ${MARS_PROCEDURAL_CONTENT_SOURCES}
)
target_include_directories(mars_scene_cooker PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_scene_cooker)

set(SOURCE_SCENE "${CMAKE_CURRENT_SOURCE_DIR}/assets/scenes/ares_reach.marscene")
set(COOKED_SCENE_DIR "${CMAKE_CURRENT_BINARY_DIR}/assets/scenes")
set(COOKED_SCENE "${COOKED_SCENE_DIR}/ares_reach.marscene.bin")

add_custom_command(
  OUTPUT "${COOKED_SCENE}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${COOKED_SCENE_DIR}"
  COMMAND "$<TARGET_FILE:mars_scene_cooker>"
          --input "${SOURCE_SCENE}"
          --output "${COOKED_SCENE}"
  DEPENDS mars_scene_cooker "${SOURCE_SCENE}"
  VERBATIM
)
add_custom_target(mars_assets ALL DEPENDS "${COOKED_SCENE}")

set(MARS_GAME_SOURCES
  ${MARS_SCENE_ASSET_SOURCES}
  ${MARS_PROCEDURAL_CONTENT_SOURCES}
  ${MARS_CHARACTER_SOURCES}
  src/game/collision.cpp
  src/game/collision.h
  src/game/game_state.cpp
  src/game/game_state.h
  src/game/replay.cpp
  src/game/replay.h
  src/game/save_state.cpp
  src/game/save_state.h
  src/renderer/render_scene.h
)

set(MARS_INPUT_SOURCES
  src/platform/native_input.cpp
  src/platform/native_input.h
)

add_executable(
  mars_native
  WIN32
  src/main.cpp
  src/main_impl_00.inl
  src/main_impl_01.inl
  src/main_impl_02.inl
  src/main_impl_03.inl
  src/platform/win32_window.cpp
  src/platform/win32_window.h
  src/renderer/d3d12_renderer.cpp
  src/renderer/d3d12_renderer.h
  src/renderer/d3d12_renderer_impl_00.inl
  src/renderer/d3d12_renderer_impl_01.inl
  src/renderer/d3d12_renderer_impl_02.inl
  src/renderer/d3d12_renderer_impl_03.inl
  src/renderer/d3d12_renderer_impl_04.inl
  src/renderer/d3d12_renderer_impl_05.inl
  src/renderer/d3d12_renderer_impl_06.inl
  src/renderer/d3d12_renderer_impl_07.inl
  src/renderer/d3d12_renderer_impl_08.inl
  src/renderer/fence_retirement.h
  src/renderer/gpu_upload.cpp
  src/renderer/gpu_upload.h
  ${MARS_GENERATED_MATERIAL_SOURCES}
  ${MARS_VISUAL_SLICE_SOURCES}
  ${MARS_AUDIO_SOURCES}
  ${MARS_GAME_SOURCES}
  ${MARS_INPUT_SOURCES}
)

add_dependencies(mars_native mars_shaders mars_assets)
target_include_directories(mars_native PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(
  mars_native
  PRIVATE
    UNICODE
    _UNICODE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
if(MARS_ENABLE_D3D12_VALIDATION)
  target_compile_definitions(mars_native PRIVATE MARS_ENABLE_D3D12_VALIDATION=1)
else()
  target_compile_definitions(mars_native PRIVATE MARS_ENABLE_D3D12_VALIDATION=0)
endif()
mars_strict_warnings(mars_native)
target_link_libraries(
  mars_native
  PRIVATE
    d3d12
    dxgi
    dxguid
    ole32
    shell32
    user32
    winmm
    xinput9_1_0
)

add_executable(mars_native_game_tests tests/game_state_tests.cpp ${MARS_GAME_SOURCES})
add_dependencies(mars_native_game_tests mars_assets)
target_include_directories(mars_native_game_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_native_game_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_native_game_tests)
add_test(NAME native_game_state COMMAND mars_native_game_tests "${COOKED_SCENE}")

add_executable(mars_scene_mesh_tests tests/scene_mesh_tests.cpp ${MARS_GAME_SOURCES})
add_dependencies(mars_scene_mesh_tests mars_assets)
target_include_directories(mars_scene_mesh_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_scene_mesh_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_scene_mesh_tests)
add_test(NAME cooked_procedural_mesh_contract COMMAND mars_scene_mesh_tests "${COOKED_SCENE}")

add_executable(mars_native_input_tests tests/input_tests.cpp ${MARS_INPUT_SOURCES})
target_include_directories(mars_native_input_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_native_input_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_native_input_tests)
target_link_libraries(mars_native_input_tests PRIVATE user32 xinput9_1_0)
add_test(NAME native_input_parity COMMAND mars_native_input_tests)

add_executable(mars_procedural_content_tests tests/procedural_geometry_tests.cpp ${MARS_PROCEDURAL_CONTENT_SOURCES})
target_include_directories(mars_procedural_content_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_procedural_content_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_procedural_content_tests)
add_test(NAME procedural_content_generation COMMAND mars_procedural_content_tests)

add_executable(mars_generated_material_tests tests/generated_material_tests.cpp ${MARS_GENERATED_MATERIAL_SOURCES})
target_include_directories(mars_generated_material_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_generated_material_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_generated_material_tests)
add_test(NAME generated_material_content COMMAND mars_generated_material_tests)

add_executable(
  mars_fence_retirement_tests
  tests/fence_retirement_tests.cpp
  src/renderer/fence_retirement.h
)
target_include_directories(mars_fence_retirement_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(mars_fence_retirement_tests PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
mars_strict_warnings(mars_fence_retirement_tests)
add_test(NAME gpu_fence_resource_retirement COMMAND mars_fence_retirement_tests)

add_executable(mars_visual_slice_tests tests/visual_slice_tests.cpp src/renderer/visual_slice.cpp src/renderer/visual_slice.h)
target_include_directories(mars_visual_slice_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_visual_slice_tests)
add_test(NAME phase5_visual_slice_contract COMMAND mars_visual_slice_tests)

add_executable(mars_generated_environment_tests tests/generated_environment_tests.cpp src/renderer/generated_environment.cpp src/renderer/generated_environment.h)
target_include_directories(mars_generated_environment_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_generated_environment_tests)
add_test(NAME phase5_generated_environment_ibl COMMAND mars_generated_environment_tests)

add_executable(mars_character_rig_tests tests/character_rig_tests.cpp ${MARS_CHARACTER_SOURCES})
target_include_directories(mars_character_rig_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_character_rig_tests)
add_test(NAME phase5_character_rig COMMAND mars_character_rig_tests)

add_executable(mars_procedural_audio_tests tests/procedural_audio_tests.cpp ${MARS_AUDIO_SOURCES})
target_include_directories(mars_procedural_audio_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_procedural_audio_tests)
add_test(NAME phase5_project_synthesized_audio COMMAND mars_procedural_audio_tests)

add_custom_command(
  TARGET mars_native
  POST_BUILD
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/shaders"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          ${MARS_SHADER_OUTPUTS}
          "$<TARGET_FILE_DIR:mars_native>/shaders"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/assets/scenes"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${COOKED_SCENE}"
          "$<TARGET_FILE_DIR:mars_native>/assets/scenes/ares_reach.marscene.bin"
)
