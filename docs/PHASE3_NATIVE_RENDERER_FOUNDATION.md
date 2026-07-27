# Phase 3: Windows Native Renderer Foundation

## Purpose

Phase 3 begins the migration from the Python/Pygame compatibility prototype to the Windows shipping runtime. The target boundary is a custom C++23 executable using Win32, Direct3D 12, DXGI, HLSL compiled by DXC, and CMake.

This tranche is a renderer kernel, not an AAA visual slice. It must not be described as high-fidelity gameplay, authored 3D content, or final graphics.

## Current source boundary

- `native/CMakeLists.txt` — Windows-native build, validation policy, and shader compilation
- `native/src/main.cpp` — executable, packaging self-test, WARP smoke test, and top-level failure boundary
- `native/src/platform/win32_window.*` — visible and hidden Win32 window ownership
- `native/src/renderer/d3d12_renderer.*` — D3D12 device, depth-tested 3D pipeline, frame resources, resize, synchronization, timing, device-loss diagnostics, and GPU readback
- `native/shaders/triangle.hlsl` — DXC vertex and pixel shader with transforms, normals, and directional lighting
- `config/phase3_renderer.json` — machine-readable CI, hardware, visual, and AAA truth
- `tools/phase3_renderer_audit.py` — fail-closed architecture and evidence audit

## Implemented renderer proof

The current native executable renders a rotating indexed cube through a perspective camera. The path includes:

- Direct3D 12 feature-level 12_0 device creation,
- hardware and Microsoft WARP adapter selection,
- flip-discard swap chain and double-buffered frame ownership,
- explicit command allocators, command list, queue, barriers, fences, and waits,
- resize-safe render-target and depth-buffer recreation,
- 32-bit depth testing,
- per-frame 256-byte scene constant buffers,
- world, view, and projection transforms,
- vertex normals and simple directional plus sky-fill lighting,
- CPU frame-time telemetry,
- device-removal reason reporting,
- optional back-buffer readback with a deterministic checksum and non-background pixel count.

The validation-enabled WARP test renders three frames, resizes from 640×360 to 800×450, renders three more frames, captures the final back buffer, and rejects output that contains fewer than 1,000 non-background pixels.

## Windows build

From an x64 MSVC developer shell with a Windows SDK containing `dxc.exe`:

```powershell
$dxc = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter dxc.exe -Recurse |
  Where-Object { $_.FullName -match '\\x64\\dxc\.exe$' } |
  Sort-Object FullName -Descending |
  Select-Object -First 1

cmake -S native -B build/native -G Ninja `
  -DCMAKE_BUILD_TYPE=RelWithDebInfo `
  -DMARS_ENABLE_D3D12_VALIDATION=ON `
  -DDXC_EXECUTABLE="$($dxc.FullName)"
cmake --build build/native --parallel
.\build\native\mars_native.exe --self-test
.\build\native\mars_native.exe --warp-smoke-test
```

The packaging self-test proves that the executable and compiled DXIL payload were delivered together. The WARP smoke test proves that the validation-enabled software D3D12 device can execute the 3D draw, resize, synchronize, present, and return meaningful pixels. Neither test claims founder hardware behavior or human visual approval.

## Verified CI boundary

At exact implementation head `85ebd4d28a504988818e00d052fc2be445ecc649`:

- native renderer run `30230916130` passed strict MSVC `/W4 /WX`, DXC, packaging, validation-enabled WARP, resize, presentation, GPU readback, and artifact upload,
- compatibility run `30230916160` passed Python 3.11/3.12 quality, the complete test suite, all protected replays and audits, and the same-runner performance guard.

Subsequent documentation-only commits do not alter that renderer implementation. The latest branch head must still remain green before the tranche advances.

## Live founder-PC verification

After the latest branch head is green, run:

```powershell
.\build\native\mars_native.exe
```

The live verification must confirm:

1. a 1600×900 window opens,
2. the lit rotating perspective cube is visible and correctly depth-tested,
3. resizing preserves correct aspect, depth, and presentation,
4. closing exits cleanly,
5. the D3D12 debug layer emits no corruption or error messages,
6. repeated startup and shutdown do not hang or crash,
7. hardware frame behavior is acceptable on the founder reference PC.

Only after that direct verification may `founder_hardware_validation` or `founder_visual_inspection` change from `pending`.

## Protected boundary

The Python/Pygame runtime remains available for Classic Mode, deterministic replay, save migration, and behavior comparison. Phase 3 does not remove or rewrite those systems.

## Next renderer work after this tranche

- production frame-resource and descriptor allocation policy,
- versioned scene, camera, mesh, and material contracts,
- default-heap upload path and resource lifetime tracking,
- GPU timestamp queries and durable capture artifacts,
- authored asset ingestion,
- native Ares Reach graybox migration.
