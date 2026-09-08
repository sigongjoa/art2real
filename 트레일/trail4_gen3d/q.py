import bpy,sys,os,numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    me=o.data
    mi=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get("material_index",mi)
    print(o.name,"재질",[m.name for m in me.materials],"면별분포",np.bincount(mi).tolist()[:6])
