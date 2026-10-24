"""Render hardware and optional battery close-ups from the saved final assembly."""

from pathlib import Path

import bpy
from mathutils import Vector

out = Path(bpy.data.filepath).parent
s = bpy.context.scene
s.frame_set(1)
cam = s.camera
cam.data.animation_data_clear()
cam.data.ortho_scale = 0.065
cam.location = Vector((-0.045, -0.095, 0.055))
cam.rotation_euler = (
    (Vector((-0.005, 0, 0.019)) - cam.location).to_track_quat("-Z", "Y").to_euler()
)
s.render.resolution_x = 1400
s.render.resolution_y = 1000
s.cycles.samples = 48
for child in cam.children:
    child.hide_render = True
for o in s.objects:
    if o.type in ("LIGHT", "CAMERA"):
        continue
    o.hide_render = True
keep = (
    "XIAO ESP32-S3 control PCB",
    "ESP32 RF shield",
    "Castellated plated contact",
    "Contact bore",
    "Decoupling capacitor",
    "Capacitor silver termination",
    "Logic IC",
    "IC lead",
    "Native USB-C receptacle",
    "USB-C contact tongue",
    "USB-C fine contact",
    "Board model label",
)
for o in s.objects:
    if any(o.name.startswith(p) for p in keep):
        o.hide_render = False
s.render.filepath = str(out / "mainboard_detail.png")
bpy.ops.render.render(write_still=True)
# Optional battery stays isolated from baseline; no powered circuit is demonstrated.
for o in s.objects:
    if o.type not in ("LIGHT", "CAMERA"):
        o.hide_render = True
collection = next(c for c in bpy.data.collections if c.name.startswith("22 OPTIONAL"))
collection.hide_render = False
collection.hide_viewport = False
for o in collection.objects:
    o.hide_render = False
cam.location = Vector((0.07, -0.055, 0.055))
cam.rotation_euler = (
    (Vector((0, 0.04, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
)
cam.data.ortho_scale = 0.085
s.render.filepath = str(out / "optional_battery_packaging.png")
bpy.ops.render.render(write_still=True)
print("DETAILS_COMPLETE", flush=True)
