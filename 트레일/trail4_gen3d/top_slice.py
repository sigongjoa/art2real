import math, os, sys, json
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
ZC=float(argv[2])
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
keep=cen[:,2]>ZC
u,n=np.unique(pid[keep],return_counts=True)
print(f"z>{ZC} 면 {int(keep.sum()):,}")
for i in np.argsort(-n)[:8]:
    nm=names[u[i]-1] if 0<u[i]<=len(names) else f"?{u[i]}"
    s=(pid==u[i])&keep; cc=cen[s]
    print(f"  {nm:16s} {int(n[i]):6,}  x[{cc[:,0].min():+.3f},{cc[:,0].max():+.3f}] "
          f"y[{cc[:,1].min():+.3f},{cc[:,1].max():+.3f}] z max {cc[:,2].max():.3f}")
rng=np.random.default_rng(3)
pal={int(p):tuple(rng.uniform(0.2,0.95,3)) for p in np.unique(pid)}
ca=me.color_attributes.new("t",'BYTE_COLOR','CORNER')
buf=np.empty(len(me.loops)*4,np.float32); buf[3::4]=1.0
ls=np.empty(nf,np.int32); me.polygons.foreach_get("loop_start",ls)
lt=np.empty(nf,np.int32); me.polygons.foreach_get("loop_total",lt)
for i in range(nf):
    col=pal[int(pid[i])] if keep[i] else (0.88,0.88,0.90)
    s=ls[i]*4
    for j in range(lt[i]): buf[s+j*4:s+j*4+3]=col
ca.data.foreach_set("color",buf); me.update()
me.materials.clear()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='VERTEX'
sc.display.shading.show_cavity=True
sc.render.film_transparent=True
sc.render.resolution_x=800; sc.render.resolution_y=620
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=0.62
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((90,"side"),(0,"front"),(45,"q")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.92); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("TOP OK")
