"""Build the IHZA S. head-only voxel mascot in Blender.

Requirements: Blender 3.6+ (no external Python packages).
Input: original-sprite.png in the same folder as this script.

Geometry contract:
- Front-facing source sprite: 32x32 pixels.
- Every source pixel is represented by a 1x1x1 cube.
- All additional depth voxels use the same 1x1x1 cube size and integer grid.
- No scaled cuboids, bevels, subdivision, or smooth voxel geometry.

Run from Blender's Scripting workspace. The script builds a collection, camera,
lighting and saves ihza_mascot_voxel_blockout.blend next to this file.
"""

from pathlib import Path
import math
import bpy
from mathutils import Vector

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "original-sprite.png"
OUTPUT_BLEND = BASE_DIR / "ihza_mascot_voxel_blockout.blend"
VOXEL = 1.0

# Original Aseprite colors -> refined pastel palette.
# Any unrecognized source color is preserved approximately.
COLOR_MAP = {
    (162, 162, 255): (200, 182, 242, 255),  # lilac highlight
    (82, 82, 166):   (75, 59, 98, 255),      # deep plum
    (94, 94, 255):   (169, 149, 214, 255),   # lavender
    (117, 117, 255): (169, 149, 214, 255),   # lavender
    (107, 107, 255): (169, 149, 214, 255),   # lavender
    (171, 171, 255): (200, 182, 242, 255),   # lilac
    (140, 140, 255): (169, 149, 214, 255),   # lavender
    (101, 101, 166): (75, 59, 98, 255),      # deep plum
    (149, 149, 219): (200, 182, 242, 255),   # lilac
    (153, 153, 255): (200, 182, 242, 255),   # lilac
    (255, 220, 201): (246, 210, 195, 255),   # peach
    (180, 255, 255): (101, 201, 214, 255),   # cyan
    (251, 86, 86):   (224, 123, 123, 255),   # coral
    (243, 73, 73):   (224, 123, 123, 255),   # coral
}

PALETTE_NAMES = {
    (169, 149, 214, 255): "Lavender",
    (200, 182, 242, 255): "Lilac",
    (246, 210, 195, 255): "Peach",
    (101, 201, 214, 255): "Cyan",
    (224, 123, 123, 255): "Coral",
    (75, 59, 98, 255): "Plum",
}


