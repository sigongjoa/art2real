# -*- coding: utf-8 -*-
"""CAD 얼굴 판(brow/eye/muzzle/뿔)을 생성 머리에 얹는다.

    blender -b --python add_face.py -- out/df_baked.blend out/withface

ep01 교훈 — 디테일은 조각하지 않고 **별개 오브젝트로 얹는다**. 생성 머리는
매끈한 돔이라 바이저·입가리개가 없는데, trail3 CAD 에 이미 그 판들이 있다.
정렬은 assign_named 와 같다 (높이로 배율, 접지선만 맞춤).
"""
import glob, math, os, sys
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
PXD=os.path.join(HERE,"..","trail3_freecad","proxy")
FACE=["a_brow","a_eye","a_eye_M","a_muzzle","a_helm_spike","a_helm_horn","a_helm_horn_M"]
COL={"a_brow":(0.93,0.93,0.95,1),"a_eye":(0.85,0.20,0.18,1),"a_eye_M":(0.85,0.20,0.18,1),
     "a_muzzle":(0.20,0.20,0.24,1),"a_helm_spike":(0.93,0.93,0.95,1),
     "a_helm_horn":(0.85,0.70,0.28,1),"a_helm_horn_M":(0.85,0.70,0.28,1)}
bpy.ops.wm.open_mainfile(filepath=SRC)
gen=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
c=np.empty(len(gen.data.polygons)*3); gen.data.polygons.foreach_get("center",c); c=c.reshape(-1,3)
gl,gh=c.min(0),c.max(0)
# 전체 프록시로 배율·접지 계산 (assign_named 와 동일)
allv=[]
for p in sorted(glob.glob(os.path.join(PXD,"*.stl"))):
    if os.path.splitext(os.path.basename(p))[0] in {"c_cuirass","c_helm"}: continue
    bpy.ops.wm.stl_import(filepath=p)
    o=bpy.context.selected_objects[0]
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v)
    allv.append(v.reshape(-1,3)*0.001)
    bpy.data.objects.remove(o,do_unlink=True)
pts=np.vstack(allv); lo,hi=pts.min(0),pts.max(0)
s=(gh[2]-gl[2])/(hi[2]-lo[2])
zoff=gl[2]-lo[2]*s
print(f"배율 {s:.4f}  z오프셋 {zoff:+.4f}")
added=[]
for nm in FACE:
    p=os.path.join(PXD,nm+".stl")
    if not os.path.exists(p): print("없음",nm); continue
    bpy.ops.wm.stl_import(filepath=p)
    o=bpy.context.selected_objects[0]; o.name=nm
    o.scale=(0.001*s,)*3
    o.location=(0,0,zoff)
    m=bpy.data.materials.new(nm); m.use_nodes=True
    nt=m.node_tree; em=nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value=COL[nm]
    nt.links.new(em.outputs["Emission"],nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m)
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
    w=v*0.001*s+np.array([0,0,zoff])
    print(f"  {nm:16s} 면 {len(o.data.polygons):>5,} x[{w[:,0].min():+.3f},{w[:,0].max():+.3f}] "
          f"z[{w[:,2].min():+.3f},{w[:,2].max():+.3f}]")
    added.append(o.name)
print(f"얹은 판 {len(added)}개")
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=700
sc.view_settings.view_transform='Standard'
w_=bpy.data.worlds.new("w"); w_.use_nodes=True
w_.node_tree.nodes["Background"].inputs[1].default_value=1.5; sc.world=w_
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=0.40
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side"),(35,"q")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.905); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=PRE+".blend")
print("FACE OK")
