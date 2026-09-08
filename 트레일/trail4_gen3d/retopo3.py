# -*- coding: utf-8 -*-
"""가장 큰 셸만 남기고 QuadriFlow. 안 되면 Voxel Remesh 로 대체.

    blender -b --python retopo3.py -- <src> <out> <데시> <목표>
"""
import os, sys, time
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,OUT=os.path.abspath(argv[0]),os.path.abspath(argv[1])
DEC=int(argv[2]); TGT=int(argv[3])
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
if DEC<len(o.data.polygons):
    d=o.modifiers.new("d",'DECIMATE'); d.ratio=DEC/len(o.data.polygons)
    bpy.ops.object.modifier_apply(modifier="d")
# 셸 분리 -> 최대만
bpy.ops.mesh.separate(type='LOOSE') if False else None
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen=set(); comps=[]
for v in bm.verts:
    if v.index in seen: continue
    st=[v]; seen.add(v.index); c=[]
    while st:
        x=st.pop(); c.append(x.index)
        for e in x.link_edges:
            y=e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
print(f"셸 {len(comps)}개 상위 {[len(c) for c in comps[:6]]}")
if len(comps)>1:
    keep=set(comps[0])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(o.data)
bm.free()
print(f"최대 셸만: 면 {len(o.data.polygons):,}")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.dissolve_degenerate(threshold=1e-5)
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
ok=False
t=time.time()
try:
    bpy.ops.object.quadriflow_remesh(target_faces=TGT, use_preserve_sharp=False,
                                     use_preserve_boundary=False, use_mesh_symmetry=False)
    ok=len(o.data.polygons)!=DEC
    print(f"QuadriFlow {time.time()-t:.0f}s -> 면 {len(o.data.polygons):,} "
          f"{'성공' if ok else '조용히 실패'}")
except Exception as e:
    print("예외:", str(e)[:140])
if not ok:
    print("-> Voxel Remesh 로 대체")
    t=time.time()
    r=o.modifiers.new("r",'REMESH'); r.mode='VOXEL'
    r.voxel_size=0.006; r.adaptivity=0.0
    bpy.ops.object.modifier_apply(modifier="r")
    print(f"Voxel {time.time()-t:.0f}s -> 면 {len(o.data.polygons):,}")
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active=o
    t=time.time()
    try:
        n0=len(o.data.polygons)
        bpy.ops.object.quadriflow_remesh(target_faces=TGT, use_preserve_sharp=False,
                                         use_preserve_boundary=False, use_mesh_symmetry=False)
        print(f"QuadriFlow(voxel 후) {time.time()-t:.0f}s -> 면 {len(o.data.polygons):,} "
              f"{'성공' if len(o.data.polygons)!=n0 else '조용히 실패'}")
    except Exception as e:
        print("예외2:", str(e)[:140])
bm=bmesh.new(); bm.from_mesh(o.data)
nq=sum(1 for f in bm.faces if len(f.verts)==4); vol=bm.calc_volume(signed=True); bm.free()
print(f"최종 면 {len(o.data.polygons):,} 쿼드 {nq/max(len(o.data.polygons),1)*100:.0f}% "
      f"부피 {vol*1e6:.0f}cm3")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED "+OUT)
