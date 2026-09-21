# -*- coding: utf-8 -*-
"""**잔물결을 잡는다** — 평면은 살리고 자글거림만 죽인다 (2026-09-21).

    python 잔물결.py [케이스=오메가몬]   -> out/잔물결_<케이스>.png · out/결과물/<케이스>/잔물결.ply

사용자(09-21): 「그러면 **잔물결 일단 고쳐** 봐봐」

`다면체.py` 가 보였다 — 우리 표면은 모서리가 TripoSG 보다 **많은데**(0.118 vs 0.028)
평면 조각이 **0** 이다. 각진 게 아니라 **자글거리는** 것이다.

판본 셋을 같은 자로 잰다 (자는 `실험_20260918/면.py` 의 `roughness` · `dihedral` 을 그대로 쓴다):

    A 기준       면 다듬기 결과 그대로
    B 타우빈      라플라시안 λ/μ — **대조군.** 09-21 `매끈.py` 에서 디테일을 먹었다
    C 양방향 법선  이웃 법선을 **각이 비슷할 때만** 평균 낸다 (Fleishman/Jones 계열).
                 평면은 뭉개고 모서리는 남긴다 — 사전지식 없이, 우리 표면 통계만 쓴다

**순서가 중요하다** — 몸을 먼저 펴고 **그 위에 먹선을 새긴다** (09-21 `먹선.py` 에서 배운 것).

문턱을 **먼저 적는다**:

    Q1  C 의 거칠기가 A 의 **절반 아래**
    Q2  C 의 **선 재현**이 A 대비 −0.03 이내 (디테일을 안 먹는다)
    Q3  지어냄 안 늚 · 못덮음 +0.3%p 이내
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
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260918")
import hull as H
import 닮음 as DM
import 면다듬기 as FM
import 매끈먹선 as MI
import 면 as SURF
import 다면체 as POLY
W = H.W
OUT = H.OUT
깊이 = 0.015                     # 09-21 디테일 실험에서 맞바꿈이 제일 싼 값
반복 = 5                         # 양방향 법선 필터 횟수
각폭 = 0.35                      # 법선이 이만큼 다르면 남이다 (라디안 아님 · 법선 차 크기)
타우빈 = 10                      # 대조군 반복


def 타우빈펴기(m, it=타우빈, lam=0.5, mu=-0.53):
    L = trimesh.smoothing.laplacian_calculation(m, equal_weight=True)
    V = np.asarray(m.vertices, float).copy()
    for _ in range(it):
        V = V + lam * (L @ V - V)
        V = V + mu * (L @ V - V)
    return trimesh.Trimesh(V, np.asarray(m.faces), process=False)


def 양방향(m, it=반복, 각폭=각폭):
    """**양방향 법선 필터** — 이웃 법선을 거리 · 법선차로 가중해 평균 내고, 정점을 거기 맞춘다.
    평면은 평평해지고 모서리는 남는다 (라플라시안은 둘 다 뭉갠다)."""
    F = np.asarray(m.faces)
    V = np.asarray(m.vertices, float).copy()
    adj = m.face_adjacency
    쌍 = np.vstack([adj, adj[:, ::-1]])                           # 양방향
    for _ in range(it):
        mm = trimesh.Trimesh(V, F, process=False)
        fn, fc, fa = mm.face_normals, mm.triangles_center, mm.area_faces
        σc = float(np.sqrt(fa.mean()))                            # 거리 폭 = 면 한 변 정도
        d = np.linalg.norm(fc[쌍[:, 0]] - fc[쌍[:, 1]], axis=1)
        s = np.linalg.norm(fn[쌍[:, 0]] - fn[쌍[:, 1]], axis=1)
        w = fa[쌍[:, 1]] * np.exp(-(d / σc) ** 2 / 2) * np.exp(-(s / 각폭) ** 2 / 2)
        새 = np.zeros_like(fn)
        for k in range(3):
            np.add.at(새[:, k], 쌍[:, 0], w * fn[쌍[:, 1], k])
        새 += fn * fa[:, None]                                     # 자기 자신
        새 /= np.maximum(np.linalg.norm(새, axis=1, keepdims=True), 1e-12)
        # 정점 갱신 — 각 정점을 이웃 면의 (새 법선) 평면 쪽으로 민다
        dv = np.zeros_like(V)
        cnt = np.zeros(len(V))
        for k in range(3):
            idx = F[:, k]
            proj = (새 * (fc - V[idx])).sum(1)
            np.add.at(dv, idx, 새 * proj[:, None])
            np.add.at(cnt, idx, 1.0)
        V += dv / np.maximum(cnt, 1)[:, None]
    return trimesh.Trimesh(V, F, process=False)


def 덮개(원, 편, f, ax):
    """편 결과 중 **hull 밖으로 나간 정점만** 원래 자리로 되돌린다 — 지어냄 약속을 지킨다."""
    u, _, z = ax
    V = np.asarray(편.vertices, float).copy()
    V0 = np.asarray(원.vertices, float)
    ix = (V[:, 0] - u[0]) / (u[1] - u[0])
    iy = (V[:, 1] - u[0]) / (u[1] - u[0])
    iz = (V[:, 2] - z[0]) / (z[1] - z[0])
    val = ndimage.map_coordinates(f, [ix, iy, iz], order=1, mode="nearest")
    밖 = val < 0
    V[밖] = V0[밖]
    return trimesh.Trimesh(V, np.asarray(편.faces), process=False), int(밖.sum())


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
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
        w2 = MI.창선(raw, p, bs, case, v)
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
    print("  몸 면 %d · 칸 %d" % (len(몸.faces), 칸수), flush=True)

    원선 = MI.창선(raw, p, bs, case, "front") & ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    MI.잘게 = 1                                                    # 비교용 — 세 판본 모두 같은 조건
    fh, _ = H.field_hull(masks, back_sign=bs, n=N)                 # hull 상한 — 덮개용
    B, nB = 덮개(몸, 타우빈펴기(몸), fh, ax)
    C, nC = 덮개(몸, 양방향(몸), fh, ax)
    print("  hull 밖으로 나가 되돌린 정점  타우빈 %d · 양방향 %d (전체 %d)" % (nB, nC, len(몸.vertices)), flush=True)
    표 = []
    for 이름, 몸x in (("A 기준", 몸), ("B 타우빈 %d회 (대조군)" % 타우빈, B),
                      ("C 양방향 법선 %d회" % 반복, C)):
        거 = SURF.roughness(몸x)["거칠기"]                          # **몸에서** 잰다 (먹선 전)
        di = SURF.dihedral(몸x)
        m = MI.새김(몸x, raw, p, bs, case, 깊이)[0]                  # 몸을 편 뒤에 먹선을 새긴다
        rp = DM.창렌더(m, os.path.join(OUT, "잔물결_%s_%s.png" % (case, 이름[0])))
        rim = cv2.imdecode(np.fromfile(rp, np.uint8), cv2.IMREAD_UNCHANGED)
        회 = cv2.cvtColor(rim[:, :, :3], cv2.COLOR_BGR2GRAY)
        보임 = (cv2.Canny(cv2.GaussianBlur(회, (3, 3), 0), 20, 60) > 0) & 안
        재 = float((원선 & ndimage.binary_dilation(보임, iterations=3)).sum()) / max(원선.sum(), 1)
        V2, F2 = np.asarray(m.vertices), np.asarray(m.faces)
        못, 지어 = {}, 0
        for v in W.VIEWS:
            s = np.asarray(W.silhouette(V2, F2, v, bs if v == "back" else None)).astype(bool)
            a = masks[v].astype(bool)
            못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
            지어 += int((s & ~a).sum())
        평조 = POLY.재다(m)["평면 조각 몫"]
        표.append({"판본": 이름, "거칠기": 거, "평평": di["평평"], "계단": di["계단"],
                   "평면 조각 몫": 평조, "선 재현": round(재, 3), "못덮음": 못, "지어냄": 지어, "png": rp})
        print("  %-22s 거칠기 %.4f · 평평 %.3f · 계단 %.3f · 평면조각 %.3f · 선 재현 %.3f · 못덮음 %s · 지어냄 %d"
              % (이름, 거, di["평평"], di["계단"], 평조, 재, [float(x) for x in 못.values()], 지어), flush=True)
        if 이름.startswith("C"):
            m.export(os.path.join(d, "잔물결.ply"))

    A = 표[0]
    Q = {}
    for r in 표[1:]:
        Q[r["판본"]] = {"Q1 거칠기 절반 아래": bool(r["거칠기"] < 0.5 * A["거칠기"]),
                       "Q2 선 재현 -0.03 이내": bool(r["선 재현"] >= A["선 재현"] - 0.03),
                       "Q3 지어냄·못덮음 유지": bool(r["지어냄"] <= A["지어냄"] * 1.02
                                              and all(r["못덮음"][v] <= A["못덮음"][v] + 0.3 for v in W.VIEWS))}
        print("  %-22s %s" % (r["판본"], " · ".join("%s %s" % (k, "통과" if v else "짐")
                                                   for k, v in Q[r["판본"]].items())), flush=True)

    S, C박스 = 470, (300, 210, 720, 630)
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원im = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    sheet = Image.new("RGB", (4 * (S + 8), 2 * (S + 8) + 150), "white")
    행1 = [원im.resize((S, S))] + [Image.open(r["png"]).convert("RGB").resize((S, S)) for r in 표]
    행2 = [원im.crop(C박스).resize((S, S))] + [Image.open(r["png"]).convert("RGB").crop(C박스).resize((S, S)) for r in 표]
    for i, im in enumerate(행1):
        sheet.paste(im, (i * (S + 8), 140))
    for i, im in enumerate(행2):
        sheet.paste(im, (i * (S + 8), 140 + S + 8))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "잔물결 잡기 — 평면은 살리고 자글거림만 죽인다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "거칠기 %.4f -> %.4f (타우빈 %.4f) · 평면 조각 %.3f -> %.3f · 선 재현 %.3f -> %.3f"
            % (표[0]["거칠기"], 표[2]["거칠기"], 표[1]["거칠기"],
               표[0]["평면 조각 몫"], 표[2]["평면 조각 몫"], 표[0]["선 재현"], 표[2]["선 재현"]), (28, 110, 60), f본)
    dr.text((14, 78), "몸을 먼저 펴고 **그 위에 먹선을 새긴다** — 순서를 바꾸면 선이 먼저 뭉개진다 (09-21)",
            (90, 92, 100), f작)
    dr.text((14, 104), "아래 줄은 가슴 확대", (90, 92, 100), f작)
    for i, t in enumerate(["원화"] + [r["판본"] for r in 표]):
        dr.text((i * (S + 8) + 6, 122), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "잔물결_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "깊이": 깊이, "반복": 반복, "각폭": 각폭,
               "표": [{k: v for k, v in r.items() if k != "png"} for r in 표], "판정": Q},
              open(os.path.join(OUT, "기록", "잔물결_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")


