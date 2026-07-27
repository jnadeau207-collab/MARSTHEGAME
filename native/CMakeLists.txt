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

set(SHADER_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/shaders/scene.hlsl")
set(SHADER_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/shaders")
set(VERTEX_SHADER "${SHADER_OUTPUT_DIR}/scene.vs.dxil")
set(PIXEL_SHADER "${SHADER_OUTPUT_DIR}/scene.ps.dxil")

add_custom_command(
  OUTPUT "${VERTEX_SHADER}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${SHADER_OUTPUT_DIR}"
  COMMAND "${DXC_EXECUTABLE}" -nologo -Ges -O3 -T vs_6_0 -E VSMain
          -Fo "${VERTEX_SHADER}" "${SHADER_SOURCE}"
  DEPENDS "${SHADER_SOURCE}"
  VERBATIM
)

add_custom_command(
  OUTPUT "${PIXEL_SHADER}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${SHADER_OUTPUT_DIR}"
  COMMAND "${DXC_EXECUTABLE}" -nologo -Ges -O3 -T ps_6_0 -E PSMain
          -Fo "${PIXEL_SHADER}" "${SHADER_SOURCE}"
  DEPENDS "${SHADER_SOURCE}"
  VERBATIM
)

add_custom_target(mars_shaders DEPENDS "${VERTEX_SHADER}" "${PIXEL_SHADER}")

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

set(MARS_SCENE_ASSET_SOURCES
  src/assets/scene_asset.cpp
  src/assets/scene_asset.h
)

set(MARS_MESH_ASSET_SOURCES
  src/assets/json.cpp
  src/assets/json.h
  src/assets/mesh_asset.cpp
  src/assets/mesh_asset.h
)

set(MARS_PROCEDURAL_GEOMETRY_SOURCES
  src/renderer/procedural_geometry.cpp
  src/renderer/procedural_geometry.h
)

add_executable(
  mars_scene_cooker
  tools/scene_cooker_main.cpp
  ${MARS_SCENE_ASSET_SOURCES}
)
target_include_directories(mars_scene_cooker PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_scene_cooker)

add_executable(
  mars_mesh_cooker
  tools/mesh_cooker_main.cpp
  ${MARS_MESH_ASSET_SOURCES}
)
target_include_directories(mars_mesh_cooker PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
mars_strict_warnings(mars_mesh_cooker)

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

set(SOURCE_BEACON_MESH "${CMAKE_CURRENT_SOURCE_DIR}/assets/meshes/beacon.gltf")
set(COOKED_MESH_DIR "${CMAKE_CURRENT_BINARY_DIR}/assets/meshes")
set(COOKED_BEACON_MESH "${COOKED_MESH_DIR}/beacon.marsmesh.bin")

add_custom_command(
  OUTPUT "${COOKED_BEACON_MESH}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${COOKED_MESH_DIR}"
  COMMAND "$<TARGET_FILE:mars_mesh_cooker>"
          --id beacon
          --input "${SOURCE_BEACON_MESH}"
          --output "${COOKED_BEACON_MESH}"
  DEPENDS mars_mesh_cooker "${SOURCE_BEACON_MESH}"
  VERBATIM
)

add_custom_target(
  mars_assets
  ALL
  DEPENDS "${COOKED_SCENE}" "${COOKED_BEACON_MESH}"
)

set(MARS_GAME_SOURCES
  src/game/collision.cpp
  src/game/collision.h
  src/game/game_state.cpp
  src/game/game_state.h
  src/game/replay.cpp
  src/game/replay.h
  src/game/save_state.cpp
  src/game/save_state.h
  src/renderer/render_scene.h
  ${MARS_PROCEDURAL_GEOMETRY_SOURCES}
  ${MARS_SCENE_ASSET_SOURCES}
)

set(MARS_INPUT_SOURCES
  src/platform/native_input.cpp
  src/platform/native_input.h
)

add_executable(
  mars_native
  WIN32
  src/main.cpp
  src/platform/win32_window.cpp
  src/platform/win32_window.h
  src/renderer/d3d12_renderer.cpp
  src/renderer/d3d12_renderer.h
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
    xinput9_1_0
)

add_executable(
  mars_native_game_tests
  tests/game_state_tests.cpp
  ${MARS_GAME_SOURCES}
)
add_dependencies(mars_native_game_tests mars_assets)
target_include_directories(mars_native_game_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(
  mars_native_game_tests
  PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
mars_strict_warnings(mars_native_game_tests)
add_test(NAME native_game_state COMMAND mars_native_game_tests "${COOKED_SCENE}")

add_executable(
  mars_scene_mesh_tests
  tests/scene_mesh_tests.cpp
  ${MARS_GAME_SOURCES}
)
add_dependencies(mars_scene_mesh_tests mars_assets)
target_include_directories(mars_scene_mesh_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(
  mars_scene_mesh_tests
  PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
mars_strict_warnings(mars_scene_mesh_tests)
add_test(NAME cooked_procedural_mesh_contract COMMAND mars_scene_mesh_tests "${COOKED_SCENE}")

add_executable(
  mars_native_input_tests
  tests/input_tests.cpp
  ${MARS_INPUT_SOURCES}
)
target_include_directories(mars_native_input_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(
  mars_native_input_tests
  PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
mars_strict_warnings(mars_native_input_tests)
target_link_libraries(mars_native_input_tests PRIVATE user32 xinput9_1_0)
add_test(NAME native_input_parity COMMAND mars_native_input_tests)

add_executable(
  mars_procedural_content_tests
  tests/procedural_geometry_tests.cpp
  ${MARS_PROCEDURAL_GEOMETRY_SOURCES}
)
target_include_directories(
  mars_procedural_content_tests
  PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src"
)
target_compile_definitions(
  mars_procedural_content_tests
  PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
mars_strict_warnings(mars_procedural_content_tests)
add_test(NAME procedural_content_generation COMMAND mars_procedural_content_tests)

add_executable(
  mars_native_mesh_tests
  tests/mesh_asset_tests.cpp
  ${MARS_MESH_ASSET_SOURCES}
)
add_dependencies(mars_native_mesh_tests mars_assets)
target_include_directories(mars_native_mesh_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(
  mars_native_mesh_tests
  PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)
mars_strict_warnings(mars_native_mesh_tests)
add_test(
  NAME native_gltf_mesh_pipeline
  COMMAND mars_native_mesh_tests "${SOURCE_BEACON_MESH}" "${COOKED_BEACON_MESH}"
)

add_custom_command(
  TARGET mars_native
  POST_BUILD
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/shaders"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${VERTEX_SHADER}"
          "$<TARGET_FILE_DIR:mars_native>/shaders/scene.vs.dxil"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${PIXEL_SHADER}"
          "$<TARGET_FILE_DIR:mars_native>/shaders/scene.ps.dxil"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/assets/scenes"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${COOKED_SCENE}"
          "$<TARGET_FILE_DIR:mars_native>/assets/scenes/ares_reach.marscene.bin"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/assets/meshes"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${COOKED_BEACON_MESH}"
          "$<TARGET_FILE_DIR:mars_native>/assets/meshes/beacon.marsmesh.bin"
)
