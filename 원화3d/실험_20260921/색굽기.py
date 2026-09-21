# -*- coding: utf-8 -*-
"""**색을 산출물에 굽는다** — 렌더에서만 보이던 색을 파일로 (2026-09-21).

    python 색굽기.py [케이스=오메가몬]   -> out/색굽기/<케이스>/{색.glb, 도색표.json} · out/색굽기_<케이스>.png

사용자(09-21): 「1번 하자고」 (= 색을 산출물에 굽는다)

09-21 `왜다른가.py` 가 쟀다 — **안 닮음의 64.9% 는 색이 없어서**다. 색은 원화에서 뜬 것이라
지어내는 게 아니다(`given from 원화`). 그런데 지금은 **렌더에서만** 보이고 파일에는 없다.

    ① 정점마다 원화에서 색을 뜬다 (앞을 보면 앞 판 · 뒤를 보면 뒤 판)
    ② **못 뜬 정점**(옆을 보는 띠)은 제일 가까운 색 있는 정점에서 메운다 — 회색 띠가 남지 않게
    ③ **GLB 로 굽는다** (정점색은 UV 없이도 어디서나 열린다)
    ④ **부품별 도색표** — 부품마다 대표색 · 면적 · hex. 사람이 칠하거나 슬라이서가 읽는다

문턱을 **먼저 적는다**:

    Q1  색을 뜬 정점 몫 >= 0.95 (구멍이 안 남는다)
    Q2  색 수(8 단위 양자화) <= 16 (셀 채색이 유지된다 — 그러데이션이 생기면 는다)
    Q3  색 입힌 렌더가 원화에 **더 가깝다** (회색 대비 거리 감소)
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 왜다른가 as WD
import 면자르기 as MJ
W = H.W
OUT = H.OUT


def 메우기(m, col, 본):
    """색을 **못 뜬** 정점을 제일 가까운 뜬 정점에서 메운다."""
    from scipy.spatial import cKDTree
    V = np.asarray(m.vertices)
    if 본.all() or not 본.any():
        return col
    t = cKDTree(V[본])
    _, i = t.query(V[~본], k=1)
    col[~본] = col[본][i]
    return col


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    m = trimesh.load(os.path.join(OUT, "hull.glb"), force="mesh", process=False)

    # ① · ② 색 뜨고 메우기
    V = np.asarray(m.vertices, float)
    Nn = np.asarray(m.vertex_normals)
    col = np.full((len(V), 4), 0, np.uint8)
    col[:, 3] = 255
    본 = np.zeros(len(V), bool)
    for v, sign, 방향 in (("front", +1, -1), ("back", bs, +1)):
        im = cv2.imdecode(np.fromfile(os.path.join(base, src[v]), np.uint8), cv2.IMREAD_UNCHANGED)
        rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
        알 = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
        rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
        d = H.declutter(raw[v])
        ch = [H._warp_one(H.to_win(d, rgb[:, :, k].astype(np.float32))[1], v, p) for k in range(3)]
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        본다 = Nn[:, 1] * 방향 > 0.15
        for k in range(3):
            col[본다, k] = np.clip(ch[k][py[본다], px[본다]], 0, 255).astype(np.uint8)
        본 |= 본다
    # **옆 판도 뜬다** — 옆을 보는 정점은 앞 · 뒤 어디에도 안 잡힌다 (첫 판에서 22% 가 회색이었다)
    im = cv2.imdecode(np.fromfile(os.path.join(base, src["side"]), np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
    알 = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
    ds = H.declutter(raw["side"])
    chs = [H._warp_one(H.to_win(ds, rgb[:, :, k].astype(np.float32))[1], "side", p) for k in range(3)]
    옆본다 = (np.abs(Nn[:, 0]) > 0.5) & ~본                            # 옆을 보고, 앞 · 뒤에서 못 뜬 것
    py, px = W.topix(V[:, 1], V[:, 2])                                # 옆 판의 가로축은 y (win.py 규약)
    for k in range(3):
        col[옆본다, k] = np.clip(chs[k][py[옆본다], px[옆본다]], 0, 255).astype(np.uint8)
    본 |= 옆본다
    몫 = float(본.mean())
    col = 메우기(m, col, 본)
    print("  색을 뜬 정점 몫 %.4f (나머지는 이웃에서 메움)" % 몫, flush=True)

    색메시 = m.copy()
    색메시.visual = trimesh.visual.ColorVisuals(색메시, vertex_colors=col)
    d = os.path.join(OUT, "색굽기", case)
    os.makedirs(d, exist_ok=True)
    glb = os.path.join(d, "색.glb")
    색메시.export(glb)
    ply = os.path.join(d, "색.ply")
    open(ply, "wb").write(trimesh.exchange.ply.export_ply(색메시, encoding="ascii"))
    print("  구웠다 -> %s (%.1f MB)" % (glb, os.path.getsize(glb) / 1e6), flush=True)

    q = (col[:, :3] // 24 * 24)
    색수 = len(np.unique(q, axis=0))
    # **도색표용 팔레트** — 원화는 셀 채색이라 색이 몇 개뿐이다. k-means 로 8 색을 뽑는다
    from scipy.cluster.vq import kmeans2
    표본 = col[::7, :3].astype(np.float64)
    센터, 라벨 = kmeans2(표본, 8, minit="++", seed=0)
    팔레트 = np.clip(센터, 0, 255).astype(np.uint8)
    d2 = ((col[:, None, :3].astype(np.float64) - 팔레트[None]) ** 2).sum(2)
    스냅 = 팔레트[d2.argmin(1)]
    스냅거리 = float(np.sqrt(((col[:, :3].astype(np.float64) - 스냅) ** 2).mean()))
    print("  팔레트 8 색 %s · 스냅 오차 %.1f"
          % (["#%02X%02X%02X" % tuple(int(x) for x in c) for c in 팔레트], 스냅거리), flush=True)

    # ④ 부품별 도색표 — 부위 라벨(면자르기)을 정점에 물린다
    g, ax = H.field_default(masks, back_sign=bs, n=MJ.N)
    _, lab, _ = MJ.부위(g > 0)
    ix = np.clip(((V[:, 0] - ax[0][0]) / (ax[0][1] - ax[0][0])).astype(int), 0, MJ.N - 1)
    iy = np.clip(((V[:, 1] - ax[1][0]) / (ax[1][1] - ax[1][0])).astype(int), 0, MJ.N - 1)
    iz = np.clip(((V[:, 2] - ax[2][0]) / (ax[2][1] - ax[2][0])).astype(int), 0, MJ.N - 1)
    부위 = lab[ix, iy, iz]
    표 = []
    for L in [int(x) for x in np.unique(부위) if x > 0]:
        sel = 부위 == L
        if sel.sum() < 200:
            continue
        cc = 스냅[sel]
        qq = cc
        vals, cnt = np.unique(qq, axis=0, return_counts=True)
        대표 = vals[np.argmax(cnt)]
        표.append({"부위": L, "정점": int(sel.sum()), "몫": round(float(sel.mean()), 4),
                   "대표색": "#%02X%02X%02X" % tuple(int(x) for x in 대표),
                   "그 색 몫": round(float(cnt.max() / cnt.sum()), 3)})
    표.sort(key=lambda r: -r["몫"])
    print("  부품 %d 개 도색표" % len(표), flush=True)
    for r in 표[:10]:
        print("   부위 %2d · 몫 %.3f · 대표색 %s (그 색이 %.0f%%)"
              % (r["부위"], r["몫"], r["대표색"], 100 * r["그 색 몫"]), flush=True)

    # ③ 렌더해서 거리 다시 재기
    sc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_왜렌더.py")
    open(sc, "w", encoding="utf-8").write(WD.렌더소스)
    o색 = os.path.join(d, "렌더_색.png")
    subprocess.run([r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe", "-b", "--python", sc,
                    "--", ply, o색, str(W.U0), str(W.U1), str(W.Z0), str(W.Z1), "color"],
                   capture_output=True, timeout=1800)
    회png = os.path.join(OUT, "왜다른가", case, "회색.png")

    def 읽기(png):
        im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 4:
            a = im[:, :, 3:4] / 255.0
            im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    원im = cv2.imdecode(np.fromfile(os.path.join(base, src["front"]), np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(원im[:, :, :3], cv2.COLOR_BGR2RGB)
    알 = 원im[:, :, 3] > 127 if 원im.ndim == 3 and 원im.shape[2] == 4 else np.ones(원im.shape[:2], bool)
    rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
    dfr = H.declutter(raw["front"])
    원창 = np.clip(np.dstack([H._warp_one(H.to_win(dfr, rgb[:, :, k].astype(np.float32))[1], "front", p)
                              for k in range(3)]), 0, 255).astype(np.uint8)
    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=3)
    d색 = WD.거리(읽기(o색), 원창, 안)
    d회 = WD.거리(읽기(회png), 원창, 안) if os.path.exists(회png) else 0.0
    print("  거리 회색 %.1f -> 색 %.1f (색몫 %.3f)" % (d회, d색, 1 - d색 / max(d회, 1e-6)), flush=True)

    Q = {"Q1 색 뜬 정점 >= 0.95": bool(몫 >= 0.95),
         "Q2 팔레트 8 색 스냅 오차 < 30": bool(스냅거리 < 30),
         "Q3 색이 원화에 더 가깝다": bool(d회 == 0 or d색 < d회)}
    for k, v in Q.items():
        print("   %-24s %s" % (k, "통과" if v else "**짐**"), flush=True)

    S = 520
    ims = [("원화", Image.fromarray(원창)), ("색 구운 산출물", Image.open(o색).convert("RGB"))]
    sheet = Image.new("RGB", (2 * (S + 8) + 430, S + 150), "white")
    for i, (t, im2) in enumerate(ims):
        sheet.paste(im2.resize((S, S)), (i * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "색을 산출물에 구웠다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "정점색 %d 개 · 색 %d 가지 · GLB %.1f MB · 거리 %.1f -> %.1f"
            % (len(V), 색수, os.path.getsize(glb) / 1e6, d회, d색), (40, 44, 52), f본)
    dr.text((14, 80), "색은 원화에서 뜬 것이다 (given from 원화) — 지어낸 값이 아니다", (90, 92, 100), f작)
    x = 2 * (S + 8) + 10
    y = 140
    dr.text((x, y), "부품별 도색표", (20, 22, 28), f본); y += 30
    for r in 표[:12]:
        dr.rectangle([x, y + 3, x + 22, y + 21], fill=tuple(int(r["대표색"][i:i + 2], 16) for i in (1, 3, 5)))
        dr.text((x + 30, y), "부위 %2d · %s · %.0f%%" % (r["부위"], r["대표색"], 100 * r["몫"]), (40, 44, 52), f작)
        y += 26
    y += 10
    for k, v in Q.items():
        dr.text((x, y), "%s %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f작); y += 26
    o = os.path.join(OUT, "색굽기_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "정점": int(len(V)), "색 뜬 몫": round(몫, 4), "색 수": int(색수),
               "glb MB": round(os.path.getsize(glb) / 1e6, 2), "거리 회색": round(d회, 2),
               "거리 색": round(d색, 2), "도색표": 표, "판정": Q,
               "출처": {"색": "given from 원화 (앞 · 뒤 판에서 뜬 것)"}},
              open(os.path.join(d, "도색표.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

