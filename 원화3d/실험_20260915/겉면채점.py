# -*- coding: utf-8 -*-
"""**속을 채운 정답으로 다시 잰다** (2026-09-15).

    python 겉면채점.py 검사
    python 겉면채점.py [케이스...]     기본 VRoid 11장 -> out/기록/겉면채점.json
    python 겉면채점.py 그림            옆 단면 -> out/겉면채점_단면.png
    python 겉면채점.py 뷰어 실험_20260915/치마속검수대_틀.html <출력.html>   3D 뷰어 (정답 · 속채움 · hull, gzip 메시 1.7 MB)

사람 판단 (09-15): 레진 굿즈 원형은 치마 속이 안 보여도 된다 — 차 있어도 팔린다.
그런데 정답 메시는 치마 속이 비어 있어 hull 이 채운 속을 **틀린 부피**로 센다.
그래서 정답을 **높이마다 닫힌 구멍을 채운 것**(치마 고리 속 · 소매 속)으로 바꿔 같은 판본을 다시 잰다.

    속채운정답   정답 복셀을 z 층마다 `binary_fill_holes` — 층 안에서 테두리로 둘러싸인 빈 곳만 찬다.
                다리 사이처럼 밖과 이어진 틈은 안 찬다
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import 오라클 as O
import 정답 as J
from 재질 import CASES

OUTJ = os.path.join(HERE, "out", "기록", "겉면채점.json")
SPEC = (("이진", 1.00, "타원", 0), ("타원1.00", 1.00, "타원", 1), ("오라클1.00", 1.00, "오라클", 1))


def fill_slices(T):
    """z 층(마지막 축)마다 닫힌 구멍을 채운다."""
    out = T.copy()
    for k in range(T.shape[2]):
        if T[:, :, k].any():
            out[:, :, k] = ndimage.binary_fill_holes(T[:, :, k])
    return out


def iou(A, B):
    return float((A & B).sum() / max((A | B).sum(), 1))


def run(cases):
    out = json.load(open(OUTJ, encoding="utf-8")) if os.path.exists(OUTJ) else {}
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        row = {}
        builds = {}
        for name, lam, which, pick in SPEC:
            if which not in builds:
                builds[which] = O.build(c, truth, lam, which)
            plain, deep, axes, _ = builds[which]
            G, og = J.grid(O.C.to_mesh(deep if pick else plain, axes))
            A, B = J.common(T, ot, G, og)
            F = fill_slices(A)
            row[name] = {"빈정답": round(iou(A, B), 4), "속채운정답": round(iou(F, B), 4)}
        row["속채움/정답 부피"] = round(float(F.sum() / A.sum()), 3)
        out[c] = row
        print("  %-24s 속채움 %.2f배 · " % (c[:24], row["속채움/정답 부피"]) +
              " · ".join("%s %.3f → %.3f" % (k, v["빈정답"], v["속채운정답"]) for k, v in row.items() if isinstance(v, dict)), flush=True)
        json.dump(out, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % OUTJ)


def figure(cases):
    """케이스마다 옆에서 본 가운데 단면 (x 가운데 층) — 회색 정답 · 파랑 속채움으로 더해진 곳 · 빨강 선 타원1.00 hull."""
    import cv2
    rows = []
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        plain, deep, axes, _ = O.build(c, truth, 1.00, "타원")
        G, og = J.grid(O.C.to_mesh(deep, axes))
        A, B = J.common(T, ot, G, og)
        F = fill_slices(A)
        tiles = []
        for x in (A.shape[0] // 2, int(A.shape[0] * 0.40)):       # 가운데 · 조금 옆 (다리 하나를 지나는 층)
            a, f, b = A[x].T[::-1], F[x].T[::-1], B[x].T[::-1]    # (y 깊이, z 위) -> 화면 (행=위, 열=깊이)
            im = np.full(a.shape + (3,), 255, np.uint8)
            im[f & ~a] = (235, 170, 90)                          # BGR 파랑 — 속채움
            im[a] = (150, 150, 150)
            edge = b & ~ndimage.binary_erosion(b)
            im[edge] = (30, 30, 220)
            tiles.append(cv2.resize(im, (im.shape[1] * 4, im.shape[0] * 4), interpolation=cv2.INTER_NEAREST))
        h = max(t.shape[0] for t in tiles)
        row = np.hstack([cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles])
        cv2.putText(row, c[:24], (8, 28), 0, 0.8, (0, 0, 0), 2)
        rows.append(row)
    w = max(r.shape[1] for r in rows)
    img = np.vstack([cv2.copyMakeBorder(r, 0, 12, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows])
    p = os.path.join(HERE, "out", "겉면채점_단면.png")
    cv2.imencode(".png", img)[1].tofile(p)
    print("  -> %s" % p)


def viewer(cases, template, dst):
    """3D 뷰어 데이터 — 케이스마다 정답 메시 · 속채움으로 더해진 복셀 면 · 타원1.00 hull 복셀 면.
    정점은 케이스 bbox 로 16비트 양자화 · 면은 32비트 · base64. `template` 의 `/*DATA*/null` 을 바꿔 `dst` 에 쓴다."""
    import base64
    import gzip
    from skimage import measure
    enc = lambda a: base64.b64encode(gzip.compress(a.tobytes(), 9)).decode()     # 뷰어가 DecompressionStream 으로 푼다
    scores = json.load(open(OUTJ, encoding="utf-8"))
    res = {}
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        _, deep, axes, _ = O.build(c, truth, 1.00, "타원")
        G, og = J.grid(O.C.to_mesh(deep, axes))
        A, B = J.common(T, ot, G, og)
        lo = np.minimum(ot, og)
        F = fill_slices(A)

        def surf(vol):
            v, f, _, _ = measure.marching_cubes(np.pad(vol, 1).astype(np.uint8), 0.5)
            return (v - 1 + lo) * J.PITCH, f

        welded = trimesh.Trimesh(truth.vertices, truth.faces, process=False)
        welded.merge_vertices()                                              # 재질마다 끊긴 같은 자리 정점을 잇는다
        meshes = {"정답": (np.asarray(welded.vertices), np.asarray(welded.faces)), "속채움": surf(F & ~A), "hull": surf(B)}
        allv = np.vstack([v for v, _ in meshes.values()])
        mn, sc = allv.min(0), float((allv.max(0) - allv.min(0)).max())
        res[c] = {"min": mn.tolist(), "scale": sc, "점수": scores[c],
                  "meshes": {k: {"v": enc(np.round((v - mn) / sc * 65535).astype("<u2")), "f": enc(f.astype("<u4"))}
                             for k, (v, f) in meshes.items()}}
        print("  %-24s 면 %s" % (c[:24], {k: len(f) for k, (_, f) in meshes.items()}), flush=True)
    html = open(template, encoding="utf-8").read()
    assert "/*DATA*/null" in html, "틀에 자리표시가 없다"
    open(dst, "w", encoding="utf-8").write(html.replace("/*DATA*/null", json.dumps(res, ensure_ascii=False)))
    print("  -> %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1e6))


def selfcheck():
    # 속 빈 원통(치마) 은 차고, 떨어진 두 기둥(다리) 사이는 안 찬다
    T = np.zeros((20, 20, 6), bool)
    yy, xx = np.mgrid[:20, :20]
    r = np.hypot(yy - 10, xx - 10)
    T[:, :, :3] = ((r >= 6) & (r < 8))[:, :, None]
    T[4:7, 4:7, 3:] = T[13:16, 13:16, 3:] = True
    F = fill_slices(T)
    assert F[10, 10, 0] and not F[10, 10, 4] and F[:, :, 3:].sum() == T[:, :, 3:].sum(), "층 채움이 틀렸다"
    print("  자가검사 통과 — 치마 고리는 차고 다리 사이는 안 찬다")


if __name__ == "__main__":
    a = sys.argv[1:]
    selfcheck()
    if a[:1] == ["뷰어"]:                                 # 뷰어 <틀.html> <출력.html>
        viewer(["avatarsample_d_darkness", "avatarsample_g", "sakurada_fumiriya"], a[1], a[2])
    elif a[:1] == ["그림"]:
        figure(a[1:] or ["avatarsample_d_darkness", "avatarsample_g", "sakurada_fumiriya"])
    elif a[:1] != ["검사"]:
        run(a or CASES)
