# -*- coding: utf-8 -*-
"""**선으로 면을 다듬는다** — 먹선을 홈이 아니라 **판의 경계**로 쓴다 (2026-09-21).

    python 면다듬기.py [케이스=오메가몬]   -> out/면다듬기_<케이스>.png · out/결과물/<케이스>/면.ply

사용자(09-21): 「중요한 선 정보는 추출을 하는데 **선을 바탕으로 면을 니가 안 다듬었지**」 — 맞다.
`carve_ink` 는 선 자리를 0.006 만큼 파기만 한다. 선 **사이**는 그대로 타원이라 판이 다 부푼다.

여기서는 선을 **칸의 경계**로 쓴다:

    ① 앞 · 뒤 깊이맵   장에서 기둥마다 제일 앞 · 제일 뒤 칸을 읽는다            <- 잰 것
    ② 칸              먹선으로 갈린 연결성분 (앞 판 · 뒤 판 따로)              <- 원화가 준 것
    ③ 면 맞춤          칸마다 깊이에 **평면 하나**를 최소제곱으로 맞춘다          <- 잰 것
    ④ 안쪽으로만       `앞 = max(맞춘 면, 원래 앞)` · `뒤 = min(...)`.
                      **절대 hull 밖으로 안 나간다** -> 지어냄이 늘 수 없다

그러면 칸 안은 평평해지고 칸 경계에서 깊이가 **툭 끊긴다** — 그게 갑주의 판이다.

문턱을 **먼저 적는다** (대조군: 같은 격자의 지금 파이프라인):

    Q1  **지어냄이 안 는다** (구조상 그래야 한다 — 안쪽으로만 민다)
    Q2  못덮음 앞 · 뒤가 안 나빠진다 (앞 · 뒤 실루엣은 y 만 건드리므로 그대로여야 한다)
    Q3  **모서리몫이 오른다** — 이웃 면 사이 각 30° 이상인 넓이 몫
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
N = 256
칸최소 = 12                     # 격자 화소. 이보다 작은 칸은 면을 안 맞춘다 (원래 깊이를 쓴다)
얇음 = 5                        # 칸. 앞뒤 두께가 이보다 얇은 기둥은 면 맞춤에서 뺀다 (칼 · 가시 · 뿔)
버팀 = 2.0                      # 맞춤에서 이 표준편차 밖은 버리고 다시 맞춘다 (칼 · 가시가 면을 끈다)


def 면맞춤(y, sel):
    """칸 안 깊이에 평면 z = a·x + b·z + c 를 맞춘다 (이상점 한 번 버리고 다시)."""
    xs, zs = np.where(sel)
    v = y[sel].astype(float)
    A = np.stack([xs, zs, np.ones(len(xs))], 1)
    try:
        c = np.linalg.lstsq(A, v, rcond=None)[0]
        r = v - A @ c
        keep = np.abs(r) <= 버팀 * max(r.std(), 1e-6)
        if keep.sum() >= 6:
            c = np.linalg.lstsq(A[keep], v[keep], rcond=None)[0]
    except np.linalg.LinAlgError:
        return None
    return c


def 다듬기(g, 선N, 열):
    """선으로 갈린 칸마다 앞 · 뒤 깊이를 평면으로 바꾼다. **안쪽으로만** 민다."""
    occ = g > 0
    있 = occ.any(1)
    앞 = np.where(있, occ.argmax(1), 0)
    뒤 = np.where(있, N - 1 - occ[:, ::-1].argmax(1), 0)
    두께 = 뒤 - 앞
    칸, n = ndimage.label(있 & ~선N & 열)
    크기 = np.bincount(칸.ravel())
    앞2, 뒤2, 편 = 앞.astype(float), 뒤.astype(float), []
    for i in range(1, n + 1):
        if 크기[i] < 칸최소:
            continue
        sel = (칸 == i) & (두께 >= 얇음)                 # **얇은 기둥은 건드리지 않는다** — 칼끝 · 가시가 사라진다
        if sel.sum() < 칸최소:
            continue
        xs, zs = np.where(sel)
        A = np.stack([xs, zs, np.ones(len(xs))], 1)
        for src, dst, 안쪽 in ((앞, 앞2, np.maximum), (뒤, 뒤2, np.minimum)):
            c = 면맞춤(src, sel)
            if c is None:
                continue
            dst[sel] = 안쪽(A @ c, src[sel])          # **안쪽으로만** — hull 밖으로 못 나간다
            편.append(float(np.abs(A @ c - src[sel]).mean()))
    겹 = 앞2 > 뒤2 - 1
    앞2[겹], 뒤2[겹] = 앞[겹], 뒤[겹]                    # 뒤집힌 칸은 원래대로
    return 앞2, 뒤2, 있, int(n), float(np.mean(편) if 편 else 0)


def 장으로(앞2, 뒤2, 있, f):
    """앞 · 뒤 깊이맵 -> 연속 장 (칸 경계에서 y 가 툭 끊긴다)."""
    y = np.arange(N)[None, :, None]
    d = np.minimum(y - 앞2[:, None, :], 뒤2[:, None, :] - y) + 0.5
    # 빈 기둥을 -2 로 막으면 **가로 경계가 반 칸 안으로 밀린다**(마칭큐브가 채운 칸과 -2 사이를 보간한다 ·
    # 못덮음 5.51 -> 8.27 의 원인). 그렇다고 hull 장 f 로 채우면 타원이 깎아낸 데까지 되살아나 **지어냄이 는다**
    # (3,247 -> 5,877). 그래서 **지금 장 g 가 가로 경계를 맡는다** — 결과는 지금 것의 부분집합이다.
    d = np.where(있[:, None, :], d, 1e3).astype(np.float32)
    return np.minimum(d, f)


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "결과물", case)
    os.makedirs(d, exist_ok=True)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    g, (u, _, z) = H.field_default(masks, back_sign=bs, n=N)
    f, _ = H.field_hull(masks, back_sign=bs, n=N)

    # 먹선을 창에 앉혀 격자로 (앞 · 뒤 따로)
    선 = {}
    for v in ("front", "back"):
        s1 = H.ink_map(os.path.join(base, src[v]))
        _, w2 = H.to_win(H.declutter(raw[v]), s1.astype(np.float32))
        w2 = H._warp_one(w2, v, p) > 0.5
        if v == "back" and bs < 0:
            w2 = w2[:, ::-1]
        k = W.RES // N
        선[v] = w2.reshape(N, k, N, k).any((1, 3)).T[:, ::-1]        # (x, z) 격자 · z 는 위가 큰 값
    앞반 = np.zeros((N, N), bool)
    앞반[:] = True
    앞2, 뒤2, 있, 칸수, 편 = 다듬기(g, 선["front"] | 선["back"], 앞반)
    새 = 장으로(앞2, 뒤2, 있, g)          # 가로 경계는 지금 장이 맡는다 (부분집합 보장)

    V, Fc = H.mesh_from_field(새, (u, u, z))
    면메시 = trimesh.Trimesh(V, Fc, process=False)
    ps = 면메시.split(only_watertight=False)
    if len(ps) > 1:
        # **제일 큰 것만 남기면 안 된다** — 판마다 깊이가 끊겨 조각이 갈린다 (09-21 바퀴 2 와 같은 실수)
        큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
        print("  조각 %d -> 부스러기 %d 버림" % (len(ps), len(ps) - len(큰)), flush=True)
        면메시 = trimesh.util.concatenate(큰) if 큰 else 면메시
    if 면메시.volume < 0:
        면메시.invert()
    면메시.export(os.path.join(d, "면.ply"))
    V0, F0 = H.mesh_from_field(g, (u, u, z))
    통 = max(trimesh.Trimesh(V0, F0, process=False).split(only_watertight=False), key=lambda q: abs(q.volume))

    def 재다(m):
        V, F = np.asarray(m.vertices), np.asarray(m.faces)
        못, 지어 = {}, 0
        for v in W.VIEWS:
            s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
            a = masks[v].astype(bool)
            못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
            지어 += int((s & ~a).sum())
        ang = m.face_adjacency_angles
        w = m.area_faces[m.face_adjacency].mean(1)
        모 = float(w[ang >= np.radians(30)].sum()) / max(float(w.sum()), 1e-9)
        평 = float(w[ang < np.radians(5)].sum()) / max(float(w.sum()), 1e-9)
        return 못, 지어, 평, 모

    못1, 지어1, 평1, 모1 = 재다(통)
    못2, 지어2, 평2, 모2 = 재다(면메시)
    Q = {"Q1 지어냄 안 늚": bool(지어2 <= 지어1),
         "Q2 앞·뒤 못덮음 안 나빠짐": bool(못2["front"] <= 못1["front"] + 0.3 and 못2["back"] <= 못1["back"] + 0.3),
         "Q3 모서리몫 오름": bool(모2 > 모1)}
    print("  칸 %d 개 · 면 맞춤 평균 편차 %.2f 칸" % (칸수, 편))
    print("  지금  못덮음 %s · 지어냄 %d · 평탄 %.3f · 모서리 %.3f"
          % ([float(x) for x in 못1.values()], 지어1, 평1, 모1))
    print("  면판  못덮음 %s · 지어냄 %d · 평탄 %.3f · 모서리 %.3f"
          % ([float(x) for x in 못2.values()], 지어2, 평2, 모2))
    for k, v in Q.items():
        print("   %-24s %s" % (k, "통과" if v else "짐"))

    r1 = DM.창렌더(통, os.path.join(OUT, "면다듬기_지금_%s.png" % case))
    r2 = DM.창렌더(면메시, os.path.join(OUT, "면다듬기_면판_%s.png" % case))
    S = 620
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", (3 * (S + 8), S + 150), "white")
    for i, im in enumerate((원, Image.open(r1).convert("RGB").resize((S, S)),
                            Image.open(r2).convert("RGB").resize((S, S)))):
        sheet.paste(im, (i * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 21)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "선으로 면을 다듬었다 — 먹선을 홈이 아니라 **판의 경계**로 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), "칸 %d 개마다 깊이에 평면을 맞췄다 (평균 편차 %.2f 칸) · **안쪽으로만** 밀어 hull 밖으로 안 나간다"
            % (칸수, 편), (90, 92, 100), f본)
    dr.text((14, 82), "모서리몫 %.3f -> **%.3f**   평탄몫 %.3f -> %.3f   지어냄 %d -> %d"
            % (모1, 모2, 평1, 평2, 지어1, 지어2), (28, 110, 60), f본)
    dr.text((14, 110), "못덮음 앞·옆·뒤  %s -> %s"
            % ([float(x) for x in 못1.values()], [float(x) for x in 못2.values()]), (60, 64, 72), f작)
    for i, t in enumerate(("원화", "지금 (타원 단면)", "선으로 면을 다듬은 것")):
        dr.text((i * (S + 8) + 6, 116), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "면다듬기_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "격자": N, "칸": 칸수, "면 편차": round(편, 3),
               "지금": {"못덮음": 못1, "지어냄": 지어1, "평탄몫": round(평1, 4), "모서리몫": round(모1, 4)},
               "면판": {"못덮음": 못2, "지어냄": 지어2, "평탄몫": round(평2, 4), "모서리몫": round(모2, 4)},
               "판정": Q, "손잡이": {"칸최소": 칸최소, "버팀": 버팀, "출처": "guessed(눈으로)"}},
              open(os.path.join(OUT, "기록", "면다듬기_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")


