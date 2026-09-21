# -*- coding: utf-8 -*-
"""**홈의 반지름을 일정하게** — 선의 연결 정보(뼈대)에서 판다 (2026-09-21).

    python 홈반지름.py [케이스=오메가몬] [깊이=0.015]   -> out/홈반지름_<케이스>.png

사용자(09-21): 「홈 같은 녀석들 **이어진 연결 정보**를 바탕으로 **반지름이 일정하게** 할 수 없어?」

지금 골은 **선 마스크의 거리장**으로 판다. 그러면 골 폭이 **원화가 그은 붓 굵기를 그대로 따라간다** —
굵게 그은 데는 넓고 얕은 골, 가늘게 그은 데는 좁은 골, 선이 만나는 자리는 뭉쳐서 웅덩이가 된다.

고친 것: 선을 **뼈대(중심선)로 가늘게 만든 뒤** 그 거리장으로 판다. 그러면
**어디서나 반지름이 같은 홈**이 나온다 — 붓 굵기가 아니라 **선이 지나간 자리**만 쓴다.

    A 마스크 거리장 (지금)    골 폭 = 원화 선 굵기 + 반폭
    B 뼈대 거리장 (일정)      골 폭 = 2 × 반폭 로 **고정**

재는 것 (문턱을 먼저 적는다):

    Q1  **골 폭 들쭉날쭉(변동계수)이 절반 아래**로 준다
    Q2  선 재현이 A 대비 −0.03 이내
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
import 잔물결 as RP
W = H.W
OUT = H.OUT


def 뼈대(선):
    """선을 **중심선 한 줄**로 — 붓 굵기를 버리고 «지나간 자리»만 남긴다."""
    from skimage.morphology import skeletonize
    return skeletonize(선)


def 골폭(w, 선):
    """골 폭의 들쭉날쭉 — 조각마다 «깊이 절반 이상인 화소 / 뼈대 길이» 를 재고 변동계수를 낸다."""
    sk = 뼈대(선)
    lab, n = ndimage.label(선, np.ones((3, 3), bool))
    폭 = []
    for i in range(1, n + 1):
        m = lab == i
        L = int((sk & m).sum())
        if L < 30:
            continue
        폭.append(float((w[m] > 0.5).sum()) / L)
    if len(폭) < 3:
        return 0.0, 0.0
    폭 = np.array(폭)
    return float(폭.mean()), float(폭.std() / max(폭.mean(), 1e-6))


def main(case="오메가몬", depth=0.015):
    from PIL import Image, ImageDraw
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    N = FM.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    fh, _ = H.field_hull(masks, back_sign=bs, n=N)
    선N = {}
    for v in ("front", "back"):
        w2 = MI.창선(raw, p, bs, case, v, 조각최소=0)
        if v == "back" and bs < 0:
            w2 = w2[:, ::-1]
        k = W.RES // N
        선N[v] = w2.reshape(N, k, N, k).any((1, 3)).T[:, ::-1]
    앞2, 뒤2, 있, _, _ = FM.다듬기(g, 선N["front"] | 선N["back"], np.ones((N, N), bool))
    몸 = trimesh.Trimesh(*H.mesh_from_field(FM.장으로(앞2, 뒤2, 있, g), ax), process=False)
    ps = 몸.split(only_watertight=False)
    if len(ps) > 1:
        큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
        몸 = trimesh.util.concatenate(큰) if 큰 else 몸
    if 몸.volume < 0:
        몸.invert()
    몸, _ = RP.덮개(몸, RP.타우빈펴기(몸), fh, ax)                     # 09-21 채택한 몸 (잔물결 −60%)

    선앞 = MI.창선(raw, p, bs, case, "front", 조각최소=0)
    원선 = 선앞 & ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    MI.잘게 = 1

    표 = []
    for 이름, 뼈 in (("A 마스크 거리장 (지금)", False), ("B 뼈대 거리장 (반지름 일정)", True)):
        원본V골 = MI.V골
        if 뼈:
            MI.V골 = lambda 선: 원본V골(뼈대(선))                      # 뼈대에서 판다
        try:
            m = MI.새김(몸, raw, p, bs, case, depth)[0]
            w2d = MI.V골(선앞)
            평, 변 = 골폭(w2d, 선앞)
            rp = DM.창렌더(m, os.path.join(OUT, "홈반지름_%s_%s.png" % (case, 이름[0])))
        finally:
            MI.V골 = 원본V골
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
        표.append({"판본": 이름, "골 폭 평균": round(평, 2), "골 폭 변동계수": round(변, 3),
                   "선 재현": round(재, 3), "못덮음": 못, "지어냄": 지어, "png": rp})
        print("  %-26s 골 폭 %.2f 화소 · **변동계수 %.3f** · 선 재현 %.3f · 못덮음 %s · 지어냄 %d"
              % (이름, 평, 변, 재, [float(x) for x in 못.values()], 지어), flush=True)

    A, B = 표
    Q = {"Q1 골 폭 변동계수 절반 아래": bool(B["골 폭 변동계수"] < 0.5 * A["골 폭 변동계수"]),
         "Q2 선 재현 -0.03 이내": bool(B["선 재현"] >= A["선 재현"] - 0.03),
         "Q3 지어냄·못덮음 유지": bool(B["지어냄"] <= A["지어냄"] * 1.02
                                and all(B["못덮음"][v] <= A["못덮음"][v] + 0.3 for v in W.VIEWS))}
    for k, v in Q.items():
        print("   %-26s %s" % (k, "통과" if v else "짐"))

    S = 470
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원im = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    상자 = [("가슴", (300, 210, 720, 630)), ("다리", (330, 560, 700, 1000))]
    sheet = Image.new("RGB", (3 * (S + 8), 2 * (S + 8) + 130), "white")
    for r, (이름박스, 박스) in enumerate(상자):
        sheet.paste(원im.crop(박스).resize((S, S)), (0, 130 + r * (S + 8)))
        for i, t in enumerate(표):
            sheet.paste(Image.open(t["png"]).convert("RGB").crop(박스).resize((S, S)),
                        ((i + 1) * (S + 8), 130 + r * (S + 8)))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "홈 반지름을 일정하게 — 붓 굵기 말고 **선이 지나간 자리**에서 판다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), "골 폭 %.2f -> %.2f 화소 · **들쭉날쭉(변동계수) %.3f -> %.3f** · 선 재현 %.3f -> %.3f"
            % (A["골 폭 평균"], B["골 폭 평균"], A["골 폭 변동계수"], B["골 폭 변동계수"],
               A["선 재현"], B["선 재현"]), (28, 110, 60), f본)
    dr.text((14, 80), "위 줄 가슴 · 아래 줄 다리 확대. 선의 **연결 정보**(뼈대)를 쓰면 굵게 그은 데도 가늘게 그은 데도 "
                      "홈이 같은 폭이다.", (90, 92, 100), f작)
    for i, t in enumerate(["원화"] + [r["판본"] for r in 표]):
        dr.text((i * (S + 8) + 6, 108), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "홈반지름_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "깊이": depth, "반폭": MI.반폭,
               "표": [{k: v for k, v in r.items() if k != "png"} for r in 표], "판정": Q},
              open(os.path.join(OUT, "기록", "홈반지름_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 0.015)
