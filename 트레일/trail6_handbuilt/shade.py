# -*- coding: utf-8 -*-
"""**형태 탓인가 셰이딩 탓인가**를 가른다.

    blender -b --python shade.py -- out/pauldron_v3.blend

모델을 원화 crop 창과 **같은 정사영**으로 레이캐스트해 법선맵을 얻고,
광원 방향을 반구 전체로 훑으며 셀 2톤(n.l < t = 그늘)을 만든다.
원화의 그늘 마스크와 IoU 를 잰다.

    잘 맞는 방향이 있다  ->  형태는 쓸 만하고 셰이딩이 문제였다
    어느 방향도 안 맞다  ->  형태가 틀렸다 (그림자는 핑계)

기준선을 같이 잰다 — 아무 방향이나 골랐을 때의 중앙값, 그리고
"전부 그늘" / "전부 밝음" 의 IoU. 기준선 없는 지표는 지표가 아니다 (94번).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
SS = 2                     # 슈퍼샘플 배수
cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
wc = lambda c: -0.6 + c * 1.2 / (RES - 1)
wz = lambda r: 1.1 - r * 1.2 / (RES - 1)


def normalmap(path, x0, x1, y0, y1):
    """crop 창과 같은 창으로 정사영 레이캐스트. -y 방향(앞)에서 쏜다."""
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
    V, F = [], []
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        me = o.data
        b = len(V)
        V += [(o.matrix_world @ v.co)[:] for v in me.vertices]
        F += [[i + b for i in p.vertices] for p in me.polygons]
    bv = BVHTree.FromPolygons(V, F)
    H, W = (y1 - y0) * SS, (x1 - x0) * SS
    N = np.zeros((H, W, 3), np.float32)
    M = np.zeros((H, W), bool)
    ys = np.array(V)[:, 1]
    y_start = float(ys.min()) - 0.5
    for j in range(H):
        z = wz(y0 + j / SS)
        for i in range(W):
            x = wc(x0 + i / SS)
            hit = bv.ray_cast(Vector((x, y_start, z)), Vector((0, 1, 0)), 3.0)
            if hit[0] is None:
                continue
            N[j, i] = hit[1][:]
            M[j, i] = True
    # 원래 해상도로 되돌린다
    N = N.reshape(y1 - y0, SS, x1 - x0, SS, 3).mean((1, 3))
    Mf = M.reshape(y1 - y0, SS, x1 - x0, SS).mean((1, 3))
    n = np.linalg.norm(N, axis=2, keepdims=True)
    N = np.divide(N, n, out=np.zeros_like(N), where=n > 1e-6)
    return N, Mf > 0.5


def art_shade(x0, x1, y0, y1):
    """원화의 **그늘 마스크**. 재질별로 가장 밝은 톤을 바탕으로 잡고 그보다 어두우면 그늘."""
    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    C = raw[y0:y1, x0:x1, :3].astype(np.int16)
    S = (raw[..., 3] > 0)[y0:y1, x0:x1]
    V = C.max(2)
    ink = (V < 110) & S                       # 먹선은 그늘이 아니다. 빼고 센다
    body = S & ~ink
    lav = body & (C[..., 2] - C[..., 0] > 8)
    gold = body & (C[..., 0] - C[..., 2] > 20)
    sh = np.zeros_like(body)
    for m in (lav, gold):
        if m.sum() < 50:
            continue
        v = V[m]
        # 2톤 셀이라 밝기 히스토그램이 두 봉우리다. 오츠로 가른다
        h = np.histogram(v, bins=64, range=(0, 256))[0].astype(float)
        tot, cum, mu = h.sum(), np.cumsum(h), np.cumsum(h * (np.arange(64) * 4 + 2))
        best, bt = -1, 0
        for k in range(1, 63):
            w0, w1 = cum[k], tot - cum[k]
            if w0 < 1 or w1 < 1:
                continue
            var = w0 * w1 * (mu[k] / w0 - (mu[-1] - mu[k]) / w1) ** 2
            if var > best:
                best, bt = var, k * 4 + 2
        sh |= m & (V < bt)
    return sh, body, ink


def main():
    path = sys.argv[sys.argv.index("--") + 1]
    y0, y1 = int(rr(0.995)), int(rr(0.770))
    x0, x1 = int(cc(0.110)), int(cc(0.260))
    sh, body, ink = art_shade(x0, x1, y0, y1)
    N, M = normalmap(path, x0, x1, y0, y1)
    both = M & body & ~ink
    print("원화 몸통 %d 화소 (먹선 %d)   그늘 %d = %.1f%%"
          % (body.sum(), ink.sum(), sh.sum(), 100 * sh.sum() / body.sum()))
    print("모델이 덮은 화소 %d   겹치는 곳 %d (실루엣 IoU %.3f)"
          % (M.sum(), both.sum(), (M & body).sum() / max((M | body).sum(), 1)))
    frac = float((sh & both).sum()) / max(both.sum(), 1)     # 겹치는 곳의 그늘 비율

    tgt = sh[both]
    rows = []
    for el in range(-60, 90, 15):
        for az in range(0, 360, 15):
            l = np.array([math.cos(math.radians(el)) * math.cos(math.radians(az)),
                          -math.sin(math.radians(el)),           # -y 가 앞
                          math.cos(math.radians(el)) * math.sin(math.radians(az))])
            d = (N[both] @ l)
            t = np.quantile(d, frac)                            # 그늘 면적을 원화에 맞춘다
            p = d < t
            iou = (p & tgt).sum() / max((p | tgt).sum(), 1)
            rows.append((iou, az, el, float(t)))
    rows.sort(reverse=True)
    allv = np.array([r[0] for r in rows])
    print("\n광원 %d방향 훑기   IoU  최고 %.3f  중앙 %.3f  최저 %.3f"
          % (len(rows), allv.max(), np.median(allv), allv.min()))
    print("  기준선: 전부 그늘 %.3f   무작위(면적만 맞춤) 기대 %.3f"
          % (tgt.sum() / max(len(tgt), 1), frac * tgt.mean() / max(frac + tgt.mean() - frac * tgt.mean(), 1e-9)))
    for iou, az, el, t in rows[:5]:
        print("  IoU %.3f  방위 %3d도 고도 %+3d도  임계 %.3f" % (iou, az, el, t))
    json.dump({"best": rows[0][:3], "median": float(np.median(allv)),
               "frac": frac, "sil_iou": float((M & body).sum() / max((M | body).sum(), 1))},
              open(os.path.join(HERE, "out", "shade.json"), "w"))
    np.save(os.path.join(HERE, "out", "_N.npy"), N)
    np.save(os.path.join(HERE, "out", "_M.npy"), M)
    np.save(os.path.join(HERE, "out", "_artsh.npy"), sh)
    np.save(os.path.join(HERE, "out", "_body.npy"), body)


if __name__ == "__main__":
    main()
