
import bpy, math, sys, glob, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
d, out, tag, explode = a[0], a[1], a[2], float(a[3])
cols = eval(a[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for i, f in enumerate(sorted(glob.glob(os.path.join(d, "부품_*.ply")))):
    bpy.ops.wm.ply_import(filepath=f)
    o = bpy.context.selected_objects[0]
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("m%d" % i); mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    c = cols[i % len(cols)]
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    b.inputs["Roughness"].default_value = 0.5
    o.data.materials.append(mat)
    objs.append(o)
allb = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(v[i] for v in allb) for i in range(3))); mx = Vector((max(v[i] for v in allb) for i in range(3)))
ctr = (mn + mx) / 2; size = max(mx - mn) * (1.12 + explode * 1.4)
if explode:
    for o in objs:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        c = sum(bb, Vector((0, 0, 0))) / 8
        v = c - ctr
        if v.length > 1e-6:
            o.location = o.location + v.normalized() * (size * explode)
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = size
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, rot, e in (("key", (55, 0, -40), 1.6), ("fill", (70, 0, 120), 0.4), ("rim", (120, 0, 200), 0.7)):
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
for name, az in (("앞", 0), ("사선", 40), ("옆", 90)):
    t = math.radians(az)
    cam.location = ctr + Vector((math.sin(t) * 6, -math.cos(t) * 6, 0.0))
    cam.rotation_euler = (math.radians(90), 0, t)
    sc.render.filepath = "%s/파츠_%s_%s.png" % (out, tag, name)
    bpy.ops.render.render(write_still=True)
print("렌더 끝", tag)
