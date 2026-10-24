"""X-Glasses XG-01 concept assembly. Run with Blender 4.5 --background --python.
All authored coordinates are millimetres; scene geometry is in metres.
Component envelopes are references, NOT certified manufacturing geometry.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("--output", default=str(ROOT / "artifacts/mechanical/xg01"))
parser.add_argument("--render", action="store_true")
args = parser.parse_args(
    sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
)
OUT = Path(args.output).resolve()
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 240
scene.world = bpy.data.worlds.new("Studio world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
    0.13,
    0.17,
    0.22,
    1,
)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.4
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = False
parts = []
roots = {}


def mm(v):
    return Vector(v) * 0.001


def material(name, color, metal=0, rough=0.4, transmission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    n = m.node_tree.nodes.get("Principled BSDF")
    n.inputs["Base Color"].default_value = (*color, 1)
    n.inputs["Metallic"].default_value = metal
    n.inputs["Roughness"].default_value = rough
    n.inputs["Transmission Weight"].default_value = transmission
    n.inputs["IOR"].default_value = 1.46
    return m


mat = {
    "body": material("01 | Graphite PA12 concept", (0.055, 0.072, 0.088), 0.25, 0.32),
    "trim": material("02 | Titanium grey", (0.28, 0.34, 0.39), 0.8, 0.25),
    "blue": material("03 | Signal cyan", (0.015, 0.45, 0.64), 0.55, 0.26),
    "rubber": material("04 | Soft contact silicone", (0.022, 0.031, 0.039), 0, 0.75),
    "lens": material("05 | Removable smoke lens", (0.15, 0.29, 0.34), 0, 0.12, 0.72),
    "pcb": material("06 | PCB reference envelope", (0.025, 0.19, 0.13), 0.15, 0.48),
    "gold": material("07 | Contact gold", (0.68, 0.39, 0.08), 0.75, 0.28),
    "black": material("08 | Optical isolation", (0.005, 0.008, 0.014), 0.05, 0.24),
    "glass": material("09 | Camera glass", (0.012, 0.055, 0.09), 0.5, 0.08),
    "white": material("10 | Technical lettering", (0.68, 0.83, 0.9), 0.1, 0.6),
    "orange": material("11 | Flexible interconnect", (0.62, 0.22, 0.055), 0.4, 0.42),
    "floor": material("12 | Studio surface", (0.019, 0.029, 0.044), 0.15, 0.58),
}


def group(name, offset):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    obj = bpy.data.objects.new(name + " / EXPLODE", None)
    collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.006
    obj["explosion_mm"] = list(offset)
    for frame, factor in ((1, 0), (35, 0), (110, 1), (150, 1), (225, 0), (240, 0)):
        obj.location = mm(offset) * factor
        obj.keyframe_insert(data_path="location", frame=frame)
    roots[name] = obj
    return collection, obj


G = {
    "frame": group("01 Frame chassis", (0, 0, 0)),
    "lensL": group("02 Left lens", (-12, -38, -9)),
    "lensR": group("03 Right lens", (12, -38, -9)),
    "retainers": group("04 Lens retainers", (0, 26, -9)),
    "pod": group("05 Sensor enclosure", (0, 0, 23)),
    "face": group("06 Optical faceplate", (0, -69, 34)),
    "camera": group("07 XIAO Sense camera stack", (-26, -25, 45)),
    "tof": group("08 VL53L5CX carrier", (29, -24, 45)),
    "bracket": group("09 Rigid alignment carrier", (0, 28, 40)),
    "back": group("10 Sensor rear cover", (0, 50, 47)),
    "nose": group("11 Nose pads", (0, -4, -43)),
    "left": group("12 Left temple shell", (-43, 4, 0)),
    "right": group("13 Right temple shell", (43, 4, 0)),
    "covers": group("14 Temple service covers", (0, 4, 46)),
    "imu": group("15 IMU reference carrier", (18, 4, 26)),
    "haptic": group("16 Haptic driver and motor", (-18, 4, 29)),
    "buttons": group("17 Tactile controls", (-60, 2, 30)),
    "pads": group("18 Ear contact sleeves", (0, 20, -22)),
    "usb": group("19 USB cable and strain relief", (45, 32, -6)),
    "fasteners": group("20 Fasteners and hinge pins", (0, 0, 70)),
    "wires": group("21 Internal harness schematic", (0, 10, 15)),
}


def register(
    o,
    name,
    material_key,
    g=None,
    note="Concept geometry; fit and tolerances unverified",
):
    o.name = name
    if material_key:
        o.data.materials.append(mat[material_key])
    if g:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        G[g][0].objects.link(o)
        o.parent = G[g][1]
        o["part_id"] = f"XG-{len(parts) + 1:03d}"
        o["design_status"] = note
        parts.append(o)
    return o


def bevel(o, radius=0.6, segments=3):
    b = o.modifiers.new("Edge radius / mm", "BEVEL")
    b.width = radius * 0.001
    b.segments = segments
    b.limit_method = "ANGLE"
    o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
    return o


def box(name, center, size, material_key, g=None, radius=0.5, note="Concept envelope"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=mm(center))
    o = bpy.context.object
    o.dimensions = mm(size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register(o, name, material_key, g, note)
    if radius:
        bevel(o, radius)
    return o


def cylinder(name, center, radius, length, material_key, g=None, axis="Y", vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius * 0.001,
        depth=length * 0.001,
        location=mm(center),
    )
    o = bpy.context.object
    if axis == "Y":
        o.rotation_euler[0] = math.pi / 2
    elif axis == "X":
        o.rotation_euler[1] = math.pi / 2
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register(o, name, material_key, g)
    bevel(o, 0.2, 2)
    return o


def cut(o, cutter):
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new("Machined opening", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def tube(name, coords, radius, material_key, g=None):
    c = bpy.data.curves.new(name, "CURVE")
    c.dimensions = "3D"
    c.resolution_u = 16
    c.bevel_depth = radius * 0.001
    c.bevel_resolution = 4
    spline = c.splines.new("BEZIER")
    spline.bezier_points.add(len(coords) - 1)
    for p, co in zip(spline.bezier_points, coords):
        p.co = mm(co)
        p.handle_left_type = p.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, c)
    scene.collection.objects.link(o)
    return register(o, name, material_key, g)


def contour(cx, width, height, cz, n=80):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = math.copysign(abs(math.cos(a)) ** 0.72, math.cos(a)) * width / 2
        z = math.copysign(abs(math.sin(a)) ** 0.8, math.sin(a)) * height / 2
        pts.append((cx + x, cz + z))
    return pts


def eyewire(name, cx, width, height, thickness, depth, y, material_key, g, solid=False):
    outer = contour(cx, width, height, -5)
    inner = contour(cx, width - 2 * thickness, height - 2 * thickness, -5)
    loops = [outer, outer] if solid else [outer, outer, inner, inner]
    verts = []
    for j, points in enumerate(loops):
        yy = y + (depth / 2 if j % 2 else -depth / 2)
        verts.extend(
            [(x * 0.001, (yy + 0.0011 * x * x) * 0.001, z * 0.001) for x, z in points]
        )
    n = len(outer)
    faces = []
    for i in range(n):
        k = (i + 1) % n
        faces.append((i, k, n + k, n + i))
        if not solid:
            faces.extend(
                [
                    (2 * n + k, 2 * n + i, 3 * n + i, 3 * n + k),
                    (k, i, 2 * n + i, 2 * n + k),
                    (n + i, n + k, 3 * n + k, 3 * n + i),
                ]
            )
    if solid:
        faces.extend([tuple(reversed(range(n))), tuple(range(n, 2 * n))])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(o)
    register(o, name, material_key, g)
    bevel(o, 0.45)
    return o


# Main frame: lens apertures remain real openings, not black filled shapes.
for side, cx in (("L", -35), ("R", 35)):
    eyewire(side + " structural lens rim", cx, 62, 42, 3.1, 5, 0, "body", "frame")
    eyewire(
        side + " replaceable lens",
        cx,
        55.4,
        35.4,
        0,
        1.2,
        0.3,
        "lens",
        "lens" + side,
        True,
    )
    eyewire(side + " rear lens clamp", cx, 58, 38, 1.3, 1.3, 3.25, "trim", "retainers")
    tube(
        side + " brow accent",
        [(cx - 27, 2, 15), (cx, 0, 17), (cx + 27, 2, 15)],
        0.65,
        "blue",
        "frame",
    )
tube("Rigid bridge", [(-8, 0.2, 7), (0, -0.2, 10), (8, 0.2, 7)], 2.8, "body", "frame")
for s in (-1, 1):
    tube(
        "Brow to hinge " + str(s),
        [(s * 60, 4, 13), (s * 69, 7, 14), (s * 73, 12, 14)],
        3.4,
        "body",
        "frame",
    )

# Sensor pod sized around a full Sense stack, not an imaginary naked sensor.
pod = box(
    "Central sensor enclosure / 54 x 25 x 28",
    (0, -1, 22),
    (54, 25, 28),
    "body",
    "pod",
    2,
)
cut(pod, box("tool cavity", (0, 1, 22), (50, 30, 24), None, radius=0))
# Open front and rear: faceplate is removable, bracket and back cover separate.
face = box(
    "Optical faceplate / separate apertures",
    (0, -14.25, 22),
    (54, 1.5, 28),
    "trim",
    "face",
    1.1,
)
cut(face, cylinder("tool camera", (-12, -14, 22), 5.8, 8, None))
cut(face, box("tool ToF", (14, -14, 22), (10, 8, 5.5), None, radius=0))
# ToF baffle has an open optical channel; no invented opaque IR window.
baffle = box(
    "ToF open optical baffle", (14, -12.5, 22), (11, 3, 6.5), "black", "tof", 0.35
)
cut(baffle, box("tool ToF baffle", (14, -12.5, 22), (9, 5, 4.5), None, radius=0))
box(
    "ToF Tx-Rx divider placeholder",
    (14, -12.5, 22),
    (0.6, 2.7, 4.4),
    "black",
    "tof",
    0.1,
    "Divider position must follow actual VL53L5CX optical package and cover-window guide",
)
back = box("Sensor rear service cover", (0, 12.4, 22), (53, 1.6, 27), "body", "back", 1)
for x in (-19, -14, -9, 9, 14, 19):
    cut(back, box("vent cutter", (x, 12.4, 30), (2, 5, 5), None, radius=0))
carrier = box(
    "Rigid common camera-ToF carrier", (0, 8.7, 22), (48, 2, 23), "trim", "bracket", 0.7
)
cut(carrier, box("carrier relief", (0, 8.7, 22), (8, 5, 13), None, radius=0))
for x in (-23, 23):
    for z in (12, 32):
        cylinder("Carrier standoff", (x, 5.5, z), 1.7, 5, "trim", "bracket")
        cut(face, cylinder("tool screw", (x, -14, z), 0.9, 6, None))
        cylinder(
            "M1.6 concept face screw", (x, -15.5, z), 1.35, 1.2, "trim", "fasteners"
        )
        box("Screw slot", (x, -16.15, z), (1.6, 0.15, 0.25), "black", "fasteners", 0.05)
# Sense electronics, oriented vertically in XZ. Simplified stack reference.
box(
    "XIAO ESP32-S3 PCB / 21 x 17.8",
    (-12, 5.5, 22),
    (21, 1.1, 17.8),
    "pcb",
    "camera",
    0.3,
    "Seeed official 21 x 17.8 mm board; 15 mm stack reference, component positions schematic",
)
box("Sense expansion PCB", (-12, 1.8, 22), (20, 1.1, 17), "pcb", "camera", 0.25)
box("ESP32 shield reference", (-12, 4, 22), (12, 1.7, 12), "trim", "camera", 0.25)
box("Camera package reference", (-12, -2.6, 22), (9, 7, 9), "black", "camera", 0.6)
cylinder("Camera barrel", (-12, -7.5, 22), 5.2, 5, "black", "camera")
cylinder("Camera optical element", (-12, -10.2, 22), 4.4, 0.65, "glass", "camera")
box(
    "Native USB-C shell reference", (-12, 5, 31), (8.8, 5.5, 3.2), "trim", "camera", 0.7
)
box("Native USB-C tongue", (-12, 3, 32.2), (6.9, 2.5, 0.6), "black", "camera", 0.2)
for x in (-21.5, -2.5):
    for z in range(15, 30, 2):
        box("Castellated pad", (x, 4.8, z), (1, 0.4, 1), "gold", "camera", 0.1)
box(
    "VL53L5CX carrier / 12.7 x 17.78",
    (14, -7.5, 22),
    (12.7, 1, 17.78),
    "pcb",
    "tof",
    0.25,
    "Pololu 3417 nominal 0.5 x 0.7 in carrier; hole locations not replicated",
)
box("VL53L5CX package / 6.4 x 3", (14, -9, 22), (6.4, 1.5, 3), "black", "tof", 0.2)
for x in (12, 16):
    box("ToF optical channel", (x, -9.85, 22), (2.2, 0.2, 2), "glass", "tof", 0.15)
for z in (16, 18.54, 21.08, 23.62, 26.16, 28.7):
    cylinder("ToF header pad", (9, -8.1, z), 0.65, 0.15, "gold", "tof", vertices=20)

# Nose supports and contact pads.
for s in (-1, 1):
    tube(
        "Adjustable nose arm " + str(s),
        [(s * 8, 2, 4), (s * 9, 9, -3), (s * 11, 11, -10)],
        0.9,
        "trim",
        "nose",
    )
    o = box(
        "Soft replaceable nose pad " + str(s),
        (s * 11, 12, -10),
        (7, 4, 15),
        "rubber",
        "nose",
        1.8,
    )
    o.rotation_euler[1] = s * math.radians(13)

# Temple shells: open inner pockets with separate service plates.
for side, s, g in (("L", -1, "left"), ("R", 1, "right")):
    shell = box(
        side + " front electronics temple", (s * 73, 45, 12), (10, 64, 23), "body", g, 2
    )
    cut(shell, box("temple pocket", (s * 71.5, 45, 12), (9, 59, 19), None, radius=0))
    lid = box(
        side + " inner service plate",
        (s * 68, 45, 12),
        (1.2, 63, 22),
        "trim",
        "covers",
        0.5,
    )
    tube(
        side + " tapered rear arm",
        [
            (s * 73, 75, 12),
            (s * 71, 99, 10),
            (s * 68, 123, 7),
            (s * 65, 143, -3),
            (s * 64, 151, -15),
        ],
        3.4,
        "body",
        g,
    )
    tube(
        side + " silicone ear sleeve",
        [(s * 68, 122, 7), (s * 65, 141, -3), (s * 64, 151, -15)],
        4.1,
        "rubber",
        "pads",
    )
    cylinder(side + " hinge barrel", (s * 73, 11, 12), 3.4, 14, "trim", g, "Z")
    cylinder(
        side + " hinge pivot pin", (s * 73, 11, 12), 1.1, 16, "blue", "fasteners", "Z"
    )
    box(side + " cyan temple inset", (s * 78.1, 44, 15), (0.5, 35, 1.6), "blue", g, 0.2)
    for y in (18, 72):
        cylinder(
            side + " service cover screw",
            (s * 67.2, y, 12),
            1.4,
            1,
            "trim",
            "fasteners",
            "X",
        )
# IMU and haptic are packaging envelopes, not supplier-exact CAD.
box(
    "LSM6DSOX carrier allowance",
    (73, 36, 12),
    (1.2, 26, 20),
    "pcb",
    "imu",
    0.3,
    "26 x 20 mm reserved carrier; exact purchased breakout and holes pending",
)
box("IMU package reference", (71.9, 36, 12), (1.1, 4, 3), "black", "imu", 0.15)
box(
    "DRV2605L carrier allowance",
    (-73, 49, 12),
    (1.2, 22, 19),
    "pcb",
    "haptic",
    0.3,
    "22 x 19 mm reserved carrier; exact purchased board and driver fit pending",
)
box("Haptic driver package", (-71.8, 49, 12), (1.1, 5, 5), "black", "haptic", 0.2)
cylinder("ERM coin motor placeholder", (-72, 68, 12), 5, 3, "trim", "haptic", "X")
for y, kind in ((27, "Primary confirm"), (41, "Cancel repeat")):
    box(
        kind + " tactile cap",
        (-79, y, 24),
        (5, 9, 2.3),
        "blue" if y == 27 else "rubber",
        "buttons",
        0.9,
    )
    box(kind + " switch envelope", (-73, y, 20.2), (5, 6, 3), "black", "buttons", 0.4)
# Schematic routed interconnects: routing volume, not connector-approved harness.
tube(
    "Sensor bus across brow",
    [(16, 7, 15), (30, 5, 16), (55, 8, 16), (70, 16, 15), (73, 24, 15)],
    0.65,
    "orange",
    "wires",
)
tube(
    "Left control and haptic bus",
    [(-12, 7, 15), (-40, 6, 16), (-66, 12, 15), (-73, 22, 15), (-73, 64, 15)],
    0.6,
    "orange",
    "wires",
)
tube(
    "USB internal route concept",
    [
        (-12, 6, 32),
        (0, 8, 33),
        (26, 9, 31),
        (45, 9, 18),
        (65, 13, 17),
        (73, 23, 17),
        (73, 73, 17),
        (70, 110, 9),
    ],
    1.4,
    "rubber",
    "wires",
)
box("Rear USB strain-relief boot", (70, 112, 8), (8, 15, 9), "rubber", "usb", 2)
tube(
    "USB cable / one host only",
    [
        (70, 117, 8),
        (76, 139, 0),
        (89, 158, -18),
        (106, 164, -28),
        (124, 150, -31),
        (123, 131, -31),
    ],
    1.5,
    "rubber",
    "usb",
)
box("USB-C overmould", (123, 124, -31), (10, 16, 5.2), "rubber", "usb", 1.5)
box("USB-C host plug", (123, 113, -31), (8.3, 7, 2.5), "trim", "usb", 0.8)


# Branding sits on the physical faceplate and explodes with it.
def text3d(
    name,
    body,
    location,
    size,
    material_key="white",
    g=None,
    rotation=(math.pi / 2, 0, 0),
):
    c = bpy.data.curves.new(name, "FONT")
    c.body = body
    c.size = size * 0.001
    c.extrude = 0.015 * 0.001
    o = bpy.data.objects.new(name, c)
    scene.collection.objects.link(o)
    o.location = mm(location)
    o.rotation_euler = rotation
    return register(o, name, material_key, g)


text3d("Face branding", "X / G", (-4, -15.08, 13.2), 2.7, "white", "face")
text3d("ToF marking", "ToF", (10, -15.08, 29), 2, "white", "face")
text3d("Camera marking", "RGB", (-16, -15.08, 29), 2, "white", "face")
# Studio, camera and camera-locked editorial information.
box("Studio plinth", (0, 50, -72), (1600, 1600, 5), "floor", radius=3)
bpy.ops.object.camera_add(location=mm((270, -390, 250)))
cam = bpy.context.object
cam.name = "Camera / product and explosion"
cam.rotation_euler = (mm((0, 48, 8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
scene.camera = cam
for frame, scale in (
    (1, 0.36),
    (35, 0.36),
    (110, 0.46),
    (150, 0.46),
    (225, 0.36),
    (240, 0.36),
):
    cam.data.ortho_scale = scale
    cam.data.keyframe_insert(data_path="ortho_scale", frame=frame)


def area(name, position, power, size, color):
    bpy.ops.object.light_add(type="AREA", location=mm(position))
    o = bpy.context.object
    o.name = name
    o.data.energy = power
    o.data.shape = "DISK"
    o.data.size = size * 0.001
    o.data.color = color
    o.rotation_euler = (mm((0, 45, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()


area("Key softbox", (-180, -150, 300), 1.8, 260, (0.8, 0.9, 1))
area("Warm fill", (230, 80, 200), 1.5, 220, (1, 0.84, 0.68))
area("Cyan rim", (-100, 240, 150), 2.4, 180, (0.35, 0.75, 1))
area("Front strip", (0, -260, 40), 0.75, 160, (1, 1, 1))


def overlay(name, body, x, y, size, color):
    o = text3d(name, body, (0, 0, 0), size, color)
    o.parent = cam
    o.location = (x, y, -0.5)
    o.rotation_euler = (0, 0, 0)
    # Keep positions and type size fixed relative to render as camera zooms.
    for frame, scale in (
        (1, 1),
        (35, 1),
        (110, 0.46 / 0.36),
        (150, 0.46 / 0.36),
        (225, 1),
        (240, 1),
    ):
        o.location = (x * scale, y * scale, -0.5)
        o.scale = (scale,) * 3
        o.keyframe_insert(data_path="location", frame=frame)
        o.keyframe_insert(data_path="scale", frame=frame)
    return o


overlay("Title", "X-GLASSES", -0.143, 0.089, 10, "white")
overlay("Subtitle", "XG-01   /   ToF ASSISTIVE EYEWEAR", -0.141, 0.079, 2.7, "blue")
overlay(
    "Footer",
    "STRUCTURAL CONCEPT   /   USB POWER + DATA   /   REV 01",
    -0.141,
    -0.093,
    2.3,
    "white",
)
overlay(
    "Footer note",
    "REFERENCE ENVELOPES  -  FIT, OPTICS AND WEAR TESTS PENDING",
    -0.141,
    -0.1,
    1.8,
    "white",
)
label = overlay("View label", "01 / ASSEMBLED", 0.083, 0.088, 2.8, "blue")
for frame, title in (
    (1, "ASSEMBLED"),
    (35, "DISASSEMBLE"),
    (110, "EXPLODED"),
    (150, "REASSEMBLE"),
    (225, "ASSEMBLED"),
):
    scene.timeline_markers.new(title, frame=frame)
scene["design_status"] = (
    "Concept assembly; not a manufacturing release or safety validation"
)
scene["source_dimensions"] = (
    "Seeed XIAO Sense 21x17.8x15 mm; Pololu3417 12.7x17.78x2.54 mm envelope"
)
scene["playback"] = (
    "Space: play 1-240. Frame 1/240 assembled; 110-150 exploded. See collections 01-21."
)
scene["hardware_scope"] = (
    "Single forward VL53L5CX, RGB, IMU, haptic, two buttons; USB host power; no battery"
)
readme = bpy.data.texts.new("READ ME - 操作说明")
readme.write(
    "X-GLASSES XG-01 / 概念结构模型\n\n时间轴1/240帧：装配；110-150帧：爆炸展开。空格播放。\n集合01-21为独立装配组，零件含part_id和design_status属性。\n场景单位毫米，几何用米存储。\n电子器件是包络参考，不是加工级原厂CAD；线缆为走线示意。\n中央舱54x25x28mm，镜框宽约156mm。\nUSB供电，耳机连接主机。无电池，无安全通行承诺。\n详细方案与复现脚本见 docs/hardware/mechanical。\n"
)
# Review scene uses the same animated parts; evaluate all geometry at assembly.
scene.frame_set(1)
bpy.context.view_layer.update()
with (OUT / "parts.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["part_id", "name", "group", "x_mm", "y_mm", "z_mm", "status"])
    for o in parts:
        w.writerow(
            [
                o["part_id"],
                o.name,
                o.parent.name,
                *[round(v * 1000, 3) for v in o.dimensions],
                o["design_status"],
            ]
        )
# Persist a comfortable perspective and material view for interactive opening.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type == "VIEW_3D":
            a.spaces.active.region_3d.view_distance = 0.34
            a.spaces.active.region_3d.view_location = mm((0, 48, 8))
            a.spaces.active.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            a.spaces.active.shading.type = "MATERIAL"
            a.spaces.active.clip_start = 0.001
            a.spaces.active.clip_end = 10
bpy.ops.object.select_all(action="DESELECT")
scene.render.filepath = str(OUT / "assembled.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "X-Glasses_XG01.blend"), compress=True)
if args.render:
    for frame, name, title in (
        (1, "assembled", "01 / ASSEMBLED"),
        (130, "exploded", "02 / EXPLODED"),
    ):
        scene.frame_set(frame)
        label.data.body = title
        scene.render.filepath = str(OUT / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    # Open-cover view makes electronics inspectable without claiming a true section.
    scene.frame_set(1)
    hidden = ["pod", "face", "back", "covers"]
    for g in hidden:
        G[g][0].hide_render = True
    label.data.body = "03 / OPEN COVERS"
    scene.render.filepath = str(OUT / "internal.png")
    bpy.ops.render.render(write_still=True)
    for g in hidden:
        G[g][0].hide_render = False
    scene.frame_set(1)
    label.data.body = "01 / ASSEMBLED"
report = {
    "blender": bpy.app.version_string,
    "part_objects": len(parts),
    "assembly_groups": len(G),
    "frames": [1, 240],
    "assembled_frames": [1, 240],
    "exploded_frames": [110, 150],
    "units": "metres internally; millimetres displayed",
    "status": "concept_only",
    "manufacturing_validation": False,
    "hardware_validation": False,
}
(OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("XG01_BUILD_COMPLETE", json.dumps(report))
