import bpy, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\B1"
sc = H.scene(res=(400, 400))
bpy.ops.import_scene.gltf(filepath=r"G:\art2real\트레일\trail4_gen3d\out\knights\h_Omegamon_main.glb")
obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("MESHES", [(o.name, len(o.data.vertices), len(o.data.polygons)) for o in obs])
o = obs[0]
bpy.context.view_layer.objects.active = o
for x in obs: x.select_set(x == o)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mod = o.modifiers.new("d", "DECIMATE"); mod.ratio = 60000 / len(o.data.polygons); bpy.ops.object.modifier_apply(modifier="d")
bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
lo = mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); hi = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
print("BBOX", lo, hi, "VERTS", len(o.data.vertices))
c = (lo + hi) / 2; s = 100 / max(hi - lo)
o.location = -c * s; o.scale = (s, s, s); bpy.ops.object.transform_apply(location=True, scale=True)
o.color = (0.9, 0.9, 0.92, 1)
for n, (yaw, pitch) in {"y-":(0,0), "x+":(90,0), "y+":(180,0), "x-":(-90,0), "top":(0,89), "bot":(0,-89)}.items():
    H.look((0,0,0), yaw, pitch, ortho=120); H.shot(os.path.join(OUT, "check_%s.png" % n))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "head60k.blend"))
