# -*- coding: utf-8 -*-
"""여러 각도 원화에서 정면(1 번)과 같은 데이터 뽑기 (10-02 사용자 「뒤에 혹 같은 건 빼고 각 그림에서 처음 1 번처럼 뽑아내라고 데이터를」).
답지(피규어 · 키트) 제외 · 돔 없음. 장마다:
  ① 머리 윤곽 — 있는 것(윤곽3_정면 · 윤곽2_3-4)은 그대로, 나머지는 SAM 상자(+ 얼굴 위 점) → SAM 씨앗 GrabCut(SAM씨앗.py 와 같은 식) · 옆은 윤곽3 이 부리를 빼서 다시
  ② 먹선 칸 — 선파츠_같은조건.py 와 같은 규칙 · 머리 높이 HP=600 에 맞춤
  ③ 그림자 — 칸마다 밝기 오츠 두 무리 · 밝기 차 > 18 이고 어두운 비 10~90 % 일 때만(원화그림자.py 규칙 · 이름 묶음 대신 칸 단위 — 새 장엔 이름이 아직 없다)
출력 out/오메가몬2/지표/각도데이터/<장>.npz(라벨 · 그림자 · 배율) · 각도데이터_시트.png · 각도데이터.json"""
import os, json, numpy as np, cv2, torch
from PIL import Image, ImageDraw, ImageFont
R = r"G:\art2real\원화3d\out"; K = os.path.join(R, "오메가몬2", "지표"); O = os.path.join(K, "각도데이터"); os.makedirs(O, exist_ok=True)
D = os.path.join(R, "번역", "디지몬")
장들 = [("1 정면 · 02", r"장면\02_역습\yt_172.0_얼굴_정면.jpg", "윤곽3_정면_전체.npy", None),
       ("2 옆 · 02", r"장면\02_역습\yt_235.0_머리_옆.jpg", None, ((420, 0, 960, 330), [(480, 195), (640, 180), (720, 200)])),
       ("3 3/4 · 02", r"장면\02_역습\yt_140.5_얼굴_3-4_망토.jpg", None, (340, 0, 830, 345)),
       ("4 위에서 · 02", r"장면\02_역습\wk_Omegamon_M04.jpg", "윤곽2_3-4_전체.npy", None),
       ("5 옆 3/4 · tri", r"다각도\wk_Omegamon_Adv_tri2.png", None, ((0, 0, 600, 470), [(350, 250), (230, 380), (150, 330)])),
       ("6 뒤 · 설정화", r"원작\Omegamon1.png", None, (850, 95, 1000, 245))]
HP = 600; BH, 닫힘, 최소 = 1.8, 1.5, 0.35
sam = proc = None
def SAM윤곽(im, box):
    box, pts = box if isinstance(box[0], tuple) else (box, None)
    global sam, proc
    if sam is None:
        from transformers import SamModel, SamProcessor
        proc = SamProcessor.from_pretrained("facebook/sam-vit-base"); sam = SamModel.from_pretrained("facebook/sam-vit-base").to("cuda" if torch.cuda.is_available() else "cpu")
    x0, y0, x1, y1 = box; H, W = im.shape[:2]
    inp = proc(Image.fromarray(im[:, :, ::-1]), input_boxes=[[[x0, y0, x1, y1]]], **({"input_points": [[[list(q) for q in pts]]]} if pts else {}), return_tensors="pt").to(sam.device)
    with torch.no_grad(): o = sam(**inp)
    m = proc.image_processor.post_process_masks(o.pred_masks.cpu(), inp["original_sizes"].cpu(), inp["reshaped_input_sizes"].cpu())[0][0]
    mS = m[int(o.iou_scores[0, 0].cpu().numpy().argmax())].numpy().astype(bool); bx = np.zeros((H, W), bool); bx[y0:y1, x0:x1] = True; mS &= bx
    gc = np.full((H, W), cv2.GC_BGD, np.uint8); gc[bx] = cv2.GC_PR_BGD; gc[cv2.erode(mS.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(mS.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0] = cv2.GC_FGD
    b_, f_ = np.zeros((1, 65)), np.zeros((1, 65)); cv2.grabCut(im, gc, None, b_, f_, 5, cv2.GC_INIT_WITH_MASK)
    m = (((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)) | (mS if pts else False)) & bx;   # 점을 준 장은 SAM 이 잡은 어두운 부리도 살린다
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    m = lab == (1 + st[1:, cv2.CC_STAT_AREA].argmax()); cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(cs, key=cv2.contourArea).reshape(-1, 2)
def 칸(im, 윤곽):
    hh = np.ptp(윤곽[:, 1]); s = HP / hh; big = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA); 윤 = (윤곽 * s).astype(np.int32)
    g = cv2.cvtColor(cv2.bilateralFilter(big, 7, 30, 7), cv2.COLOR_BGR2GRAY); 안 = np.zeros(g.shape, np.uint8); cv2.fillPoly(안, [윤], 1); 안 = 안.astype(bool)
    lo, hi = np.percentile(g[안], [2, 98]); g = np.clip((g.astype(float) - lo) * 255 / max(1, hi - lo), 0, 255).astype(np.uint8)
    u = HP / 100; kb = max(3, int(BH * u) | 1); kc = max(2, int(닫힘 * u)); ka = max(9, int(4 * u) | 1)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kb, kb))); 먹 = bh > max(18, np.percentile(bh[안], 90))
    적 = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, ka, 6) > 0
    L = g.astype(float); 어둠 = (L < 0.35 * np.median(L[안])) & 안; 어둠 = cv2.morphologyEx(어둠.astype(np.uint8), cv2.MORPH_OPEN, np.ones((max(3, int(u)),) * 2, np.uint8)) > 0
    선 = (먹 | 적) & 안 & ~cv2.erode(어둠.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool); 벽 = 선.astype(np.uint8); cv2.polylines(벽, [윤], True, 1, 3)
    벽 = cv2.morphologyEx(벽, cv2.MORPH_CLOSE, np.ones((kc, kc), np.uint8)) > 0
    n, lab = cv2.connectedComponents((안 & ~벽).astype(np.uint8), connectivity=4); 면적 = np.bincount(lab.ravel(), minlength=n); 최소px = 최소 / 100 * HP * HP
    for _ in range(6):
        작은 = [i for i in range(1, n) if 0 < 면적[i] < 최소px]
        if not 작은: break
        for i in 작은:
            m = lab == i; 둘레 = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m; 이웃 = lab[둘레]; 이웃 = 이웃[(이웃 != 0) & (이웃 != i)]
            if len(이웃): j = np.bincount(이웃).argmax(); lab[m] = j; 면적[j] += 면적[i]; 면적[i] = 0
    ids = [i for i in range(1, n) if 면적[i] > 0]; 라벨 = np.zeros_like(lab)
    for k_, i in enumerate(ids): 라벨[lab == i] = k_ + 1
    _, idx = cv2.distanceTransformWithLabels((라벨 == 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL); ys, xs = np.nonzero(라벨 > 0)
    참조 = np.zeros(idx.max() + 1, np.int32); 참조[idx[ys, xs]] = 라벨[ys, xs]; 라벨 = np.where((라벨 == 0) & 안, 참조[idx], 라벨); 라벨[~안] = 0
    return big, 라벨, s, 벽 & 안
def 그림자(big, 라벨, 벽):
    Lum = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)[:, :, 0]; sh = np.zeros(라벨.shape, bool); n = 0
    for i in range(1, 라벨.max() + 1):
        m = (라벨 == i) & ~벽; v = Lum[m]
        if v.size < 50: continue
        t, _ = cv2.threshold(v.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); dk = v < t
        if dk.any() and (~dk).any() and v[~dk].mean() - v[dk].mean() > 18 and 0.1 < dk.mean() < 0.9: sh[np.nonzero(m)[0][dk], np.nonzero(m)[1][dk]] = True; n += 1
    return sh, n
