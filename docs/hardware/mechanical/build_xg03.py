"""X-Glasses BLACK / OV5640 concept assembly. Run with Blender 4.5 --background --python.
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
parser.add_argument("--output", default=str(ROOT / "artifacts/mechanical/xg03"))
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
scene.render.resolution_x = 1920
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 240
scene.world = bpy.data.worlds.new("Studio world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.65, 0.67, 0.7, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
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
    "body": material("01 | Graphite PA12 concept", (0.012, 0.015, 0.018), 0.18, 0.32),
    "trim": material("02 | Titanium grey", (0.18, 0.19, 0.2), 0.8, 0.23),
    "blue": material("03 | Signal cyan", (0.015, 0.45, 0.64), 0.55, 0.26),
    "rubber": material("04 | Soft contact silicone", (0.022, 0.031, 0.039), 0, 0.75),
    "lens": material("05 | Removable smoke lens", (0.5, 0.55, 0.58), 0, 0.08, 0.94),
    "pcb": material("06 | PCB reference envelope", (0.025, 0.19, 0.13), 0.15, 0.48),
    "gold": material("07 | Contact gold", (0.68, 0.39, 0.08), 0.75, 0.28),
    "black": material("08 | Optical isolation", (0.005, 0.008, 0.014), 0.05, 0.24),
    "glass": material("09 | Camera glass", (0.012, 0.055, 0.09), 0.5, 0.08),
    "white": material("10 | Technical lettering", (0.68, 0.83, 0.9), 0.1, 0.6),
    "orange": material("11 | Flexible interconnect", (0.62, 0.22, 0.055), 0.4, 0.42),
    "floor": material("12 | Studio surface", (0.54, 0.55, 0.56), 0, 0.65),
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
    "pod": group("05 Continuous brow shell", (0, 0, 62)),
    "face": group("06 Optical trim and seals", (0, -54, 25)),
    "camera": group("07 XIAO Sense OV5640 stack", (-22, -22, 34)),
    "tof": group("08 VL53L5CX carrier", (28, -20, 32)),
    "bracket": group("09 Rigid alignment carrier", (0, 20, 32)),
    "back": group("10 Inner brow service cover", (0, 45, 34)),
    "nose": group("11 Nose pads", (0, -4, -43)),
    "left": group("12 Left temple shell", (-43, 4, 0)),
    "right": group("13 Right temple shell", (43, 4, 0)),
    "covers": group("14 Temple service covers", (0, 14, 54)),
    "imu": group("15 IMU reference carrier", (18, 4, 26)),
    "haptic": group("16 Haptic driver and motor", (-18, 4, 29)),
    "buttons": group("17 Tactile controls", (-60, 2, 30)),
    "pads": group("18 Ear contact sleeves", (0, 20, -22)),
    "usb": group("19 USB cable and strain relief", (45, 32, -6)),
    "fasteners": group("20 Fasteners and hinge pins", (0, 0, 95)),
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


# Chosen design budgets: central 60mm span, 26mm high, 25mm front-back.
# The 4th-power rounded section is also used by the independent fit verifier.
def brow(x):
    u = max(0, min(1, (abs(x) - 30) / 47))
    smooth = u * u * (3 - 2 * u)
    return (
        (x, -1 + 0.0024 * x * x, 19 + 0.7 * smooth),
        12.5 - 4 * smooth,
        13 - 2.5 * smooth,
    )


XS = [-77 + 154 * i / 120 for i in range(121)]
shell = sweep(
    "Brow outer shell / 26H x 25D central",
    [brow(x) for x in XS],
    "X",
    "body",
    "pod",
    exponent=0.5,
)
inner = []
for x in [-75.5 + 151 * i / 118 for i in range(119)]:
    c, a, b = brow(x)
    inner.append((c, a - 1.5, b - 1.5))
cut(shell, sweep("Brow cavity tool", inner, "X", None, None, exponent=0.5))
cut(
    shell,
    box("Wearer-facing assembly opening", (0, 12, 19), (66, 13, 20), None, radius=0),
)
cut(shell, cylinder("RGB opening tool", (-5, -14, 19), 5.2, 14, None))
cut(shell, box("ToF opening tool", (19, -13, 19), (8.8, 14, 5.2), None, radius=0))
# Discrete USB and harness routing reliefs are hidden at the temples.
for x in (-72, 72):
    cut(shell, cylinder("Brow harness port", (x, 12, 19), 2, 14, None, axis="X"))


def skin_strip(name, x0, x1, zmid, height, depth, key, g, back=False):
    verts = []
    n = 88
    m = 12
    for layer in range(2):
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            c, a, b = brow(x)
            taper = min(
                1, max(0.001, 1 - ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 12) ** 0.3
            )
            for j in range(m + 1):
                z = zmid + (j / m - 0.5) * height * taper
                u = max(0, 1 - abs((z - c[2]) / b) ** 4) ** 0.25
                sign = 1 if back else -1
                y = c[1] + sign * (a * u + 0.12 - layer * depth)
                verts.append((x, y, z))
    q = (n + 1) * (m + 1)
    faces = []
    for i in range(n):
        for j in range(m):
            k = i * (m + 1) + j
            faces.append((k, k + m + 1, k + m + 2, k + 1))
            faces.append((q + k + 1, q + k + m + 2, q + k + m + 1, q + k))
    for i in range(n):
        for j in (0, m):
            k = i * (m + 1) + j
            faces.append((k, k + m + 1, q + k + m + 1, q + k))
    for i in (0, n):
        for j in range(m):
            k = i * (m + 1) + j
            faces.append((k, k + 1, q + k + 1, q + k))
    return smooth_mesh(name, verts, faces, key, g)


# Black-on-black flush insert is integral to the brow contour, not a sensor box.
visor = skin_strip("Flush optical insert", -19, 32, 19, 11, 0.55, "black", "face")
cut(visor, cylinder("RGB trim opening", (-5, -14, 19), 4.9, 15, None))
cut(visor, box("ToF trim opening", (19, -13, 19), (8.1, 15, 4.6), None, radius=0))
cover = skin_strip(
    "Curved inner brow access lid", -34, 34, 19, 21, 0.85, "rubber", "back", back=True
)
# Small upper edge seam emphasises a continuous surface; all fasteners inward.
skin_strip("Upper satin edge accent", -71, 71, 26, 0.35, 0.2, "trim", "pod")
# Matching upper seals and optical gasket remain independently editable.
for x, z, rad in ((-5, 19, 5.6),):
    gasket = cylinder("Camera gasket blank", (x, -11.8, z), rad, 0.6, "rubber", "face")
    cut(gasket, cylinder("Gasket clear aperture", (x, -11.8, z), 4.8, 3, None))


# Panto lens outlines, keeping the accepted rounded form and thin lower rims.
def lens_outline(cx, scale=1):
    pts = []
    for i in range(112):
        t = 2 * math.pi * i / 112
        dx = 30.8 * signed_power(math.cos(t), 0.78) * scale
        dz = 19.3 * signed_power(math.sin(t), 0.95) * scale
        # A slightly straighter upper edge and softly lifted outer corner.
        if dz > 0:
            dz *= 0.88
        z = -10 + dz + 0.04 * (abs(cx + dx) - 35)
        x = cx + dx
        y = -6.5 + 0.0023 * x * x
        pts.append((x, y, z))
    return pts


def lens_component(name, cx, filled, key, g):
    outer = lens_outline(cx, 0.953 if filled else 1)
    inner = lens_outline(cx, 0.945)
    n = len(outer)
    loops = [outer, outer] if filled else [outer, outer, inner, inner]
    depth = 1.1 if filled else 2.6
    verts = []
    for k, loop in enumerate(loops):
        verts.extend(
            [(x, y + (-depth / 2 if k % 2 == 0 else depth / 2), z) for x, y, z in loop]
        )
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        if not filled:
            faces.extend(
                [
                    (j, i, 2 * n + i, 2 * n + j),
                    (n + i, n + j, 3 * n + j, 3 * n + i),
                    (2 * n + i, 3 * n + i, 3 * n + j, 2 * n + j),
                ]
            )
    if filled:
        faces.extend([tuple(reversed(range(n))), tuple(range(n, 2 * n))])
    o = smooth_mesh(name, verts, faces, key, g)
    bevel(o, 0.3)
    return o


for side, cx in (("L", -35), ("R", 35)):
    lens_component(side + " orbital frame", cx, False, "body", "frame")
    lens_component(side + " optical lens reference", cx, True, "lens", "lens" + side)
    for dx in (-19, 19):
        x = cx + dx
        box(
            side + " concealed lens retention tab",
            (x, -3 + 0.0023 * x * x, 6),
            (4, 2, 2),
            "body",
            "retainers",
            0.5,
        )
tube(
    "Sculpted integral nose bridge",
    [(-9, -6, 2), (-5, -7, 4), (0, -8, 5), (5, -7, 4), (9, -6, 2)],
    2,
    "body",
    "frame",
)
for side in (-1, 1):
    tube(
        "Nosepad titanium arm " + str(side),
        [(side * 8, -4, 1), (side * 9, 1, -5), (side * 10, 4, -12)],
        0.75,
        "trim",
        "nose",
    )
    pad = box(
        "Replaceable soft nosepad " + str(side),
        (side * 10, 5, -12),
        (6, 3.8, 13),
        "rubber",
        "nose",
        1.8,
    )
    pad.rotation_euler[1] = side * 0.22

# Nominal hardware reservation solids: visible only as wire cages, excluded from render.
reservations = {}


def reserve(name, center, size, g):
    o = box(
        name,
        center,
        size,
        None,
        g,
        radius=0,
        note="Nominal reservation; fit-only geometry",
    )
    o.hide_render = True
    o.display_type = "WIRE"
    o["fit_reservation"] = True
    reservations[name] = o
    return o


reserve("FIT / XIAO complete 21x17.8x15", (-5, -2.1, 19), (21, 15, 17.8), "camera")
reserve(
    "FIT / XIAO support allowance 22x18.8x17", (-5, -0.6, 19), (22, 17, 18.8), "camera"
)
reserve("FIT / USB plug allowance", (-21.5, 2.3, 19), (12, 4.2, 9.4), "usb")
reserve("FIT / Pololu3417 nominal", (19, -6.77, 19), (12.7, 2.54, 17.78), "tof")
# Four local standoffs support the carrier, outside board keepouts.
carrier = box(
    "Rigid shared optical mounting carrier",
    (4, 7, 19),
    (52, 1.2, 22),
    "trim",
    "bracket",
    1.2,
)
cut(carrier, box("Carrier wiring relief", (5, 7, 19), (5, 4, 13), None, radius=0))
for x in (-20, 29):
    for z in (11, 27):
        boss = cylinder(
            "M1.6 optical carrier boss", (x, 8.2, z), 1.5, 2.5, "body", "bracket"
        )
        cut(boss, cylinder("Boss pilot", (x, 8.2, z), 0.65, 4, None))

# Detailed XIAO and camera board representations; placement of tiny passives schematic.
main = box(
    "XIAO ESP32-S3 control PCB / 21x17.8",
    (-5, 4.4, 19),
    (21, 1.1, 17.8),
    "pcb",
    "camera",
    0.35,
    "Nominal outer board dimensions; populated layout illustrative, not vendor-exact CAD",
)
box("Sense expansion PCB", (-5, 0.9, 19), (20, 1, 17), "pcb", "camera", 0.3)
box("ESP32 RF shield", (-3, 2.8, 20), (10.2, 1.8, 11.2), "trim", "camera", 0.4)
# Fine castellated edge contacts and plated vias.
for x in (-15, 5):
    for z in (11.7, 14.24, 16.78, 19.32, 21.86, 24.4, 26.94):
        cylinder(
            "Castellated plated contact",
            (x, 3.75, z),
            0.58,
            0.24,
            "gold",
            "camera",
            vertices=24,
        )
        cylinder("Contact bore", (x, 3.6, z), 0.27, 0.1, "black", "camera", vertices=20)
for z in (12.5, 15, 17.5, 20, 22.5, 25):
    box(
        "Decoupling capacitor", (-11, 3.5, z), (1.1, 0.5, 0.65), "rubber", "camera", 0.1
    )
    box(
        "Capacitor silver termination",
        (-10.55, 3.2, z),
        (0.2, 0.15, 0.65),
        "trim",
        "camera",
        0.04,
    )
for x, z in ((1, 12), (-6, 12), (-11, 24.6), (2, 25.7)):
    box("Logic IC", (x, 3.3, z), (2.2, 0.8, 2), "black", "camera", 0.15)
    for dx in (-1.3, 1.3):
        for dz in (-0.65, 0, 0.65):
            box(
                "IC lead",
                (x + dx, 3.2, z + dz),
                (0.4, 0.25, 0.2),
                "trim",
                "camera",
                0.03,
            )
# Native USB socket insertion direction is X; reserve its plug volume separately.
usb_socket = box(
    "Native USB-C receptacle", (-12.75, 2.3, 19), (5.5, 3.2, 8.8), "trim", "camera", 0.7
)
cut(
    usb_socket,
    box("USB-C socket opening", (-15.5, 2.3, 19), (1.4, 2.5, 7.1), None, radius=0),
)
box("USB-C contact tongue", (-15.3, 2.3, 19), (0.4, 0.65, 6.6), "black", "camera", 0.2)
for z in [16.5 + i * 0.45 for i in range(12)]:
    box("USB-C fine contact", (-15.4, 1.9, z), (0.2, 0.1, 0.18), "gold", "camera", 0.03)
# Short custom right-angle plug is a packaging study; its exact supplier is not selected.
box(
    "Internal right-angle USB plug",
    (-21.25, 2.3, 19),
    (11.5, 3.8, 9),
    "rubber",
    "usb",
    0.9,
    "Connector reserve only; selected part and bend radius require verification",
)
box("Camera ZIF connector", (-5, -0.15, 25), (8.4, 1.5, 2.2), "rubber", "camera", 0.35)
box("ZIF latch", (-5, -1, 25), (8, 0.45, 0.8), "black", "camera", 0.15)
# Amber flex ribbon, copper traces, supported at the camera carrier.
flex = box(
    "OV5640 amber FPC reference",
    (-5, -1.7, 21),
    (8, 0.2, 6),
    "orange",
    "camera",
    0.15,
    "OV5640-family reference; as-bought camera/FPC revision not dimensionally captured",
)
for x in [-8.2 + i * 0.45 for i in range(15)]:
    box("FPC copper trace", (x, -1.83, 21), (0.12, 0.03, 5.4), "gold", "camera", 0.02)
box(
    "OV5640 lens package reference",
    (-5, -4.8, 19),
    (8.5, 4.5, 8.5),
    "black",
    "camera",
    0.6,
    "8.5mm camera-body drawing reference; lens/AF batch and connector must be checked on bought unit",
)
cylinder("OV5640 lens barrel", (-5, -8, 19), 4.5, 2.6, "black", "camera")
cylinder("OV5640 front lens glass", (-5, -9.45, 19), 3.8, 0.3, "glass", "camera")
cylinder(
    "Camera entrance pupil reference", (-5, -9.5, 19), 2.1, 0.08, "black", "camera"
)
# Detailed ToF reference. Actual projected zone mapping and optical exclusion unverified.
box("Pololu 3417 VL53L5CX carrier", (19, -6, 19), (12.7, 1, 17.78), "pcb", "tof", 0.3)
box("VL53L5CX package 6.4x3", (19, -7.25, 19), (6.4, 1.5, 3), "black", "tof", 0.2)
for x in (17, 21):
    box(
        "ToF emitter receiver optical area",
        (x, -9.07, 19),
        (1.7, 0.15, 1.8),
        "glass",
        "tof",
        0.15,
    )
for z in (12, 14.54, 17.08, 19.62, 22.16, 24.7):
    cylinder(
        "ToF plated header pad", (14, -6.6, z), 0.56, 0.2, "gold", "tof", vertices=24
    )
    cylinder("ToF plated hole", (14, -6.73, z), 0.25, 0.1, "black", "tof", vertices=20)
for x, z in ((22, 13), (23, 25), (17, 25)):
    box("ToF passives", (x, -6.8, z), (1.2, 0.5, 0.7), "rubber", "tof", 0.1)
hood = box(
    "ToF optical isolation hood", (19, -10, 19), (8.6, 2.6, 5), "black", "tof", 0.4
)
cut(hood, box("ToF unobstructed path", (19, -10, 19), (7.5, 5, 3.8), None, radius=0))
box(
    "ToF Tx Rx isolation septum",
    (19, -10.2, 19),
    (0.4, 2.4, 3.6),
    "black",
    "tof",
    0.1,
    "Baffle placeholder: final exclusion geometry and crosstalk testing pending",
)


# Tapered, hollow temples with compound curvature and inner maintenance covers.
def temple(side, y, delta=0):
    t = (y - 22) / 126
    x = side * (76 + 1.5 * math.sin(t * math.pi) - 9 * max(0, (t - 0.58) / 0.42) ** 1.6)
    z = 19 - 7 * t - 20 * max(0, (t - 0.68) / 0.32) ** 1.6
    a = 7.2 - 3.7 * t + delta
    b = 12.5 + 1.3 * math.sin(min(1, t / 0.48) * math.pi) - 6.9 * t * t + delta
    return ((x, y, z), a, b)


for side_name, side, g in (("L", -1, "left"), ("R", 1, "right")):
    body = sweep(
        side_name + " seamless tapered temple",
        [temple(side, 22 + 126 * i / 96) for i in range(97)],
        "Y",
        "body",
        g,
        exponent=0.6,
    )
    inner = []
    for y in [25 + 60 * i / 50 for i in range(51)]:
        c, a, b = temple(side, y)
        inner.append((c, a - 1.25, b - 1.25))
    cut(body, sweep("Temple cavity tool", inner, "Y", None, None, exponent=0.6))
    cut(
        body,
        box("Temple access slot", (side * 71, 53, 18), (6, 55, 15), None, radius=0),
    )
    verts = []
    n = 68
    m = 16
    for i in range(n + 1):
        y = 26 + 56 * i / n
        c, a, b = temple(side, y)
        for j in range(m + 1):
            dz = (j / m * 2 - 1) * (b - 1.4)
            u = max(0, 1 - abs(dz / b) ** (2 / 0.6)) ** (0.6 / 2)
            verts.append((c[0] - side * (a * u + 0.04), y, c[2] + dz))
    faces = []
    for i in range(n):
        for j in range(m):
            k = i * (m + 1) + j
            faces.append((k, k + m + 1, k + m + 2, k + 1))
    lid = smooth_mesh(
        side_name + " inner curved temple lid", verts, faces, "rubber", "covers"
    )
    mmod = lid.modifiers.new("Lid wall", "SOLIDIFY")
    mmod.thickness = 0.0008
    bevel(lid, 0.3)
    # Concealed stepped hinge knuckles and separate pin.
    for z in (13.5, 19, 24.5):
        knuckle = cylinder(
            side_name + " hinge knuckle", (side * 76, 22, z), 2.2, 4, "trim", g, "Z"
        )
        cut(
            knuckle, cylinder("Hinge bore", (side * 76, 22, z), 0.85, 7, None, axis="Z")
        )
    cylinder(
        side_name + " hinge pivot pin",
        (side * 76, 22, 19),
        0.8,
        16,
        "trim",
        "fasteners",
        "Z",
    )
    # Soft overmould fits over arm; model a hollow sleeve.
    sleeve = sweep(
        side_name + " silicone ear sleeve",
        [temple(side, 114 + 34 * i / 32, 0.28) for i in range(33)],
        "Y",
        "rubber",
        "pads",
        exponent=0.7,
    )
    cut(
        sleeve,
        sweep(
            "Sleeve internal tool",
            [temple(side, 113 + 36 * i / 32, -0.05) for i in range(33)],
            "Y",
            None,
            None,
            exponent=0.7,
        ),
    )
    # Tiny satin side rail and control locator, no large decorative hardware.
    pts = []
    for y in (29, 40, 51, 62, 73):
        c, a, b = temple(side, y)
        pts.append((c[0] + side * (a + 0.05), y, c[2] + 1))
    tube(side_name + " fine side accent", pts, 0.18, "trim", g)

reserve("FIT / IMU complete", (77, 43, 18), (4.6, 25.6, 17.8), "imu")
reserve("FIT / Haptic complete", (-77, 47, 18), (4.6, 25.8, 17.8), "haptic")
for side, ybase, groupkey in ((1, 43, "imu"), (-1, 47, "haptic")):
    for y in (ybase - 9, ybase + 9):
        box(
            "STEMMA QT connector reference",
            (side * 75.7, y, 18),
            (2, 4, 4),
            "rubber",
            groupkey,
            0.3,
        )
        for z in (16.8, 17.6, 18.4, 19.2):
            box(
                "QT fine contact",
                (side * 74.6, y, z),
                (0.2, 2, 0.25),
                "gold",
                groupkey,
                0.03,
            )

# Populated auxiliary boards are reference reservations, not exact purchased CAD.
box(
    "LSM6DSOX carrier reservation",
    (78.7, 43, 18),
    (1.2, 25.6, 17.8),
    "pcb",
    "imu",
    0.35,
    "Adafruit4438 nominal 25.6x17.8x4.6 complete envelope; component layout illustrative",
)
box("IMU package", (77.7, 43, 18), (1, 4, 3), "black", "imu", 0.15)
for y in (34, 37, 40, 46, 49, 52):
    box("IMU contact", (78.0, y, 23), (0.2, 0.7, 0.9), "gold", "imu", 0.06)
box(
    "DRV2605L carrier reservation",
    (-78.7, 47, 18),
    (1.2, 25.8, 17.8),
    "pcb",
    "haptic",
    0.35,
    "Adafruit2305 nominal 25.8x17.8x4.6 complete envelope; component layout illustrative",
)
box("DRV2605 driver package", (-77.7, 47, 18), (1, 4.5, 4.5), "black", "haptic", 0.2)
for y in (39, 42, 45, 48, 51, 54):
    box("Haptic contact", (-78.0, y, 23), (0.2, 0.7, 0.9), "gold", "haptic", 0.06)
cylinder(
    "Coin vibration motor reference", (-75.8, 69, 17), 4, 2.8, "trim", "haptic", "X"
)
for y, name in ((35, "Confirm"), (49, "Cancel repeat")):
    c, a, b = temple(-1, y)
    box(name + " switch", (c[0], y, c[2] + b - 2), (4, 5, 2), "black", "buttons", 0.3)
    cap = box(
        name + " flush key",
        (c[0], y, c[2] + b + 0.15),
        (5.5, 7.5, 0.9),
        "rubber",
        "buttons",
        1,
    )
    # A low tactile ridge distinguishes keys without visual dependence.
    box(
        name + " tactile ridge",
        (c[0], y, c[2] + b + 0.7),
        (3, 0.5, 0.3),
        "trim",
        "buttons",
        0.12,
    )
# Routed loom stays behind the optical module and within side volume.
tube(
    "ToF I2C loom",
    [(19, -5, 25), (20, 3, 27), (30, 5, 24), (50, 11, 22), (73, 21, 20), (76, 42, 18)],
    0.45,
    "orange",
    "wires",
)
tube(
    "Left haptic and button loom",
    [(-5, 5, 24), (-25, 6, 24), (-47, 9, 23), (-73, 20, 20), (-76, 64, 18)],
    0.45,
    "orange",
    "wires",
)
tube(
    "Internal USB harness study",
    [
        (-28, 2.3, 19),
        (-31, 4, 21),
        (-25, 7, 25),
        (0, 7, 26),
        (35, 9, 24),
        (58, 13, 22),
        (76, 26, 21),
        (77, 65, 18),
        (73, 113, 8),
    ],
    1.0,
    "rubber",
    "wires",
)
# External USB data/power cable exits at ear-rear, supplier bend radius unverified.
tube(
    "Integral ear-rear strain relief",
    [(73, 113, 8), (73, 121, 5), (74, 128, 1)],
    2,
    "rubber",
    "usb",
)
tube(
    "External USB tether",
    [(74, 127, 1), (82, 145, -13), (98, 145, -28), (111, 130, -32), (109, 115, -32)],
    1.15,
    "rubber",
    "usb",
)
box("Host USB-C overmould", (109, 109, -32), (8.5, 12, 4.5), "rubber", "usb", 1.5)
box("Host USB-C metal plug", (109, 101, -32), (7.8, 5, 2.4), "trim", "usb", 0.6)


# Real recesses and heads rather than un-detailed screw cylinders.
def screw(name, center, axis="Y", g="fasteners"):
    head = cylinder(name + " head", center, 1.2, 0.8, "trim", g, axis, vertices=32)
    cutter = box(
        "Screw driver recess",
        center,
        (1.45, 2, 0.32) if axis == "Y" else (2, 1.45, 0.32),
        None,
        radius=0,
    )
    cut(head, cutter)
    return head


for x in (-29, 30):
    c, a, b = brow(x)
    for z in (12, 26):
        screw("Brow M1.6 screw", (x, c[1] + a + 0.5, z))
for side in (-1, 1):
    for y in (30, 77):
        c, a, b = temple(side, y)
        screw("Temple M1.6 screw", (c[0] - side * (a + 0.55), y, c[2]), axis="X")

# Optional battery is a separately hidden concept collection, not an operating circuit.
G["battery"] = group("22 OPTIONAL battery packaging / not baseline", (0, 0, 0))
start_optional = len(parts)
cell = box(
    "OPTIONAL LiPo pouch envelope",
    (0, 45, 0),
    (7, 38, 15),
    "trim",
    "battery",
    1.2,
    "Candidate envelope ONLY. No capacity, swelling allowance, supplier or power path approved",
)
box(
    "OPTIONAL pouch insulated seal",
    (0, 25.5, 0),
    (7.5, 1.5, 15.5),
    "orange",
    "battery",
    0.4,
)
box("OPTIONAL protection PCB", (0, 21.5, 0), (1, 6, 13), "pcb", "battery", 0.25)
box("OPTIONAL protection IC", (-1, 21.5, 0), (1, 3, 3), "black", "battery", 0.15)
tube(
    "OPTIONAL positive lead",
    [(0, 18, 4), (0, 13, 5), (2, 10, 5)],
    0.3,
    "orange",
    "battery",
)
tube(
    "OPTIONAL negative lead",
    [(0, 18, -4), (0, 13, -3), (2, 10, -3)],
    0.3,
    "black",
    "battery",
)
box("OPTIONAL battery microplug", (3, 10, 1), (4, 4, 10), "rubber", "battery", 0.6)
for o in parts[start_optional:]:
    o["optional_only"] = True
G["battery"][0].hide_render = True
G["battery"][0].hide_viewport = True


# Studio, typography, and reproducible still views.
def text3d(
    name, body, location, size, key="white", g=None, rotation=(math.pi / 2, 0, 0)
):
    c = bpy.data.curves.new(name, "FONT")
    c.body = body
    c.size = size * 0.001
    c.extrude = 0.006 * 0.001
    o = bpy.data.objects.new(name, c)
    scene.collection.objects.link(o)
    o.location = mm(location)
    o.rotation_euler = rotation
    return register(o, name, key, g)


# Tiny board silkscreen is a reference label, not a reproduction of PCB artwork.
text3d("Board model label", "XIAO / S3", (-7, 1.85, 19), 1, "white", "camera")
text3d("Camera label", "OV5640", (-8, -7.2, 24.2), 0.8, "white", "camera")
box("Studio floor", (0, 40, -63), (1300, 1300, 3), "floor", radius=0)
bpy.ops.object.camera_add(location=mm((255, -390, 215)))
cam = bpy.context.object
cam.name = "Camera / BLACK final"
cam.rotation_euler = (mm((3, 46, 2)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
scene.camera = cam
for frame, scale in (
    (1, 0.315),
    (35, 0.315),
    (110, 0.435),
    (150, 0.435),
    (225, 0.315),
    (240, 0.315),
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
    o.data.size_y = size * 0.00065
    o.data.color = color
    o.rotation_euler = (mm((0, 40, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()


area("Soft key", (-150, -180, 270), 3.4, 280, (0.92, 0.96, 1))
area("Warm fill", (220, -60, 200), 1.9, 240, (1, 0.96, 0.91))
area("Edge strip", (-30, 220, 190), 3.8, 250, (0.8, 0.9, 1))
area("Front soft strip", (0, -240, 40), 0.5, 170, (1, 1, 1))
mat["ink"] = material("13 | Editorial dark ink", (0.018, 0.025, 0.033), 0, 0.7)
mat["silver"] = material("14 | Budget annotation", (0.13, 0.18, 0.22), 0, 0.6)


for key, color in (("ink", (0.018, 0.023, 0.03, 1)), ("silver", (0.07, 0.09, 0.11, 1))):
    nodes = mat[key].node_tree.nodes
    nodes.clear()
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = 1
    outnode = nodes.new("ShaderNodeOutputMaterial")
    mat[key].node_tree.links.new(emit.outputs[0], outnode.inputs["Surface"])


def overlay(name, body, x, y, size, key="ink"):
    o = text3d(name, body, (0, 0, 0), size, key)
    o.parent = cam
    o.rotation_euler = (0, 0, 0)
    for frame, k in (
        (1, 1),
        (35, 1),
        (110, 0.435 / 0.315),
        (150, 0.435 / 0.315),
        (225, 1),
        (240, 1),
    ):
        o.location = (x * k, y * k, -0.46)
        o.scale = (k,) * 3
        o.keyframe_insert(data_path="location", frame=frame)
        o.keyframe_insert(data_path="scale", frame=frame)
    return o


overlay("Title", "X / GLASSES", -0.14, 0.084, 8.2)
overlay("Subtitle", "BLACK  /  OV5640 + ToF", -0.139, 0.073, 2.5, "silver")
overlay(
    "Footer", "INTEGRATED STRUCTURE   /   USB POWER + DATA", -0.139, -0.087, 2, "silver"
)
overlay(
    "Caveat",
    "NOMINAL PACKAGING STUDY  -  PHYSICAL FIT / THERMAL / OPTICAL TESTS PENDING",
    -0.139,
    -0.094,
    1.55,
    "silver",
)
label = overlay("View label", "01 / ASSEMBLED", 0.085, 0.085, 2, "silver")
for frame, title in (
    (1, "ASSEMBLED"),
    (35, "DISASSEMBLE"),
    (110, "EXPLODED"),
    (150, "REASSEMBLE"),
    (225, "ASSEMBLED"),
):
    scene.timeline_markers.new(title, frame=frame)
scene["design_status"] = (
    "User-approved black design; nominal fit study, not manufacturing release"
)
scene["brow_budget_mm_XZY"] = [60, 26, 25]
scene["wall_budget_mm"] = 1.5
scene["hardware_revision"] = (
    "User owns OV5640; exact purchased FPC/lens/board geometry still to measure"
)
scene["main_stack_nominal_mm_XZY"] = [21, 17.8, 15]
scene["playback"] = (
    "Space: 10s explode/restore. Frame1/240 assembled,130 exploded. Collection22 optional only."
)
readme = bpy.data.texts.new("READ ME - 使用说明")
readme.write(
    "X-GLASSES / BLACK / OV5640\n\n用户已确认黑色整体造型与加厚眉框。\n空格播放240帧拆装；1/240装配，130爆炸。\n集合01-21为基线，22为独立电池包络候选，默认隐藏。\nFIT开头对象为隐藏渲染的真实尺度名义包络。\n眉框中央60宽，26高，25前后深；壁厚预算1.5。\n主控板官方名义21x17.8x15，具体到货OV5640仍需量取。\n小元件/安装孔/线缆/连接器为结构参考，不是精确原厂CAD或生产图。\nUSB供电，无已验证电池电路。\n详细操作与实际校核见交付README和verification.json。\n"
)
scene.frame_set(1)
bpy.context.view_layer.update()
# Use true evaluated world-space geometry for BOM dimensions, excluding Blender curve cages.
deps = bpy.context.evaluated_depsgraph_get()
with (OUT / "parts.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(
        [
            "part_id",
            "name",
            "assembly",
            "optional",
            "fit_only",
            "width_x_mm",
            "depth_y_mm",
            "height_z_mm",
            "status",
        ]
    )
    for o in parts:
        eo = o.evaluated_get(deps)
        mesh = eo.to_mesh()
        pts = [eo.matrix_world @ v.co for v in mesh.vertices] if mesh else []
        dims = (
            [(max(v[i] for v in pts) - min(v[i] for v in pts)) * 1000 for i in range(3)]
            if pts
            else [0] * 3
        )
        eo.to_mesh_clear()
        w.writerow(
            [
                o["part_id"],
                o.name,
                o.parent.name,
                bool(o.get("optional_only")),
                bool(o.get("fit_reservation")),
                *[round(v, 3) for v in dims],
                o["design_status"],
            ]
        )
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type == "VIEW_3D":
            a.spaces.active.region_3d.view_distance = 0.34
            a.spaces.active.region_3d.view_location = mm((0, 44, 0))
            a.spaces.active.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            a.spaces.active.shading.type = "MATERIAL"
            a.spaces.active.clip_start = 0.001
            a.spaces.active.clip_end = 10
bpy.ops.object.select_all(action="DESELECT")
scene.render.filepath = str(OUT / "assembled.png")
bpy.ops.wm.save_as_mainfile(
    filepath=str(OUT / "X-Glasses_BLACK_OV5640.blend"), compress=True
)
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
    label.data.body = "03 / INTERNAL LAYOUT"
    scene.render.filepath = str(OUT / "internal.png")
    bpy.ops.render.render(write_still=True)
    for g in ("pod", "face", "back", "covers"):
        G[g][0].hide_render = False
    # The front orthographic view reveals actual silhouette and brow height.
    for child in cam.children:
        child.hide_render = True
    oldloc = cam.location.copy()
    oldrot = cam.rotation_euler.copy()
    cam.location = mm((0, -420, 28))
    cam.rotation_euler = (
        (mm((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    )
    cam.data.animation_data_clear()
    cam.data.ortho_scale = 0.23
    label.data.body = "04 / FRONT"
    scene.render.filepath = str(OUT / "front.png")
    bpy.ops.render.render(write_still=True)
    # Close-up of populated reference boards, with external skins temporarily removed.
    cam.location = mm((125, -190, 130))
    cam.rotation_euler = (
        (mm((0, 12, 18)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    )
    cam.data.ortho_scale = 0.15
    for g in ("pod", "face", "back", "covers"):
        G[g][0].hide_render = True
    label.data.body = "05 / HARDWARE DETAIL"
    scene.render.filepath = str(OUT / "hardware_detail.png")
    bpy.ops.render.render(write_still=True)
    for g in ("pod", "face", "back", "covers"):
        G[g][0].hide_render = False
    cam.location = oldloc
    cam.rotation_euler = oldrot
    scene.frame_set(1)
    label.data.body = "01 / ASSEMBLED"
# The saved file precedes view-only render changes; re-open verifier checks that artifact.
report = {
    "blender": bpy.app.version_string,
    "part_objects": len(parts),
    "baseline_groups": 21,
    "optional_groups": 1,
    "nominal_brow_budget_mm_XZY": [60, 26, 25],
    "main_stack_nominal_mm_XZY": [21, 17.8, 15],
    "user_camera": "OV5640",
    "hardware_verified": False,
    "manufacturing_verified": False,
}
(OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("BLACK_BUILD_COMPLETE", json.dumps(report), flush=True)
