"""X-Glasses XG-02 concept assembly. Run with Blender 4.5 --background --python.
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
parser.add_argument("--output", default=str(ROOT / "artifacts/mechanical/xg02"))
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
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1800
scene.render.resolution_y = 1200
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
    "body": material("01 | Graphite PA12 concept", (0.025, 0.035, 0.043), 0.3, 0.29),
    "trim": material("02 | Titanium grey", (0.13, 0.17, 0.19), 0.75, 0.25),
    "blue": material("03 | Signal cyan", (0.015, 0.45, 0.64), 0.55, 0.26),
    "rubber": material("04 | Soft contact silicone", (0.022, 0.031, 0.039), 0, 0.75),
    "lens": material("05 | Removable smoke lens", (0.055, 0.11, 0.14), 0.2, 0.1, 0.48),
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
    "pod": group("05 Continuous brow shell", (0, 0, 40)),
    "face": group("06 Flush optical ribbon", (0, -50, 28)),
    "camera": group("07 XIAO Sense camera stack", (-26, -25, 45)),
    "tof": group("08 VL53L5CX carrier", (29, -24, 45)),
    "bracket": group("09 Rigid alignment carrier", (0, 28, 40)),
    "back": group("10 Inner brow service cover", (0, 38, 18)),
    "nose": group("11 Nose pads", (0, -4, -43)),
    "left": group("12 Left temple shell", (-43, 4, 0)),
    "right": group("13 Right temple shell", (43, 4, 0)),
    "covers": group("14 Temple service covers", (0, 4, 42)),
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


# Continuous industrial form. The enclosure IS the brow frame.
def smooth_mesh(name, verts, faces, key, g, subdiv=0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([mm(v) for v in verts], [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(o)
    register(o, name, key, g)
    for f in mesh.polygons:
        f.use_smooth = True
    if subdiv:
        m = o.modifiers.new("Continuous surface", "SUBSURF")
        m.levels = subdiv
        m.render_levels = subdiv
    return o


def signed_power(v, p):
    return math.copysign(abs(v) ** p, v)


def sweep(name, samples, axis, key, g, exponent=0.62, n=64):
    # Each sample: centre xyz, horizontal half size, vertical half size.
    verts = []
    for center, a, b in samples:
        for j in range(n):
            t = 2 * math.pi * j / n
            u = a * signed_power(math.cos(t), exponent)
            v = b * signed_power(math.sin(t), exponent)
            if axis == "X":
                verts.append((center[0], center[1] + u, center[2] + v))
            else:
                verts.append((center[0] + u, center[1], center[2] + v))
    faces = []
    for k in range(len(samples) - 1):
        for j in range(n):
            q = (j + 1) % n
            faces.append((k * n + j, k * n + q, (k + 1) * n + q, (k + 1) * n + j))
    faces.extend(
        [
            tuple(reversed(range(n))),
            tuple(range((len(samples) - 1) * n, len(samples) * n)),
        ]
    )
    o = smooth_mesh(name, verts, faces, key, g)
    # Recalculate orientation for Boolean reliability on both sweep axes.
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    o.select_set(False)
    return o


def brow(x):
    t = abs(x) / 77
    return (
        (x, -1 + 20 * t * t, 14.5 + 1.5 * t),
        8.7 + 2.8 * math.exp(-((x / 37) ** 2)),
        8.2 + 4.8 * math.exp(-((x / 42) ** 2)),
    )


xs = [-77 + 154 * i / 96 for i in range(97)]
shell = sweep(
    "Monocoque brow / continuous outer skin", [brow(x) for x in xs], "X", "body", "pod"
)
inner = []
for x in [-75 + 150 * i / 94 for i in range(95)]:
    c, a, b = brow(x)
    inner.append((c, a - 1.5, b - 1.5))
cut(shell, sweep("Brow inner cavity", inner, "X", None, None))
# Inner maintenance opening: external front and top remain uninterrupted.
cut(shell, box("Rear service aperture", (0, 11, 14), (91, 13, 17), None, radius=0))
cut(shell, cylinder("Camera aperture", (-10, -13, 15), 5.05, 16, None))
cut(shell, box("ToF aperture", (18, -13, 15), (8.5, 16, 4.8), None, radius=0))


# Continuous black inlay, following the same front curvature.
def ribbon(name, x0, x1, zmid, height, thickness, key, g, yoffset=0):
    verts = []
    n = 100
    for layer in range(2):
        for edge in (-1, 1):
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                c, a, b = brow(x)
                taper = min(
                    1,
                    math.sqrt(
                        max(0.001, 1 - ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 8)
                    ),
                )
                z = zmid + edge * height / 2 * taper
                v = abs((z - c[2]) / b)
                u = max(0, 1 - v ** (2 / 0.62)) ** (0.62 / 2)
                y = c[1] - a * u - 0.16 - yoffset + layer * thickness
                verts.append((x, y, z))
    faces = []
    q = n + 1
    for i in range(n):
        faces.extend(
            [
                (i, i + 1, q + i + 1, q + i),
                (2 * q + i, 3 * q + i, 3 * q + i + 1, 2 * q + i + 1),
                (i, 2 * q + i, 2 * q + i + 1, i + 1),
                (q + i, q + i + 1, 3 * q + i + 1, 3 * q + i),
            ]
        )
    faces.extend([(0, q, 3 * q, 2 * q), (n, 2 * q + n, 3 * q + n, q + n)])
    return smooth_mesh(name, verts, faces, key, g)


visor = ribbon("Flush dark sensor ribbon", -54, 54, 15, 11, 0.65, "black", "face", 0.3)
cut(visor, cylinder("Visor camera opening", (-10, -13, 15), 4.8, 16, None))
cut(visor, box("Visor ToF opening", (18, -13, 15), (7.8, 16, 4.2), None, radius=0))
# No decorative cables: accent is a narrow inset which follows the brow shoulder.
ribbon("Continuous satin upper highlight", -71, 71, 22.3, 0.6, 0.3, "trim", "pod", 0.1)
# Inner curved cover, follows back wall; fasteners only on wearer-facing surface.
verts = []
for i in range(61):
    x = -48 + 96 * i / 60
    c, a, b = brow(x)
    for j in range(13):
        z = 6 + 17 * j / 12
        v = abs((z - c[2]) / b)
        u = max(0, 1 - v ** (2 / 0.62)) ** (0.62 / 2)
        verts.append((x, c[1] + a * u + 0.08, z))
faces = [
    (13 * i + j, 13 * (i + 1) + j, 13 * (i + 1) + j + 1, 13 * i + j + 1)
    for i in range(60)
    for j in range(12)
]
cover = smooth_mesh("Curved wearer-facing brow cover", verts, faces, "rubber", "back")
sol = cover.modifiers.new("Cover thickness", "SOLIDIFY")
sol.thickness = 0.0012
bevel(cover, 0.5)


# Slim curved lens rims integrated under the brow, with a shared bridge.
def lens_shape(cx, scale=1):
    # Rounded angular sport lens; upper outer corners rise toward temple.
    points = []
    n = 96
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 31 * signed_power(math.cos(t), 0.68) * scale
        z = 20 * signed_power(math.sin(t), 0.83) * scale
        z += (abs(cx + x) - 35) * 0.065
        points.append((cx + x, -8.5 + (0.0027 * (cx + x) ** 2), -8 + z))
    return points


def lens_part(name, cx, solid, key, g):
    outer = lens_shape(cx, 1 if not solid else 0.944)
    inner = lens_shape(cx, 0.934)
    n = len(outer)
    loops = [outer, outer] if solid else [outer, outer, inner, inner]
    depth = 1.2 if solid else 3.2
    verts = []
    for k, loop in enumerate(loops):
        verts.extend(
            [(x, y + (-depth / 2 if k % 2 == 0 else depth / 2), z) for x, y, z in loop]
        )
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        if not solid:
            faces.extend(
                [
                    (j, i, 2 * n + i, 2 * n + j),
                    (n + i, n + j, 3 * n + j, 3 * n + i),
                    (2 * n + i, 3 * n + i, 3 * n + j, 2 * n + j),
                ]
            )
    if solid:
        faces.extend([tuple(reversed(range(n))), tuple(range(n, 2 * n))])
    o = smooth_mesh(name, verts, faces, key, g)
    bevel(o, 0.35)
    return o


for side, cx in (("L", -35), ("R", 35)):
    lens_part(side + " thin integrated orbital rim", cx, False, "body", "frame")
    lens_part(side + " curved smoke lens", cx, True, "lens", "lens" + side)
    # Small concealed rear retainers, rather than a second visible spectacle frame.
    for x in (cx - 22, cx + 22):
        box(
            side + " rear lens retainer",
            (x, -5 + 0.0027 * x * x, 9),
            (5, 2, 2),
            "body",
            "retainers",
            0.6,
        )
tube(
    "Sculpted nose bridge",
    [(-9, -8, 4), (-5, -9, 6), (0, -10, 7), (5, -9, 6), (9, -8, 4)],
    2.1,
    "body",
    "frame",
)
for s in (-1, 1):
    tube(
        "Nose support " + str(s),
        [(s * 8, -6, 1), (s * 9, 0, -6), (s * 10, 3, -12)],
        0.9,
        "trim",
        "nose",
    )
    o = box(
        "Floating silicone nosepad " + str(s),
        (s * 10, 4, -12),
        (6, 3.8, 13),
        "rubber",
        "nose",
        1.8,
    )
    o.rotation_euler[1] = s * 0.2

# Carrier and actual board envelopes fit within the brow cavity.
carrier = box(
    "Common rigid RGB-ToF carrier", (4, 6, 15), (48, 1.5, 20), "trim", "bracket", 1.5
)
cut(carrier, box("Carrier relief", (4, 6, 15), (8, 4, 12), None, radius=0))
box(
    "XIAO main PCB 21x17.8",
    (-10, 3, 15),
    (21, 1.1, 17.8),
    "pcb",
    "camera",
    0.3,
    "Official board outline envelope; detailed connector placement schematic",
)
box("Sense camera expansion", (-10, -0.3, 15), (20, 1.1, 17), "pcb", "camera", 0.3)
box("ESP32 metal shield", (-10, 1.6, 15), (12, 1.6, 12), "trim", "camera", 0.4)
box("Camera package", (-10, -4, 15), (8, 6, 8), "black", "camera", 0.6)
cylinder("Recessed camera barrel", (-10, -8.5, 15), 4.8, 4, "black", "camera")
cylinder("Camera glass", (-10, -10.75, 15), 4.3, 0.5, "glass", "camera")
cylinder("Camera iris", (-10, -11.05, 15), 2.2, 0.12, "black", "camera")
cylinder(
    "Lens highlight", (-11.2, -11.13, 16.1), 0.5, 0.08, "blue", "camera", vertices=24
)
box("Native USB-C reference", (-10, 3.4, 23), (8.8, 5.5, 3.2), "trim", "camera", 0.5)
for x in (-19.5, -0.5):
    for z in (8, 10.54, 13.08, 15.62, 18.16, 20.7):
        box("XIAO contact", (x, 2.3, z), (1, 0.3, 1), "gold", "camera", 0.1)
box(
    "VL53L5CX 3417 carrier",
    (18, -5.7, 15),
    (12.7, 1, 17.78),
    "pcb",
    "tof",
    0.3,
    "Pololu nominal carrier outline; layout and mounts schematic",
)
box("VL53L5CX package", (18, -7.1, 15), (6.4, 1.5, 3), "black", "tof", 0.2)
for x in (16, 20):
    box("ToF optical area", (x, -8, 15), (2, 0.25, 2), "glass", "tof", 0.2)
baffle = box(
    "Short ToF light-isolation hood", (18, -9, 15), (8.3, 3, 4.5), "black", "tof", 0.4
)
cut(baffle, box("Clear ToF path", (18, -9, 15), (7, 5, 3.6), None, radius=0))
box("Tx Rx separator concept", (18, -9.4, 15), (0.45, 2.5, 3.4), "black", "tof", 0.1)
for x in (-30, 35):
    cylinder("Internal carrier standoff", (x, 3.5, 15), 1.8, 5, "trim", "bracket")
    cylinder("Hidden brow screw", (x, 11.8, 15), 1.25, 1, "trim", "fasteners")


# Tapered organic temples. Exterior body and inner hatches share one silhouette.
def temple(s, y, inflate=0):
    t = (y - 20) / 128
    x = s * (76 + 2 * math.sin(t * math.pi) - 9 * max(0, (t - 0.55) / 0.45) ** 1.6)
    z = 15 - 6 * t - 20 * max(0, (t - 0.66) / 0.34) ** 1.6
    a = 6.7 - 3.6 * t + inflate
    b = 10.1 - 5.8 * t + inflate
    return ((x, y, z), a, b)


for side, s, g in (("L", -1, "left"), ("R", 1, "right")):
    ys = [20 + 128 * i / 80 for i in range(81)]
    body = sweep(
        side + " flowing temple", [temple(s, y) for y in ys], "Y", "body", g, 0.67
    )
    cavity = []
    for y in [24 + 63 * i / 40 for i in range(41)]:
        c, a, b = temple(s, y)
        cavity.append((c, a - 1.4, b - 1.3))
    cut(body, sweep("Temple inner cavity", cavity, "Y", None, None, 0.67))
    cut(
        body, box("Inner hatch aperture", (s * 71, 53, 13), (7, 54, 13), None, radius=0)
    )
    verts = []
    for i in range(51):
        y = 26 + 57 * i / 50
        c, a, b = temple(s, y)
        for j in range(13):
            dz = (j / 6 - 1) * (b - 1.6)
            u = max(0, 1 - abs(dz / b) ** (2 / 0.67)) ** (0.67 / 2)
            verts.append((c[0] - s * (a * u + 0.08), y, c[2] + dz))
    faces = [
        (13 * i + j, 13 * (i + 1) + j, 13 * (i + 1) + j + 1, 13 * i + j + 1)
        for i in range(50)
        for j in range(12)
    ]
    hatch = smooth_mesh(
        side + " curved inner service hatch", verts, faces, "rubber", "covers"
    )
    m = hatch.modifiers.new("Service cover skin", "SOLIDIFY")
    m.thickness = 0.001
    bevel(hatch, 0.45)
    # Long fine metallic brand rail, recessed rather than attached pod.
    coords = []
    for y in (27, 38, 49, 60, 71):
        c, a, b = temple(s, y)
        coords.append((c[0] + s * (a + 0.08), y, c[2] + 1.2))
    tube(side + " satin side signature", coords, 0.3, "trim", g)
    # Cyan touch point, tiny rather than an oversized glowing line.
    c, a, b = temple(s, 30)
    box(
        side + " cyan detail",
        (c[0] + s * a, 30, c[2] + 1.2),
        (0.35, 4, 1),
        "blue",
        g,
        0.2,
    )
    sleeve = sweep(
        side + " soft ear sleeve",
        [temple(s, y, 0.25) for y in [112 + 36 * i / 30 for i in range(31)]],
        "Y",
        "rubber",
        "pads",
        0.8,
    )
    # Hollow sleeve so the matching arm is not a solid intersecting tube.
    cut(
        sleeve,
        sweep(
            "Sleeve inner",
            [temple(s, y, -0.05) for y in [111 + 38 * i / 30 for i in range(31)]],
            "Y",
            None,
            None,
            0.8,
        ),
    )
    cylinder(
        side + " concealed hinge pivot",
        (s * 76, 21, 15),
        1.1,
        14,
        "trim",
        "fasteners",
        "Z",
    )
    for y in (30, 77):
        cylinder(
            side + " hatch screw", (s * 70.6, y, 13), 1.1, 1, "trim", "fasteners", "X"
        )
# Boards are reservations for the selected electronics; exact breakout revision pending.
box(
    "IMU carrier allowance",
    (76, 43, 14),
    (1.2, 25, 16),
    "pcb",
    "imu",
    0.4,
    "Reserved carrier envelope; actual board revision to verify before manufacture",
)
box("IMU chip", (74.8, 43, 14), (1, 4, 3), "black", "imu", 0.2)
box(
    "Haptic driver carrier allowance",
    (-76, 51, 14),
    (1.2, 22, 15),
    "pcb",
    "haptic",
    0.4,
    "Reserved carrier envelope; exact DRV2605 breakout may require layout revision",
)
box("Haptic controller", (-74.8, 51, 14), (1, 5, 5), "black", "haptic", 0.2)
cylinder("Coin haptic motor", (-76, 70, 12), 4, 2.8, "trim", "haptic", "X")
for y, key in ((36, "blue"), (49, "rubber")):
    c, a, b = temple(-1, y)
    button = box(
        "Flush tactile key " + str(y),
        (c[0], y, c[2] + b + 0.1),
        (6, 8, 1.1),
        key,
        "buttons",
        1.4,
    )
    box(
        "Button switch " + str(y),
        (c[0], y, c[2] + b - 2),
        (4, 5, 2),
        "black",
        "buttons",
        0.4,
    )
# Harness follows internal brow and temple channels; invisible when assembled.
tube(
    "Internal ToF and IMU loom",
    [(18, 1, 12), (35, 4, 13), (54, 11, 14), (73, 19, 14), (76, 40, 14)],
    0.6,
    "orange",
    "wires",
)
tube(
    "Internal left control loom",
    [(-10, 4, 12), (-32, 4, 13), (-55, 11, 14), (-75, 23, 14), (-76, 66, 13)],
    0.6,
    "orange",
    "wires",
)
tube(
    "USB internal loom",
    [
        (-10, 4, 23),
        (0, 5, 23),
        (35, 7, 18),
        (58, 13, 15),
        (76, 25, 15),
        (77, 65, 13),
        (75, 96, 9),
        (72, 119, 4),
    ],
    1.1,
    "rubber",
    "wires",
)
# Small rear exit integrated with temple; external cable kept secondary in hero view.
tube(
    "Ear-rear strain relief",
    [(72, 116, 4), (72, 124, 1), (73, 132, -2)],
    2.3,
    "rubber",
    "usb",
)
tube(
    "USB data cable",
    [(73, 130, -1), (81, 148, -15), (99, 148, -30), (112, 129, -36), (108, 112, -36)],
    1.2,
    "rubber",
    "usb",
)
plug = box("USB-C overmould", (106, 107, -36), (8.5, 13, 4.5), "rubber", "usb", 1.6)
plug.rotation_euler[2] = -0.2
plug = box("USB-C plug", (104.6, 98, -36), (7.8, 6, 2.4), "trim", "usb", 0.6)
plug.rotation_euler[2] = -0.2


# Subtle physical branding and studio editorial text.
def text3d(
    name, body, location, size, key="white", g=None, rotation=(math.pi / 2, 0, 0)
):
    c = bpy.data.curves.new(name, "FONT")
    c.body = body
    c.size = size * 0.001
    c.extrude = 0.008 * 0.001
    o = bpy.data.objects.new(name, c)
    scene.collection.objects.link(o)
    o.location = mm(location)
    o.rotation_euler = rotation
    return register(o, name, key, g)


# The front remains visually quiet; the studio title carries the brand.
# A low dark studio floor catches the floating silhouette without a heavy platform.
box("Studio floor", (0, 40, -59), (1200, 1200, 3), "floor", radius=0)
bpy.ops.object.camera_add(location=mm((245, -360, 210)))
cam = bpy.context.object
cam.name = "Camera / refined eyewear"
cam.rotation_euler = (mm((4, 49, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
scene.camera = cam
for frame, scale in (
    (1, 0.31),
    (35, 0.31),
    (110, 0.43),
    (150, 0.43),
    (225, 0.31),
    (240, 0.31),
):
    cam.data.ortho_scale = scale
    cam.data.keyframe_insert(data_path="ortho_scale", frame=frame)


def area(name, position, power, size, color):
    bpy.ops.object.light_add(type="AREA", location=mm(position))
    o = bpy.context.object
    o.name = name
    o.data.energy = power
    o.data.shape = "RECTANGLE"
    o.data.size = size * 0.001
    o.data.size_y = size * 0.00055
    o.data.color = color
    o.rotation_euler = (mm((0, 40, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()


area("Large cool key", (-150, -150, 260), 2.7, 260, (0.83, 0.92, 1))
area("Soft warm fill", (210, -40, 200), 1.5, 200, (1, 0.92, 0.83))
area("Long edge light", (-20, 200, 180), 3.2, 240, (0.55, 0.8, 1))
area("Lens strip", (0, -230, 30), 0.55, 160, (0.75, 0.9, 1))
# Make editorial labels readable independent of studio material lighting.
for k in ("white", "blue"):
    p = mat[k].node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = mat[k].diffuse_color
    p.inputs["Emission Strength"].default_value = 0.25


def overlay(name, body, x, y, size, key):
    o = text3d(name, body, (0, 0, 0), size, key)
    o.parent = cam
    o.rotation_euler = (0, 0, 0)
    for frame, factor in (
        (1, 1),
        (35, 1),
        (110, 0.43 / 0.31),
        (150, 0.43 / 0.31),
        (225, 1),
        (240, 1),
    ):
        o.location = (x * factor, y * factor, -0.45)
        o.scale = (factor,) * 3
        o.keyframe_insert(data_path="location", frame=frame)
        o.keyframe_insert(data_path="scale", frame=frame)
    return o


overlay("Title", "X / GLASSES", -0.139, 0.081, 8, "white")
overlay("Subtitle", "FLOW 02", -0.138, 0.069, 3.1, "blue")
overlay(
    "Design line",
    "CONTINUOUS FORM.   CONCEALED INTELLIGENCE.",
    -0.138,
    -0.085,
    2.1,
    "white",
)
overlay(
    "Footer",
    "ToF + RGB  /  USB TETHERED  /  INDUSTRIAL DESIGN CONCEPT",
    -0.138,
    -0.093,
    1.65,
    "white",
)
label = overlay("View label", "01 / ASSEMBLED", 0.086, 0.083, 2.2, "blue")
for frame, title in (
    (1, "ASSEMBLED"),
    (35, "OPEN"),
    (110, "EXPLODED"),
    (150, "CLOSE"),
    (225, "ASSEMBLED"),
):
    scene.timeline_markers.new(title, frame=frame)
scene["design_status"] = (
    "XG02 integrated industrial design concept; not manufacturing CAD"
)
scene["playback"] = "1 / 240 assembled; 110-150 exploded; Space to play"
scene["hardware_scope"] = "Single ToF and RGB; USB host-powered; no battery"
readme = bpy.data.texts.new("READ ME - 操作说明")
readme.write(
    "X-GLASSES / FLOW 02\n连续弧面上眉框、隐藏传感器、渐薄镜腿。\n空格播放240帧拆装；1/240装配，130爆炸。\nOutliner集合01-21可独立编辑。\n电子器件为包络参考，光学/热/公差/佩戴未验证。\n内部线缆示意，不能直接制造。\n"
)
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
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type == "VIEW_3D":
            a.spaces.active.region_3d.view_distance = 0.32
            a.spaces.active.region_3d.view_location = mm((0, 45, 0))
            a.spaces.active.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            a.spaces.active.shading.type = "MATERIAL"
            a.spaces.active.clip_start = 0.001
            a.spaces.active.clip_end = 10
bpy.ops.object.select_all(action="DESELECT")
scene.render.filepath = str(OUT / "assembled.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "X-Glasses_FLOW02.blend"), compress=True)
if args.render:
    for frame, name, title in (
        (1, "assembled", "01 / ASSEMBLED"),
        (130, "exploded", "02 / EXPLODED"),
    ):
        scene.frame_set(frame)
        label.data.body = title
        scene.render.filepath = str(OUT / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    for g in ("pod", "face", "back", "covers"):
        G[g][0].hide_render = True
    label.data.body = "03 / UNDER THE SKIN"
    scene.render.filepath = str(OUT / "internal.png")
    bpy.ops.render.render(write_still=True)
    for g in ("pod", "face", "back", "covers"):
        G[g][0].hide_render = False
    scene.frame_set(1)
    label.data.body = "01 / ASSEMBLED"
report = {
    "blender": bpy.app.version_string,
    "part_objects": len(parts),
    "assembly_groups": len(G),
    "design": "FLOW02 / continuous brow and tapered temples",
    "status": "concept_only",
    "hardware_verified": False,
    "manufacturing_verified": False,
}
(OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("FLOW02_BUILD_COMPLETE", json.dumps(report))
