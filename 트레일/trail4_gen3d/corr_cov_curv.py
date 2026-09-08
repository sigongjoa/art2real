# -*- coding: utf-8 -*-
"""미관측(가려짐)과 곡률이 실제로 연관되는지. 두 그림은 다른 걸 재지만
가려지는 곳은 대개 오목하니 상관이 있을 법하다."""
import math, os, sys
import bpy, bmesh, numpy as np
from mathutils import Vector
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
TWO_PI=2*math.pi
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o
d=o.modifiers.new("d",'DECIMATE'); d.ratio=0.12; bpy.ops.object.modifier_apply(modifier="d")
s=o.modifiers.new("s",'SMOOTH'); s.iterations=30; s.factor=0.7
bpy.ops.object.modifier_apply(modifier="s")
me=o.data; nf=len(me.polygons)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
nor=np.empty(nf*3); me.polygons.foreach_get("normal",nor); nor=nor.reshape(-1,3)
a3=np.empty(nf); me.polygons.foreach_get("area",a3)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
ang=np.zeros(len(me.vertices))
for f in bm.faces:
    vs=[l.vert for l in f.loops]; n=len(vs)
    for i,v in enumerate(vs):
        e1=vs[(i-1)%n].co-v.co; e2=vs[(i+1)%n].co-v.co
        if e1.length>1e-12 and e2.length>1e-12: ang[v.index]+=e1.angle(e2)
bnd=np.array([any(len(e.link_faces)<2 for e in v.link_edges) for v in bm.verts])
bm.free()
K=np.where(bnd, math.pi-ang, TWO_PI-ang)
fK=np.array([np.mean([K[v] for v in p.vertices]) for p in me.polygons])
seen=np.zeros(nf,bool)
for dv in ((0,1,0),(-1,0,0),(0,-1,0)):
    v=Vector(dv)
    for k in np.nonzero(nor@np.array(dv)<-0.05)[0]:
        c=Vector(cen[k]); hit,loc,_,_=o.ray_cast(c-v*4.0,v)
        if hit and (loc-c).length<=0.006: seen[k]=True
print(f"면 {nf:,}  가시 {seen.sum():,} / 미관측 {(~seen).sum():,}")
print(f"{'구분':10s} {'K 평균':>9s} {'K 중앙':>9s} {'K<0 비율':>9s} {'|K| 평균':>9s}")
for m,lab in ((seen,"가시"),(~seen,"미관측")):
    print(f"{lab:10s} {fK[m].mean():+9.4f} {np.median(fK[m]):+9.4f} "
          f"{(fK[m]<0).mean()*100:8.1f}% {np.abs(fK[m]).mean():9.4f}")
print(f"\n상관 corr(가려짐, K) = {np.corrcoef((~seen).astype(float), fK)[0,1]:+.3f}")
print(f"     corr(가려짐, |K|) = {np.corrcoef((~seen).astype(float), np.abs(fK))[0,1]:+.3f}")
