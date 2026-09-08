# -*- coding: utf-8 -*-
"""왜곡 119 가 전체인지 몇 개인지. 섬별 왜곡과 총곡률의 관계."""
import math, os, sys
import bpy, bmesh, numpy as np
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
HERE=os.path.dirname(os.path.abspath(__file__))
TWO_PI=2*math.pi
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
nf=len(me.polygons)
K=np.load(os.path.join(HERE,"curv_K.npy"))
# K 는 1/면적 로 나눈 값이니 정점면적을 곱해 적분값으로 되돌린다
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
varea=np.zeros(len(me.vertices))
for f in bm.faces:
    a=f.calc_area()/len(f.loops)
    for l in f.loops: varea[l.vert.index]+=a
uvl=bm.loops.layers.uv.active; bm.faces.ensure_lookup_table()
isl=np.full(nf,-1); cur=0
for f in bm.faces:
    if isl[f.index]>=0: continue
    st=[f]; isl[f.index]=cur
    while st:
        c=st.pop()
        for l in c.loops:
            lr=l.link_loop_radial_next; g=lr.face
            if isl[g.index]>=0: continue
            if (l[uvl].uv-lr.link_loop_next[uvl].uv).length<1e-5 and \
               (l.link_loop_next[uvl].uv-lr[uvl].uv).length<1e-5:
                isl[g.index]=cur; st.append(g)
    cur+=1
vis=np.full(len(me.vertices),-1)
a3=[];a2=[]
for f in bm.faces:
    a3.append(f.calc_area())
    p=[l[uvl].uv for l in f.loops]
    a2.append(0.5*abs(sum(p[i].x*p[(i+1)%len(p)].y-p[i].y*p[(i+1)%len(p)].x for i in range(len(p)))))
    for l in f.loops:
        if vis[l.vert.index]<0: vis[l.vert.index]=isl[f.index]
bm.free()
a3=np.array(a3); a2=np.array(a2)
Kint=K*varea
rows=[]
for i in range(cur):
    m=isl==i
    if m.sum()<30: continue
    ok=(a3[m]>1e-12)&(a2[m]>1e-14)
    if ok.sum()<30: continue
    sc=np.sqrt(a2[m][ok]/a3[m][ok])
    d=float(np.percentile(sc,95)/max(np.percentile(sc,5),1e-12))
    rows.append((int(m.sum()), float(a3[m].sum()), float(np.abs(Kint[vis==i]).sum()), d))
R=np.array(rows)
face,ar,om,dist=R[:,0],R[:,1],R[:,2],R[:,3]
print(f"섬 {len(R)}개 (30면 이상)")
print(f"왜곡 분위: p50 {np.percentile(dist,50):.2f}  p75 {np.percentile(dist,75):.2f} "
      f"p90 {np.percentile(dist,90):.2f}  p99 {np.percentile(dist,99):.2f}  최대 {dist.max():.0f}")
for cap in (1.5,2,3,5,10):
    m=dist<=cap
    print(f"  왜곡<={cap:4.1f} 인 섬 {m.sum():3d}개 ({m.mean()*100:4.0f}%), "
          f"면적 {ar[m].sum()/ar.sum()*100:5.1f}%")
print(f"\n상관 corr(∫|K|, log왜곡) = {np.corrcoef(om,np.log(dist))[0,1]:+.3f}")
print(f"     corr(면적,  log왜곡) = {np.corrcoef(ar,np.log(dist))[0,1]:+.3f}")
bad=np.argsort(-dist)[:6]
print(f"{'면':>7s} {'면적':>8s} {'∫|K|':>8s} {'왜곡':>9s}  <- 최악 6개")
for b in bad: print(f"{int(face[b]):7,} {ar[b]:8.4f} {om[b]:8.2f} {dist[b]:9.1f}")
