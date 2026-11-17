# IHZA S. Mascot — 40×40 Voxel Blockout

The updated source sprite was checked and is **40×40 px**, with a transparent **4 px margin** around the visible 32×32 artwork.

## Files
- `build_voxel_mascot_40x40.py`: Blender 3.6+ script that builds the voxel head, saves a .blend file, exports GLB, and renders a preview.
- `original-sprite-40x40.png`: transparent source sprite used by the builder.

## Run
1. Download both files into the same folder.
2. Open Blender 3.6+.
3. Go to Scripting, open the Python script and click Run Script.
4. The .blend, .glb and preview PNG are saved beside the script.

## Geometry contract
- Every visible source pixel becomes one 1×1×1 cube on the front plane.
- Added depth uses identical unit cubes aligned to integer coordinates.
- No scaled cuboids, bevels, subdivision, or smooth voxel geometry.

The rear volume is a first-pass approximation and still needs visual review from side/back views.
