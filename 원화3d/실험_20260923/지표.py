# -*- coding: utf-8 -*-
"""**자 여럿** — 부피 IoU 하나로 그림 같은 것을 판정하던 것을 그만둔다 (2026-09-23).

    python 지표.py            얼린 10 케이스 -> out/기록/지표_<때>.json

사용자(09-23): 「IoU 말고 다른 지표는 없는 거야? 이거는 그림에 가까운 건데 어떻게 IoU 만으로 한다는 거지?」 — 맞다.
부피 IoU 는 **복셀 겹침**만 본다. 그림처럼 보이나 · 새 각도에서 맞나 · 표면이 매끈한가는 못 본다.

    ① 부피 IoU            지금 쓰던 것 (복셀 겹침)
    ② 챔퍼 거리 mm        우리 겉면 ↔ **정답 원본 메시** 겉면의 최근접 거리(양방향 · 중앙 · 95%). 전고 150 mm 기준
    ③ 새 각도 실루엣 IoU  입력으로 쓴 앞 · 옆 · 뒤를 **뺀** 12 각도에서 본 그림자끼리의 IoU (그림으로 보이는 닮음)
    ④ 표면 각도           이웃 면 사이 각 중앙 · 90% (평평한 판은 작다 · 계단은 45°)
    ⑤ 부피 비             우리/정답
정답은 **복셀이 아니라 원본 메시**를 쓴다 — 09-23 에 확인한 대로 복셀 정답은 45° 계단이라 표면 판정에 못 쓴다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC

전고mm = 150.0
각도수 = 12


def 메시로(V, 축):
    """등위면을 뽑는다.

    **V 가 실수 장이면 장을 그대로 쓴다(0 등위면).** 예전에는 `g > 0` 으로 0/1 을 만들어 넘겼는데,
    그러면 연속값을 버리고 복셀 껍데기에서 면을 뽑는 셈이라 **격자 계단이 그대로 남는다**
    (09-24 사용자 지적으로 찾음: 거칠기 0.098, 격자를 384 로 키우면 0.146 으로 «더 나빠졌다»).
    장을 그대로 쓰면 0.053 이고 384 에서도 0.055 로 격자에 안 휘둘린다. 정답 메시가 0.082 다."""
    V = np.asarray(V)
    if V.dtype == bool or V.dtype == np.uint8:
        f = ndimage.gaussian_filter(np.pad(V, 2).astype(np.float32), 0.6)
        수준 = 0.5
    else:
        f = np.pad(V.astype(np.float32), 2, constant_values=float(V.min()))
        수준 = 0.0
    v, faces, _, _ = measure.marching_cubes(f, 수준)
    v -= 2
    ux, uy, z = 축
    v = np.stack([np.interp(v[:, 0], np.arange(len(ux)), ux),
                  np.interp(v[:, 1], np.arange(len(uy)), uy),
                  np.interp(v[:, 2], np.arange(len(z)), z)], 1)
    m = trimesh.Trimesh(v, faces[:, ::-1], process=False); m.fix_normals()
    return m


def 각(m, n=40000):
    a = m.copy(); a.merge_jvertices() if False else a.merge_vertices()
    ang = np.degrees(a.face_adjacency_angles)
    if len(ang) > n: ang = np.random.default_rng(0).choice(ang, n, replace=False)
    return float(np.median(ang)), float(np.percentile(ang, 90))


def 챔퍼(a, b, 배율, n=60000):
    """양방향 최근접 거리(mm). a · b 는 메시."""
    pa = a.sample(n) * 배율
    pb = b.sample(n) * 배율
    d1, _ = cKDTree(pb).query(pa)
    d2, _ = cKDTree(pa).query(pb)
    d = np.concatenate([d1, d2])
    return float(np.median(d)), float(np.percentile(d, 95))


def 그림자(m, R, 크기=256):
    """점을 뿌려 만든 그림자(실루엣) 마스크 — 우리와 정답에 같은 방법을 쓴다."""
    p = (m.sample(120000) - m.bounds.mean(0)) @ R.T
    q = p[:, [0, 2]]                                   # 보는 방향은 +y — 화면은 (x, z)
    s = 크기 * 0.42 / max(np.abs(q).max(), 1e-9)
    ij = np.rint(q * s + 크기 / 2).astype(int)
    ij = ij[(ij >= 0).all(1) & (ij < 크기).all(1)]
    M = np.zeros((크기, 크기), bool); M[ij[:, 0], ij[:, 1]] = True
    M = ndimage.binary_closing(M, np.ones((3, 3), bool), iterations=2)
    return ndimage.binary_fill_holes(M)


def 각도들():
    """입력 세 판(정면 · 옆 · 뒤)을 뺀 각도 — 비스듬한 것 위주."""
    out = []
    for yaw in (30, 60, 120, 150, 210, 240, 300, 330):
        out.append((yaw, 0))
    for yaw in (45, 135, 225, 315):
        out.append((yaw, 30))
    return out[:각도수]


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    우 = 메시로(O, (ux, uy, z))
    배율 = 전고mm / max(tm.extents[2], 1e-9)
    r = {"① 부피 IoU": round(PB.재기(O, T)["IoU"], 3), "⑤ 부피 비": round(float(O.sum() / max(T.sum(), 1)), 3)}
    중, p95 = 챔퍼(우, tm, 배율)
    r["② 챔퍼 mm"] = {"중앙": round(중, 2), "95%": round(p95, 2)}
    ious = []
    for yaw, pitch in 각도들():
        R = (trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1])[:3, :3]
             @ trimesh.transformations.rotation_matrix(np.radians(pitch), [1, 0, 0])[:3, :3])
        a, b = 그림자(우, R), 그림자(tm, R)
        ious.append((a & b).sum() / max((a | b).sum(), 1))
    r["③ 새 각도 실루엣 IoU"] = {"중앙": round(float(np.median(ious)), 3), "최저": round(float(np.min(ious)), 3)}
    au, at = 각(우), 각(tm)
    r["④ 표면 각도"] = {"우리 중앙": round(au[0], 2), "우리 90%": round(au[1], 1),
                    "정답 중앙": round(at[0], 2), "정답 90%": round(at[1], 1)}
    return r


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-28s IoU %.3f | 챔퍼 %4.1f/%5.1f mm | 새각도 %.3f(최저 %.3f) | 표면각 %4.1f°(정답 %4.1f°)  %.0f초"
              % (c[:28], r["① 부피 IoU"], r["② 챔퍼 mm"]["중앙"], r["② 챔퍼 mm"]["95%"],
                 r["③ 새 각도 실루엣 IoU"]["중앙"], r["③ 새 각도 실루엣 IoU"]["최저"],
                 r["④ 표면 각도"]["우리 중앙"], r["④ 표면 각도"]["정답 중앙"], time.time() - t0), flush=True)
    M = lambda f: round(float(np.median([f(기록[c]) for c in GC.케이스들])), 3)
    요약 = {"부피 IoU": M(lambda r: r["① 부피 IoU"]),
          "챔퍼 중앙 mm": M(lambda r: r["② 챔퍼 mm"]["중앙"]), "챔퍼 95% mm": M(lambda r: r["② 챔퍼 mm"]["95%"]),
          "새 각도 실루엣 IoU 중앙": M(lambda r: r["③ 새 각도 실루엣 IoU"]["중앙"]),
          "새 각도 최저": M(lambda r: r["③ 새 각도 실루엣 IoU"]["최저"]),
          "표면각 우리": M(lambda r: r["④ 표면 각도"]["우리 중앙"]), "표면각 정답": M(lambda r: r["④ 표면 각도"]["정답 중앙"]),
          "부피 비": M(lambda r: r["⑤ 부피 비"])}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "지표_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
