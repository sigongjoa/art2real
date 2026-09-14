# -*- coding: utf-8 -*-
"""**윤곽을 벡터로 두고 기둥을 정확히 교차한다** — 도형 11개에서 복셀 hull 과 맞댄다.

    python 정확hull.py     -> out/기록/정확hull_<날짜>.json · out/정확hull_그림.png

근거 `claudedocs/research_앨리어싱_20260913.md` 권고 1 · Rivers · Durand · Igarashi (SIGGRAPH 2010).
09-11 해상도 트랙이 적은 다음 수 「윤곽을 벡터로」다.

## 만드는 법

    판 알파 -> 부화소 윤곽 (skimage find_contours 0.5, 선형보간)
            -> shapely 다각형 (구멍은 짝홀로)
            -> 보는 방향으로 민 기둥 (trimesh extrude_polygon)
            -> 기둥 셋 교집합 (manifold3d)

**입력 알파는 덮인 비율이다** (`시트.coverage`, 4 배로 그려 줄임 = `시트.py --초정밀` 과 같은 것). 벤치 판 png 의 알파는
0/255 라 벡터로 따도 화소 계단이 남는다. 손그림 원화라면 선의 안티앨리어싱 회색값이 이 역할이다.

## 채점 — 격자 없이

hull 은 정답을 덮으므로 **비율 = vol(정답) / vol(hull)** (도형.py 해석값과 같은 뜻). 부피는 메시에서 바로.
**덮음 = vol(정답 ∩ hull) / vol(정답)** — 1 이어야 hull 이 상한이다.

    복셀 hull   지금 파이프라인의 이진 hull (판 png -> 256³ -> 마칭큐브) = 오라클.build 의 plain
    정확 hull   위

해석값은 매끈한 도형 기준이라 96 각 원기둥은 π/4 보다 0.0006 작다 — 그 몫이 바닥이다.

## 판정 — 돌리기 전에 적는다 (2026-09-13 밤)

    오차     해석값이 있는 8개 중 **과반에서** 정확 hull 의 |비율 − 해석값| 이 복셀 hull 보다 작다
    덮음     11개 모두 정확 hull 의 덮음 ≥ 0.999 (상한이 깨지면 안 된다)
    결       45도 꼭짓점 법선 명암 그림 — 「관찰」로만 적는다
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
os.chdir(HERE)
import win as W
import 오라클 as O
import 도형 as SH
import 시트 as ST

DEPTH = 2.4                                         # 기둥 길이 — 창 폭 1.2 의 두 배


def ring_polys(alpha):
    """덮인 비율 알파 -> 창 좌표 shapely 다각형 (구멍 짝홀)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from skimage import measure
    cs = measure.find_contours(np.pad(alpha, 1), 0.5)
    rings = []
    for c in cs:
        if len(c) < 4:
            continue
        r, q = c[:, 0] - 1, c[:, 1] - 1
        u = W.U0 + (q + 0.5) / W.RES * (W.U1 - W.U0)
        z = W.Z1 - (r + 0.5) / W.RES * (W.Z1 - W.Z0)
        p = Polygon(np.stack([u, z], 1)).buffer(0)
        if p.area > 1e-8:
            rings.append(p)
    rings.sort(key=lambda p: -p.area)
    region = None
    for p in rings:                                 # 짝홀 — 바깥 윤곽 안의 윤곽은 구멍
        region = p if region is None else region.symmetric_difference(p)
    return unary_union(region) if region is not None else None


def cylinder(poly, view):
    """창 좌표 (u, z) 다각형을 보는 방향으로 민 기둥. u 는 front +x · side +y · back −x."""
    parts = list(poly.geoms) if hasattr(poly, "geoms") else [poly]   # 실루엣이 떨어진 두 조각이면 (두기둥) 조각마다 민다
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, DEPTH) for p in parts])  # 지역 (x', y') = (u, z), z' 로
    h = DEPTH / 2
    M = {"front": [[1, 0, 0, 0], [0, 0, 1, -h], [0, 1, 0, 0], [0, 0, 0, 1]],
         "back": [[-1, 0, 0, 0], [0, 0, 1, -h], [0, 1, 0, 0], [0, 0, 0, 1]],
         "side": [[0, 0, 1, -h], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]}[view]
    m.apply_transform(np.array(M, float))
    if m.volume < 0:
        m.invert()
    return m


def exact_hull(truth):
    V, F = np.asarray(truth.vertices), np.asarray(truth.faces)
    cyl = []
    for v in W.VIEWS:
        alpha = ST.coverage(V, F, v, ss=4)
        poly = ring_polys(alpha)
        cyl.append(cylinder(poly, v))
    return trimesh.boolean.intersection(cyl, engine="manifold")


def cover(truth, hull_mesh):
    try:
        inter = trimesh.boolean.intersection([truth, hull_mesh], engine="manifold")
        return float(inter.volume / truth.volume)
    except Exception as e:                           # 정답이 여러 몸통을 이어 붙인 것이면 불리언이 실패할 수 있다
        print("    덮음 계산 실패 (%s)" % type(e).__name__)
        return None


