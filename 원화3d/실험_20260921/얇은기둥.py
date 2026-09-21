# -*- coding: utf-8 -*-
"""**얇은 기둥은 타원 말고 사각으로** — 뿔 · 칼끝이 깎이는 것을 막는다 (2026-09-21).

    python 얇은기둥.py [케이스=오메가몬] [문턱칸=5]   -> out/얇은기둥_<케이스>.png · out/기록/얇은기둥_*.json

09-21 `깎인곳.py` 가 찾았다 — 깎인 27% 는 **표면 껍질**이지만(깊은 곳 0.0%),
**높이별로 보면 z 0.94(뿔 · 볏)에서 retention 0.306** 이다. 가늘고 뾰족한 데를 타원이 먹는다.

까닭은 단순하다. 폭 `2a` · 깊이 `2b` 인 칸에서

    타원 단면 넓이 = π·a·b ≈ 0.785 × (사각 4ab)    <- 늘 21.5% 를 잃는다
    그런데 **a 나 b 가 한두 칸이면** 그 21.5% 가 «전부»가 된다 (남는 게 한 칸도 안 된다)

그래서 **얇은 기둥(min(2a, 2b) < 문턱 칸)에서는 사각 단면**을 쓴다. 가정을 바꾸는 게 아니라
**같은 직사각형 안에서 더 보수적인 쪽**(더 많이 남기는 쪽)을 고르는 것이다 — VH 밖으로는 여전히 못 나간다.

문턱을 **먼저 적는다** (대조군: 지금 파이프라인):

    Q1  **높이별 retention 최솟값 >= 0.5** (지금 0.306)
    Q2  **지어냄이 안 는다** (VH 로 덮개를 씌우니 구조상 그래야 한다)
    Q3  못덮음 앞 · 뒤가 +0.3%p 이내
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 닮음 as DM
W = H.W
OUT = H.OUT


def 장(masks, bs, n, 문턱칸):
    """`hull.field_ellipse` 와 같은 식인데 **얇은 기둥만 사각**으로."""
    u = W.U0 + (np.arange(n) + 0.5) / n * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(n) + 0.5) / n * (W.Z1 - W.Z0)
    rows = np.clip(((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES).astype(int), 0, W.RES - 1)
    F, S = masks["front"], masks["side"]
    B = masks["back"][:, ::-1] if bs < 0 else masks["back"]
    cell = (W.U1 - W.U0) / n
    g = np.full((n, n, n), -2.0, np.float32)
    사각칸 = 0
    for k, r in enumerate(rows):
        xr, yr = H._구간(F[r] & B[r]), H._구간(S[r])
        if not xr or not yr:
            continue
        X, A = H._축값(xr, u)
        Y, Bh = H._축값(yr, u)
        타원 = (1.0 - X[:, None] - Y[None, :]) * np.minimum(A[:, None], Bh[None, :]) / 2 / cell
        # 사각 단면 — |x-cx| <= a 이고 |y-cy| <= b. X = ((x-cx)/a)^2 이므로 sqrt(X) = |x-cx|/a
        사각 = np.minimum(A[:, None] * (1 - np.sqrt(X))[:, None],
                          Bh[None, :] * (1 - np.sqrt(Y))[None, :]) / cell
        얇 = (np.minimum(A[:, None], Bh[None, :]) * 2 / cell) < 문턱칸
        g[:, :, k] = np.where(얇, 사각, 타원)
        사각칸 += int(얇.sum())
    return g, (u, u, z), 사각칸


def 재다(m, masks, bs):
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    못, 지어 = {}, 0
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
        지어 += int((s & ~a).sum())
    return 못, 지어


def main(case="오메가몬", 문턱칸=5):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = 256
    f, ax = H.field_hull(masks, back_sign=bs, n=N)
    VH = f > 0
    지금, _ = H.field_default(masks, back_sign=bs, n=N)
    새, _, 사각칸 = 장(masks, bs, N, 문턱칸)
    # 지금 파이프라인과 같은 뒷단: 높이 스무딩 + VH 덮개
    새 = np.minimum(np.maximum(ndimage.gaussian_filter1d(새, H.SMOOTH_Z, axis=2), 새 - H.SMOOTH_GUARD), f)

    결과 = {}
    for 이름, gg in (("지금 (타원)", 지금), ("얇은 기둥 사각", 새)):
        M = gg > 0
        ret = float(M.sum()) / max(float(VH.sum()), 1)
        높이 = [float(M[:, :, k].sum()) / float(VH[:, :, k].sum())
                for k in range(N) if VH[:, :, k].sum() > 50]
        V, F2 = H.mesh_from_field(gg, ax)
        m = trimesh.Trimesh(V, F2, process=False)
        ps = m.split(only_watertight=False)
        if len(ps) > 1:
            큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
            m = trimesh.util.concatenate(큰) if 큰 else m
        못, 지어 = 재다(m, masks, bs)
        결과[이름] = {"retention": round(ret, 4), "높이 최소": round(min(높이), 3),
                     "못덮음": 못, "지어냄": 지어, "면": len(m.faces), "mesh": m}
        print("  %-14s retention %.4f · 높이 최소 %.3f · 못덮음 %s · 지어냄 %d"
              % (이름, ret, min(높이), [float(x) for x in 못.values()], 지어), flush=True)
    A, Bv = 결과["지금 (타원)"], 결과["얇은 기둥 사각"]
    Q = {"Q1 높이별 최소 retention >= 0.5": bool(Bv["높이 최소"] >= 0.5),
         "Q2 지어냄 안 늚": bool(Bv["지어냄"] <= A["지어냄"] * 1.02),
         "Q3 못덮음 앞·뒤 +0.3%p 이내": bool(Bv["못덮음"]["front"] <= A["못덮음"]["front"] + 0.3
                                        and Bv["못덮음"]["back"] <= A["못덮음"]["back"] + 0.3)}
    print("  사각으로 푼 칸 %d" % 사각칸, flush=True)
    for k, v in Q.items():
        print("   %-30s %s" % (k, "통과" if v else "**짐**"), flush=True)

    r1 = DM.창렌더(A["mesh"], os.path.join(OUT, "얇은기둥_지금_%s.png" % case))
    r2 = DM.창렌더(Bv["mesh"], os.path.join(OUT, "얇은기둥_사각_%s.png" % case))
    S = 470
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    박스 = (330, 80, 700, 450)                                        # 머리 · 어깨 (뿔이 있는 데)
    행1 = [원.resize((S, S))] + [Image.open(x).convert("RGB").resize((S, S)) for x in (r1, r2)]
    행2 = [원.crop(박스).resize((S, S))] + [Image.open(x).convert("RGB").crop(박스).resize((S, S)) for x in (r1, r2)]
    sheet = Image.new("RGB", (3 * (S + 8), 2 * (S + 8) + 150), "white")
    for i, im in enumerate(행1):
        sheet.paste(im, (i * (S + 8), 150))
    for i, im in enumerate(행2):
        sheet.paste(im, (i * (S + 8), 150 + S + 8))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "얇은 기둥은 타원 말고 사각 · %s (문턱 %d 칸)" % (case, 문턱칸), (20, 22, 28), f제)
    dr.text((14, 50), "retention %.4f -> %.4f · **높이별 최소 %.3f -> %.3f** · 지어냄 %d -> %d"
            % (A["retention"], Bv["retention"], A["높이 최소"], Bv["높이 최소"], A["지어냄"], Bv["지어냄"]),
            (28, 110, 60), f본)
    dr.text((14, 80), "못덮음 %s -> %s"
            % ([float(x) for x in A["못덮음"].values()], [float(x) for x in Bv["못덮음"].values()]), (60, 64, 72), f본)
    dr.text((14, 110), "아랫줄은 머리 · 어깨 확대 (뿔이 있는 데)", (90, 92, 100), f작)
    for i, t in enumerate(("원화", "지금 (타원)", "얇은 기둥 사각")):
        dr.text((i * (S + 8) + 6, 132), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "얇은기둥_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "문턱칸": 문턱칸, "사각 칸": 사각칸,
               "지금": {k: v for k, v in A.items() if k != "mesh"},
               "사각": {k: v for k, v in Bv.items() if k != "mesh"}, "판정": Q},
              open(os.path.join(OUT, "기록", "얇은기둥_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", int(a[2]) if len(a) > 2 else 5)
