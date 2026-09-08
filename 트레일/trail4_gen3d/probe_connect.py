# -*- coding: utf-8 -*-
"""파츠가 3D 에서 실제로 이어져 있는지 센다.

UV 섬이 수백 개인 게 UV 문제가 아니라 **파츠 배정이 얼룩덜룩해서** 3D 에서부터
조각나 있는 것일 수 있다. 최근접 프록시 배정은 표면을 따라가지 않으니 그럴 만하다.
"""
import os, sys
import bpy, bmesh, numpy as np, json
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
nf=len(me.polygons)
lab=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",lab)
names=json.load(open(os.path.join(os.path.dirname(SRC),"..","named_parts.json")))
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
adj=[[] for _ in range(nf)]
for e in bm.edges:
    if len(e.link_faces)==2:
        a,b=e.link_faces[0].index,e.link_faces[1].index
        adj[a].append(b); adj[b].append(a)
bm.free()
print(f"{'파츠':20s} {'면':>8s} {'3D조각':>7s} {'최대조각':>8s} {'최대비':>6s}")
rows=[]
for pid in np.unique(lab):
    sel=np.nonzero(lab==pid)[0]
    if len(sel)<400: continue
    ks=set(sel.tolist()); seen=set(); comps=[]
    for f in sel:
        if f in seen: continue
        st=[f]; seen.add(f); n=0
        while st:
            c=st.pop(); n+=1
            for j in adj[c]:
                if j in ks and j not in seen:
                    seen.add(j); st.append(j)
        comps.append(n)
    comps.sort(reverse=True)
    nm=names[pid-1] if 0<pid<=len(names) else f"p{pid}"
    rows.append((nm,len(sel),len(comps),comps[0],comps[0]/len(sel)))
rows.sort(key=lambda r:-r[2])
for nm,f,k,mx,rt in rows[:14]:
    print(f"{nm:20s} {f:8,} {k:7,} {mx:8,} {rt*100:5.0f}%")
print(f"... 총 {len(rows)}파츠, 3D조각 합계 {sum(r[2] for r in rows):,}")
