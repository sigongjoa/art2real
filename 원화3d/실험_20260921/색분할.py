# -*- coding: utf-8 -*-
"""**도안의 색분할을 부품 라벨로 쓴다** — 분수령 대신 (2026-09-21).

    python 색분할.py [케이스=메카2]   -> out/색분할_<케이스>.png · out/기록/색분할_*.json

사용자(09-21): 「대조군이 아니라 **GPT 분할을 써**」

분해도는 부품이 흩어져 있어 3D 어디에 붙는지 모른다. 그래서 **조립된 자세 그대로,
부품마다 다른 단색**으로 칠한 판을 받았다 (`out/도안생성/<케이스>/색분할.png` · 삼면).
이건 그림이 아니라 **라벨 지도**라 바로 먹일 수 있다.

    ① 세 판으로 자르고 색을 양자화해 **부품 라벨 지도**를 만든다 (검은 선은 이웃 라벨로 메운다)
    ② `to_win` 으로 창에 앉힌다 — **마스크와 라벨을 같은 변환으로** (INTER_NEAREST 라 라벨이 안 섞인다)
    ③ 기둥마다 **앞 절반은 앞 판 라벨 · 뒤 절반은 뒤 판 라벨** (`부품.py` 09-13 규칙 그대로)
    ④ 같은 라벨이라도 떨어져 있으면 다른 부품 (좌우 팔이 같은 색이어도 갈린다)

문턱을 **먼저 적는다**:

    Q1  색 지도 실루엣이 원화 판과 **IoU >= 0.85** (다른 그림이면 못 쓴다)
    Q2  **부피의 99% 이상**이 어떤 부품에든 붙는다 (빈 라벨이 없다)
    Q3  부품이 **6 개 이상** (한 색으로 뭉치지 않는다)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 도안생성 as DS
W = H.W
OUT = H.OUT
N = 256
색뭉치 = 32                     # 색 양자화 칸 (0~255)
최소몫 = 0.004                  # 판 넓이 대비 이보다 작은 색은 부품으로 안 본다
부품최소 = 0.006                 # 부피 대비 이보다 작은 3D 조각은 **이웃 부품에 붙인다** (버리지 않는다)


def 라벨지도(png):
    """색칠 판 -> (몸 마스크, 부품 라벨). 검은 선과 부스러기는 **가장 가까운 부품**에 붙인다."""
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_COLOR)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    몸 = ndimage.binary_fill_holes(g < 235)
    q = (im // 색뭉치).astype(np.int32)
    코드 = q[:, :, 0] * 10000 + q[:, :, 1] * 100 + q[:, :, 2]
    코드 = np.where(몸, 코드, -1)
    값, 수 = np.unique(코드[몸], return_counts=True)
    쓸 = [v for v, n in zip(값, 수) if n >= 최소몫 * 몸.sum() and not (v < 0)]
    # 검정(선)은 부품이 아니다 — 밝기로 거른다
    쓸 = [v for v in 쓸 if g[코드 == v].mean() > 60]
    라벨 = np.zeros(몸.shape, np.int32)
    for i, v in enumerate(쓸, 1):
        라벨[코드 == v] = i
    빈 = 몸 & (라벨 == 0)
    if 빈.any() and (라벨 > 0).any():
        idx = ndimage.distance_transform_edt(라벨 == 0, return_distances=False, return_indices=True)
        라벨 = np.where(빈, 라벨[tuple(idx)], 라벨)
    라벨[~몸] = 0
    return 몸, 라벨, len(쓸)


def main(case="메카2"):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "도안생성", case)
    판디 = os.path.join(d, "색판")
    if not os.path.exists(os.path.join(판디, "front.png")):
        DS.자르기(os.path.join(d, "색분할.png"), 판디)

    # 원화 판 (지금 케이스가 쓰는 것)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)

    색마스크, 색라벨, iou = {}, {}, {}
    for v in ("front", "side", "back"):
        몸, 라벨, n = 라벨지도(os.path.join(판디, "%s.png" % v))
        m2, l2 = H.to_win(몸, 라벨.astype(np.float32))
        m2 = H._warp_one(m2.astype(np.float32), v, p) > 0.5
        l2 = np.rint(H._warp_one(l2, v, p)).astype(np.int32)
        l2[~m2] = 0
        색마스크[v], 색라벨[v] = m2, l2
        a = masks[v].astype(bool)
        iou[v] = float((a & m2).sum()) / max(float((a | m2).sum()), 1)
        print("  %-6s 색 %2d 개 · 원화 판과 IoU %.3f" % (v, n, iou[v]), flush=True)

    g, ax = H.field_default(masks, back_sign=bs, n=N)
    O = g > 0
    # 격자로 줄이기 — 라벨은 최빈값이 아니라 **가운데 값**으로 (INTER_NEAREST 와 같은 뜻)
    k = W.RES // N
    앞L = 색라벨["front"][::k, ::k].T[:, ::-1]                       # (x, z)
    뒤L = 색라벨["back"][::k, ::k].T[:, ::-1]
    if bs < 0:
        뒤L = 뒤L[::-1, :]
    뒤L = 뒤L + (앞L.max() if 앞L.size else 0)                        # 앞 · 뒤 라벨이 안 겹치게
    뒤L[뒤L == 앞L.max()] = 0

    lab = np.zeros(O.shape, np.int32)
    있 = O.any(1)
    앞 = np.where(있, O.argmax(1), 0)
    뒤 = np.where(있, N - 1 - O[:, ::-1].argmax(1), 0)
    가운데 = (앞 + 뒤) // 2
    y = np.arange(N)[None, :, None]
    앞쪽 = y <= 가운데[:, None, :]
    lab = np.where(O & 앞쪽, 앞L[:, None, :], 0)
    lab = np.where(O & ~앞쪽, 뒤L[:, None, :], lab)
    # 라벨이 0 인 복셀은 제일 가까운 라벨에 붙인다
    빈 = O & (lab == 0)
    if 빈.any() and (lab > 0).any():
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab = np.where(빈, lab[tuple(idx)], lab)
    lab[~O] = 0

    # 같은 색이라도 **떨어져 있으면 다른 부품** (좌우 팔)
    부품 = np.zeros_like(lab)
    다음 = 0
    for v in [int(x) for x in np.unique(lab) if x > 0]:
        cc, n = ndimage.label(lab == v)
        크 = np.bincount(cc.ravel())
        for i in range(1, n + 1):
            if 크[i] < 부품최소 * O.sum():
                continue                                          # 작은 조각은 아래에서 **이웃에 붙인다** (버리지 않는다)
            다음 += 1
            부품[cc == i] = 다음
    남 = O & (부품 == 0)
    if 남.any() and (부품 > 0).any():
        idx = ndimage.distance_transform_edt(부품 == 0, return_distances=False, return_indices=True)
        부품 = np.where(남, 부품[tuple(idx)], 부품)
        부품[~O] = 0
    붙 = float((부품 > 0).sum()) / max(float(O.sum()), 1)
    크기 = np.bincount(부품.ravel())
    크기[0] = 0
    몫 = sorted((크기[크기 > 0] / O.sum()).tolist(), reverse=True)
    Q = {"Q1 색 지도 IoU >= 0.85": bool(min(iou.values()) >= 0.85),
         "Q2 부피 99% 이상 붙음": bool(붙 >= 0.99),
         "Q3 부품 6 개 이상": bool(다음 >= 6)}
    print("  부품 %d · 붙은 부피 %.4f · 부피 몫 %s" % (다음, 붙, ["%.3f" % v for v in 몫[:10]]), flush=True)
    for kq, vq in Q.items():
        print("   %-24s %s" % (kq, "통과" if vq else "**짐**"), flush=True)

    # 그림 — 앞에서 본 색칠
    팔 = [(230, 70, 70), (70, 140, 230), (70, 190, 110), (240, 170, 40), (170, 100, 220),
          (40, 190, 200), (230, 120, 180), (140, 150, 60), (120, 120, 200), (200, 90, 60),
          (90, 170, 90), (210, 150, 210), (150, 110, 70), (100, 190, 240), (250, 120, 90)]
    첫 = np.zeros((N, N), np.int32)
    for j in range(N):
        vv = 부품[:, j, :].T
        새 = (첫 == 0) & (vv > 0)
        첫[새] = vv[새]
    rgb = np.full((N, N, 3), 255, np.uint8)
    for i in range(1, 다음 + 1):
        rgb[첫 == i] = 팔[(i - 1) % len(팔)]
    S = 520
    그림 = Image.fromarray(rgb[::-1]).resize((S, S), Image.NEAREST)
    원 = Image.open(os.path.join(판디, "front.png")).convert("RGB")
    원 = 원.resize((int(원.width * S / 원.height), S))
    sheet = Image.new("RGB", (원.width + S + 380, S + 120), "white")
    sheet.paste(원, (0, 110))
    sheet.paste(그림, (원.width + 10, 110))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    dr.text((14, 14), "도안의 색분할을 부품 라벨로 썼다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 48), "색 지도 IoU  앞 %.3f · 옆 %.3f · 뒤 %.3f   /   부품 %d · 붙은 부피 %.4f"
            % (iou["front"], iou["side"], iou["back"], 다음, 붙), (60, 64, 72), f본)
    y0 = 110
    for kq, vq in Q.items():
        dr.text((원.width + S + 20, y0), "%s %s" % (kq, "통과" if vq else "짐"),
                (28, 110, 60) if vq else (200, 40, 40), f본)
        y0 += 30
    o = os.path.join(OUT, "색분할_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "색 지도 IoU": {k: round(v, 4) for k, v in iou.items()},
               "부품": 다음, "붙은 부피": round(붙, 4), "부피 몫": [round(v, 4) for v in 몫],
               "판정": Q}, open(os.path.join(OUT, "기록", "색분할_%s_%s.json"
                                            % (case, time.strftime("%Y%m%d_%H%M"))), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "메카2")

