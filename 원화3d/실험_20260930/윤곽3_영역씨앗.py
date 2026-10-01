# -*- coding: utf-8 -*-
"""윤곽 3 — 안쪽 영역(09-29 면 라벨)을 GrabCut 씨앗으로 (10-01 「grabcut 으로 안에 영역을 바탕으로 segmentation 을 해봐」).
    python 윤곽3_영역씨앗.py -> out/오메가몬2/지표/윤곽3_<장>.png (왼 라벨 씨앗 · 가운데 GrabCut 2판 · 오른쪽 윤곽3) · 윤곽3_<장>_전체.npy · 윤곽3.json
씨앗: 머리 라벨 합집합을 침식(9 px) = 확실한 앞 · 머리 라벨 팽창(15 px) 안 = 아마 앞 · 깃 · 어깨 라벨 팽창 = 확실한 뒤 · 그 밖 상자 안 = 아마 뒤 · 상자 밖 = 확실한 뒤.
라벨은 3 배 해상도(영역.py S=3) → [::3, ::3] 로 캡처 해상도."""
import os, sys, json, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); K = J(OUT, "..", "지표"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
머리 = {"02_정면": set(range(1, 22)) | {24, 25, 26, 30, 31}, "02_옆": set(range(1, 16))}
뒤 = {"02_정면": {22, 23, 27, 28, 29, 32, 33}, "02_옆": {16, 17}}
결과 = {}
for 장 in ("02_정면", "02_옆"):
    im = 읽(기록[장]["파일"]); H, W = im.shape[:2]; x0, y0, x1, y1 = 기록[장]["상자"]
    L = np.load(J(D, 장 + "_영역.npz"))["라벨"][::3, ::3]; L = cv2.resize(L.astype(np.int32), (W, H), interpolation=cv2.INTER_NEAREST)
    M머 = np.isin(L, list(머리[장])).astype(np.uint8); M뒤 = np.isin(L, list(뒤[장])).astype(np.uint8)
    M머 = cv2.morphologyEx(M머, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))                      # 라벨 사이 먹선 틈 메움
    gc = np.full((H, W), cv2.GC_BGD, np.uint8); box = np.zeros((H, W), bool); box[max(0, y0 - 40):min(H, y1 + 40), max(0, x0 - 40):min(W, x1 + 40)] = True
    gc[box] = cv2.GC_PR_BGD
    gc[cv2.dilate(M머, np.ones((15, 15), np.uint8)) > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(M머, np.ones((9, 9), np.uint8)) > 0] = cv2.GC_FGD
    gc[cv2.dilate(M뒤, np.ones((7, 7), np.uint8)) > 0] = cv2.GC_BGD
    bg_, fg_ = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64); cv2.grabCut(im, gc, None, bg_, fg_, 6, cv2.GC_INIT_WITH_MASK)
    m = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m); m = (lab == (1 + st[1:, cv2.CC_STAT_AREA].argmax())).astype(np.uint8) if n > 1 else m
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); 컨 = max(cs, key=cv2.contourArea).reshape(-1, 2); np.save(J(K, "윤곽3_%s_전체.npy" % 장.split("_")[1]), 컨)
    컨2 = np.load(J(K, "윤곽2_%s_전체.npy" % 장.split("_")[1])); m2 = np.zeros((H, W), np.uint8); cv2.fillPoly(m2, [컨2.astype(np.int32)], 1)
    결과[장] = {"IoU_윤곽2": round(float(((m > 0) & (m2 > 0)).sum() / max(1, ((m > 0) | (m2 > 0)).sum())), 3), "면적비_윤곽3/2": round(float(m.sum() / max(1, m2.sum())), 3), "사람판정": ""}
    pad = 60; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad); tiles = []
    씨앗 = im.copy(); 씨앗[gc == cv2.GC_FGD] = (0.4 * 씨앗[gc == cv2.GC_FGD] + 0.6 * np.array([0, 200, 0])).astype(np.uint8); 씨앗[gc == cv2.GC_BGD] = (0.5 * 씨앗[gc == cv2.GC_BGD] + 0.5 * np.array([0, 0, 220])).astype(np.uint8); 씨앗[gc == cv2.GC_PR_FGD] = (0.7 * 씨앗[gc == cv2.GC_PR_FGD] + 0.3 * np.array([0, 200, 0])).astype(np.uint8)
    for name, mk, col in (("씨앗(초록 앞 · 빨강 뒤)", None, None), ("GrabCut 2판", m2 > 0, (0, 200, 0)), ("윤곽3 · 영역 씨앗", m > 0, (255, 0, 200))):
        t = 씨앗.copy() if mk is None else im.copy()
        if mk is not None:
            ov = t.copy(); ov[mk] = (0.45 * ov[mk] + 0.55 * np.array(col)).astype(np.uint8); t = cv2.addWeighted(t, 0.35, ov, 0.65, 0); c2, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(t, c2, -1, col, 3)
        t = t[Y0:Y1, X0:X1]; t = cv2.resize(t, (int(t.shape[1] * 520 / t.shape[0]), 520)); cv2.rectangle(t, (0, 0), (t.shape[1], 36), (0, 0, 0), -1); tiles.append((t, name))
    from PIL import Image, ImageDraw, ImageFont; img = Image.fromarray(np.hstack([t for t, _ in tiles])[:, :, ::-1]); dr = ImageDraw.Draw(img); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); x = 0
    for t, name in tiles: dr.text((x + 8, 6), name, font=ft, fill=(255, 255, 255)); x += t.shape[1]
    img.save(J(K, "윤곽3_%s.png" % 장)); print(장, 결과[장])
json.dump(결과, open(J(K, "윤곽3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
