# -*- coding: utf-8 -*-
"""머리 윤곽선(실루엣) 따기 · 2 판 — 학습 모델 없이(09-29 「SAM 쓰지 말고 알고리즘적으로」 · 「얼굴을 너무 작게 잡았네 · 뿔이 있어서 애매」).
    python 윤곽.py -> out/오메가몬2/지표/윤곽2_<캡처>.png (빨강 전체 · 초록 몸통 · 주황 돌출) · 윤곽2_<캡처>_{전체,몸통}.npy (컨투어 점 N×2 원본 px)
방법: 상자를 뿔 · 안테나까지 넓힌다 → 오츠 밝기로 흰 갑주를 「확실한 앞」 씨앗, 굵은 어두운 덩어리(9 px 침식 · 먹선은 사라짐)를 「확실한 뒤」 씨앗 → GrabCut(마스크 초기화)
   → 9 px 닫힘으로 먹선 잇기 → 가장 큰 성분 = 전체 실루엣 → 타원 열림(k px)으로 가는 돌출(안테나)을 떼어 몸통 / 돌출로 나눈다. 뿔은 굵어 몸통에 남는다.
1 판 실패: 상자 초기화만 쓰면 상자가 좁을 땐 뿔 · 안테나가 잘리고, 넓히면 상자 안이 다 앞이 된다 · 먹선을 배경 씨앗으로 찍으면 얼굴이 선 따라 조각난다.
남은 것: 정면 왼쪽 흰 깃이 볼 날개에 붙어 몸통에 들어온다(같은 색 · 맞닿음) · 3/4 M04 는 깃 · 소년 팔과 맞닿아 상자만으로는 샘.
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
캡처 = {"정면": ("yt_172.0_얼굴_정면.jpg", (690, 10, 1180, 505), 21), "옆": ("yt_235.0_머리_옆.jpg", (400, 0, 990, 305), 17), "3-4": ("wk_Omegamon_M04.jpg", (830, 0, 1440, 700), 21)}
흰배경 = {"3-4"}                                     # 흰 투구가 흰 배경 위 — 밝기 씨앗이 배경까지 앞으로 잡는다 → 먹선 벽 방식
def 실루엣(im, 상자, 반복=6):
    x0, y0, x1, y1 = 상자; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); H, W = g.shape; box = np.zeros((H, W), bool); box[y0:y1, x0:x1] = True
    t, _ = cv2.threshold(g[box], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); 밝 = (g > t) & box
    어둠 = cv2.erode(((g < t * 0.55) & box).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    앞 = cv2.erode(cv2.morphologyEx(밝.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((5, 5), np.uint8)) > 0
    mask = np.full((H, W), cv2.GC_BGD, np.uint8); mask[box & ~어둠] = cv2.GC_PR_FGD; mask[앞] = cv2.GC_FGD; mask[어둠] = cv2.GC_BGD
    cv2.grabCut(im, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 반복, cv2.GC_INIT_WITH_MASK)
    mk = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8); mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); big = max(cs, key=cv2.contourArea); full = np.zeros_like(mk); cv2.drawContours(full, [big], -1, 1, -1); return full
def 실루엣_먹선벽(im, 상자, S=3, 큰=0.15):
    """흰 배경용(09-29): 먹선 ∪ Sobel ∪ 어두움을 벽으로 두고, 상자 테두리에 닿는 **큰** 성분(배경 · 깃 · 다른 인물)을 뺀 나머지 = 머리. 뿔처럼 테두리에 닿아도 작은 것은 남긴다."""
    from 소벨 import 소벨선
    x0, y0, x1, y1 = 상자; c = im[y0:y1, x0:x1]; c3 = cv2.bilateralFilter(cv2.resize(c, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), 7, 30, 7); g = cv2.cvtColor(c3, cv2.COLOR_BGR2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))); a = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 6) > 0; _, sob = 소벨선(c3)
    벽 = cv2.dilate(((bh > 18) | a | (sob > 0) | (g < 60)).astype(np.uint8), np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((벽 == 0).astype(np.uint8), connectivity=4)
    테 = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))); 테.discard(0)
    m = ((lab > 0) & ~np.isin(lab, list(테))).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    nn, l2, s2, _ = cv2.connectedComponentsWithStats(m); i = 1 + int(np.argmax(s2[1:, cv2.CC_STAT_AREA])); m = (l2 == i).astype(np.uint8)   # 얼굴(테두리 안 닿는 것 중 가장 큼)
    닿 = cv2.dilate(m, np.ones((45, 45), np.uint8)) > 0                                                                                    # 뿔: 테두리에 닿지만 닿는 길이가 짧고(뿔 끝이 잘림) 얼굴 가까이 있는 성분은 되살린다
    가장자리 = np.zeros_like(lab, bool); 가장자리[0] = 가장자리[-1] = True; 가장자리[:, 0] = 가장자리[:, -1] = True
    for j in 테:
        접촉 = int(((lab == j) & 가장자리).sum())
        if st[j, cv2.CC_STAT_AREA] < 큰 * lab.size and 접촉 < 120 and ((lab == j) & 닿).any(): m[lab == j] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); f3 = np.zeros_like(m); cv2.drawContours(f3, [max(cs, key=cv2.contourArea)], -1, 1, -1)
    full = np.zeros(im.shape[:2], np.uint8); full[y0:y1, x0:x1] = cv2.resize(f3, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST); return full
def 나누기(full, k):
    core = cv2.morphologyEx(full, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    cs, _ = cv2.findContours(core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cc = max(cs, key=cv2.contourArea)
    ps, _ = cv2.findContours(((full == 1) & (core == 0)).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return cc, [p for p in ps if cv2.contourArea(p) > 150]
if __name__ == "__main__":
    for n, (f, 상자, k) in 캡처.items():
        im = 읽기(J(장면, f)); full = 실루엣_먹선벽(im, 상자) if n in 흰배경 else 실루엣(im, 상자); cs, _ = cv2.findContours(full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); big = max(cs, key=cv2.contourArea); cc, ps = 나누기(full, k)
        vis = im.copy(); cv2.drawContours(vis, [big], -1, (0, 0, 255), 2); cv2.drawContours(vis, [cc], -1, (0, 255, 0), 3); cv2.drawContours(vis, ps, -1, (0, 200, 255), 2)
        p = J(OUT, "윤곽2_%s.png" % n); cv2.imencode(".png", vis)[1].tofile(p); np.save(J(OUT, "윤곽2_%s_전체.npy" % n), big.reshape(-1, 2)); np.save(J(OUT, "윤곽2_%s_몸통.npy" % n), cc.reshape(-1, 2))
        print(p, "전체", len(big), "몸통", len(cc), "돌출", len(ps))
