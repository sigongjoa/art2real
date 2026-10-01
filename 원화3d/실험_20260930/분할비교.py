# -*- coding: utf-8 -*-
"""분할 모델 대조 — 「분할 모델 안 쓰기로 했으면 실제로 돌려 보고 좋은지 나쁜지 알아봐야지」(10-01).
    python 분할비교.py -> out/오메가몬2/지표/분할비교_<장>.png (SAM 상자 프롬프트 · rembg · 우리 GrabCut 2판 나란히) · 분할비교.json(IoU · 사람 판정 자리)
같은 머리 상자(자료.json)를 셋에 똑같이 준다. 정답 마스크는 없다 — 비교는 **눈**으로(렌더는 내가 먼저 본다) · 숫자는 서로 간 IoU 만."""
import os, sys, json, numpy as np, cv2, torch
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 집합 import OUT, J
import 윤곽
D = J(OUT, "..", "자료"); K = J(OUT, "..", "지표"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
from transformers import SamModel, SamProcessor
dev = "cuda" if torch.cuda.is_available() else "cpu"
proc = SamProcessor.from_pretrained("facebook/sam-vit-base"); sam = SamModel.from_pretrained("facebook/sam-vit-base").to(dev)
from rembg import remove, new_session
rs = new_session("isnet-anime")                                         # 애니 전용 모델이 있다 — 공정하게 그걸 쓴다
결과 = {}
for 장 in ("02_정면", "02_3-4", "02_옆"):
    im = 읽(기록[장]["파일"]); x0, y0, x1, y1 = 기록[장]["상자"]; rgb = Image.fromarray(im[:, :, ::-1])
    # 1 SAM — 상자 프롬프트
    inp = proc(rgb, input_boxes=[[[x0, y0, x1, y1]]], return_tensors="pt").to(dev)
    with torch.no_grad(): o = sam(**inp)
    m = proc.image_processor.post_process_masks(o.pred_masks.cpu(), inp["original_sizes"].cpu(), inp["reshaped_input_sizes"].cpu())[0][0]
    sc = o.iou_scores[0, 0].cpu().numpy(); mSAM = m[int(sc.argmax())].numpy().astype(bool)
    # 2 rembg(isnet-anime) — 상자로 자른 조각에 돌려 알파 > 128
    crop = rgb.crop((x0, y0, x1, y1)); out = remove(crop, session=rs); a = np.array(out)[:, :, 3] > 128
    mRB = np.zeros(im.shape[:2], bool); mRB[y0:y1, x0:x1] = a
    # 3 우리 GrabCut 2판(윤곽.py) — 저장된 결과를 쓴다
    npy = J(K, "윤곽2_%s_전체.npy" % 장.split("_")[1]); 컨 = np.load(npy); mGC = np.zeros(im.shape[:2], np.uint8); cv2.fillPoly(mGC, [컨.astype(np.int32)], 1); mGC = mGC.astype(bool)
    def iou(a, b): return round(float((a & b).sum() / max(1, (a | b).sum())), 3)
    결과[장] = {"SAM_점수": round(float(sc.max()), 3), "IoU_SAM_GC": iou(mSAM, mGC), "IoU_RB_GC": iou(mRB, mGC), "IoU_SAM_RB": iou(mSAM, mRB), "사람판정": ""}
    # 그림: 상자 둘레를 넉넉히 잘라 셋 나란히 · 마스크 윤곽을 색으로
    pad = 60; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(im.shape[1], x1 + pad), min(im.shape[0], y1 + pad)
    tiles = []
    for name, mk, col in (("SAM (상자 프롬프트)", mSAM, (0, 80, 255)), ("rembg isnet-anime", mRB, (255, 120, 0)), ("우리 GrabCut 2판", mGC, (0, 200, 0))):
        t = im.copy(); ov = t.copy(); ov[mk] = (0.45 * ov[mk] + 0.55 * np.array(col)).astype(np.uint8); t = cv2.addWeighted(t, 0.35, ov, 0.65, 0)
        cs, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(t, cs, -1, col, 3)
        t = t[Y0:Y1, X0:X1]; t = cv2.resize(t, (int(t.shape[1] * 520 / t.shape[0]), 520))
        cv2.rectangle(t, (0, 0), (t.shape[1], 36), (0, 0, 0), -1); tiles.append((t, name))
    sheet = np.hstack([t for t, _ in tiles]); x = 0
    img = Image.fromarray(sheet[:, :, ::-1]); from PIL import ImageDraw, ImageFont; dr = ImageDraw.Draw(img); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22)
    for t, name in tiles: dr.text((x + 8, 6), name, font=ft, fill=(255, 255, 255)); x += t.shape[1]
    img.save(J(K, "분할비교_%s.png" % 장)); print(장, 결과[장])
json.dump(결과, open(J(K, "분할비교.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
