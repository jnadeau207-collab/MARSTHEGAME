cmake_minimum_required(VERSION 3.25)

project(MARSTHEGAME_Native LANGUAGES CXX)

if(NOT WIN32)
  message(FATAL_ERROR "The Phase 3 renderer foundation is Windows-only and requires Direct3D 12.")
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

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

set(SHADER_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/shaders/triangle.hlsl")
set(SHADER_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/shaders")
set(VERTEX_SHADER "${SHADER_OUTPUT_DIR}/triangle.vs.dxil")
set(PIXEL_SHADER "${SHADER_OUTPUT_DIR}/triangle.ps.dxil")

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

add_executable(
  mars_native
  WIN32
  src/main.cpp
  src/platform/win32_window.cpp
  src/platform/win32_window.h
  src/renderer/d3d12_renderer.cpp
  src/renderer/d3d12_renderer.h
)

add_dependencies(mars_native mars_shaders)

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
target_compile_options(
  mars_native
  PRIVATE
    /W4
    /WX
    /permissive-
    /EHsc
    /Zc:__cplusplus
    /utf-8
)
target_link_libraries(
  mars_native
  PRIVATE
    d3d12
    dxgi
    dxguid
    user32
)

add_custom_command(
  TARGET mars_native
  POST_BUILD
  COMMAND "${CMAKE_COMMAND}" -E make_directory "$<TARGET_FILE_DIR:mars_native>/shaders"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${VERTEX_SHADER}"
          "$<TARGET_FILE_DIR:mars_native>/shaders/triangle.vs.dxil"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "${PIXEL_SHADER}"
          "$<TARGET_FILE_DIR:mars_native>/shaders/triangle.ps.dxil"
)
