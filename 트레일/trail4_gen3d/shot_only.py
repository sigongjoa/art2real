import math, os, sys, json
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
KEEP=set(json.loads(argv[2]))
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
pid=np.empty(len(me.polygons),np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
keep={i+1 for i,n in enumerate(names) if n in KEEP}
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[f for f in bm.faces if pid[f.index] not in keep],context='FACES')
bm.to_mesh(me); bm.free()
v=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",v); v=v.reshape(-1,3)
if len(v):
    print(f"{sorted(KEEP)} 면 {len(me.polygons):,} x[{v[:,0].min():+.3f},{v[:,0].max():+.3f}] "
          f"y[{v[:,1].min():+.3f},{v[:,1].max():+.3f}] z[{v[:,2].min():+.3f},{v[:,2].max():+.3f}]")
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='MATCAP'; sc.display.shading.studio_light='basic_1.exr'
sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.85,0.85,0.87)
sc.render.film_transparent=True
sc.render.resolution_x=560; sc.render.resolution_y=700
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=0.6
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((90,"side"),(0,"front")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.88); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("ONLY OK")
