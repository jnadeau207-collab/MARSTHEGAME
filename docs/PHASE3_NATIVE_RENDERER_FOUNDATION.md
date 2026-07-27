# Phase 3: Windows Native Renderer Foundation

## Purpose

Phase 3 begins the migration from the Python/Pygame compatibility prototype to the Windows shipping runtime. The target boundary is a custom C++23 executable using Win32, Direct3D 12, DXGI, HLSL compiled by DXC, and CMake.

This tranche is a renderer kernel, not an AAA visual slice. It must not be described as high-fidelity gameplay, authored 3D content, or final graphics.

## Current source boundary

- `native/CMakeLists.txt` — Windows-native build and shader compilation
- `native/src/main.cpp` — executable, self-test, and top-level failure boundary
- `native/src/platform/win32_window.*` — Win32 window and message ownership
- `native/src/renderer/d3d12_renderer.*` — D3D12 device, presentation, pipeline, geometry, resize, and synchronization
- `native/shaders/triangle.hlsl` — first DXC vertex and pixel shader
- `config/phase3_renderer.json` — machine-readable truth and unresolved evidence
- `tools/phase3_renderer_audit.py` — fail-closed architecture audit

## Windows build

From an x64 MSVC developer shell with a Windows SDK containing `dxc.exe`:

```powershell
$dxc = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter dxc.exe -Recurse |
  Where-Object { $_.FullName -match '\\x64\\dxc\.exe$' } |
  Sort-Object FullName -Descending |
  Select-Object -First 1

cmake -S native -B build/native -G Ninja `
  -DCMAKE_BUILD_TYPE=RelWithDebInfo `
  -DDXC_EXECUTABLE="$($dxc.FullName)"
cmake --build build/native --parallel
.\build\native\mars_native.exe --self-test
```

The self-test proves that the executable and compiled DXIL payload were packaged together. It intentionally does not create a GPU device or claim that a live rendered frame was visually inspected.

## Live founder-PC verification

After the Windows CI build is clean, run:

```powershell
.\build\native\mars_native.exe
```

The live verification must confirm:

1. a 1600×900 window opens,
2. the indexed triangle is visible,
3. resizing preserves correct presentation,
4. closing exits cleanly,
5. the D3D12 debug layer emits no corruption or error messages,
6. repeated startup and shutdown do not hang or crash.

Only after that direct verification may `validation_clean_runtime` and `indexed_mesh_rendered` change from `pending`.

## Protected boundary

The Python/Pygame runtime remains available for Classic Mode, deterministic replay, save migration, and behavior comparison. Phase 3 does not remove or rewrite those systems.

## Next renderer work after this tranche

- depth buffer and 3D transform constants,
- production frame-resource and descriptor allocation policy,
- versioned scene/camera/mesh/material contracts,
- default-heap upload path and resource lifetime tracking,
- GPU timestamp and device-removal evidence,
- native Ares Reach graybox migration.
