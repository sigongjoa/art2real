# -*- coding: utf-8 -*-
"""퇴화면 제거 + 데시메이트 후 QuadriFlow.

    blender -b --python retopo2.py -- <src> <out> <데시면수> <목표쿼드>

메시는 다양체인데도 QuadriFlow 가 '법선 방향이 일관되지 않다'며 거부했다.
뒤집힘 의심 에지 1,870 개가 원인으로 보이고, 그건 대개 **면적 0 에 가까운 퇴화면**의
법선이 무작위라서다. dissolve_degenerate 로 걷고 규모도 줄여서 다시 건다.
"""
import math, os, sys, time
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,OUT=os.path.abspath(argv[0]),os.path.abspath(argv[1])
DEC=int(argv[2]) if len(argv)>2 else 150000
TGT=int(argv[3]) if len(argv)>3 else 60000
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)

def diag(tag):
    bm=bmesh.new(); bm.from_mesh(o.data)
    a=np.array([f.calc_area() for f in bm.faces])
    flip=sum(1 for e in bm.edges if len(e.link_faces)==2
             and e.link_faces[0].normal.dot(e.link_faces[1].normal)<-0.9)
    nq=sum(1 for f in bm.faces if len(f.verts)==4)
    bm.free()
    print(f"[{tag}] 면 {len(o.data.polygons):,} 쿼드 {nq/max(len(o.data.polygons),1)*100:.0f}% "
          f"면적 최소 {a.min()*1e9:.2f}e-9 p1 {np.percentile(a,1)*1e6:.3f}e-6 "
          f"뒤집힘의심 {flip:,}")
diag("원본")
if DEC < len(o.data.polygons):
    d=o.modifiers.new("d",'DECIMATE'); d.ratio=DEC/len(o.data.polygons)
    bpy.ops.object.modifier_apply(modifier="d")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.dissolve_degenerate(threshold=1e-5)
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.mesh.delete_loose()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
diag("정리 후")
t=time.time()
try:
    bpy.ops.object.quadriflow_remesh(target_faces=TGT, use_preserve_sharp=False,
                                     use_preserve_boundary=False, use_mesh_symmetry=False)
    print(f"QuadriFlow {time.time()-t:.0f}s")
except Exception as e:
    print("예외:", str(e)[:150])
diag("리메시 후")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED "+OUT)
