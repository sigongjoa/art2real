# -*- coding: utf-8 -*-
"""**디테일이 없다** — 면 다듬기 + 먹선을 합치고, 홈 깊이를 재서 고른다 (2026-09-21).

    python 디테일.py [케이스=오메가몬]   -> out/디테일_<케이스>.png · out/결과물/<케이스>/디테일_d<깊이>.ply

사용자(09-21): 「이번에도 형태는 잘 잡는데 **디테일은 아무것도 없어**」

까닭 둘. **하나는 내 실수다.**

    ① 바퀴 2 부터 보여준 것(`부위.ply` · `면.ply`)에는 **먹선 새김이 빠져 있었다.**
       장에서 바로 메시로 갔고 `carve_ink` 를 안 불렀다. 선이 아예 없는 것을 보여드린 셈이다.
    ② 공식 판(`hull.glb`)에도 홈 깊이가 **0.006**(키의 0.6%)뿐이고, 그 위에 높이 스무딩 σ3 이
       걸려 더 얕아진다. 150 mm 로 뽑으면 0.9 mm — **눈에 거의 안 보인다.**

그래서 여기서는 둘을 합치고(면 다듬기 + 먹선) **깊이를 바꿔 가며 잰다.** 문턱을 먼저 적는다:

    Q1  깊이를 키워도 **지어냄이 안 는다** (홈은 안쪽으로만 판다)
    Q2  깊이를 키워도 못덮음이 +0.5%p 안에 든다
    Q3  **렌더에 보이는 선의 원화 선 재현**이 깊이와 함께 오른다 (좌우 반전 대조와 같이 본다)
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
깊이들 = (0.006, 0.015, 0.030)          # 창 단위 (키 = 1.0). 지금 기본은 0.006


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
    d = os.path.join(OUT, "결과물", case)
    os.makedirs(d, exist_ok=True)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    N = FM.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)

    # 먹선을 창 · 격자로 (면 다듬기와 같은 것)
    선 = {}
    for v in ("front", "back"):
        s1 = H.ink_map(os.path.join(base, src[v]))
        _, w2 = H.to_win(H.declutter(raw[v]), s1.astype(np.float32))
        w2 = H._warp_one(w2, v, p) > 0.5
        if v == "back" and bs < 0:
            w2 = w2[:, ::-1]
        k = W.RES // N
        선[v] = w2.reshape(N, k, N, k).any((1, 3)).T[:, ::-1]
    앞2, 뒤2, 있, 칸수, 편 = FM.다듬기(g, 선["front"] | 선["back"], np.ones((N, N), bool))
    새 = FM.장으로(앞2, 뒤2, 있, g)
    V, Fc = H.mesh_from_field(새, ax)
    몸 = trimesh.Trimesh(V, Fc, process=False)
    ps = 몸.split(only_watertight=False)
    if len(ps) > 1:
        큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
        몸 = trimesh.util.concatenate(큰) if 큰 else 몸
    if 몸.volume < 0:
        몸.invert()

    # 원화 안쪽 선 (잴 대상)
    s1 = H.ink_map(os.path.join(base, src["front"]))
    _, w2 = H.to_win(H.declutter(raw["front"]), s1.astype(np.float32))
    원선 = (H._warp_one(w2, "front", p) > 0.5) & ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)
    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=4)

    표, 그림 = [], []
    for 깊 in 깊이들:
        m = H.carve_ink(몸, raw, p, bs, case, depth=깊)
        f출 = os.path.join(d, "디테일_d%03d.ply" % int(깊 * 1000))
        DM.내보내기(m, f출) if hasattr(DM, "내보내기") else m.export(f출)
        rp = DM.창렌더(m, os.path.join(OUT, "디테일_%s_d%03d.png" % (case, int(깊 * 1000))))
        rim = cv2.imdecode(np.fromfile(rp, np.uint8), cv2.IMREAD_UNCHANGED)
        회 = cv2.cvtColor(rim[:, :, :3], cv2.COLOR_BGR2GRAY)
        보임 = (cv2.Canny(cv2.GaussianBlur(회, (3, 3), 0), 20, 60) > 0) & 안
        맞 = ndimage.binary_dilation(보임, iterations=3)
        재 = float((원선 & 맞).sum()) / max(원선.sum(), 1)
        맞c = ndimage.binary_dilation(보임[:, ::-1] & 안, iterations=3)
        재c = float((원선 & 맞c).sum()) / max(원선.sum(), 1)
        V2, F2 = np.asarray(m.vertices), np.asarray(m.faces)
        못, 지어 = {}, 0
        for v in W.VIEWS:
            s = np.asarray(W.silhouette(V2, F2, v, bs if v == "back" else None)).astype(bool)
            a = masks[v].astype(bool)
            못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
            지어 += int((s & ~a).sum())
        ang = m.face_adjacency_angles
        w = m.area_faces[m.face_adjacency].mean(1)
        모 = float(w[ang >= np.radians(30)].sum()) / max(float(w.sum()), 1e-9)
        표.append({"깊이": 깊, "mm(키 150)": round(깊 * 150, 2), "못덮음": 못, "지어냄": 지어,
                   "선 재현": round(재, 3), "대조": round(재c, 3), "이득": round(재 - 재c, 3),
                   "모서리몫": round(모, 3)})
        그림.append(rp)
        print("  깊이 %.3f (%.1f mm) · 못덮음 %s · 지어냄 %d · 선 재현 %.3f (대조 %.3f) · 모서리 %.3f"
              % (깊, 깊 * 150, [float(x) for x in 못.values()], 지어, 재, 재c, 모), flush=True)

    기 = 표[0]
    Q = {"Q1 지어냄 안 늚": bool(max(r["지어냄"] for r in 표) <= 기["지어냄"] * 1.02),
         "Q2 못덮음 +0.5%p 이내": bool(all(r["못덮음"][v] <= 기["못덮음"][v] + 0.5 for r in 표 for v in W.VIEWS)),
         "Q3 선 재현이 깊이와 함께 오름": bool(표[-1]["선 재현"] >= 기["선 재현"])}
    for k, v in Q.items():
        print("   %-28s %s" % (k, "통과" if v else "짐"))

    S = 560
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", ((len(표) + 1) * (S + 8), S + 150), "white")
    sheet.paste(원, (0, 140))
    for i, rp in enumerate(그림):
        sheet.paste(Image.open(rp).convert("RGB").resize((S, S)), ((i + 1) * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 29)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 21)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 18)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "디테일 — 면 다듬기 + 먹선을 합치고 **홈 깊이**를 바꿔 가며 쟀다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "바퀴 2 부터 보여준 결과물에는 **먹선 새김이 빠져 있었다** (내 실수). 여기서 둘을 합쳤다.",
            (200, 40, 40), f본)
    dr.text((14, 80), "칸 %d 개 면 다듬기 + 먹선 홈. 홈은 **안쪽으로만** 판다 — 실루엣도 지어냄도 안 는다."
            % 칸수, (90, 92, 100), f작)
    dr.text((14, 106), "원화", (60, 64, 72), f작)
    for i, r in enumerate(표):
        x = (i + 1) * (S + 8) + 6
        dr.text((x, 106), "홈 깊이 %.3f = %.1f mm (150 mm 기준)" % (r["깊이"], r["mm(키 150)"]), (20, 22, 28), f작)
        dr.text((x, 82), "선 재현 %.3f (대조 %.3f) · 모서리 %.3f · 지어냄 %d"
                % (r["선 재현"], r["대조"], r["모서리몫"], r["지어냄"]), (28, 110, 60), f작)
    o = os.path.join(OUT, "디테일_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "격자": N, "칸": 칸수, "표": 표, "판정": Q},
              open(os.path.join(OUT, "기록", "디테일_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
