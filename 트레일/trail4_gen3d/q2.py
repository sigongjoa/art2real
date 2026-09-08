import bpy,sys,os,json,numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
HERE=os.path.dirname(os.path.abspath(__file__))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
pid=np.empty(len(me.polygons),np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
cen=np.empty(len(me.polygons)*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
a3=np.empty(len(me.polygons)); me.polygons.foreach_get("area",a3)
m=(cen[:,2]>0.86)&(np.abs(cen[:,0])<0.13)     # 머리 돔 구간
print(f"머리 돔 구간 면 {int(m.sum()):,}")
u,c=np.unique(pid[m],return_counts=True)
for i in np.argsort(-c)[:8]:
    n=names[u[i]-1] if 0<u[i]<=len(names) else f"?{u[i]}"
    print(f"  {n:18s} {int(c[i]):>7,} ({c[i]/m.sum()*100:5.1f}%)")
