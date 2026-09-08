# -*- coding: utf-8 -*-
"""비다양체 진단 + 정리 후 QuadriFlow 재시도.

    blender -b --python manifold.py -- out/depthfit.blend out/retopo.blend 60000
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

def diag(tag):
    bm=bmesh.new(); bm.from_mesh(o.data)
    e_bnd=sum(1 for e in bm.edges if len(e.link_faces)<2)
    e_multi=sum(1 for e in bm.edges if len(e.link_faces)>2)
    v_loose=sum(1 for v in bm.verts if not v.link_faces)
    # 법선 일관성: 인접 면이 서로 반대로 향하는 에지
    flip=0
    for e in bm.edges:
        if len(e.link_faces)==2:
            a,b=e.link_faces
            if a.normal.dot(b.normal)<-0.9: flip+=1
    bm.free()
    print(f"[{tag}] 면 {len(o.data.polygons):,}  경계에지 {e_bnd:,}  "
          f"3면이상에지 {e_multi:,}  뜬정점 {v_loose:,}  뒤집힘의심 {flip:,}")
diag("원본")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.mesh.delete_loose()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold(use_wire=True, use_boundary=True, use_multi_face=True,
                                 use_non_contiguous=True, use_verts=True)
bpy.ops.object.mode_set(mode='OBJECT')
sel=np.zeros(len(o.data.vertices),bool)
o.data.vertices.foreach_get("select",sel)
print(f"비다양체 정점 {int(sel.sum()):,}")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.fill_holes(sides=8)
bpy.ops.object.mode_set(mode='OBJECT')
diag("정리 후")
t=time.time()
try:
    bpy.ops.object.quadriflow_remesh(target_faces=TGT, use_preserve_sharp=True,
                                     use_preserve_boundary=False, use_mesh_symmetry=True)
    n=len(o.data.polygons)
    print(f"QuadriFlow {time.time()-t:.0f}s -> {n:,}면")
except Exception as e:
    print("quadriflow 예외:", str(e)[:150])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED "+OUT)
