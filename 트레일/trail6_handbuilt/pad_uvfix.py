# -*- coding: utf-8 -*-
"""**캡의 빈 UV 를 메운다.** 254면 중 121면(면적 54.5%)이 UV 면적 0이었다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python pad_uvfix.py

build.py 의 layout() 은 겉면에만 UV 를 냈다. 나머지는 루프가 한 점에 뭉쳐 있어
텍셀을 안 차지하고, 렌더가 아틀라스 배경(체커)을 읽어 검게 나왔다.

고치는 방법은 오늘 만든 것 그대로 — **판 라벨 경계를 이음선으로 박고 편다.**
뿔 넷은 UV 가 멀쩡하므로(UV면적 0인 면 0개) 건드리지 않는다.
"""
import bpy, bmesh, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pad_remap as PR                      # assign()/colour() 재사용
import tri_uv

OUT = os.path.join(HERE, "out")


def uvstat(me):
    nf = len(me.polygons)
    uv = np.empty(len(me.loops)*2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    ar = np.empty(nf); me.polygons.foreach_get("area", ar)
    a2 = np.array([0.5*abs(np.dot(uv[ls[i]:ls[i]+lt[i], 0], np.roll(uv[ls[i]:ls[i]+lt[i], 1], -1))
                           - np.dot(uv[ls[i]:ls[i]+lt[i], 1], np.roll(uv[ls[i]:ls[i]+lt[i], 0], -1)))
                   for i in range(nf)])
    tiny = a2 < 1e-7
    ok = (ar > 1e-12) & (a2 > 1e-14)
    s = np.sqrt(a2[ok]/ar[ok]); s /= np.median(s)
    dev = float(np.percentile(s, 95)/max(np.percentile(s, 5), 1e-9))
    return tiny.sum(), float(ar[tiny].sum()/ar.sum()*100), dev, float(a2.sum())


bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "pauldron.blend"))
cap = [o for o in bpy.context.scene.objects if o.name == "sh_pauldron_cap"][0]
me = cap.data
print("전   UV면적0 면 %d (면적 %.1f%%)  밀도편차 %.2f  UV면적합 %.3f" % uvstat(me))

lab, src = PR.assign(me, cap)
bpy.context.view_layer.objects.active = cap
for x in bpy.context.scene.objects:
    x.select_set(x is cap)

bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
for e in bm.edges:
    lf = e.link_faces
    e.seam = (len(lf) != 2) or (lab[lf[0].index] != lab[lf[1].index])
nseam = sum(1 for e in bm.edges if e.seam)
bm.to_mesh(me); bm.free()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
print("후   UV면적0 면 %d (면적 %.1f%%)  밀도편차 %.2f  UV면적합 %.3f  이음선 %d"
      % (uvstat(me) + (nseam,)))

# 캡만 다시 굽는다 (뿔은 원래 UV 를 그대로 쓰므로 pad_remap 을 다시 돌린다)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "pauldron_uvfix.blend"))
print("-> out/pauldron_uvfix.blend")
