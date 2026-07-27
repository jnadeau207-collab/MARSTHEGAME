# MARSTHEGAME

A custom-engine action game with an AAA-quality target.

## Current product truth

The repository currently contains two distinct runtimes:

1. **Python + Pygame compatibility runtime** — the original procedural 2D prototype, protected Classic Mode, deterministic gameplay/save/replay oracle, and rapid validation tooling.
2. **C++23 + Direct3D 12 native runtime** — the Windows shipping architecture now under active development.

The Python runtime is not the final graphics architecture. The native renderer is not yet an AAA visual slice. The current truthful visual state is a validation-clean 3D renderer kernel with a lit, depth-tested perspective cube and verified GPU pixel readback.

## Native Windows runtime

Requirements:

- Windows 10/11
- x64 MSVC developer environment
- CMake 3.25+
- Ninja
- Windows SDK with `dxc.exe`

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
.\build\native\mars_native.exe
```

Automated native checks:

```powershell
.\build\native\mars_native.exe --self-test
.\build\native\mars_native.exe --warp-smoke-test
```

The WARP smoke test creates a validation-enabled Direct3D 12 software device, renders and resizes the 3D scene, reads back the back buffer, and rejects output without a meaningful non-background pixel region.

## Python compatibility runtime

Requirements:

- Python 3.11 or 3.12
- Pygame 2.5+

```bash
python -m pip install -r requirements.txt
python main.py
```

### Compatibility controls

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | A/D or arrows | Left stick |
| Jump | Space / K | A / Cross |
| Dash | Left Shift / J | X |
| Attack | J / Z | B |
| Interact | E / F | Y |
| Pause | Escape / P | Start |
| Confirm | Enter / Space | A |

## Playable content

### Classic Mode

Eight short procedural 2D chapters remain protected and replayable as legacy compatibility content:

1. Pretoria Streets
2. Crossing (Canada)
3. College & Zip2
4. X.com / PayPal Wars
5. Tesla Factory Floor
6. SpaceX: Failures Before Flight
7. Starship to Mars
8. Mars Colony

### Fictionalized campaign

Implemented:

- **Ares Reach: First Descent**
- **Relay Echo**

Planned and non-playable:

- **Phobos Vector**
- **Frontier Burn**

The implemented missions currently run through the Python compatibility backend. Native gameplay migration begins after the renderer foundation and versioned scene/asset contracts.

## Remaining phases

Six major phases remain after the completed repository/gameplay/campaign foundations:

- Phase 3 — Windows native renderer foundation
- Phase 4 — scene, asset, animation, and gameplay migration
- Phase 5 — AAA visual vertical slice
- Phase 6 — campaign content production
- Phase 7 — optimization, tooling, packaging, and soak
- Phase 8 — external validation and release evidence

See `AUTHORITATIVE_PRODUCTION_PLAN.md` for the founder-controlled production authority.

## Quality claim

`AAA-quality target` is accurate. `AAA-quality achieved` is not.

The claim may change only after authored shipping content, founder hardware/visual approval, performance and soak evidence, complete campaign quality, and representative external playtests satisfy the committed gates.
