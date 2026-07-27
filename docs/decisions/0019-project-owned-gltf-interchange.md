# ADR 0019: Project-owned glTF interchange

- Status: Accepted
- Date: 2026-07-27
- Decision owner: Founder

## Decision

MARSTHEGAME may use a strict, deliberately limited glTF 2.0 ingestion path for geometry authored and retained inside this repository.

This does not introduce an external asset library, a marketplace dependency, or a third-party engine. Procedural code-authored terrain, rocks, columns, and other project-owned generated content remain first-class production systems. glTF serves as a project-owned interchange format for geometry that is more naturally expressed as authored mesh data.

## Initial supported subset

- one glTF 2.0 mesh
- one indexed TRIANGLES primitive
- one embedded base64 buffer
- POSITION and NORMAL float VEC3 accessors
- unsigned byte, unsigned short, or unsigned int indices
- no sparse accessors, morph targets, skinning, materials, textures, or external files

The importer fails closed on malformed JSON, invalid ranges, unsupported features, non-finite data, invalid normals, bad indices, degenerate triangles, inconsistent counts, and excessive sizes.

## Cooked package

The native mesh cooker produces a versioned binary package with:

- stable project-owned mesh identifier
- source provenance hash
- cooked payload checksum
- cooked bounds
- deterministic vertex and index payloads
- transactional temporary-file commit and backup rotation

## Current boundary

This decision and its first implementation prove CPU-side ingestion, deterministic cooking, package validation, and corruption rejection. The current executable continues to render the existing procedural mesh atlas until a separate renderer integration tranche is completed and verified.
