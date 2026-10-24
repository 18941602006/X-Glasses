"""Verify saved FLOW02 assembly and optionally export a preview movie."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

scene = bpy.context.scene
out = Path(bpy.data.filepath).parent
assert Path(bpy.data.filepath).name == "X-Glasses_FLOW02.blend"
parts = [o for o in scene.objects if "part_id" in o]
roots = [o for o in scene.objects if "explosion_mm" in o]
assert len(roots) == 21 and len(parts) > 70
assert len({o["part_id"] for o in parts}) == len(parts)
assert scene.unit_settings.length_unit == "MILLIMETERS"
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
        assert all(math.isfinite(v) for vertex in o.data.vertices for v in vertex.co)
# Compute actual world-space vertices, rather than conservative curve bounding boxes.
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
print("ACTUAL_STRUCTURAL_ENVELOPE_MM", size, flush=True)
assert 145 < size[0] < 180 and 140 < size[1] < 200 and 45 < size[2] < 85
shell = bpy.data.objects["Monocoque brow / continuous outer skin"]
# A local ray against just the external shell must clear camera and ToF apertures.
for x, z in ((-10, 15), (18, 15)):
    inv = shell.matrix_world.inverted()
    origin = inv @ Vector((x * 0.001, -0.04, z * 0.001))
    direction = inv.to_3x3() @ Vector((0, 1, 0))
    hit = shell.ray_cast(origin, direction, distance=0.035)[0]
    assert not hit, "Blocked optical axis"
report = {
    "blender": bpy.app.version_string,
    "parts": len(parts),
    "groups": len(roots),
    "unique_ids": True,
    "explosion_matches": True,
    "assembly_returns_exactly": True,
    "max_transform_error": error,
    "finite_nonempty_geometry": True,
    "shell_camera_and_tof_axes_clear": True,
    "structural_envelope_mm_xyz": [round(v, 2) for v in size],
    "manufacturing_clearances_verified": False,
    "optical_fov_verified": False,
    "collision_free_claim": False,
    "hardware_verified": False,
}
(out / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("FLOW02_VERIFIED", json.dumps(report), flush=True)
if "--movie" in sys.argv:
    scene.cycles.samples = 4
    scene.render.resolution_percentage = 50
    scene.render.fps = 8
    scene.frame_step = 3
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(out / "assembly_preview.mp4")
    bpy.data.objects["View label"].data.body = "ASSEMBLY / EXPLODE"
    bpy.ops.render.render(animation=True)
    print("FLOW02_MOVIE_COMPLETE", flush=True)
