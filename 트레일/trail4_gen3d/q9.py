# -*- coding: utf-8 -*-
"""측면에서 다리가 두 기둥으로 보이는 정체. 파츠별로 y 범위를 본다."""
import os, sys, json
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
HERE=os.path.dirname(os.path.abspath(__file__))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
pid=np.empty(len(me.polygons),np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
c=np.empty(len(me.polygons)*3); me.polygons.foreach_get("center",c); c=c.reshape(-1,3)
m=(c[:,2]>0.18)&(c[:,2]<0.40)          # 정강이 높이
print(f"정강이 높이(z 0.18~0.40) 면 {int(m.sum()):,}")
u,n=np.unique(pid[m],return_counts=True)
print(f"{'파츠':18s} {'면':>7s} {'y 범위':>18s} {'x 범위':>18s}")
for i in np.argsort(-n)[:10]:
    s=(pid==u[i])&m
    nm=names[u[i]-1] if 0<u[i]<=len(names) else f"?{u[i]}"
    print(f"{nm:18s} {int(n[i]):7,} [{c[s,1].min():+.3f},{c[s,1].max():+.3f}] "
          f"[{c[s,0].min():+.3f},{c[s,0].max():+.3f}]")
# 측면(y) 히스토그램으로 기둥 세기
h,e=np.histogram(c[m,1],bins=48)
gap=[(e[i],e[i+1]) for i in range(48) if h[i]<n.sum()*0.002]
print("\ny 분포 (측면에서 본 가로) — 빈 구간:", [f"[{a:+.3f},{b:+.3f}]" for a,b in gap][:6])
print("y 범위 전체:", f"[{c[m,1].min():+.3f},{c[m,1].max():+.3f}]")
