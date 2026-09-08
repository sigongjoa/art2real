# -*- coding: utf-8 -*-
"""삼각형 품질이 UV 섬 수에 영향을 주는지. 같은 면 수, 정리 유무만 다르게.

    blender -b --python uv_quality.py -- out/depthfit.blend out/retopo.blend
"""
import math, os, sys
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
def islands(me):
    bm=bmesh.new(); bm.from_mesh(me); uvl=bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    seen,n=set(),0
    for f in bm.faces:
        if f.index in seen: continue
        n+=1; st=[f]; seen.add(f.index)
        while st:
            c=st.pop()
            for l in c.loops:
                lr=l.link_loop_radial_next; g=lr.face
                if g.index in seen: continue
                if (l[uvl].uv-lr.link_loop_next[uvl].uv).length<1e-5 and \
                   (l.link_loop_next[uvl].uv-lr[uvl].uv).length<1e-5:
                    seen.add(g.index); st.append(g)
    bm.free(); return n
def stretch(o):
    m=o.data; nf=len(m.polygons)
    uv=np.empty(len(m.loops)*2); m.uv_layers[0].data.foreach_get("uv",uv); uv=uv.reshape(-1,2)
    ls=np.empty(nf,np.int32); m.polygons.foreach_get("loop_start",ls)
    lt=np.empty(nf,np.int32); m.polygons.foreach_get("loop_total",lt)
    a3=np.empty(nf); m.polygons.foreach_get("area",a3)
    a2=np.array([0.5*abs(np.dot(uv[s:s+t,0],np.roll(uv[s:s+t,1],-1))-
                         np.dot(uv[s:s+t,1],np.roll(uv[s:s+t,0],-1))) for s,t in zip(ls,lt)])
    ok=(a3>1e-12)&(a2>1e-14); sc=np.sqrt(a2[ok]/a3[ok])
    return float(np.percentile(sc,95)/max(np.percentile(sc,5),1e-12)), float(a2.sum())
for tag,path,dec in (("정리 없이 데시 150k",argv[0],150000),("정리+데시 150k",argv[1],0)):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    if dec and dec<len(o.data.polygons):
        d=o.modifiers.new("d",'DECIMATE'); d.ratio=dec/len(o.data.polygons)
        bpy.ops.object.modifier_apply(modifier="d")
    bm=bmesh.new(); bm.from_mesh(o.data)
    ar=np.array([max(e.calc_length() for e in f.edges)/max(min(e.calc_length() for e in f.edges),1e-9)
                 for f in bm.faces]); bm.free()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    d_,f_=stretch(o)
    print(f"{tag:22s} 면 {len(o.data.polygons):,}  종횡비 p95 {np.percentile(ar,95):5.2f}  "
          f"섬 {islands(o.data):6,}  왜곡 {d_:5.2f}  UV채움 {f_:.3f}")
