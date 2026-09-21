# -*- coding: utf-8 -*-
"""**선이 우둘투둘하다** — 홈을 거리장 V 골로 파고 메시를 잘게 나눈다 (2026-09-21).

    python 매끈먹선.py [케이스=오메가몬] [깊이=0.015]   -> out/매끈먹선_<케이스>.png

사용자(09-21): 「지금 보여? 이거는 지금 **선 자체가 우둘투둘한** 거?」 맞다. 까닭은 셋이고 전부 표본 문제다.

    ① 홈 모양    `carve_ink` 는 선 지도를 **가우시안 한 번 흐려** 쓴다. 벽이 들쭉날쭉하다
    ② 표본       `W.topix` 는 **정수 화소**로 읽는다. 정점이 1~2 화소짜리 선을 **맞히거나 놓친다**
    ③ 조밀도     마칭큐브 256 격자 + 한 번 쪼갬 = 정점 간격이 원화 **2 화소**.
                 선 폭과 같은 수준이라 골이 계단이 된다

고친 것:

    거리장 V 골   `1 - 거리/반폭` 에 smoothstep — **폭과 깊이가 어디서나 같다**
    겹선형 표본   `map_coordinates(order=1)` — 정수 반올림을 없앤다
    두 번 쪼갬    정점 간격을 선 폭의 절반 아래로
    부드러운 문   법선 게이트를 계단(> 0.35) 대신 smoothstep(0.2~0.5)

재는 것: **골 밝기의 흔들림** — 렌더에서 원화 선 자리의 밝기 표준편차. 골이 고르면 작다.
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
import 면다듬기 as FM
W = H.W
OUT = H.OUT
반폭 = 3.0                      # 화소(1024). 골의 반폭 — 원화 선이 보통 2~4 화소다
잘게 = 2                        # 쪼개는 횟수. 정점 간격을 선 폭 아래로
문0, 문1 = 0.20, 0.50           # 법선 게이트 smoothstep 구간


def 창선(raw, p, bs, case, v):
    """원화 먹선 -> 창 1024 bool."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    s1 = H.ink_map(os.path.join(base, src[v]))
    _, w2 = H.to_win(H.declutter(raw[v]), s1.astype(np.float32))
    return H._warp_one(w2, v, p) > 0.5


def V골(선):
    """거리장 V 골 — 폭과 깊이가 어디서나 같다 (마스크를 흐리는 것과 다르다)."""
    d = ndimage.distance_transform_edt(~선)
    w = np.clip(1.0 - d / 반폭, 0, 1)
    return (w * w * (3 - 2 * w)).astype(np.float32)               # smoothstep


def 겹표본(im, u, z):
    """월드 (u, z) 에서 **겹선형** 표본 — 정수 반올림을 없앤다."""
    col = (np.asarray(u, float) - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - np.asarray(z, float)) / (W.Z1 - W.Z0) * W.RES - 0.5
    return ndimage.map_coordinates(im, [row, col], order=1, mode="nearest")


def 새김(mesh, raw, p, bs, case, depth):
    m = mesh
    for _ in range(잘게):
        m = m.subdivide()
    V = np.asarray(m.vertices, float).copy()
    Nn = np.asarray(m.vertex_normals)
    for v, sign, 방향 in (("front", +1, -1), ("back", bs, +1)):
        골 = V골(창선(raw, p, bs, case, v))
        w = 겹표본(골, sign * V[:, 0], V[:, 2])
        t = np.clip((Nn[:, 1] * 방향 - 문0) / (문1 - 문0), 0, 1)
        문 = t * t * (3 - 2 * t)                                  # 계단이 아니라 smoothstep
        V[:, 1] -= 방향 * depth * w * 문
    return trimesh.Trimesh(V, np.asarray(m.faces), process=False), m


def 흔들림(rp, 원선):
    """렌더에서 원화 선 자리의 밝기 표준편차 — 골이 고르면 작다."""
    import cv2
    im = cv2.imdecode(np.fromfile(rp, np.uint8), cv2.IMREAD_UNCHANGED)
    g = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    lab, n = ndimage.label(원선)
    크 = np.bincount(lab.ravel())
    쓸 = [i for i in range(1, n + 1) if 크[i] >= 60]
    if not 쓸:
        return 0.0
    v = [float(g[lab == i].std()) for i in 쓸]
    return float(np.average(v, weights=[크[i] for i in 쓸]))


