
import bpy, math, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
if src.lower().endswith(".glb"):
    bpy.ops.import_scene.gltf(filepath=src)
else:
    bpy.ops.wm.ply_import(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mat = bpy.data.materials.new("m"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.72, 0.73, 0.76, 1); b.inputs["Roughness"].default_value = 0.42
for o in objs:
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
bb = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(v[i] for v in bb) for i in range(3))); mx = Vector((max(v[i] for v in bb) for i in range(3)))
ctr = (mn + mx) / 2; size = max(mx - mn) * 1.08
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = size
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
t = math.radians(35)
cam.location = ctr + Vector((math.sin(t) * 9, -math.cos(t) * 9, 0.0))
cam.rotation_euler = (math.radians(90), 0, t)
for nm, rot, e in (("key", (55, 0, -40), 2.2), ("fill", (70, 0, 120), 0.5), ("rim", (120, 0, 200), 0.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
    l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
    l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.2
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("렌더 끝")
