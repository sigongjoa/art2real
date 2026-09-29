# -*- coding: utf-8 -*-
"""실루엣 안쪽 먹선 · 검은 면(눈구멍) 따기 — 학습 모델 없이 (09-29 「배경은 땄으니 얼굴 안쪽 디테일」).
    python 선화.py -> out/오메가몬2/지표/선화_<캡처>.png (왼쪽 캡처 위 겹침: 빨강 먹선 · 파랑 검은 면 · 초록 실루엣 / 오른쪽 선화) · 선화_<캡처>_only.png · 선화_<캡처>.npz(선 · 검은면 · 실루엣, 3 배)
방법(3 배 확대 · 양방향 필터 뒤):
  먹선 = 블랙햇(15 px 타원 — 밝은 바탕 위 가늘고 어두운 것)  OR  적응 문턱(31 px 블록 · 국소 대비 — 그늘 속 선)  → 실루엣 안 · 60 px 미만 조각 제거 → 세선화
  검은 면 = 실루엣 안에서 절대 어두움(L < 실루엣 밝기의 35 %) 이면서 굵은 것(7 px 열림) — 눈구멍 · 목 그늘. 먹선과 따로 둔다(블랙햇은 굵은 어두움을 못 본다).
  선화 = 실루엣 컨투어 + 먹선 + 검은 면 윤곽.
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J; from 윤곽 import 캡처, 실루엣, 읽기
S = 3
def 세선(b):
    if hasattr(cv2, "ximgproc"): return cv2.ximgproc.thinning(b)
    skel = np.zeros_like(b); e = b.copy(); k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while cv2.countNonZero(e):
        o = cv2.morphologyEx(e, cv2.MORPH_OPEN, k); skel |= e - o; e = cv2.erode(e, k)
    return skel
def 선따기(im, full):
    im3 = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC); im3 = cv2.bilateralFilter(im3, 7, 30, 7); g = cv2.cvtColor(im3, cv2.COLOR_BGR2GRAY)
    m3 = cv2.erode(cv2.resize(full, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST), np.ones((7, 7), np.uint8)) > 0
    L = float(np.percentile(g[m3], 60))
    검면 = ((g < L * 0.35) & m3).astype(np.uint8); 검면 = cv2.morphologyEx(검면, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(검면, connectivity=8); 검면 = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 200]).astype(np.uint8)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    t, _ = cv2.threshold(bh[m3], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    a = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 6) > 0
    선 = (((bh > max(t, 18)) | a) & m3 & (검면 == 0)).astype(np.uint8) * 255
    선 = cv2.morphologyEx(선, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(선, connectivity=8); 선 = (np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 60]).astype(np.uint8) * 255)
    return im3, m3, 세선(선), 검면
if __name__ == "__main__":
    for n, (f, 상자, k) in 캡처.items():
        im = 읽기(J(장면, f)); full = 실루엣(im, 상자); im3, m3, thin, 검면 = 선따기(im, full)
        cs, _ = cv2.findContours(m3.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); ks, _ = cv2.findContours(검면, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        선화 = np.full(m3.shape, 255, np.uint8); 선화[cv2.dilate(thin, np.ones((2, 2), np.uint8)) > 0] = 0; cv2.drawContours(선화, cs, -1, 0, 2); 선화[검면 > 0] = 40
        ov = im3.copy(); ov[검면 > 0] = (ov[검면 > 0] * 0.4 + np.array((255, 80, 0)) * 0.6).astype(np.uint8); ov[cv2.dilate(thin, np.ones((3, 3), np.uint8)) > 0] = (0, 0, 255); cv2.drawContours(ov, cs, -1, (0, 255, 0), 2)
        x0, y0, x1, y1 = [v * S for v in 상자]; Sx = np.concatenate([ov[y0:y1, x0:x1], cv2.cvtColor(선화[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)], 1)
        p = J(OUT, "선화_%s.png" % n); cv2.imencode(".png", Sx)[1].tofile(p); cv2.imencode(".png", 선화)[1].tofile(J(OUT, "선화_%s_only.png" % n)); np.savez_compressed(J(OUT, "선화_%s.npz" % n), 선=thin > 0, 검은면=검면 > 0, 실루엣=m3)
        print(p, "선 화소", int((thin > 0).sum()), "검은 면", len(ks))
