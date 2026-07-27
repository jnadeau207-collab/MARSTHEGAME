# Phase 5 Implementation Notes

The renderer is intentionally split into ordered implementation fragments included by `d3d12_renderer.cpp`. This keeps one translation unit and private implementation scope while allowing the large explicit Direct3D 12 pass graph to remain reviewable.

The fragments are not independent compilation units and must remain included in numeric order.
