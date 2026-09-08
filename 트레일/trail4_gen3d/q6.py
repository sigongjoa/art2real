import bpy,sys,os,numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
gen=[x for x in bpy.context.scene.objects if x.type=='MESH' and x.name.startswith(("atlas","geometry"))]
gen=gen[0] if gen else [x for x in bpy.context.scene.objects if x.type=='MESH'][0]
c=np.empty(len(gen.data.polygons)*3); gen.data.polygons.foreach_get("center",c); c=c.reshape(-1,3)
print(f"기준 메시: {gen.name}")
print(f"{'z':>6s} {'생성 머리 폭':>12s} {'생성 깊이':>10s}")
for z in (0.87,0.89,0.91,0.93,0.95):
    m=(np.abs(c[:,2]-z)<0.006)&(np.abs(c[:,0])<0.14)
    if m.sum()<20: continue
    print(f"{z:6.2f} {c[m,0].max()-c[m,0].min():12.3f} {c[m,1].max()-c[m,1].min():10.3f}")
print()
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not o.name.startswith("a_"): continue
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
    w=np.array([(o.matrix_world@__import__("mathutils").Vector(p))[:] for p in v[:400]])
    print(f"{o.name:16s} 폭 {w[:,0].max()-w[:,0].min():.3f} 깊이 {w[:,1].max()-w[:,1].min():.3f} "
          f"z[{w[:,2].min():.3f},{w[:,2].max():.3f}]")
