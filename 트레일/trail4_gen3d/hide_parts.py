import math, os, sys, json
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
DROP=set(json.loads(argv[2]))
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
pid=np.empty(len(me.polygons),np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
drop={i+1 for i,n in enumerate(names) if n in DROP}
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[f for f in bm.faces if pid[f.index] in drop],context='FACES')
bm.to_mesh(me); bm.free()
print(f"제외 {sorted(DROP)} -> 면 {len(me.polygons):,}")
bpy.ops.wm.save_as_mainfile(filepath=PRE+".blend")
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.render.film_transparent=True
sc.render.resolution_x=540; sc.render.resolution_y=980
sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new("w"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[1].default_value=1.5; sc.world=w
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.15
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((90,"R"),(270,"L"),(0,"front")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("HIDE OK")
