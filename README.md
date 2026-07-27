# MARSTHEGAME

A Windows-first custom-engine action game with an AAA-quality target.

## Current playable state

The repository contains one game runtime:

- **C++23** for the engine and gameplay runtime
- **Direct3D 12** for rendering
- **HLSL compiled with DXC** for shaders
- **CMake + Ninja + MSVC** for builds

The current executable is a native Ares Reach graybox. The player lands inside a Mars traversal arena, moves through terrain and structural obstacles, and completes the mission by reaching the objective beacon. The camera follows the player and the entire scene is rendered as independently transformed, depth-tested, directionally lit geometry.

This is real native gameplay infrastructure, not final art. The AAA-quality target has not yet been achieved.

## Controls

| Action | Input |
|---|---|
| Move | WASD or arrow keys |
| Sprint | Left or right Shift |
| Reset mission | R |
| Exit | Escape |

## Build on Windows

Requirements:

- Windows 10 or 11
- x64 MSVC developer environment
- CMake 3.25+
- Ninja
- Windows SDK containing `dxc.exe`

```powershell
$dxc = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter dxc.exe -Recurse |
  Where-Object { $_.FullName -match '\x64\dxc\.exe$' } |
  Sort-Object FullName -Descending |
  Select-Object -First 1

cmake -S native -B build/native -G Ninja `
  -DCMAKE_BUILD_TYPE=RelWithDebInfo `
  -DMARS_ENABLE_D3D12_VALIDATION=ON `
  -DDXC_EXECUTABLE="$($dxc.FullName)"
cmake --build build/native --parallel
ctest --test-dir build/native --output-on-failure
.\build\native\mars_native.exe
```

## Automated native verification

```powershell
.\build\native\mars_native.exe --self-test
.\build\native\mars_native.exe --warp-smoke-test
```

The WARP smoke test creates a validation-enabled Direct3D 12 software device, runs the native Ares Reach scene, resizes the swap chain, reads back the rendered frame, and rejects output without a substantial non-background pixel region.

## Production state

- Phase 0 — repository and product authority: complete
- Phase 1 — gameplay-system foundation: complete
- Phase 2 — campaign and mission-state architecture: complete
- Phase 3 — Windows native renderer foundation: complete
- Phase 4 — native scene, asset, animation, and gameplay migration: in progress
- Phase 5 — AAA visual vertical slice: pending
- Phase 6 — campaign production: pending
- Phase 7 — optimization, tooling, packaging, and soak: pending
- Phase 8 — external validation and release evidence: pending

See `AUTHORITATIVE_PRODUCTION_PLAN.md` for the binding production gates.

## Quality claim

`AAA-quality target` is accurate. `AAA-quality achieved` is not.
