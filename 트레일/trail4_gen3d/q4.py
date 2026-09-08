import bpy,sys,os,numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
c=np.empty(len(me.polygons)*3); me.polygons.foreach_get("center",c); c=c.reshape(-1,3)
a=np.empty(len(me.polygons)); me.polygons.foreach_get("area",a)
print(f"{'구간':16s} {'면':>8s} {'y 중심(면적가중)':>16s} {'y 범위':>20s}")
for z0,z1,nm in ((0.88,1.00,"머리"),(0.84,0.88,"목"),(0.68,0.84,"가슴"),
                 (0.50,0.68,"허리·골반"),(0.15,0.40,"정강이")):
    m=(c[:,2]>=z0)&(c[:,2]<z1)&(np.abs(c[:,0])<0.13)
    if not m.sum(): continue
    y=c[m,1]; w=a[m]
    print(f"{nm:16s} {int(m.sum()):8,} {np.average(y,weights=w):+16.4f} "
          f"[{y.min():+.3f},{y.max():+.3f}]")
