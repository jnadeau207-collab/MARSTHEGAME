#!/usr/bin/env python3
"""Audit the Phase 3 Windows-native renderer foundation without overstating visuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "AUTHORITATIVE_PRODUCTION_PLAN.md",
    "config/phase3_renderer.json",
    "docs/decisions/0016-windows-native-renderer.md",
    "native/CMakeLists.txt",
    "native/shaders/triangle.hlsl",
    "native/src/main.cpp",
    "native/src/platform/win32_window.cpp",
    "native/src/platform/win32_window.h",
    "native/src/renderer/d3d12_renderer.cpp",
    "native/src/renderer/d3d12_renderer.h",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_phase3_renderer(manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "evidence": evidence,
            }
        )

    record(
        "manifest_truth",
        manifest.get("schema_version") == 1
        and manifest.get("phase") == "Phase 3"
        and manifest.get("status") == "in_progress"
        and manifest.get("tranche") == "windows_native_renderer_foundation"
        and manifest.get("shipping_runtime_language") == "c++23"
        and manifest.get("graphics_api") == "direct3d12"
        and manifest.get("shader_language") == "hlsl"
        and manifest.get("shader_compiler") == "dxc"
        and manifest.get("build_system") == "cmake"
        and manifest.get("primary_platform") == "windows"
        and manifest.get("third_party_game_engine") is False
        and manifest.get("three_js_shipping_runtime") is False
        and manifest.get("pygame_role") == "compatibility_and_behavior_oracle"
        and manifest.get("remaining_phase_count_after_phase2") == 6
        and manifest.get("aaa_claim") == "target_not_achieved",
        manifest,
    )

    verification_values = {
        key: manifest.get(key)
        for key in (
            "native_build_verification",
            "native_runtime_self_test",
            "validation_clean_runtime",
            "indexed_mesh_rendered",
        )
    }
    record(
        "verification_states_bounded",
        all(value in {"pending", "passed"} for value in verification_values.values()),
        verification_values,
    )
    record(
        "visual_claim_fail_closed",
        manifest.get("visual_quality_claim") == "prototype_kernel_only"
        and manifest.get("aaa_claim") == "target_not_achieved"
        and manifest.get("validation_clean_runtime") == "pending"
        and manifest.get("indexed_mesh_rendered") == "pending",
        {
            "visual_quality_claim": manifest.get("visual_quality_claim"),
            "aaa_claim": manifest.get("aaa_claim"),
            "validation_clean_runtime": manifest.get("validation_clean_runtime"),
            "indexed_mesh_rendered": manifest.get("indexed_mesh_rendered"),
        },
    )

    missing = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing, missing)

    cmake = (ROOT / "native/CMakeLists.txt").read_text(encoding="utf-8")
    renderer = (ROOT / "native/src/renderer/d3d12_renderer.cpp").read_text(encoding="utf-8")
    shader = (ROOT / "native/shaders/triangle.hlsl").read_text(encoding="utf-8")
    entrypoint = (ROOT / "native/src/main.cpp").read_text(encoding="utf-8")
    record(
        "native_build_contract",
        "CMAKE_CXX_STANDARD 23" in cmake
        and "DXC_EXECUTABLE" in cmake
        and "d3d12" in cmake
        and "dxgi" in cmake
        and "mars_native" in cmake
        and "--self-test" in entrypoint,
        {
            "cxx23": "CMAKE_CXX_STANDARD 23" in cmake,
            "dxc": "DXC_EXECUTABLE" in cmake,
            "d3d12": "d3d12" in cmake,
            "self_test": "--self-test" in entrypoint,
        },
    )
    record(
        "renderer_kernel_present",
        "D3D12CreateDevice" in renderer
        and "CreateSwapChainForHwnd" in renderer
        and "CreateCommandQueue" in renderer
        and "CreateCommandAllocator" in renderer
        and "CreateGraphicsPipelineState" in renderer
        and "DrawIndexedInstanced" in renderer
        and "ResourceBarrier" in renderer
        and "SetEventOnCompletion" in renderer
        and "ResizeBuffers" in renderer
        and "VSMain" in shader
        and "PSMain" in shader,
        {
            "device": "D3D12CreateDevice" in renderer,
            "swap_chain": "CreateSwapChainForHwnd" in renderer,
            "pipeline": "CreateGraphicsPipelineState" in renderer,
            "indexed_draw": "DrawIndexedInstanced" in renderer,
            "fence": "SetEventOnCompletion" in renderer,
            "resize": "ResizeBuffers" in renderer,
        },
    )

    plan = (ROOT / "AUTHORITATIVE_PRODUCTION_PLAN.md").read_text(encoding="utf-8")
    decision = (ROOT / "docs/decisions/0016-windows-native-renderer.md").read_text(
        encoding="utf-8"
    )
    record(
        "architecture_decision_explicit",
        "C++23" in plan
        and "Direct3D 12" in plan
        and "Exactly six major phases remain" in plan
        and "Three.js is not the shipping renderer" in plan
        and "Status: Accepted" in decision,
        {
            "plan_cxx": "C++23" in plan,
            "plan_d3d12": "Direct3D 12" in plan,
            "finite_phases": "Exactly six major phases remain" in plan,
            "three_js_boundary": "Three.js is not the shipping renderer" in plan,
        },
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 3",
        "tranche": "windows_native_renderer_foundation",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "This audit proves an explicit Windows-native renderer architecture and source/build "
            "boundary. It does not prove that a founder-reference-PC GPU run is validation-clean, "
            "that the indexed mesh has been visually inspected, or that AAA graphics exist."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path("config/phase3_renderer.json"),
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        report = audit_phase3_renderer(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 3",
            "tranche": "windows_native_renderer_foundation",
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
