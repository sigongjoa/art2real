# -*- coding: utf-8 -*-
"""부위 분할 — 윤곽3(GrabCut 영역 씨앗) 안을 부위별로 가른다 (10-01 「grabcut 을 바탕으로 segmentation · 알고리즘이든 ai 든」).
    python 부위분할.py -> out/오메가몬2/지표/부위분할_<장>.png (A 색 군집 · B 라벨 묶기 · C SAM 자동) · 부위분할_<장>_B.npz(부위 마스크) · 부위분할.json
바탕: 윤곽3_<장>_전체.npy 안만. 부위 = 투구(흰) · 속머리/눈구멍(검정) · 눈(파랑) · 뿔(흰 · 위) · 볼날개(흰 · 옆) · 마스크(흰 · 아래) · 번개무늬(파랑 · 작음).
A 색 군집: Lab 색 k=4 → 흰 · 검 · 파랑 · 먹선 → 흰은 위치로 투구/마스크/뿔/볼날개(머리 단위 y · x 문턱 — 사람이 정한 숫자).
B 라벨 묶기: 09-29 면 라벨을 부위 사전(사람이 09-30 정한 대응)으로 묶는다 → 가장 「설명 가능」.
C SAM 자동 마스크(점 격자 프롬프트 · 윤곽3 안 점만) → 겹치는 마스크는 큰 것부터 · 색으로 이름 붙임(흰/검/파)."""
import os, sys, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); K = J(OUT, "..", "지표"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
사전 = {"02_정면": {"뿔": [1, 2], "투구": [3, 4, 5, 6, 7, 8], "차양": [9, 12], "눈구멍": [10, 13], "눈": [15, 16], "볼날개": [11, 14], "마스크": [17, 18, 24, 25, 30, 31], "송곳니": [19, 20, 21, 26]},
      "02_옆": {"뿔": [1], "투구": [10], "차양": [2, 3], "눈구멍": [9, 11, 6, 8], "눈": [4, 7], "볼날개": [5], "마스크": [12, 13, 14, 15]}}
색 = {"뿔": (200, 200, 60), "투구": (240, 240, 240), "차양": (255, 150, 60), "눈구멍": (40, 40, 40), "눈": (60, 140, 255), "볼날개": (255, 90, 200), "마스크": (120, 220, 120), "송곳니": (60, 220, 220), "번개": (90, 90, 255), "기타": (120, 120, 120)}
def 칠(im, 마스크들, 윤곽):
    t = im.copy(); ov = t.copy()
    for n, m in 마스크들.items():
        if m.any(): ov[m] = (0.3 * ov[m] + 0.7 * np.array(색.get(n, 색["기타"]))[::-1]).astype(np.uint8)
    t = cv2.addWeighted(t, 0.35, ov, 0.65, 0); cv2.polylines(t, [윤곽.astype(np.int32)], True, (255, 0, 200), 2)
    pil = Image.fromarray(t[:, :, ::-1]); dr = ImageDraw.Draw(pil); f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 16)   # 한글은 PIL 로
    for n, m in 마스크들.items():
        if m.any(): ys, xs = np.nonzero(m); dr.text((int(np.median(xs)) - 10, int(np.median(ys)) - 8), n, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return np.array(pil)[:, :, ::-1].copy()
결과 = {}
for 장, 키 in (("02_정면", "정면"), ("02_옆", "옆")):
    im = 읽(기록[장]["파일"]); H, W = im.shape[:2]; x0, y0, x1, y1 = 기록[장]["상자"]
    윤곽 = np.load(J(K, "윤곽3_%s_전체.npy" % 키)); 안 = np.zeros((H, W), np.uint8); cv2.fillPoly(안, [윤곽.astype(np.int32)], 1); 안 = 안.astype(bool)
    L = cv2.resize(np.load(J(D, 장 + "_영역.npz"))["라벨"][::3, ::3].astype(np.int32), (W, H), interpolation=cv2.INTER_NEAREST)
    # ── A 색 군집 ──
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32); idx = np.nonzero(안.ravel())[0]
    _, lb, cen = cv2.kmeans(lab[idx], 4, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    군 = np.full(H * W, -1, np.int32); 군[idx] = lb.ravel(); 군 = 군.reshape(H, W)
    밝 = np.argsort(cen[:, 0]); 검군, 파군 = 밝[0], None
    for k in range(4):
        if cen[k, 2] < 118 and k != 검군: 파군 = k if 파군 is None or cen[k, 2] < cen[파군, 2] else 파군       # b 채널 낮음 = 파랑
    흰군 = [k for k in range(4) if k not in (검군, 파군)]
    A = {"눈구멍": 군 == 검군, "눈": (군 == 파군) if 파군 is not None else np.zeros((H, W), bool)}
    흰 = np.isin(군, 흰군)
    if 장 == "02_정면":  # 위치 문턱(머리 단위 ≈ px/3 · 상자 기준): 뿔 = 위 · 볼날개 = 바깥 · 마스크 = 눈 아래 · 나머지 투구
        yy, xx = np.mgrid[0:H, 0:W]; cy = (y0 + y1) / 2; hw = (x1 - x0) / 2; cx = (x0 + x1) / 2
        A["뿔"] = 흰 & (yy < y0 + 0.30 * (y1 - y0)) & (abs(xx - cx) < 0.10 * hw); A["볼날개"] = 흰 & (abs(xx - cx) > 0.62 * hw) & (yy > y0 + 0.35 * (y1 - y0)); A["마스크"] = 흰 & (yy > y0 + 0.62 * (y1 - y0)) & (abs(xx - cx) < 0.5 * hw)
        A["투구"] = 흰 & ~A["뿔"] & ~A["볼날개"] & ~A["마스크"]
    else:
        yy, xx = np.mgrid[0:H, 0:W]; A["마스크"] = 흰 & (yy > y0 + 0.5 * (y1 - y0)) & (xx < x0 + 0.5 * (x1 - x0)); A["투구"] = 흰 & ~A["마스크"]
    # ── B 라벨 묶기 ──
    B = {n: np.isin(L, ids) & 안 for n, ids in 사전[장].items()}
    남 = 안.copy()
    for m in B.values(): 남 &= ~m
    B["기타"] = 남
    # ── C SAM 자동 마스크(점 격자) ──
    import torch; from transformers import SamModel, SamProcessor
    dev = "cuda" if torch.cuda.is_available() else "cpu"; proc = SamProcessor.from_pretrained("facebook/sam-vit-base"); sam = SamModel.from_pretrained("facebook/sam-vit-base").to(dev)
    pts = [[int(x), int(y)] for y in range(y0, y1, 24) for x in range(x0, x1, 24) if 안[y, x]]
    rgb = Image.fromarray(im[:, :, ::-1]); 마스크들 = []
    for i in range(0, len(pts), 32):
        chunk = pts[i:i + 32]; inp = proc(rgb, input_points=[[[p] for p in chunk]], return_tensors="pt").to(dev)
        with torch.no_grad(): o = sam(**inp)
        ms = proc.image_processor.post_process_masks(o.pred_masks.cpu(), inp["original_sizes"].cpu(), inp["reshaped_input_sizes"].cpu())[0]; sc = o.iou_scores[0].cpu().numpy()
        for j in range(ms.shape[0]):
            k = int(sc[j].argmax()); m = ms[j][k].numpy().astype(bool) & 안
            if 0.002 * 안.sum() < m.sum() < 0.6 * 안.sum() and sc[j][k] > 0.8: 마스크들.append((float(sc[j][k]), m))
    마스크들.sort(key=lambda t: -t[1].sum()); 차지 = np.zeros((H, W), np.int32); C = {}
    for s, m in 마스크들:
        new = m & (차지 == 0)
        if new.sum() < 0.6 * m.sum(): continue
        차지[new] = len(C) + 1; g = im[new].mean(0); n = "눈구멍" if g.mean() < 70 else ("눈" if g[0] > g[2] + 25 else "흰%d" % len(C)); C[n] = new
    for n in list(C):
        if n.startswith("흰"): 색[n] = tuple(int(v) for v in np.random.RandomState(len(n) + sum(map(ord, n))).randint(120, 240, 3))
    pad = 60; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad); tiles = []
    for name, M in (("A 색 군집(k=4) + 위치", A), ("B 09-29 라벨 → 부위 사전", B), ("C SAM 자동(점 격자)", C)):
        t = 칠(im, M, 윤곽)[Y0:Y1, X0:X1]; t = cv2.resize(t, (int(t.shape[1] * 560 / t.shape[0]), 560)); cv2.rectangle(t, (0, 0), (t.shape[1], 36), (0, 0, 0), -1); tiles.append((t, name))
    img = Image.fromarray(np.hstack([t for t, _ in tiles])[:, :, ::-1]); dr = ImageDraw.Draw(img); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); x = 0
    for t, name in tiles: dr.text((x + 8, 6), name, font=ft, fill=(255, 255, 255)); x += t.shape[1]
    img.save(J(K, "부위분할_%s.png" % 장)); np.savez_compressed(J(K, "부위분할_%s_B.npz" % 키), **{n: m for n, m in B.items()})
    결과[장] = {"A_군집중심_L": [round(float(c), 1) for c in cen[:, 0]], "B_부위수": len(B), "B_기타비율": round(float(B["기타"].sum() / 안.sum()), 3), "C_마스크수": len(C), "C_덮은비율": round(float((차지 > 0).sum() / 안.sum()), 3), "사람판정": ""}
    print(장, 결과[장])
json.dump(결과, open(J(K, "부위분할.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
