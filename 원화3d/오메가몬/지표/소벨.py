# -*- coding: utf-8 -*-
"""우리 렌더의 선 — Sobel 기울기 + Canny (09-29 사용자 「우리 꺼에서 sobel filter 를 사용하는 거는 어때?」).
    python 소벨.py [판 이름 …] -> out/오메가몬2/지표/sobel_<판>.png (원본 · Sobel 크기 · Canny 겹침) · sobel_<판>_<보기>.npz(선)
캡처는 먹선이 있어 블랙햇(선화.py)이 맞고, 우리 렌더는 면 · 음영 · 렌더러가 그은 외곽선이라 기울기(Sobel)가 맞다.
알게 된 것: 렌더에 이미 검은 외곽선(블렌더 선 두께 1.3)이 있어 Sobel 이 그 선의 양쪽 가장자리를 두 줄로 잡는다 → 세선화로 한 줄로 합친다.
  더 나은 길: 우리는 3D 를 가지고 있으니 그림에서 선을 찾을 필요가 없다 — 메시에서 실루엣 · 꺾임(면 각 > 문턱) · 부품 경계를 바로 그리면 정확한 선이 나온다(다음).
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J, 경로
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
def 세선(b):
    if hasattr(cv2, "ximgproc"): return cv2.ximgproc.thinning(b)
    skel = np.zeros_like(b); e = b.copy(); k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while cv2.countNonZero(e):
        o = cv2.morphologyEx(e, cv2.MORPH_OPEN, k); skel |= e - o; e = cv2.erode(e, k)
    return skel
def 소벨선(im):
    g = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
    mag = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)); t = np.percentile(mag[mag > 2], 75)
    e = cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), int(t * 0.5), int(t * 1.5), L2gradient=True)
    e = cv2.morphologyEx(e, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)); return mag, 세선(e)
if __name__ == "__main__":
    for n in (sys.argv[1:] or ["6판"]):
        rows = []
        for 보기 in ("정면", "옆"):
            im = 읽기(경로(n, 보기)); mag, e = 소벨선(im); m8 = np.clip(mag / mag.max() * 510, 0, 255).astype(np.uint8); vis = im.copy(); vis[cv2.dilate(e, np.ones((2, 2), np.uint8)) > 0] = (0, 0, 255)
            rows.append(np.concatenate([im, cv2.cvtColor(m8, cv2.COLOR_GRAY2BGR), vis], 1)); np.savez_compressed(J(OUT, "sobel_%s_%s.npz" % (n, 보기)), 선=e > 0)
        p = J(OUT, "sobel_%s.png" % n); cv2.imencode(".png", np.concatenate(rows, 0))[1].tofile(p); print(p)
