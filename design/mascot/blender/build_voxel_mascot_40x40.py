"""
IHZA S. — voxel mascot builder for Blender 3.6+

Input:
  original-sprite-40x40.png (must sit beside this script)

Rules:
  - The sprite is 40x40 with transparent 4px margin.
  - Each visible source pixel becomes one 1x1x1 cube on the front plane.
  - All depth voxels use the same cube size and integer grid.
  - No bevel, subdivision, scaled cuboids, or smooth voxel geometry.

Run in Blender's Scripting workspace. It creates:
  ihza_mascot_voxel_40x40.blend
  ihza_mascot_voxel_40x40.glb
  voxel_mascot_preview.png
"""

from pathlib import Path
import math
import bpy
from mathutils import Vector

try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    script_text = next((item for item in bpy.data.texts if item.filepath), None)
    if script_text is None:
        raise RuntimeError(
            "Open this .py file from disk in Blender's Text Editor before running it."
        )
    BASE_DIR = Path(bpy.path.abspath(script_text.filepath)).resolve().parent

IMAGE_PATH = BASE_DIR / "original-sprite-40x40.png"
OUTPUT_BLEND = BASE_DIR / "ihza_mascot_voxel_40x40.blend"
OUTPUT_GLB = BASE_DIR / "ihza_mascot_voxel_40x40.glb"
OUTPUT_PREVIEW = BASE_DIR / "voxel_mascot_preview.png"
VOXEL = 1.0

LAV = (169, 149, 214, 255)
LIL = (200, 182, 242, 255)
PEA = (246, 210, 195, 255)
CYA = (101, 201, 214, 255)
COR = (224, 123, 123, 255)
PLU = (75, 59, 98, 255)

SOURCE_MAP = {
    (162, 162, 255): LIL,
    (82, 82, 166): PLU,
    (94, 94, 255): LAV,
    (117, 117, 255): LAV,
    (107, 107, 255): LAV,
    (171, 171, 255): LIL,
    (140, 140, 255): LAV,
    (101, 101, 166): PLU,
    (149, 149, 219): LIL,
    (153, 153, 255): LIL,
    (255, 220, 201): PEA,
    (180, 255, 255): CYA,
    (251, 86, 86): COR,
    (243, 73, 73): COR,
}

PALETTE_NAMES = {
    LAV: "Lavender",
    LIL: "Lilac",
    PEA: "Peach",
    CYA: "Cyan",
    COR: "Coral",
    PLU: "Plum",
}


def srgb_to_linear(value):
    value = value / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def dilate(mask, radius):
    height = len(mask)
    width = len(mask[0])
    result = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            result[y][x] = any(
                mask[yy][xx]
                for yy in range(max(0, y-radius), min(height, y+radius+1))
                for xx in range(max(0, x-radius), min(width, x+radius+1))
            )
    return result