결과 = {}; tiles = []; f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22)
for 이름, p, npy, box in 장들:
    im = cv2.imdecode(np.fromfile(os.path.join(D, p), np.uint8), cv2.IMREAD_COLOR)
    윤곽 = np.load(os.path.join(K, npy)).astype(float) if npy else SAM윤곽(im, box).astype(float)
    big, 라벨, s, 벽 = 칸(im, 윤곽); sh, n그 = 그림자(big, 라벨, 벽); 선화 = "설정화" in 이름
    if 선화: sh[:] = False; n그 = 0          # 선화엔 칠한 그림자가 없다
    np.savez_compressed(os.path.join(O, 이름.split()[0] + ".npz"), 라벨=라벨, 그림자=sh, s=s, 윤곽=윤곽)
    결과[이름] = {"파일": p, "윤곽": npy or "SAM 씨앗 GrabCut", "칸": int(라벨.max()), "그림자칸": n그, "그림자비": round(float(sh.sum() / max(1, (라벨 > 0).sum())), 3)}
    m = 라벨 > 0; ys, xs = np.nonzero(m); cut = lambda a: a[max(0, ys.min() - 12):ys.max() + 12, max(0, xs.min() - 12):xs.max() + 12]
    rng = np.random.RandomState(3); 팔 = rng.randint(70, 240, (라벨.max() + 2, 3)); ov = big.copy(); ov[m] = 팔[라벨[m]]; a = cv2.addWeighted(big, 0.45, ov, 0.55, 0)
    mx = cv2.dilate(라벨.astype(np.float32), np.ones((3, 3), np.uint8)); mn = -cv2.dilate((-라벨).astype(np.float32), np.ones((3, 3), np.uint8)); a[(mx != mn) & m] = 0
    b = big.copy(); b[~m] = (b[~m] * 0.3).astype(np.uint8); b[sh] = (0.4 * b[sh] + 0.6 * np.array((60, 40, 230))).astype(np.uint8)
    row = [cut(big), cut(a), cut(b)]; h = 300; row = [cv2.resize(r, (int(r.shape[1] * h / r.shape[0]), h)) for r in row]; tiles.append((np.hstack(row), 이름, 결과[이름]))
    print(이름, 결과[이름])
W = max(t.shape[1] for t, _, _ in tiles); out = Image.new("RGB", (W, len(tiles) * 340), (20, 20, 24)); d = ImageDraw.Draw(out)
for i, (t, 이름, r) in enumerate(tiles):
    out.paste(Image.fromarray(t[:, :, ::-1]), (0, i * 340 + 36)); d.text((8, i * 340 + 6), f"{이름} — 원화 · 먹선 칸 {r['칸']} · 그림자(빨강) {r['그림자칸']}칸 · 윤곽 {r['윤곽']}", font=f, fill=(255, 232, 58))
out.save(os.path.join(O, "각도데이터_시트.png")); json.dump(결과, open(os.path.join(O, "각도데이터.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
