# -*- coding: utf-8 -*-
"""머리 윤곽선(실루엣) 따기 — 학습 모델 없이(09-29 「SAM 쓰지 말고 알고리즘적으로」): GrabCut(머리 상자 초기값 · 색 혼합모델 + 그래프컷) → 닫힘 · 열림 → 가장 큰 성분 → 바깥 컨투어.
    python 윤곽.py -> out/오메가몬2/지표/윤곽_<캡처>.png (빨강 컨투어 · 초록 상자) · 윤곽_<캡처>.npy (컨투어 점 N×2 원본 px)
정면 · 옆은 배경 · 검은 목과 대비가 있어 잘 잡힌다. 3/4 M04 는 머리가 같은 흰색 깃 · 소년 팔과 맞닿아 상자만으로는 새어 나간다(상자를 좁히면 잘리고 넓히면 샘) — 깃 자리를 배경으로 찍어 주는 씨앗이 필요.
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
캡처 = {"정면": ("yt_172.0_얼굴_정면.jpg", (740, 190, 1010, 500)), "3-4": ("wk_Omegamon_M04.jpg", (830, 0, 1440, 700)), "옆": ("yt_235.0_머리_옆.jpg", (430, 30, 800, 305))}
def 윤곽(im, 상자, 반복=8):
    x0, y0, x1, y1 = 상자; mask = np.zeros(im.shape[:2], np.uint8); bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(im, mask, (x0, y0, x1 - x0, y1 - y0), bg, fg, 반복, cv2.GC_INIT_WITH_RECT)
    mk = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); mk = cv2.morphologyEx(mk, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); return max(cs, key=cv2.contourArea).reshape(-1, 2)
if __name__ == "__main__":
    for n, (f, 상자) in 캡처.items():
        im = 읽기(J(장면, f)); c = 윤곽(im, 상자); vis = im.copy(); cv2.drawContours(vis, [c.reshape(-1, 1, 2)], -1, (0, 0, 255), 3); cv2.rectangle(vis, 상자[:2], 상자[2:], (0, 200, 0), 1)
        p = J(OUT, "윤곽_%s.png" % n); cv2.imencode(".png", vis)[1].tofile(p); np.save(p[:-4] + ".npy", c); print(p, "점", len(c), "면적", int(cv2.contourArea(c.reshape(-1, 1, 2))))
