# -*- coding: utf-8 -*-
"""**리토폴로지 먼저, UV 는 그 다음.** 계단 메시를 그대로 펴는 길은 셋 다 졌다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python retopo_uv.py

어제 판은 거짓이었다. bpy 의 quadriflow_remesh 는 실패해도 {'FINISHED'} 를 돌려주고
경고 한 줄만 찍는다 — target 1500/4000/10000 세 판이 바이트까지 같았던 이유다.
그래서 여기선 **면 수가 실제로 변했는지**로 판정한다. 반환값은 안 믿는다.

측정한 한계(4.0, 헤드리스): 이 메시는 2,154면까지 리토폴로지되고 7,184면부터 무동작.
구는 65,024면도 되므로 면 수 자체가 아니라 이 형태다. 그래서 **먼저 데시메이트**한다.
어차피 목표가 저폴리 쿼드다 — 손으로 지은 견갑이 286면이고 여기 목표는 그 5배 안쪽.
"""
import bpy, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SRC = os.path.join(OUT, "tri_paint.blend")
PRE = [2000, 1000, 500]        # QuadriFlow 에 넣기 전 삼각형 예산. 위에서부터 시도
TARGETS = [800]                # 리토폴로지 목표 쿼드 수 (723 나온다. 600~800 이 이 형태의 자리)


def load():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.scene.objects:
        x.select_set(x is o)
    return o


def decimate(o, budget):
    m = o.modifiers.new("d", 'DECIMATE')
    m.ratio = min(budget / len(o.data.polygons), 1.0)
    bpy.ops.object.modifier_apply(modifier="d")
    return len(o.data.polygons)


def retopo(o, target):
    """면 수가 변해야 성공이다. 반환값은 실패해도 FINISHED 라 못 쓴다."""
    n0 = len(o.data.polygons)
    bpy.ops.object.quadriflow_remesh(mode='FACES', target_faces=target,
                                     use_preserve_sharp=True, use_preserve_boundary=True,
                                     smooth_normals=False, seed=0)
    return len(o.data.polygons) != n0


def measure(o, tag):
    """섬 수 · 텍셀 밀도 편차 · UV 면적합. 손으로 지은 것: 섬 5 · 채움 45.2%."""
    me = o.data
    nf = len(me.polygons)
    uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    ar3 = np.empty(nf); me.polygons.foreach_get("area", ar3)
    ar2 = np.zeros(nf)
    for i in range(nf):                                   # 부채꼴 삼각화로 UV 면적
        P = uv[ls[i]:ls[i] + lt[i]]
        ar2[i] = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], -1)) - np.dot(P[:, 1], np.roll(P[:, 0], -1)))
    ok = (ar3 > 1e-12) & (ar2 > 1e-14)
    s = np.sqrt(ar2[ok] / ar3[ok]); s /= np.median(s)
    dev = float(np.percentile(s, 95) / max(np.percentile(s, 5), 1e-9))

    # 섬 = UV 공간의 연결성분. 이음선으로 세면 smart_project 가 seam 을 안 찍어
    # 메시 연결성분(2)이 나온다 — render_seams.py 와 같은 자를 쓴다
    q = np.round(uv * 20000).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    par = np.arange(inv.max() + 1)
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for i in range(nf):
        r = find(inv[ls[i]])
        for k in range(1, lt[i]):
            t = find(inv[ls[i] + k])
            if r != t: par[t] = r
    nisl = len({find(inv[ls[i]]) for i in range(nf)})
    quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
    np.savez(os.path.join(OUT, "retopo_%s.npz" % tag), uv=uv, ls=ls, lt=lt)
    print("RETOPO %-8s 면 %6d (쿼드 %3.0f%%)  섬 %5d  밀도편차 %7.2f  UV면적합 %.3f"
          % (tag, nf, quads / max(nf, 1) * 100, nisl, dev, ar2.sum()))
    return nf, nisl, dev, float(ar2.sum())


rows = []
for t in TARGETS:
    o = load()
    n_src = len(o.data.polygons)
    tag, done, pre_n = "q%d" % t, False, n_src
    for budget in PRE:                      # QuadriFlow 가 받는 크기까지 내려간다
        o = load()
        pre_n = decimate(o, budget)
        if retopo(o, t):
            done = True
            break
    if not done:                            # 그래도 안 되면 복셀 리메시로 (쿼드는 나온다)
        o = load()
        o.data.remesh_voxel_size = max(o.dimensions) / 90.0
        bpy.ops.object.voxel_remesh()
        pre_n, tag = n_src, tag + "v"
        print("  QuadriFlow 무동작 -> 복셀 리메시 %d면" % len(o.data.polygons))

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    print("  %s: 원본 %d -> 데시메이트 %d -> 리토폴로지 %d"
          % (tag, n_src, pre_n, len(o.data.polygons)))
    rows.append((tag,) + measure(o, tag))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "retopo_%s.blend" % tag))

print("\n%-10s %8s %8s %10s %12s" % ("판", "면", "섬", "밀도편차", "UV면적합"))
for tag, nf, nisl, dev, s in rows:
    print("%-10s %8d %8d %10.2f %12.3f" % (tag, nf, nisl, dev, s))
assert len(set(r[1] for r in rows)) > 1, "세 판의 면 수가 같다 — 또 무동작이다"
print("\n손으로 지은 것: 286면 · 섬 5 · 채움 45.2%")
