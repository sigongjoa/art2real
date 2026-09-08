import os, sys, json
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
HERE=os.path.dirname(os.path.abspath(__file__))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
c=np.empty(nf*3); me.polygons.foreach_get("center",c); c=c.reshape(-1,3)
a=np.empty(nf); me.polygons.foreach_get("area",a)
m=c[:,2]>0.84
print(f"z>0.84 면 {int(m.sum()):,}")
print(f"{'파츠':20s} {'면':>7s} {'x 범위':>18s} {'y 범위':>18s} {'z 범위':>18s}")
u,n=np.unique(pid[m],return_counts=True)
for i in np.argsort(-n)[:10]:
    s=(pid==u[i])&m
    nm=names[u[i]-1] if 0<u[i]<=len(names) else f"?{u[i]}"
    cc=c[s]
    print(f"{nm:20s} {int(n[i]):7,} [{cc[:,0].min():+.3f},{cc[:,0].max():+.3f}] "
          f"[{cc[:,1].min():+.3f},{cc[:,1].max():+.3f}] [{cc[:,2].min():+.3f},{cc[:,2].max():+.3f}]")
# 측면에서 가장 뒤(+y)로 튀는 것
print("\n측면에서 뒤쪽(y>0.06) z>0.84:")
m2=m&(c[:,1]>0.06)
u,n=np.unique(pid[m2],return_counts=True)
for i in np.argsort(-n)[:6]:
    nm=names[u[i]-1] if 0<u[i]<=len(names) else f"?{u[i]}"
    s=(pid==u[i])&m2; cc=c[s]
    print(f"  {nm:18s} {int(n[i]):6,}  x[{cc[:,0].min():+.3f},{cc[:,0].max():+.3f}] "
          f"y[{cc[:,1].min():+.3f},{cc[:,1].max():+.3f}]")