def selfcheck():
    """상자는 hull 이 곧 정답이다 — 정확 hull 의 크기 · 비율이 칸보다 훨씬 작은 오차로 맞아야 한다."""
    m = SH._box(.6, .6, 1.)
    m.vertices = W.normalize(np.asarray(m.vertices, np.float64))
    h = exact_hull(m)
    px = (W.U1 - W.U0) / W.RES
    err = np.abs(h.bounds - m.bounds).max()
    ratio = m.volume / h.volume
    assert err < px, "상자: 정확 hull 경계가 정답과 %.4f 어긋난다 (화소 %.4f) — 좌표 규약" % (err, px)
    assert abs(ratio - 1) < 0.003, "상자: 비율 %.4f" % ratio
    print("  자가검사 통과 — 상자 경계 오차 %.5f (화소 %.5f) · 비율 %.5f" % (err, px, ratio))


def main():
    selfcheck()
    O.H.register_sheets()
    rows = []
    meshes = {}
    for name, _, ana, _ in SH.FORMS:
        case = "도형_" + name
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        t0 = time.time()
        plain, _, axes, _ = O.build(case, truth, 0.20, "파이프")
        vh = O.C.to_mesh(plain, axes)
        t1 = time.time()
        eh = exact_hull(truth)
        t2 = time.time()
        r = {"도형": name, "해석값": ana,
             "복셀": {"비율": float(truth.volume / vh.volume), "덮음": cover(truth, vh), "면": len(vh.faces), "초": t1 - t0},
             "정확": {"비율": float(truth.volume / eh.volume), "덮음": cover(truth, eh), "면": len(eh.faces), "초": t2 - t1,
                     "닫힘": bool(eh.is_watertight)}}
        rows.append(r)
        meshes[name] = (vh, eh)
        f = lambda x: "  -  " if x is None else "%.4f" % x
        print("  %-8s 해석 %s | 복셀 비율 %.4f 덮음 %s | 정확 비율 %.4f 덮음 %s 닫힘 %s · 면 %d · %.1f초" % (
            name, f(ana), r["복셀"]["비율"], f(r["복셀"]["덮음"]), r["정확"]["비율"], f(r["정확"]["덮음"]),
            r["정확"]["닫힘"], r["정확"]["면"], r["정확"]["초"]), flush=True)
    have = [r for r in rows if r["해석값"] is not None]
    better = sum(abs(r["정확"]["비율"] - r["해석값"]) < abs(r["복셀"]["비율"] - r["해석값"]) for r in have)
    covers = [r["정확"]["덮음"] for r in rows]
    ok_err = better > len(have) / 2
    ok_cov = all(c is not None and c >= 0.999 for c in covers)
    print("\n  오차  정확 hull 이 복셀보다 해석값에 가까운 도형 %d/%d · %s" % (better, len(have), "O" if ok_err else "X"))
    print("  덮음  정확 hull 최소 %s · %s" % (min((c for c in covers if c is not None), default=None),
                                          "O" if ok_cov else "X (계산 실패 포함)"))
    print("  판정  **%s**" % ("통과" if ok_err and ok_cov else "짐"))
    for r in have:
        print("    %-8s |오차| 복셀 %.4f · 정확 %.4f" % (r["도형"], abs(r["복셀"]["비율"] - r["해석값"]),
                                                   abs(r["정확"]["비율"] - r["해석값"])))
    os.makedirs(os.path.join(HERE, "out", "기록"), exist_ok=True)
    p = os.path.join(HERE, "out", "기록", "정확hull_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판정": {"오차": ok_err, "덮음": ok_cov}, "rows": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print("  기록 -> %s" % os.path.relpath(p, HERE))
    figure(meshes)


def figure(meshes, names=("원기둥", "원뿔", "구", "토러스세움", "치마")):
    from PIL import Image, ImageDraw
    from 계획 import _font
    import 앨리어싱 as AL
    S, G, LW, TOP = 300, 10, 120, 90
    im = Image.new("RGB", (LW + len(names) * (S + G), TOP + 2 * (S + 30)), "white")
    d = ImageDraw.Draw(im)
    f1, f2 = _font(24), _font(16)
    d.text((20, 14), "복셀 hull vs 정확 hull (벡터 윤곽 기둥 교차) — 45도 · 꼭짓점 법선 명암", fill=(20, 20, 20), font=f1)
    for j, n in enumerate(names):
        vh, eh = meshes[n]
        fr = AL.frame_of(vh, 45)
        d.text((LW + j * (S + G), TOP - 24), n, fill=(40, 40, 40), font=f2)
        for i, m in enumerate((vh, eh)):
            im.paste(Image.fromarray(AL.render(m, 45, fr, S)).convert("RGB"), (LW + j * (S + G), TOP + i * (S + 30)))
    for i, lab in enumerate(("복셀 hull", "정확 hull")):
        d.text((16, TOP + i * (S + 30) + S // 2), lab, fill=(20, 20, 20), font=f2)
    p = os.path.join(HERE, "out", "정확hull_그림.png")
    im.save(p)
    print("  -> %s" % os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
