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
    "docs/PHASE3_NATIVE_RENDERER_FOUNDATION.md",
    "docs/decisions/0016-windows-native-renderer.md",
    "native/CMakeLists.txt",
    "native/shaders/triangle.hlsl",
    "native/src/main.cpp",
    "native/src/platform/win32_window.cpp",
    "native/src/platform/win32_window.h",
    "native/src/renderer/d3d12_renderer.cpp",
    "native/src/renderer/d3d12_renderer.h",
}
_CI_VERIFICATION_KEYS = (
    "native_build_verification",
    "native_runtime_self_test",
    "warp_smoke_test",
    "validation_clean_ci_runtime",
    "ci_rendered_geometry_verification",
    "gpu_pixel_readback_verification",
)


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

    ci_verification = {key: manifest.get(key) for key in _CI_VERIFICATION_KEYS}
    ci_states = set(ci_verification.values())
    verification_run = manifest.get("verification_run")
    ci_pending = ci_states == {"pending"}
    ci_passed = ci_states == {"passed"}
    record(
        "ci_verification_coherent",
        (ci_pending and verification_run in {None, "requested"})
        or (
            ci_passed
            and isinstance(verification_run, str)
            and verification_run.isdigit()
        ),
        {
            "verification": ci_verification,
            "verification_run": verification_run,
        },
    )
    record(
        "visual_claim_fail_closed",
        manifest.get("visual_quality_claim") == "prototype_3d_kernel_only"
        and manifest.get("aaa_claim") == "target_not_achieved"
        and manifest.get("founder_hardware_validation") == "pending"
        and manifest.get("founder_visual_inspection") == "pending",
        {
            "visual_quality_claim": manifest.get("visual_quality_claim"),
            "aaa_claim": manifest.get("aaa_claim"),
            "founder_hardware_validation": manifest.get(
                "founder_hardware_validation"
            ),
            "founder_visual_inspection": manifest.get("founder_visual_inspection"),
        },
    )

    missing = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing, missing)

    cmake = (ROOT / "native/CMakeLists.txt").read_text(encoding="utf-8")
    renderer = (ROOT / "native/src/renderer/d3d12_renderer.cpp").read_text(
        encoding="utf-8"
    )
    renderer_header = (ROOT / "native/src/renderer/d3d12_renderer.h").read_text(
        encoding="utf-8"
    )
    shader = (ROOT / "native/shaders/triangle.hlsl").read_text(encoding="utf-8")
    entrypoint = (ROOT / "native/src/main.cpp").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/native-renderer.yml").read_text(
        encoding="utf-8"
    )
    record(
        "native_build_contract",
        "CMAKE_CXX_STANDARD 23" in cmake
        and "DXC_EXECUTABLE" in cmake
        and "MARS_ENABLE_D3D12_VALIDATION" in cmake
        and "d3d12" in cmake
        and "dxgi" in cmake
        and "mars_native" in cmake
        and "--self-test" in entrypoint
        and "--warp-smoke-test" in entrypoint
        and "/W4" in cmake
        and "/WX" in cmake,
        {
            "cxx23": "CMAKE_CXX_STANDARD 23" in cmake,
            "dxc": "DXC_EXECUTABLE" in cmake,
            "validation": "MARS_ENABLE_D3D12_VALIDATION" in cmake,
            "warnings_as_errors": "/W4" in cmake and "/WX" in cmake,
            "self_test": "--self-test" in entrypoint,
            "warp_smoke_test": "--warp-smoke-test" in entrypoint,
        },
    )
    record(
        "renderer_3d_kernel_present",
        "D3D12CreateDevice" in renderer
        and "CreateSwapChainForHwnd" in renderer
        and "CreateDepthBuffer" in renderer
        and "DXGI_FORMAT_D32_FLOAT" in renderer
        and "XMMatrixPerspectiveFovLH" in renderer
        and "SetGraphicsRootConstantBufferView" in renderer
        and "DrawIndexedInstanced" in renderer
        and "ResizeBuffers" in renderer
        and "SetEventOnCompletion" in renderer
        and "GetDeviceRemovedReason" in renderer
        and "cbuffer SceneConstants" in shader
        and "NORMAL" in shader,
        {
            "device": "D3D12CreateDevice" in renderer,
            "swap_chain": "CreateSwapChainForHwnd" in renderer,
            "depth": "CreateDepthBuffer" in renderer,
            "perspective_camera": "XMMatrixPerspectiveFovLH" in renderer,
            "scene_constants": "SetGraphicsRootConstantBufferView" in renderer,
            "indexed_draw": "DrawIndexedInstanced" in renderer,
            "resize": "ResizeBuffers" in renderer,
            "device_loss": "GetDeviceRemovedReason" in renderer,
            "lit_shader": "cbuffer SceneConstants" in shader and "NORMAL" in shader,
        },
    )
    record(
        "gpu_output_evidence_path",
        "FrameCaptureEvidence" in renderer_header
        and "RequestFrameCapture" in renderer
        and "CopyTextureRegion" in renderer
        and "ConsumeFrameCapture" in renderer
        and "non_background_pixels" in renderer
        and "capture.non_background_pixels < 1'000" in entrypoint
        and "Run validation-enabled D3D12 WARP smoke test" in workflow,
        {
            "capture_contract": "FrameCaptureEvidence" in renderer_header,
            "gpu_copy": "CopyTextureRegion" in renderer,
            "pixel_analysis": "non_background_pixels" in renderer,
            "threshold": "capture.non_background_pixels < 1'000" in entrypoint,
            "ci_warp_run": "Run validation-enabled D3D12 WARP smoke test"
            in workflow,
        },
    )

    plan = (ROOT / "AUTHORITATIVE_PRODUCTION_PLAN.md").read_text(
        encoding="utf-8"
    )
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
            "This audit proves an explicit Windows-native 3D renderer architecture, "
            "validation-enabled WARP execution contract, and GPU pixel-readback evidence "
            "path. It does not prove founder-reference-PC hardware behavior, founder visual "
            "approval, authored game art, or AAA graphics."
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
