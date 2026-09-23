
import bpy, math, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out, u0, u1, z0, z1 = a[0], a[1], float(a[2]), float(a[3]), float(a[4]), float(a[5])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=src)
o = bpy.context.selected_objects[0]
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("m"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.72, 0.73, 0.76, 1); b.inputs["Roughness"].default_value = 0.45
o.data.materials.append(mat)
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = max(u1 - u0, z1 - z0)
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = Vector(((u0 + u1) / 2, -6.0, (z0 + z1) / 2))      # **원화 창과 같은 틀** (화소가 1:1 로 맞는다)
cam.rotation_euler = (math.radians(90), 0, 0)
for nm, rot, e in (("key", (55, 0, -40), 2.0), ("fill", (70, 0, 120), 0.5), ("rim", (120, 0, 200), 0.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
    l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
    l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.22
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("렌더 끝")
