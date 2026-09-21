# -*- coding: utf-8 -*-
"""**다리의 흠집은 어디서 생기나** — 단계를 끊어 본다 (2026-09-21).

    python 흠집.py [케이스=오메가몬]   -> out/흠집_<케이스>.png · out/기록/흠집_*.json

사용자(09-21): 「지금 보여? **다리 부분에 파인 흠집** 같은 거 있는 거?」 — 보인다.
원화 다리는 선 두어 개뿐인데 우리 정강이 · 발등에는 짧은 빗금이 깔려 있다.

범인을 고르려면 **단계를 끊어서** 봐야 한다. 넷을 같은 틀로 렌더한다:

    ① 통짜 장          `hull.field_default` 그대로 (면 다듬기 없음 · 먹선 없음)
    ② + 면 다듬기      칸마다 평면 맞춤 (`면다듬기`)
    ③ + 타우빈         잔물결 펴기 (`잔물결`)
    ④ + 먹선          V 골 새김 (`매끈먹선`)

흠집이 ①에 이미 있으면 **장**이 범인이고, ②에서 생기면 **칸 경계 단차**,
④에서 생기면 **먹선 지도의 거짓 선**이다. 다리 칸만 잘라 크게 본다.
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
import 면 as SURF
W = H.W
OUT = H.OUT
다리 = (330, 560, 700, 1000)      # 1024 기준 — 허벅지 아래 ~ 발


def 큰조각(m):
    ps = m.split(only_watertight=False)
    if len(ps) > 1:
        큰 = [q for q in ps if abs(q.volume) >= 0.002 * sum(abs(w.volume) for w in ps)]
        m = trimesh.util.concatenate(큰) if 큰 else m
    if m.volume < 0:
        m.invert()
    return m


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
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
        w2 = MI.창선(raw, p, bs, case, v)
        if v == "back" and bs < 0:
            w2 = w2[:, ::-1]
        k = W.RES // N
        선N[v] = w2.reshape(N, k, N, k).any((1, 3)).T[:, ::-1]
    앞2, 뒤2, 있, 칸수, _ = FM.다듬기(g, 선N["front"] | 선N["back"], np.ones((N, N), bool))

    MI.잘게 = 1
    판 = []
    통 = 큰조각(trimesh.Trimesh(*H.mesh_from_field(g, ax), process=False))
    판.append(("① 통짜 장", 통))
    면 = 큰조각(trimesh.Trimesh(*H.mesh_from_field(FM.장으로(앞2, 뒤2, 있, g), ax), process=False))
    판.append(("② + 면 다듬기", 면))
    편, _ = RP.덮개(면, RP.타우빈펴기(면), fh, ax)
    판.append(("③ + 타우빈", 편))
    판.append(("④ + 먹선", MI.새김(편, raw, p, bs, case, 0.015)[0]))

    표, 컷 = [], []
    for 이름, m in 판:
        rp = DM.창렌더(m, os.path.join(OUT, "흠집_%s_%s.png" % (case, 이름[0])))
        컷.append((이름, rp))
        표.append({"판본": 이름, "면": len(m.faces), "거칠기": SURF.roughness(m)["거칠기"],
                   "계단": SURF.dihedral(m)["계단"]})
        print("  %-14s 면 %7d · 거칠기 %.4f · 계단 %.3f" % (이름, len(m.faces), 표[-1]["거칠기"], 표[-1]["계단"]),
              flush=True)

    # 원화 다리에 실제로 그려진 선이 몇 개인지도 같이 센다 (먹선 지도의 거짓 선 확인)
    선 = MI.창선(raw, p, bs, case, "front")
    x0, y0, x1, y1 = 다리
    칸선 = 선[y0:y1, x0:x1]
    lab, n = ndimage.label(칸선)
    크 = np.bincount(lab.ravel())
    print("  원화 다리 칸의 먹선 조각 %d 개 · 화소 %d (100 화소 이상 %d 개)"
          % (n, int(칸선.sum()), int((크[1:] >= 100).sum())), flush=True)

    S = 430
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원im = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    조각 = [("원화", 원im.crop(다리))] + [(이름, Image.open(rp).convert("RGB").crop(다리)) for 이름, rp in 컷]
    sheet = Image.new("RGB", (len(조각) * (S + 8), S + 150), "white")
    for i, (이름, im) in enumerate(조각):
        sheet.paste(im.resize((S, S)), (i * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "다리 흠집은 어디서 생기나 — 단계를 끊어 봤다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), " · ".join("%s 거칠기 %.3f" % (r["판본"], r["거칠기"]) for r in 표), (60, 64, 72), f작)
    dr.text((14, 80), "흠집이 ①에 이미 있으면 장, ②에서 생기면 칸 경계 단차, ④에서 생기면 먹선 지도의 거짓 선이다.",
            (90, 92, 100), f본)
    for i, (이름, _) in enumerate(조각):
        dr.text((i * (S + 8) + 6, 118), 이름, (60, 64, 72), f작)
    o = os.path.join(OUT, "흠집_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "표": 표, "다리 먹선 조각": int(n), "다리 먹선 화소": int(칸선.sum())},
              open(os.path.join(OUT, "기록", "흠집_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M")), ), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
