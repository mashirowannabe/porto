# IHZA S. Mascot — Voxel Blueprint

## Direction

A floating, head-only mascot derived from the original 32×32 Aseprite sprite.

- Hair: asymmetrical lavender silhouette.
- Eyes: cyan pixel-style eyes.
- Expression: calm.
- Skin: warm peach.
- Accent: coral/red hair clips or side accents, as shown in the approved concept.
- Style: refined voxel, not generic blocky low-poly.

## Core geometric rule

**1 source pixel = 1 voxel.**

All voxels use one fixed cube dimension and align to a single integer grid. Do not replace clusters of pixels with larger cuboids. Do not mix cube sizes. Do not bevel individual voxels in a way that changes their apparent unit size.

For hair volume, extend the same grid backward in layers. Shape the silhouette by adding/removing unit voxels, not by scaling individual blocks.

## Preserve from approved concept

- Keep the current face proportions and calm expression.
- Keep pixel-style eyes.
- Keep the refined pastel color direction.
- Only refine the hair geometry for strict voxel consistency. Do not redesign other facial features unless the user requests it.

## Palette (working values)

| Role | Color | Hex |
|---|---|---|
| Lavender | Main hair | #A995D6 |
| Lilac | Hair highlight | #C8B6F2 |
| Peach | Skin | #F6D2C3 |
| Cyan | Eyes | #65C9D6 |
| Coral | Hair accents / cheek accents | #E07B7B |
| Plum | Deep shadow / outlines | #4B3B62 |
| Cream | Neutral background | #F7F2EA |

Palette is a working proposal, not a final material specification.

## Modeling requirements

1. Build on a fixed voxel grid with one cube size.
2. Keep hair asymmetrical while maintaining a consistent voxel unit.
3. Use front, side, back, and 3/4 orthographic checks.
4. Ensure the back of the head is a coherent continuation of the front silhouette.
5. Keep face and eye shapes pixel-like.
6. Use lighting/materials to create depth; do not rely on irregular block sizes.

## Suggested Blender approach

- Start with one unit cube and duplicate it on integer grid coordinates.
- Use linked duplicates or a procedural collection/geometry-nodes workflow to preserve identical dimensions.
- Organize collections: Hair, Face, Eyes, Accents.
- Use orthographic views and a reference grid while placing voxels.
- Avoid subdivision and bevel modifiers on the voxel geometry.
- Export the final mascot as GLB after validating scale, origin, and materials.

## Current stage

Concept direction approved. Next work item: create a strict-grid hair voxel layout and 3D blockout. The current concept sheet is a visual reference only; its generated turnaround is not yet a production-accurate voxel map.
