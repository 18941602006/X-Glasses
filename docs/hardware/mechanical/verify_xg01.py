"""Reopen-based Blender validation and optional lightweight movie export."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

scene = bpy.context.scene
out = Path(bpy.data.filepath).parent
assert Path(bpy.data.filepath).name == "X-Glasses_XG01.blend"
parts = [o for o in scene.objects if "part_id" in o]
roots = [o for o in scene.objects if "explosion_mm" in o]
assert len(roots) == 21
assert len(parts) > 80
assert len({o["part_id"] for o in parts}) == len(parts)
assert scene.unit_settings.length_unit == "MILLIMETERS"
assert scene.frame_start == 1 and scene.frame_end == 240
assert all(o.parent in roots for o in parts)
scene.frame_set(1)
bpy.context.view_layer.update()
initial = {o.name: o.matrix_world.copy() for o in parts}
scene.frame_set(130)
bpy.context.view_layer.update()
for o in roots:
    expected = Vector(o["explosion_mm"]) * 0.001
    assert (o.location - expected).length < 1e-7, o.name
scene.frame_set(240)
bpy.context.view_layer.update()
max_error = max(
    max(
        abs(o.matrix_world[i][j] - initial[o.name][i][j])
        for i in range(4)
        for j in range(4)
    )
    for o in parts
)
assert max_error < 1e-7
scene.frame_set(1)
bpy.context.view_layer.update()
for o in parts:
    assert all(math.isfinite(v) for row in o.matrix_world for v in row)
    if o.type == "MESH":
        assert len(o.data.vertices) > 0 and len(o.data.polygons) > 0
        assert all(math.isfinite(v) for vertex in o.data.vertices for v in vertex.co)
# Structural envelope excludes external cable; evaluated geometry includes modifiers.
deps = bpy.context.evaluated_depsgraph_get()
points = []
for o in parts:
    if o.parent.name.startswith("19 ") or o.type == "FONT":
        continue
    eo = o.evaluated_get(deps)
    mesh = eo.to_mesh()
    if mesh:
        points.extend(eo.matrix_world @ v.co for v in mesh.vertices)
    eo.to_mesh_clear()
size = [
    (max(p[i] for p in points) - min(p[i] for p in points)) * 1000 for i in range(3)
]
assert 150 < size[0] < 170 and 155 < size[1] < 190 and 50 < size[2] < 75
# Verify sensor housing is open through the front: direct ray should not hit housing
# at the optical centre. It deliberately excludes faceplate and optical parts.
pod = bpy.data.objects["Central sensor enclosure / 54 x 25 x 28"]
inv = pod.matrix_world.inverted()
origin = inv @ Vector((-0.012, -0.04, 0.022))
direction = inv.to_3x3() @ Vector((0, 1, 0))
hit = pod.ray_cast(origin, direction, distance=0.035)[0]
assert not hit, "Sensor housing blocks camera optical axis"
report = {
    "blender": bpy.app.version_string,
    "reopened_file": Path(bpy.data.filepath).name,
    "part_objects": len(parts),
    "assembly_groups": len(roots),
    "unique_part_ids": True,
    "frame130_explosion_matches": True,
    "frame240_returns_to_frame1": True,
    "max_transform_error": max_error,
    "finite_nonempty_geometry": True,
    "housing_camera_axis_open": True,
    "structural_envelope_mm_xyz": [round(v, 2) for v in size],
    "manufacturing_clearances_checked": False,
    "collision_free_claim": False,
    "optical_fov_verified": False,
    "hardware_verified": False,
}
(out / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("XG01_VERIFIED", json.dumps(report))
if "--movie" in sys.argv:
    scene.cycles.samples = 4
    scene.render.resolution_percentage = 60
    scene.render.fps = 8
    scene.frame_step = 3
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(out / "assembly_preview.mp4")
    bpy.data.objects["View label"].data.body = "ASSEMBLE / EXPLODE"
    bpy.ops.render.render(animation=True)
    print("XG01_MOVIE_COMPLETE")
