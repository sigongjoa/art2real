import os, sys
import bpy, numpy as np
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
bpy.ops.wm.open_mainfile(filepath=SRC)
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    me=o.data
    print(f"{o.name}: 면 {len(me.polygons):,} 정점 {len(me.vertices):,} "
          f"UV레이어 {len(me.uv_layers)} {[l.name for l in me.uv_layers]} "
          f"재질 {[m.name for m in me.materials]}")
    a=me.attributes.get("part_id")
    if a:
        v=np.empty(len(me.polygons),np.int32); a.data.foreach_get("value",v)
        u,c=np.unique(v,return_counts=True)
        print(f"  part_id {len(u)}종, 면 중앙 {int(np.median(c)):,}, 최대 {int(c.max()):,}")
