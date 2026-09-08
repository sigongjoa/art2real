# -*- coding: utf-8 -*-
"""파츠별 0~1 UV 를 **하나의 아틀라스**로 다시 싼다. 텍셀 밀도를 3D 면적에 비례시킨다.

    blender -b --python repack_atlas.py -- out/uv3.blend out/atlas.blend

측정된 문제: 파츠마다 제 0~1 공간을 쓰니 뿔 하나와 캐논팔이 같은 넓이를 받는다.
텍셀 크기가 파츠 사이에서 0.03mm ~ 1.09mm, **32.9배** 벌어졌다.
파츠 안 왜곡(<=2.0배)은 가우스 곡률 때문에 못 없애지만 이건 배분 선택일 뿐이다.

average_islands_scale 이 섬 크기를 3D 면적에 맞추고, pack_islands 가 다시 싼다.
"""
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
ATLAS, FIG_MM = 2048, 2000.0


def stats(objs, tag):
    md, fill = [], 0.0
    for o in objs:
        m = o.data
        n = len(m.polygons)
        uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
        uv = uv.reshape(-1, 2)
        ls = np.empty(n, np.int32); m.polygons.foreach_get("loop_start", ls)
        lt = np.empty(n, np.int32); m.polygons.foreach_get("loop_total", lt)
        a3 = np.empty(n); m.polygons.foreach_get("area", a3)
        a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                                 np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                       for s, t in zip(ls, lt)])
        ok = (a3 > 1e-12) & (a2 > 1e-14)
        md.append(np.sqrt(a3[ok] / a2[ok]) / ATLAS * FIG_MM)
        fill += a2.sum()
    allmm = np.concatenate(md)
    permd = np.array([np.median(x) for x in md])
    print(f"[{tag}] 텍셀 {np.median(allmm):.3f}mm  파츠간 {permd.min():.3f}~{permd.max():.3f}mm "
          f"({permd.max()/permd.min():.1f}배)  전체 p5~p95 {np.percentile(allmm,5):.3f}~"
          f"{np.percentile(allmm,95):.3f}  UV채움 {fill:.2f}")


bpy.ops.wm.open_mainfile(filepath=SRC)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.uv_layers]
stats(objs, "전")

# 한 오브젝트로 합쳐 하나의 UV 공간에서 재배치
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
big = bpy.context.view_layer.objects.active
big.name = "atlas"
print(f"합침: 면 {len(big.data.polygons):,}  재질 {len(big.data.materials)}")

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.average_islands_scale()          # 텍셀 밀도를 3D 면적에 맞춘다
bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')
stats([big], "후")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
