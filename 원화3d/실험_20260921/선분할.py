# -*- coding: utf-8 -*-
"""**먹선을 따라 나눈다** — 홈을 파지 않고, 조립 틈이 곧 선이 되게 (2026-09-21).

    python 선분할.py [케이스=오메가몬] [틈mm=0.3]   -> out/선분할/<케이스>/부품_NNN.ply · out/선분할_<케이스>.png

사용자(09-21): 「애초에 나는 **분할하라**고 했는데」 — 맞다. 점수 매기고 심사만 돌리고 정작 안 나눴다.

    ① 먹선으로 갈린 **칸**을 앞 판 · 뒤 판에서 만든다 (`면다듬기` 와 같은 칸)
    ② 기둥마다 **앞 절반은 앞 판 칸 · 뒤 절반은 뒤 판 칸**으로 3D 라벨 (`색분할` · `부품.py` 규칙)
    ③ 칸마다 **따로** 마칭큐브 — 겉은 원래 장 g 그대로, 칸 경계에서 잘린다
    ④ 부품마다 법선 방향으로 **틈/2 만큼 안으로** 물린다 -> 부품 사이에 틈 = 선

**먹선 홈은 안 판다.** 선은 오직 부품 사이 틈에서 나온다.
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
import 파츠보기 as PV
import 잔물결 as RP
W = H.W
OUT = H.OUT
N = 256
칸최소 = 60                     # 복셀. 이보다 작은 칸은 이웃에 붙인다
흐림 = float(os.environ.get("SEAM_BLUR", "0.5"))   # 부호 거리 흐림(복셀). 1.0 은 부품마다 베개처럼 부풀었다 (09-21)


def 칸지도(case, raw, p, bs, v, 마스크):
    선 = H.ink_map(os.path.join(H.art_dir(case), H.CASES[case]["src"][v]))
    _, w2 = H.to_win(H.declutter(raw[v]), 선.astype(np.float32))
    선창 = H._warp_one(w2, v, p) > 0.5
    몸 = 마스크.astype(bool)
    칸, n = ndimage.label(몸 & ~ndimage.binary_dilation(선창, iterations=1))
    idx = ndimage.distance_transform_edt(칸 == 0, return_distances=False, return_indices=True)
    칸 = np.where(몸, 칸[tuple(idx)], 0)                              # 선 자리도 이웃 칸에 붙인다
    return 칸, n


def main(case="오메가몬", 틈mm=0.3):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    O = g > 0

    앞칸, n앞 = 칸지도(case, raw, p, bs, "front", masks["front"])
    뒤칸, n뒤 = 칸지도(case, raw, p, bs, "back", masks["back"])
    k = W.RES // N
    앞L = 앞칸[::k, ::k].T[:, ::-1]                                    # (x, z) · `색분할` 과 같은 규칙
    뒤L = 뒤칸[::k, ::k].T[:, ::-1]
    if bs < 0:
        뒤L = 뒤L[::-1, :]
    뒤L = np.where(뒤L > 0, 뒤L + n앞, 0)

    있 = O.any(1)
    앞 = np.where(있, O.argmax(1), 0)
    뒤 = np.where(있, N - 1 - O[:, ::-1].argmax(1), 0)
    y = np.arange(N)[None, :, None]
    앞쪽 = y <= ((앞 + 뒤) // 2)[:, None, :]
    lab = np.where(O & 앞쪽, 앞L[:, None, :], 0)
    lab = np.where(O & ~앞쪽, 뒤L[:, None, :], lab)
    크 = np.bincount(lab.ravel())
    작 = np.isin(lab, np.where(크 < 칸최소)[0])
    lab[작] = 0
    빈 = O & (lab == 0)
    if 빈.any():
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab = np.where(빈, lab[tuple(idx)], lab)
    lab[~O] = 0
    부품 = [int(v) for v in np.unique(lab) if v > 0]
    print("  앞 칸 %d · 뒤 칸 %d -> 3D 부품 %d" % (n앞, n뒤, len(부품)), flush=True)

    # 키 -> mm
    zs = np.where(O.any((0, 1)))[0]
    키월드 = float(ax[2][zs[-1]] - ax[2][zs[0]])
    mm = 키월드 / 150.0
    물림 = 틈mm / 2 * mm
    d = os.path.join(OUT, "선분할", case)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".ply"):
            os.remove(os.path.join(d, f))
    셀 = float(ax[0][1] - ax[0][0])
    메시들 = []
    for L in 부품:
        안 = lab == L
        if 안.sum() < 30:
            continue
        # 칸 경계를 **부호 거리**로 — 복셀 라벨을 그대로 자르면 계단이 된다 (`계단은 격자 탓`)
        sl = tuple(slice(max(a.start - 3, 0), b.stop + 3) for a, b in
                   zip(ndimage.find_objects(안.astype(np.int8))[0], ndimage.find_objects(안.astype(np.int8))[0]))
        a = 안[sl] | ~O[sl]                  # 빈 공간은 「내 편」 — 겉은 g 가 정한다. 안 그러면 겉에 계단이 생긴다 (09-21)
        sd = (ndimage.distance_transform_edt(a) - ndimage.distance_transform_edt(~a)) * 셀
        sd = ndimage.gaussian_filter(sd, 흐림) - 물림                          # **틈/2 만큼 안으로**
        gL = np.full(g.shape, -1.0, np.float32)
        gL[sl] = np.minimum(g[sl], sd)
        if gL.max() <= 0:                                               # 틈보다 얇은 칸 — 사라진다
            continue
        V, F = H.mesh_from_field(gL, ax)
        m = trimesh.Trimesh(V, F, process=False)
        if len(m.faces) < 20:
            continue
        메시들.append(RP.타우빈펴기(m))                                  # 격자 계단 — 몸과 같은 처방 (덮개는 생략)
    for i, m in enumerate(메시들):
        PV.내보내기(m, os.path.join(d, "부품_%03d.ply" % i))
    전 = trimesh.util.concatenate(메시들)
    print("  부품 메시 %d 개 · 틈 %.2f mm (물림 %.5f 월드) · 면 %d" % (len(메시들), 틈mm, 물림, len(전.faces)), flush=True)

    r = DM.창렌더(전, os.path.join(OUT, "선분할_렌더_%s.png" % case))
    기존 = os.path.join(OUT, "닮음_렌더_%s.png" % case)                  # 먹선 홈 판본 (비교용)
    S = 480
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((W.RES, W.RES)) if os.path.exists(흰) else Image.new("RGB", (W.RES, W.RES), "white")
    ims = [("원화", 원), ("먹선 홈 (지금)", Image.open(기존).convert("RGB") if os.path.exists(기존) else 원),
           ("먹선 따라 분할 (틈 %.1fmm · 홈 없음)" % 틈mm, Image.open(r).convert("RGB"))]
    박스 = (300, 180, 720, 600)
    sheet = Image.new("RGB", (3 * (S + 8), 2 * (S + 8) + 110), "white")
    for i, (t, im) in enumerate(ims):
        sheet.paste(im.resize((S, S)), (i * (S + 8), 100))
        sheet.paste(im.crop(박스).resize((S, S)), (i * (S + 8), 100 + S + 8))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 18)
    except OSError:
        f제 = f작 = None
    dr.text((14, 14), "먹선을 따라 나눴다 — 홈을 안 파고, 틈이 선이 된다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "부품 %d 개 · 틈 %.1f mm · 아랫줄 가슴 확대" % (len(메시들), 틈mm), (60, 64, 72), f작)
    for i, (t, _) in enumerate(ims):
        dr.text((i * (S + 8) + 6, 76), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "선분할_%s.png" % case)
    sheet.save(o)
    json.dump({"케이스": case, "틈mm": 틈mm, "부품": len(메시들), "앞 칸": int(n앞), "뒤 칸": int(n뒤)},
              open(os.path.join(d, "선분할.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 0.3)
