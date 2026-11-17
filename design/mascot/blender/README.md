# Blender voxel mascot generator

This folder contains the first strict-grid Blender builder for the IHZA S. head-only mascot.

## Run
1. Keep `build_voxel_mascot.py` and `original-sprite.png` in the same folder.
2. Open Blender 3.6+.
3. Switch to the Scripting workspace, open the Python file, and click Run Script.
4. The script builds a collection of voxel meshes, assigns the refined pastel palette, adds a camera and soft lights, then saves `ihza_mascot_voxel_blockout.blend` beside the script.

## Rules
- Source sprite is 32×32.
- One source pixel maps to one 1×1×1 cube.
- All added depth voxels use the same cube dimensions and integer coordinates.
- No bevel, subdivision, scaled cuboids, or smooth voxel geometry.

The source image only provides a front view. Rear volume is a first-pass voxel approximation and still needs visual review from the side/back.
