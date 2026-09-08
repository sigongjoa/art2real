# -*- coding: utf-8 -*-
"""측면 파랑(메시만)이 어느 파츠 탓인지. 렌더 대신 정점을 직접 투영한다.

    blender -b --python side_blame2.py -- out/nd_named2.blend out/blame.npz

Workbench �ertex-color 렌더는 안티에일리어싱 때문에 색이 정확히 안 나온다
(24비트 인덱스를 색으로 실었더니 디코딩이 다 깨졌다). 좌표를 그냥 내보낸다.
"""
import json, os, sys
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,OUT=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
ar=np.empty(nf); me.polygons.foreach_get("area",ar)
lv=np.empty(len(me.loops),np.int32); me.loops.foreach_get("vertex_index",lv)
ls=np.empty(nf,np.int32); me.polygons.foreach_get("loop_start",ls)
lt=np.empty(nf,np.int32); me.polygons.foreach_get("loop_total",lt)
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
# 면마다 정점 3개 (삼각형 가정, 아니면 처음 3개)
tri=np.array([[lv[ls[i]],lv[ls[i]+1],lv[ls[i]+2]] for i in range(nf)],np.int32)
np.savez(OUT, pid=pid, cen=cen, area=ar, tri=tri, co=co)
names=json.load(open(os.path.join(HERE,"named_parts.json")))
json.dump(names, open(OUT.replace(".npz","_names.json"),"w"))
print(f"내보냄 면 {nf:,} 정점 {len(co):,}")