def srgb_to_linear(v):
    v = v / 255.0
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def load_sprite_pixels(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing source sprite: {path}")
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    width, height = image.size
    if width != 32 or height != 32:
        raise ValueError(f"Expected a 32x32 sprite, got {width}x{height}")
    pixels = list(image.pixels[:])
    data = []
    for y in range(height):
        row = []
        for x in range(width):
            i = (y * width + x) * 4
            rgba = tuple(max(0, min(255, round(pixels[i + c] * 255))) for c in range(4))
            src = rgba[:3]
            mapped = COLOR_MAP.get(src, rgba)
            row.append(mapped)
        data.append(row)
    bpy.data.images.remove(image)
    return data


def dilate_mask(mask, radius=1):
    h = len(mask)
    w = len(mask[0])
    out = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            found = False
            for yy in range(max(0, y-radius), min(h, y+radius+1)):
                for xx in range(max(0, x-radius), min(w, x+radius+1)):
                    if mask[yy][xx]:
                        found = True
                        break
                if found:
                    break
            out[y][x] = found
    return out


def build_voxel_map(sprite):
    """Return {(x, y, z): rgba} where every occupied cell is one unit cube."""
    h, w = len(sprite), len(sprite[0])
    skin = (246, 210, 195, 255)
    cyan = (101, 201, 214, 255)
    coral = (224, 123, 123, 255)
    plum = (75, 59, 98, 255)
    lavender = (169, 149, 214, 255)
    lilac = (200, 182, 242, 255)

    # Pixel-art face area: skin pixels plus the small eye/cheek/nose details
    # that sit inside the face. Hair fringe remains a surface layer in front.
    raw_face = [[sprite[y][x] == skin for x in range(w)] for y in range(h)]
    face = dilate_mask(raw_face, radius=1)
    for y in range(h):
        for x in range(w):
            if 18 <= y <= 29 and 5 <= x <= 27:
                if sprite[y][x] in (cyan, coral, plum):
                    face[y][x] = True

    voxels = {}

    # Front plane: exact 32x32 sprite silhouette, one cube per pixel.
    for y in range(h):
        for x in range(w):
            voxels[(x, h - 1 - y, 0)] = sprite[y][x]

    # Extrude the face backwards as a shallow facial volume.
    for y in range(h):
        for x in range(w):
            if face[y][x]:
                for z in range(1, 7):
                    voxels[(x, h - 1 - y, z)] = skin

    # Hair voxels follow the source pixel mask. Depth varies only by integer
    # cube count, never by cube dimensions.
    for y in range(h):
        for x in range(w):
            c = sprite[y][x]
            is_hair = c in (lavender, lilac, plum)
            if is_hair and not face[y][x]:
                # Center/top hair gets more volume; outer edges taper.
                dx = (x - 15.5) / 16.0
                dy = (y - 15.5) / 16.0
                radial = max(0.0, 1.0 - dx*dx - dy*dy)
                depth = max(2, round(14.0 * math.sqrt(radial)))
                for z in range(1, depth + 1):
                    voxels.setdefault((x, h - 1 - y, z), c)
            elif c == coral and not face[y][x]:
                # Side hair accents are shallow, raised pixel blocks.
                for z in range(1, 3):
                    voxels.setdefault((x, h - 1 - y, z), coral)

    # Rounded rear skull/cap. This is the deliberately designed unseen side:
    # concentric ellipsoidal slices on the same integer voxel grid.
    # It makes the head a volume rather than a flat extruded billboard.
    for z in range(7, 17):
        t = (z - 7) / 9.0
        scale = math.sqrt(max(0.0, 1.0 - t*t))
        rx = 13.2 * scale
        ry = 14.3 * scale
        if rx < 0.75 or ry < 0.75:
            continue
        for y in range(h):
            for x in range(w):
                nx = (x - 15.5) / rx
                ny = (y - 15.5) / ry
                if nx*nx + ny*ny <= 1.0:
                    edge = nx*nx + ny*ny
                    if edge > 0.78:
                        c = plum
                    elif (x + 2*y) % 9 in (0, 1):
                        c = lilac
                    else:
                        c = lavender
                    voxels.setdefault((x, h - 1 - y, z), c)

    return voxels


def make_material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = tuple(srgb_to_linear(v) for v in rgba[:3]) + (1.0,)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = mat.diffuse_color
        bsdf.inputs["Roughness"].default_value = 0.72
    return mat


def mesh_for_color(name, rgba, coords):
    verts = []
    faces = []
    half = VOXEL / 2.0
    corners = [
        (-half,-half,-half), (half,-half,-half), (half,half,-half), (-half,half,-half),
        (-half,-half,half),  (half,-half,half),  (half,half,half),  (-half,half,half),
    ]
    cube_faces = [
        (0,3,2,1), (4,5,6,7), (0,1,5,4),
        (1,2,6,5), (2,3,7,6), (3,0,4,7),
    ]
    for x, y, z in coords:
        base = len(verts)
        # Blender-native axes: X horizontal, Y depth, Z vertical.
        center = (x - 15.5, z + 0.5, y - 15.5)
        for cx, cy, cz in corners:
            verts.append((center[0]+cx, center[1]+cy, center[2]+cz))
        for f in cube_faces:
            faces.append(tuple(base+i for i in f))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    return obj


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)


def main():
    clear_scene()
    sprite = load_sprite_pixels(IMAGE_PATH)
    voxel_map = build_voxel_map(sprite)

    collection = bpy.data.collections.new("IHZA Mascot | Voxel Head")
    bpy.context.scene.collection.children.link(collection)

    by_color = {}
    for coord, color in voxel_map.items():
        by_color.setdefault(color, []).append(coord)

    for color, coords in by_color.items():
        role = PALETTE_NAMES.get(color, "Color")
        obj = mesh_for_color("Voxel_" + role, color, coords)
        collection.objects.link(obj)
        mat = make_material("Mat_" + role, color)
        obj.data.materials.append(mat)
        obj["voxel_size"] = VOXEL
        obj["voxel_count"] = len(coords)
        obj["design_rule"] = "1 source pixel = 1 unit cube"

    # Camera and soft studio lighting for a useful first inspection render.
    bpy.ops.object.camera_add(location=(43, -52, 38))
    camera = bpy.context.object
    camera.name = "Mascot_Camera"
    look_at(camera, (0, 7, 0))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 52
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type='AREA', location=(4, -28, 28))
    key = bpy.context.object
    key.name = "Softbox_Key"
    key.data.energy = 4200
    key.data.shape = 'DISK'
    key.data.size = 24
    look_at(key, (0, 7, 0))

    bpy.ops.object.light_add(type='AREA', location=(-28, -4, 10))
    fill = bpy.context.object
    fill.name = "Softbox_Fill"
    fill.data.energy = 1800
    fill.data.size = 20
    look_at(fill, (0, 7, 0))

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'EEVEE_NEXT') else 'BLENDER_EEVEE'
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.35, 0.32, 0.38)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(BASE_DIR / "voxel_mascot_preview.png")

    # Select the mascot meshes, not the camera/lights.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    if collection.objects:
        bpy.context.view_layer.objects.active = collection.objects[0]

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    print(f"Built {len(voxel_map)} voxels; saved {OUTPUT_BLEND}")


if __name__ == "__main__":
    main()