def main(case="오메가몬", depth=0.015):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "결과물", case)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    N = FM.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    선N = {}
    for v in ("front", "back"):
        w2 = 창선(raw, p, bs, case, v)
        if v == "back" and bs < 0:
            w2 = w2[:, ::-1]
        k = W.RES // N
        선N[v] = w2.reshape(N, k, N, k).any((1, 3)).T[:, ::-1]
    앞2, 뒤2, 있, 칸수, _ = FM.다듬기(g, 선N["front"] | 선N["back"], np.ones((N, N), bool))
    V0, F0 = H.mesh_from_field(FM.장으로(앞2, 뒤2, 있, g), ax)
    몸 = trimesh.Trimesh(V0, F0, process=False)
    ps = 몸.split(only_watertight=False)
    if len(ps) > 1:
        큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
        몸 = trimesh.util.concatenate(큰) if 큰 else 몸
    if 몸.volume < 0:
        몸.invert()

    원선 = 창선(raw, p, bs, case, "front") & ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    판본 = []
    지금 = H.carve_ink(몸, raw, p, bs, case, depth=depth)
    새, 잘 = 새김(몸, raw, p, bs, case, depth)
    for 이름, m in (("지금 (흐린 마스크 · 정수 표본 · 1 번 쪼갬)", 지금), ("매끈 (V 골 · 겹선형 · %d 번 쪼갬)" % 잘게, 새)):
        rp = DM.창렌더(m, os.path.join(OUT, "매끈먹선_%s_%s.png" % (case, "지금" if m is 지금 else "매끈")))
        e = m.edges_unique_length
        간격 = float(np.median(e)) / (W.U1 - W.U0) * W.RES          # 원화 화소 단위 정점 간격
        V2, F2 = np.asarray(m.vertices), np.asarray(m.faces)
        못, 지어 = {}, 0
        for v in W.VIEWS:
            s = np.asarray(W.silhouette(V2, F2, v, bs if v == "back" else None)).astype(bool)
            a = masks[v].astype(bool)
            못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
            지어 += int((s & ~a).sum())
        판본.append({"이름": 이름, "정점 간격(원화 화소)": round(간격, 2), "면": len(m.faces),
                     "골 밝기 흔들림": round(흔들림(rp, 원선), 1), "못덮음": 못, "지어냄": 지어, "png": rp})
        print("  %-38s 정점 간격 %.2f 화소 · 면 %7d · 골 흔들림 %.1f · 못덮음 %s · 지어냄 %d"
              % (이름, 간격, len(m.faces), 판본[-1]["골 밝기 흔들림"], [float(x) for x in 못.values()], 지어), flush=True)
    Q = {"Q1 골 흔들림이 준다": bool(판본[1]["골 밝기 흔들림"] < 판본[0]["골 밝기 흔들림"]),
         "Q2 지어냄 안 늚": bool(판본[1]["지어냄"] <= 판본[0]["지어냄"] * 1.02),
         "Q3 못덮음 +0.3%p 이내": bool(all(판본[1]["못덮음"][v] <= 판본[0]["못덮음"][v] + 0.3 for v in W.VIEWS))}
    for k, v in Q.items():
        print("   %-24s %s" % (k, "통과" if v else "짐"))

    # ---- 그림: 전체 + 가슴 확대
    S, C = 520, (300, 210, 720, 630)                               # 확대할 상자 (1024 기준)
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원im = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    행1 = [원im.resize((S, S))] + [Image.open(r["png"]).convert("RGB").resize((S, S)) for r in 판본]
    행2 = [원im.crop(C).resize((S, S))] + [Image.open(r["png"]).convert("RGB").crop(C).resize((S, S)) for r in 판본]
    sheet = Image.new("RGB", (3 * (S + 8), 2 * (S + 8) + 128), "white")
    for i, im in enumerate(행1):
        sheet.paste(im, (i * (S + 8), 120))
    for i, im in enumerate(행2):
        sheet.paste(im, (i * (S + 8), 120 + S + 8))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 29)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 18)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "선이 우둘투둘한 까닭 — 표본이 성겼다 · %s (홈 깊이 %.3f)" % (case, depth), (20, 22, 28), f제)
    dr.text((14, 50), "정점 간격 %.2f -> **%.2f 원화 화소** (선 폭 2~4 화소) · 골 밝기 흔들림 %.1f -> **%.1f**"
            % (판본[0]["정점 간격(원화 화소)"], 판본[1]["정점 간격(원화 화소)"],
               판본[0]["골 밝기 흔들림"], 판본[1]["골 밝기 흔들림"]), (28, 110, 60), f본)
    dr.text((14, 78), "고친 것 — 거리장 V 골(폭 · 깊이가 어디서나 같다) · 겹선형 표본(정수 반올림 제거) · %d 번 쪼갬 · 부드러운 법선 문"
            % 잘게, (90, 92, 100), f작)
    for i, t in enumerate(["원화"] + [r["이름"] for r in 판본]):
        dr.text((i * (S + 8) + 6, 100), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "매끈먹선_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "깊이": depth, "반폭": 반폭, "잘게": 잘게,
               "판본": [{k: v for k, v in r.items() if k != "png"} for r in 판본], "판정": Q},
              open(os.path.join(OUT, "기록", "매끈먹선_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    새.export(os.path.join(d, "매끈먹선.ply"))
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 0.015)
