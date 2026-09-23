# -*- coding: utf-8 -*-
"""부품별 3D 내보내기 — 원형사.py 가 만든 부품 라벨을 **부품마다 메시**로 굽고 한 GLB 에 담는다 (2026-09-23).

    python 부품내보내기.py [케이스]   -> out/원형사/<케이스>/부품.glb · 정답.glb

사용자(09-23): 「3d로 부품별로 볼 수가 없고, 회전해서 다른 시야에서 볼 수 없다」 — 단면으로 판정하던 것을 그만둔다.
"""
import os, sys, json
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
sys.path.insert(0, r"G:rt2real\원화3d\실험_20260923")
import 원형사 as WH

전고mm = 150.0


def 메시(mask, 축, 매끈=1.0):
    f = ndimage.gaussian_filter(mask.astype(np.float32), 매끈)
    if f.max() < 0.5: return None
    v, faces, _, _ = measure.marching_cubes(np.pad(f, 1), 0.5)
    v -= 1
    ux, uy, z = 축
    v = np.stack([np.interp(v[:, 0], np.arange(len(ux)), ux),
                  np.interp(v[:, 1], np.arange(len(uy)), uy),
                  np.interp(v[:, 2], np.arange(len(z)), z)], 1)
    m = trimesh.Trimesh(v, faces[:, ::-1], process=False)   # marching_cubes 는 법선이 뒤집혀 나온다
    m.fix_normals()
    return m


def main(c="mech_Mech_4UvIHxnoSR"):
    D = os.path.join(H.OUT, "원형사", c)
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    색, _ = BB.색라벨(c, raw, masks, p, bs, O)
    쌍 = (부위.astype(np.int64) * 1000 + 색.astype(np.int64)) * O
    부품 = np.zeros(O.shape, np.int32); 다음 = 0
    for v in np.unique(쌍):
        if v == 0: continue
        l, k = ndimage.label(쌍 == v, np.ones((3, 3, 3), bool))
        부품 = np.where(l > 0, l + 다음, 부품); 다음 += k
    크기 = np.bincount(부품.ravel()); 크기[0] = 0
    작 = np.where((크기 > 0) & (크기 < 0.002 * O.sum()))[0]
    if len(작):
        idx = ndimage.distance_transform_edt(np.isin(부품, 작) | ~O, return_distances=False, return_indices=True)
        부품 = np.where(np.isin(부품, 작), 부품[tuple(idx)], 부품)
    라벨들 = [int(l) for l in np.unique(부품) if l]
    mm = 전고mm / max(int(O.any(axis=(0, 1)).sum()), 1) / ((z[1] - z[0]))   # 세계단위 -> mm
    rng = np.random.default_rng(3)
    S = trimesh.Scene()
    메타 = []
    for i, l in enumerate(라벨들):
        m = 메시(부품 == l, (ux, uy, z))
        if m is None or len(m.faces) == 0: continue
        m.apply_scale(mm)
        if len(m.faces) > 6000:                              # 웹 뷰어용으로 줄인다
            m = m.simplify_quadric_decimation(face_count=6000)
        m.visual.face_colors = np.tile(np.append(rng.integers(70, 230, 3), 255), (len(m.faces), 1))
        이름 = "부품%02d" % (i + 1)
        S.add_geometry(m, node_name=이름, geom_name=이름)
        방향 = WH.빠짐방향(부품 == l)
        메타.append({"이름": 이름, "칸": int((부품 == l).sum()), "부피mm3": round(float(m.volume), 1),
                     "크기mm": [round(float(x), 1) for x in m.extents],
                     "빠짐": [n for n, ok in zip(["+x", "-x", "+y", "-y", "+z", "-z"], 방향) if ok]})
    S.export(os.path.join(D, "부품.glb"))
    # 정답 메시도 같은 자로
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    t = 메시(T, (ux, uy, z))
    t.apply_scale(mm)
    if len(t.faces) > 40000: t = t.simplify_quadric_decimation(face_count=40000)
    t.visual.face_colors = [120, 120, 120, 255]
    t.export(os.path.join(D, "정답.glb"))
    json.dump({"케이스": c, "mm배율": mm, "부품": 메타}, open(os.path.join(D, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("부품 %d · %s" % (len(메타), D))
    for x in 메타[:6]: print(" ", x)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mech_Mech_4UvIHxnoSR")
