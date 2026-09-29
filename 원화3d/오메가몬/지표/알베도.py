# -*- coding: utf-8 -*-
"""알베도(재질) 기반 분할 · 2 판 — 셀 음영은 같은 재질의 어두운 톤이라 SAM · 고정 색 문턱이 한 판을 둘로 가른다(09-29 사용자 「알베도 기반으로」).
    python 알베도.py -> out/오메가몬2/지표/알베도_<캡처>.png (원본 · 색 무리 · 재질 지도 · 재질 + 먹선) · 알베도_<캡처>.npz(재질 라벨 · 먹선)
규칙: 셀 애니에서 **먹선이 있는 경계 = 판(부품) 경계 · 먹선 없는 색 경계 = 같은 재질의 밝은 톤/그늘 톤 경계**.
  1 화이트밸런스(가장 밝은 5 % 의 중앙색을 흰으로) → 장면 캐스트 제거   2 Lab k-means 로 색 무리 k 개
  3 맞닿은 무리 쌍마다 경계 픽셀 중 먹선이 있는 비율을 재서, 낮으면(< 먹선비) 같은 재질로 합침   4 남은 무리 = 재질 · 연결 성분 = 판 후보
1 판(고정 문턱)은 정면이 전부 「파랑」, 옆이 전부 「검」으로 나와 버림 — 장면 조명이 재질보다 컸다.
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
캡처 = {"정면 yt_172": ("yt_172.0_얼굴_정면.jpg", (700, 150, 1060, 520)), "옆 yt_235": ("yt_235.0_머리_옆.jpg", (420, 0, 820, 320)), "3-4 M04": ("wk_Omegamon_M04.jpg", (880, 180, 1320, 720))}
K, 먹선비, 경계최소, 색차최대, 밝차최대 = 8, 0.35, 150, 14, 45   # 색차 = 무리 중심의 a·b 거리(같은 색상 계열만) · 밝차 = L 차(%)
def 화밸(im):
    f = im.reshape(-1, 3).astype(np.float32); L = f.sum(1); 밝 = f[L >= np.percentile(L, 95)]; w = np.median(밝, 0); w = w / w.mean()
    return np.clip(im.astype(np.float32) / w, 0, 255).astype(np.uint8)
def 먹선(im, C=8):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, C) > 0
def 무리(im, k=K):
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    _, lab_, cen = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS); return lab_.reshape(im.shape[:2]), cen
def 합치기(라벨, 선, k, cen):
    """맞닿은 무리 쌍의 경계에서 먹선 비율이 낮으면 같은 재질(그늘 톤)로 합친다. 반환: 무리 → 재질 번호."""
    선넓 = cv2.dilate(선.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0; 부모 = list(range(k))
    def 찾(a):
        while 부모[a] != a: 부모[a] = 부모[부모[a]]; a = 부모[a]
        return a
    쌍 = {}
    for dy, dx in ((0, 1), (1, 0)):
        a = 라벨[:라벨.shape[0] - dy, :라벨.shape[1] - dx]; b = 라벨[dy:, dx:]; s = 선넓[:라벨.shape[0] - dy, :라벨.shape[1] - dx]
        m = a != b
        for i, j, ink in zip(a[m], b[m], s[m]):
            key = (min(i, j), max(i, j)); n, t = 쌍.get(key, (0, 0)); 쌍[key] = (n + 1, t + int(ink))
    for (i, j), (n, t) in sorted(쌍.items(), key=lambda kv: kv[1][1] / kv[1][0]):
        ci, cj = cen[i], cen[j]; 색차 = float(np.hypot(ci[1] - cj[1], ci[2] - cj[2])); 밝차 = abs(float(ci[0] - cj[0])) * 100 / 255
        어둠 = min(ci[0], cj[0]) * 100 / 255 < 22                                    # 검정(눈구멍 · 목)과는 합치지 않는다
        if n >= 경계최소 and t / n < 먹선비 and 색차 < 색차최대 and 밝차 < 밝차최대 and not 어둠: 부모[찾(i)] = 찾(j)
    return [찾(i) for i in range(k)], 쌍
if __name__ == "__main__":
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); rng = np.random.RandomState(7)
    for 이름, (f, box) in 캡처.items():
        im = 읽기(J(장면, f))[box[1]:box[3], box[0]:box[2]]; im = cv2.resize(im, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        im = cv2.bilateralFilter(화밸(im), 9, 40, 9); 선 = 먹선(im); 라벨, cen = 무리(im); 재질, 쌍 = 합치기(라벨, 선, K, cen)
        재질맵 = np.vectorize(lambda i: 재질[i])(라벨); ids = sorted(set(재질))
        무리그림 = np.zeros_like(im); 재질그림 = np.zeros_like(im)
        for i in range(K): 무리그림[라벨 == i] = cv2.cvtColor(np.uint8([[cen[i]]]), cv2.COLOR_LAB2BGR)[0, 0]
        for r in ids: px = im[재질맵 == r]; 재질그림[재질맵 == r] = np.median(px, 0)
        평면 = 재질그림.copy(); 평면[선] = (0, 0, 0)
        S = np.concatenate([im, 무리그림, 재질그림, 평면], 1); pil = Image.fromarray(S[:, :, ::-1]); d = ImageDraw.Draw(pil); W = im.shape[1]
        for i, t in enumerate(("화이트밸런스", "색 무리 %d" % K, "재질 %d (먹선 없는 경계로 합침)" % len(ids), "재질 + 먹선")): d.text((i * W + 8, 6), t, font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        p = J(OUT, "알베도_%s.png" % 이름.replace(" ", "_")); pil.save(p); np.savez_compressed(p[:-4] + ".npz", 재질=재질맵, 선=선)
        print(이름, "무리", K, "→ 재질", len(ids), "| 먹선비 낮은 쌍:", sorted([(i, j, round(t / n, 2)) for (i, j), (n, t) in 쌍.items() if n >= 경계최소], key=lambda x: x[2])[:6])
