"""Reopen the BLACK .blend and validate nominal packaging and animation.
This checks selected simplified geometry, not production clearances or physical safety.
"""

import itertools
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

scene = bpy.context.scene
out = Path(bpy.data.filepath).parent
assert Path(bpy.data.filepath).name == "X-Glasses_BLACK_OV5640.blend"
parts = [o for o in scene.objects if "part_id" in o]
roots = [o for o in scene.objects if "explosion_mm" in o]
assert len(roots) == 22
assert len(parts) > 200
assert len({o["part_id"] for o in parts}) == len(parts)
assert scene.unit_settings.system == "METRIC"
assert scene.unit_settings.length_unit == "MILLIMETERS"
assert scene.render.fps == 24
assert scene.frame_start == 1 and scene.frame_end == 240
scene.frame_set(1)
bpy.context.view_layer.update()
initial = {o.name: o.matrix_world.copy() for o in parts}
scene.frame_set(130)
bpy.context.view_layer.update()
for o in roots:
    assert (o.location - Vector(o["explosion_mm"]) * 0.001).length < 1e-7, o.name
scene.frame_set(240)
bpy.context.view_layer.update()
error = max(
    max(
        abs(o.matrix_world[i][j] - initial[o.name][i][j])
        for i in range(4)
        for j in range(4)
    )
    for o in parts
)
assert error < 1e-7
scene.frame_set(1)
bpy.context.view_layer.update()
for o in parts:
    assert all(math.isfinite(v) for row in o.matrix_world for v in row)
    if o.type == "MESH":
        assert len(o.data.vertices) > 0 and len(o.data.polygons) > 0
        assert all(math.isfinite(v) for p in o.data.vertices for v in p.co)


def brow_cavity_score(x, y, z):
    u = max(0, min(1, (abs(x) - 30) / 47))
    f = u * u * (3 - 2 * u)
    cy = -1 + 0.0024 * x * x
    cz = 19 + 0.7 * f
    a = 12.5 - 4 * f - 1.5
    b = 13 - 2.5 * f - 1.5
    return (abs(y - cy) / a) ** 4 + (abs(z - cz) / b) ** 4


def temple_cavity_score(x, y, z):
    side = 1 if x > 0 else -1
    t = (y - 22) / 126
    cx = side * (
        76 + 1.5 * math.sin(t * math.pi) - 9 * max(0, (t - 0.58) / 0.42) ** 1.6
    )
    cz = 19 - 7 * t - 20 * max(0, (t - 0.68) / 0.32) ** 1.6
    a = 7.2 - 3.7 * t - 1.25
    b = 12.5 + 1.3 * math.sin(min(1, t / 0.48) * math.pi) - 6.9 * t * t - 1.25
    return (abs(x - cx) / a) ** (2 / 0.6) + (abs(z - cz) / b) ** (2 / 0.6)


fit = []
for o in [p for p in parts if p.get("fit_reservation")]:
    size = [v * 1000 for v in o.dimensions]
    center = [v * 1000 for v in o.matrix_world.translation]
    is_aux = "IMU complete" in o.name or "Haptic complete" in o.name
    pad = 0.5 if is_aux or "Pololu3417" in o.name else 0
    # Dense samples along the curved cavity axis, corners in the other axes.
    if is_aux:
        coords = [
            (
                center[0] + sx * (size[0] / 2 + pad),
                center[1] + (size[1] / 2 + pad) * (i / 20 * 2 - 1),
                center[2] + sz * (size[2] / 2 + pad),
            )
            for sx, sz in itertools.product((-1, 1), repeat=2)
            for i in range(21)
        ]
        score = max(temple_cavity_score(*p) for p in coords)
    else:
        coords = [
            (
                center[0] + (size[0] / 2 + pad) * (i / 20 * 2 - 1),
                center[1] + sy * (size[1] / 2 + pad),
                center[2] + sz * (size[2] / 2 + pad),
            )
            for sy, sz in itertools.product((-1, 1), repeat=2)
            for i in range(21)
        ]
        score = max(brow_cavity_score(*p) for p in coords)
    fit.append(
        {
            "name": o.name,
            "size_mm_xyz": size,
            "additional_clearance_each_side_mm": pad,
            "max_rounded_cavity_score": score,
            "passes": score < 1,
        }
    )
# Fit failures are persisted before exiting, not discarded.
(out / "fit_results.json").write_text(json.dumps(fit, indent=2), encoding="utf-8")
for r in fit:
    print(
        "FIT",
        r["name"],
        round(r["max_rounded_cavity_score"], 5),
        r["passes"],
        flush=True,
    )
assert all(r["passes"] for r in fit), (
    "Nominal reservation conflicts with rounded cavity"
)
# Shell-only axial clearance is not a complete FoV or crosstalk test.
shell = bpy.data.objects["Brow outer shell / 26H x 25D central"]
for x in (-5, 19):
    inv = shell.matrix_world.inverted()
    origin = inv @ Vector((x * 0.001, -0.04, 0.019))
    direction = inv.to_3x3() @ Vector((0, 1, 0))
    assert not shell.ray_cast(origin, direction, distance=0.035)[0], (
        "Blocked sensor opening"
    )
# Geometric world envelope from real evaluated vertices, never curve control-point cages.
deps = bpy.context.evaluated_depsgraph_get()
points = []
for o in parts:
    if o.get("optional_only") or o.get("fit_reservation") or o.type == "FONT":
        continue
    if o.parent.name.startswith("19 "):
        continue
    eo = o.evaluated_get(deps)
    mesh = eo.to_mesh()
    if mesh:
        points.extend(eo.matrix_world @ v.co for v in mesh.vertices)
    eo.to_mesh_clear()
size = [
    (max(p[i] for p in points) - min(p[i] for p in points)) * 1000 for i in range(3)
]
report = {
    "blender": bpy.app.version_string,
    "part_objects": len(parts),
    "assembly_groups": 21,
    "optional_groups": 1,
    "fit_reservations": len(fit),
    "unique_ids": True,
    "exploded_transforms_match": True,
    "restored_transform_error": error,
    "finite_nonempty_geometry": True,
    "selected_nominal_envelopes_fit": True,
    "temple_additional_clearance_each_side_mm": 0.5,
    "sensor_shell_axes_clear": True,
    "structural_envelope_mm_xyz": [round(v, 3) for v in size],
    "checks_do_not_cover": [
        "exact as-bought OV5640 revision",
        "all-parts interference",
        "connector supplier and cable bends",
        "optical FoV and crosstalk",
        "thread tolerance",
        "hinge fatigue",
        "power or thermal",
        "human fit",
        "manufacturing readiness",
    ],
    "hardware_verified": False,
    "manufacturing_verified": False,
}
(out / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("BLACK_VERIFIED", json.dumps(report), flush=True)
if "--movie" in sys.argv:
    scene.cycles.samples = 6
    scene.render.resolution_percentage = 50
    scene.render.fps = 8
    scene.frame_step = 3
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(out / "assembly_preview.mp4")
    bpy.data.objects["View label"].data.body = "EXPLODE / RESTORE"
    bpy.ops.render.render(animation=True)
    print("BLACK_MOVIE_COMPLETE", flush=True)
