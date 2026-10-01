# -*- coding: utf-8 -*-
"""선 파츠 — 윤곽3 안을 **먹선(선)으로** 닫힌 면으로 가른다 (10-01 「색이 아니라 윤곽선 기반으로 나누라고 · 그래야 파츠 분할」).
    python 선파츠.py [닫힘=5] [최소면적비=0.004] -> out/오메가몬2/지표/선파츠_<장>.png (왼 벽(먹선+윤곽) · 가운데 면 번호 · 오른 겹침) · 선파츠_<장>.npz(라벨 · 면표) · 선파츠.json
벽 = 윤곽3 바깥선 ∪ 블랙햇 먹선(선화.py 식) ∪ 적응 문턱 ∪ 검은 면 테두리 → 닫힘 k 로 틈 메움 → 벽 아닌 곳의 4-연결 성분 = 파츠 · 작은 면은 이웃 큰 면에 합침(가장 긴 경계) · 검은 면(눈구멍)은 따로.
09-29 영역.py 와 같은 생각이지만 (1) 바탕이 머리 전용 윤곽3 (2) 손 번호 없이 자동 (3) 캡처 해상도 그대로(3 배 안 함 · 빠르게)."""
import os, sys, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); K = J(OUT, "..", "지표"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
닫힘 = int(sys.argv[1]) if len(sys.argv) > 1 else 5; 최소비 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.004
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
def 세선(b):
    try: return cv2.ximgproc.thinning(b.astype(np.uint8) * 255) > 0
    except Exception: return b
결과 = {}
for 장, 키 in (("02_정면", "정면"), ("02_옆", "옆")):
    im = 읽(기록[장]["파일"]); H, W = im.shape[:2]; x0, y0, x1, y1 = 기록[장]["상자"]
    S = 2; big = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC); big = cv2.bilateralFilter(big, 7, 30, 7); g = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    윤곽 = np.load(J(K, "윤곽3_%s_전체.npy" % 키)) * S; 안 = np.zeros(g.shape, np.uint8); cv2.fillPoly(안, [윤곽.astype(np.int32)], 1); 안 = 안.astype(bool)
    # 벽 1 먹선: 블랙햇(밝은 바탕 위 가는 어두움) ∪ 적응 문턱(그늘 속 선)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))); 먹 = bh > max(18, np.percentile(bh[안], 90))
    적 = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 6) > 0
    선 = (먹 | 적) & 안
    # 벽 2 검은 면(눈구멍 · 그늘): 절대 어두움 + 굵음 → 면 자체는 파츠 · 테두리는 벽
    L = g.astype(float); 어둠 = (L < 0.35 * np.median(L[안])) & 안; 어둠 = cv2.morphologyEx(어둠.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0
    선 = 선 & ~cv2.erode(어둠.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    벽 = 선.copy(); cv2.polylines(벽.view(np.uint8), [윤곽.astype(np.int32)], True, 1, 3)                      # 바깥 윤곽도 벽
    벽 = cv2.morphologyEx(벽.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((닫힘, 닫힘), np.uint8)) > 0
    # 면 = 벽 아닌 곳의 4-연결 성분(윤곽 안)
    빈 = (안 & ~벽).astype(np.uint8); n, lab = cv2.connectedComponents(빈, connectivity=4)
    면적 = np.bincount(lab.ravel(), minlength=n); 최소 = 최소비 * 안.sum()
    # 작은 면 → 가장 긴 경계를 나누는 이웃에 합침(반복)
    for _ in range(4):
        작은 = [i for i in range(1, n) if 0 < 면적[i] < 최소]
        if not 작은: break
        for i in 작은:
            m = lab == i; 둘레 = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m; 이웃 = lab[둘레]; 이웃 = 이웃[(이웃 != 0) & (이웃 != i)]
            if len(이웃): j = np.bincount(이웃).argmax(); lab[m] = j; 면적[j] += 면적[i]; 면적[i] = 0
    # 벽 화소를 가장 가까운 면에 배정(파츠 마스크가 선 두께만큼 비지 않게)
    ids = [i for i in range(1, n) if 면적[i] > 0]; 재 = {i: k + 1 for k, i in enumerate(ids)}; 라벨 = np.zeros_like(lab)
    for i, k in 재.items(): 라벨[lab == i] = k
    dist, idx = cv2.distanceTransformWithLabels((라벨 == 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(라벨 > 0); 참조 = np.zeros(idx.max() + 1, np.int32); 참조[idx[ys, xs]] = 라벨[ys, xs]; 채움 = 참조[idx]; 라벨 = np.where((라벨 == 0) & 안, 채움, 라벨)
    라벨[~안] = 0; 라벨 = cv2.resize(라벨.astype(np.int32), (W, H), interpolation=cv2.INTER_NEAREST); 어둠s = cv2.resize(어둠.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    k_ = len(ids); 면표 = []
    for k in range(1, k_ + 1):
        m = 라벨 == k; yy, xx = np.nonzero(m)
        if not len(xx): continue
        면표.append({"번호": k, "면적": int(m.sum()), "상자": [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())], "검은면": bool(어둠s[m].mean() > 0.5), "밝기": round(float(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[m].mean()), 1)})
    np.savez_compressed(J(K, "선파츠_%s.npz" % 키), 라벨=라벨, 면표=json.dumps(면표, ensure_ascii=False))
    결과[장] = {"파츠수": len(면표), "검은면": sum(f["검은면"] for f in 면표), "닫힘": 닫힘, "최소면적비": 최소비, "사람판정": ""}
    # 그림
    pad = 60; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    벽s = cv2.resize(벽.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0; t1 = im.copy(); t1[벽s] = (0, 0, 255); 안s = cv2.resize(안.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0; t1[~안s] = (t1[~안s] * 0.4).astype(np.uint8)
    rng = np.random.RandomState(3); 팔 = rng.randint(70, 240, (k_ + 1, 3)); t2 = np.zeros_like(im); t2[라벨 > 0] = 팔[라벨[라벨 > 0]]; t2 = cv2.addWeighted(im, 0.25, t2, 0.75, 0); t2[~안s] = (im[~안s] * 0.4).astype(np.uint8)
    t3 = im.copy(); ov = t3.copy(); ov[라벨 > 0] = 팔[라벨[라벨 > 0]]; t3 = cv2.addWeighted(t3, 0.55, ov, 0.45, 0)
    for f in 면표:
        for t in (t2,): pass
    tiles = []
    for name, t in (("벽 = 먹선 ∪ 윤곽3(빨강)", t1), ("닫힌 면 = 파츠 (%d)" % len(면표), t2), ("겹침", t3)):
        t = t[Y0:Y1, X0:X1]; sc = 560 / t.shape[0]; t = cv2.resize(t, (int(t.shape[1] * sc), 560)); cv2.rectangle(t, (0, 0), (t.shape[1], 36), (0, 0, 0), -1); tiles.append((t, name, sc))
    img = Image.fromarray(np.hstack([t for t, _, _ in tiles])[:, :, ::-1]); dr = ImageDraw.Draw(img); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); fs = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 15); x = 0
    for t, name, sc in tiles:
        dr.text((x + 8, 6), name, font=ft, fill=(255, 255, 255))
        if name.startswith("닫힌"):
            for f in 면표:
                m = 라벨 == f["번호"]; yy, xx = np.nonzero(m); cx, cy = (np.median(xx) - X0) * sc + x, (np.median(yy) - Y0) * sc + 36 * 0
                dr.text((cx - 6, cy - 8), str(f["번호"]), font=fs, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        x += t.shape[1]
    img.save(J(K, "선파츠_%s.png" % 장)); print(장, 결과[장])
json.dump(결과, open(J(K, "선파츠.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