def load_sprite(path):
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}")
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    if (width, height) != (40, 40):
        bpy.data.images.remove(image)
        raise ValueError(f"Expected 40x40 PNG, got {width}x{height}")

    values = list(image.pixels[:])
    pixels = [[None] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 4
            r, g, b, a = [int(round(values[i+c] * 255)) for c in range(4)]
            if a < 128:
                continue
            pixels[y][x] = SOURCE_MAP.get((r, g, b), (r, g, b, 255))
    bpy.data.images.remove(image)
    return pixels


def build_voxels(sprite):
    height = len(sprite)
    width = len(sprite[0])
    skin_mask = [[sprite[y][x] == PEA for x in range(width)] for y in range(height)]
    near_skin = dilate(skin_mask, 2)
    face_mask = dilate(skin_mask, 1)

    for y in range(height):
        for x in range(width):
            c = sprite[y][x]
            if c in (CYA, COR, PLU) and near_skin[y][x]:
                face_mask[y][x] = True

    voxels = {}

    # Front surface: exactly one cube for each non-transparent source pixel.
    hair_pixels = []
    for y in range(height):
        for x in range(width):
            color = sprite[y][x]
            if color is None:
                continue

            z = height - 1 - y
            voxels[(x, 0, z)] = color

            if face_mask[y][x]:
                for depth in range(1, 7):
                    voxels.setdefault((x, depth, z), PEA)
            elif color in (LAV, LIL, PLU):
                hair_pixels.append((x, y, z, color))
            elif color == COR:
                for depth in range(1, 3):
                    voxels.setdefault((x, depth, z), COR)

    # Hair depth varies by voxel count only, never by cube dimensions.
    for x, y, z, color in hair_pixels:
        dx = (x - 19.5) / 19.5
        dz = (y - 18.0) / 20.0
        profile = max(0.0, 1.0 - 0.58*dx*dx - 0.42*dz*dz)
        depth = 4 + round(7 * profile)
        for layer in range(1, depth + 1):
            voxels.setdefault((x, layer, z), color)

    # Rear skull cap: concentric integer-grid slices, still made of unit cubes.
    for depth in range(7, 16):
        t = (depth - 7) / 9.0
        scale = math.sqrt(max(0.0, 1.0 - t*t))
        rx = 15.3 * scale
        rz = 16.0 * scale
        if rx < 0.8 or rz < 0.8:
            continue
        for y in range(height):
            for x in range(width):
                if sprite[y][x] is None:
                    continue
                nx = (x - 19.5) / rx
                nz = (y - 19.5) / rz
                q = nx*nx + nz*nz
                if q <= 1.0:
                    if q > 0.80:
                        color = PLU
                    elif (x + y*2) % 11 in (0, 1, 2):
                        color = LIL
                    else:
                        color = LAV
                    voxels.setdefault((x, depth, height - 1 - y), color)

    return voxels


def make_material(color):
    name = "Mat_" + PALETTE_NAMES.get(color, "Accent")
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = tuple(srgb_to_linear(v) for v in color[:3]) + (1.0,)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = material.diffuse_color
        bsdf.inputs["Roughness"].default_value = 0.78
    return material


def create_color_mesh(name, coords):
    verts = []
    faces = []
    h = VOXEL / 2.0
    corners = [
        (-h,-h,-h), (h,-h,-h), (h,h,-h), (-h,h,-h),
        (-h,-h,h),  (h,-h,h),  (h,h,h),  (-h,h,h),
    ]
    cube_faces = [
        (0,3,2,1), (4,5,6,7), (0,1,5,4),
        (1,2,6,5), (2,3,7,6), (3,0,4,7),
    ]

    for x, depth, z in coords:
        base = len(verts)
        center = (x - 19.5, depth, z - 19.5)
        for cx, cy, cz in corners:
            verts.append((center[0]+cx, center[1]+cy, center[2]+cz))
        for face in cube_faces:
            faces.append(tuple(base + index for index in face))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def main():
    clear_scene()
    sprite = load_sprite(IMAGE_PATH)
    voxels = build_voxels(sprite)

    collection = bpy.data.collections.new("IHZA Mascot | Voxel Head")
    bpy.context.scene.collection.children.link(collection)

    by_color = {}
    for coord, color in voxels.items():
        by_color.setdefault(color, []).append(coord)

    mascot_objects = []
    for color, coords in by_color.items():
        obj = create_color_mesh("Voxel_" + PALETTE_NAMES.get(color, "Accent"), coords)
        collection.objects.link(obj)
        obj.data.materials.append(make_material(color))
        obj["voxel_size"] = VOXEL
        obj["voxel_count"] = len(coords)
        obj["design_rule"] = "1 source pixel = 1 unit cube"
        mascot_objects.append(obj)

    # Preview camera and studio lighting.
    bpy.ops.object.camera_add(location=(44, -58, 38))
    camera = bpy.context.object
    camera.name = "Mascot_Camera"
    look_at(camera, (0, 7, 0))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 58
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(4, -28, 28))
    key = bpy.context.object
    key.name = "Softbox_Key"
    key.data.energy = 4200
    key.data.shape = "DISK"
    key.data.size = 24
    look_at(key, (0, 7, 0))

    bpy.ops.object.light_add(type="AREA", location=(-28, -4, 10))
    fill = bpy.context.object
    fill.name = "Softbox_Fill"
    fill.data.energy = 1800
    fill.data.size = 20
    look_at(fill, (0, 7, 0))

    scene = bpy.context.scene
    engine_items = scene.render.bl_rna.properties["engine"].enum_items.keys()
    if "BLENDER_EEVEE_NEXT" in engine_items:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engine_items:
        scene.render.engine = "BLENDER_EEVEE"
    else:
        scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_PREVIEW)

    # Select mascot meshes only for GLB export.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mascot_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mascot_objects[0]

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        use_selection=True,
    )

    # Render preview with camera and lights.
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.scene.render.filepath = str(OUTPUT_PREVIEW)
    bpy.ops.render.render(write_still=True)

    print(f"Created {len(voxels)} unit voxels from a 40x40 transparent sprite.")


if __name__ == "__main__":
    main()
