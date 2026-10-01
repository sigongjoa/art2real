# -*- coding: utf-8 -*-
"""SAM 씨앗 + GrabCut — 「#5 에서 쓸모없다고 한 모델을 다시 데려왔다」(10-01).
    python SAM씨앗.py -> out/오메가몬2/지표/SAM씨앗_<장>.png (SAM · GrabCut 2판 · SAM 씨앗 GrabCut 나란히) · SAM씨앗_<장>_전체.npy · SAM씨앗.json
생각: 분할비교.py 에서 SAM 은 옆 · 3/4 에서 안테나까지 잡았고(GrabCut 은 못 잡음) 정면에선 벽을 잡았다(점수 0.965).
     SAM 마스크를 그대로 믿지 않고 **씨앗**으로만 쓴다 — SAM 안쪽(침식) = 「아마 앞」, 상자 밖 = 「확실한 뒤」, 나머지 GrabCut 이 결정.
걸러내기(정면 벽 사고): SAM 마스크 **안쪽**이 밝은(오츠) 비율이 낮으면(벽 · 그림자) SAM 을 버리고 2 판 그대로 → json 에 「SAM 기각」."""
import os, sys, json, numpy as np, cv2, torch
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); K = J(OUT, "..", "지표"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
from transformers import SamModel, SamProcessor
dev = "cuda" if torch.cuda.is_available() else "cpu"; proc = SamProcessor.from_pretrained("facebook/sam-vit-base"); sam = SamModel.from_pretrained("facebook/sam-vit-base").to(dev)
결과 = {}
for 장, 키 in (("02_정면", "정면"), ("02_3-4", "3-4"), ("02_옆", "옆")):
    im = 읽(기록[장]["파일"]); x0, y0, x1, y1 = 기록[장]["상자"]; H, W = im.shape[:2]; rgb = Image.fromarray(im[:, :, ::-1])
    inp = proc(rgb, input_boxes=[[[x0, y0, x1, y1]]], return_tensors="pt").to(dev)
    with torch.no_grad(): o = sam(**inp)
    m = proc.image_processor.post_process_masks(o.pred_masks.cpu(), inp["original_sizes"].cpu(), inp["reshaped_input_sizes"].cpu())[0][0]
    mSAM = m[int(o.iou_scores[0, 0].cpu().numpy().argmax())].numpy().astype(bool)
    컨 = np.load(J(K, "윤곽2_%s_전체.npy" % 키)); mGC = np.zeros((H, W), np.uint8); cv2.fillPoly(mGC, [컨.astype(np.int32)], 1); mGC = mGC.astype(bool)
    # 걸러내기: 상자 안 오츠 밝음(흰 갑주)과 SAM 이 얼마나 겹치나
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); box = np.zeros((H, W), bool); box[y0:y1, x0:x1] = True
    t, _ = cv2.threshold(g[box], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); 밝 = (g > t) & box
    겹 = float((mSAM & 밝).sum() / max(1, mSAM.sum())); 기각 = 겹 < 0.5          # SAM 마스크 안이 밝은 비율(정면 벽 = 어둡다 · 흰 배경 장은 밝음이 상자 전체라 분모를 SAM 으로)
    if 기각: mNEW = mGC
    else:
        gc = np.full((H, W), cv2.GC_BGD, np.uint8); gc[box] = cv2.GC_PR_BGD
        gc[cv2.erode(mSAM.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0] = cv2.GC_PR_FGD         # SAM 안쪽 = 아마 앞
        gc[(cv2.erode(mSAM.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0) & 밝] = cv2.GC_FGD   # SAM 깊숙한 밝은 곳 = 확실한 앞
        gc[(cv2.dilate(mSAM.astype(np.uint8), np.ones((41, 41), np.uint8)) == 0)] = cv2.GC_BGD     # SAM 에서 먼 곳 = 확실한 뒤
        bg_, fg_ = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64); cv2.grabCut(im, gc, None, bg_, fg_, 6, cv2.GC_INIT_WITH_MASK)
        mNEW = (gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)
        n, lab, st, _ = cv2.connectedComponentsWithStats(mNEW.astype(np.uint8)); mNEW = lab == (1 + st[1:, cv2.CC_STAT_AREA].argmax()) if n > 1 else mNEW
    cs, _ = cv2.findContours(mNEW.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); 컨새 = max(cs, key=cv2.contourArea).reshape(-1, 2); np.save(J(K, "SAM씨앗_%s_전체.npy" % 키), 컨새)
    def iou(a, b): return round(float((a & b).sum() / max(1, (a | b).sum())), 3)
    결과[장] = {"SAM밝음겹침": round(겹, 3), "SAM기각": bool(기각), "IoU_새_GC": iou(mNEW, mGC), "IoU_새_SAM": iou(mNEW, mSAM), "사람판정": ""}
    pad = 60; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad); tiles = []
    for name, mk, col in (("SAM", mSAM, (0, 80, 255)), ("GrabCut 2판", mGC, (0, 200, 0)), ("SAM 씨앗 GrabCut" + (" (기각→2판)" if 기각 else ""), mNEW, (255, 0, 200))):
        t_ = im.copy(); ov = t_.copy(); ov[mk] = (0.45 * ov[mk] + 0.55 * np.array(col)).astype(np.uint8); t_ = cv2.addWeighted(t_, 0.35, ov, 0.65, 0)
        c2, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(t_, c2, -1, col, 3); t_ = t_[Y0:Y1, X0:X1]; t_ = cv2.resize(t_, (int(t_.shape[1] * 520 / t_.shape[0]), 520)); cv2.rectangle(t_, (0, 0), (t_.shape[1], 36), (0, 0, 0), -1); tiles.append((t_, name))
    from PIL import ImageDraw, ImageFont; img = Image.fromarray(np.hstack([t_ for t_, _ in tiles])[:, :, ::-1]); dr = ImageDraw.Draw(img); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); x = 0
    for t_, name in tiles: dr.text((x + 8, 6), name, font=ft, fill=(255, 255, 255)); x += t_.shape[1]
    img.save(J(K, "SAM씨앗_%s.png" % 장)); print(장, 결과[장])
json.dump(결과, open(J(K, "SAM씨앗.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
