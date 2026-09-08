# -*- coding: utf-8 -*-
"""닫힌 메시에 QuadriFlow 를 걸고 UV·능선·곡률이 같이 좋아지는지 본다.

    blender -b --python retopo.py -- out/depthfit.blend out/retopo.blend [면수]

앞서 잘라낸 파츠(열린 셸)에 걸었을 땐 조용히 실패했다(면 수가 그대로였다).
자르기 **전** 닫힌 메시에 걸어야 한다.
"""
import math, os, sys, time
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,OUT=os.path.abspath(argv[0]),os.path.abspath(argv[1])
TGT=int(argv[2]) if len(argv)>2 else 60000
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
n0=len(o.data.polygons)

def stats(me,tag):
    bm=bmesh.new(); bm.from_mesh(me)
    ang=np.array([math.degrees(e.calc_face_angle(0.0)) for e in bm.edges if len(e.link_faces)==2])
    ar=[]
    for f in bm.faces:
        e=[ed.calc_length() for ed in f.edges]
        if min(e)>1e-9: ar.append(max(e)/min(e))
    nq=sum(1 for f in bm.faces if len(f.verts)==4)
    vol=bm.calc_volume(signed=True); bm.free()
    ar=np.array(ar)
    print(f"[{tag}] 면 {len(me.polygons):,} (쿼드 {nq/max(len(me.polygons),1)*100:.0f}%) "
          f"부피 {vol*1e6:.0f}cm3  법선각 p50 {np.percentile(ang,50):.1f} p95 {np.percentile(ang,95):.1f} "
          f"p99.9 {np.percentile(ang,99.9):.1f}  종횡비 p50 {np.median(ar):.2f} p95 {np.percentile(ar,95):.2f}")
stats(o.data,"전")
t=time.time()
try:
    bpy.ops.object.quadriflow_remesh(target_faces=TGT, use_preserve_sharp=True,
                                     use_preserve_boundary=True, use_mesh_symmetry=True)
except Exception as e:
    print("quadriflow 실패:", str(e)[:120]); raise SystemExit
n1=len(o.data.polygons)
print(f"QuadriFlow {time.time()-t:.0f}s  {n0:,} -> {n1:,}면")
if n1==n0:
    print("!! 면 수 불변 = 조용히 실패한 것")
stats(o.data,"후")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED "+OUT)
