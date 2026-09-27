# -*- coding: utf-8 -*-
"""실물 키트 사진에서 부품 실루엣을 떼어 정답으로 쓴다 (2026-09-27 · EG RX-78-2).

    python 키트부품.py 방패
      -> out/키트/EG_RX78/방패_정답.npz (마스크 · 윤곽 · 정규 좌표) · 방패_격자.png

크기는 임의(길이 = 1 로 정규) · 형태는 보존. 정답 = 달롱넷 74 부품 나열 사진의 그 부품 실루엣(위에서 본 것).
사진 · 설명서는 사적 이용만 — out/ (gitignore) 에 둔다."""
import os, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure

D = r"G:\art2real\원화3d\out\키트\EG_RX78"
부품표 = {"방패": dict(사진="d_egx01_j1.jpg", 상자=(800, 50, 940, 290), 색="빨강")}   # 상자 = 사진 화소 (x0, y0, x1, y1)

def 색마스크(rgb, 색):
    r, g, b = [rgb[..., i].astype(float) for i in range(3)]
    if 색 == "빨강": return (r > 110) & (r - g > 60) & (r - b > 50)
    raise ValueError(색)

def 떼기(이름):
    p = 부품표[이름]; im = np.array(Image.open(os.path.join(D, p["사진"])).convert("RGB"))
    x0, y0, x1, y1 = p["상자"]; crop = im[y0:y1, x0:x1]
    m = ndimage.binary_closing(색마스크(crop, p["색"]), iterations=2)
    lab, n = ndimage.label(m); m = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
    겉 = ndimage.binary_fill_holes(m)
    # 주축 정렬: 긴 축을 세로로
    ys, xs = np.nonzero(겉); c = np.array([xs.mean(), ys.mean()]); P = np.c_[xs, ys] - c
    w, v = np.linalg.eigh(np.cov(P.T)); 축 = v[:, 1]; 각 = np.degrees(np.arctan2(축[0], 축[1]))
    return crop, m, 겉, c, 각

if __name__ == "__main__":
    이름 = sys.argv[1]; crop, m, 겉, c, 각 = 떼기(이름)
    돌 = lambda a, order=0: ndimage.rotate(a.astype(float), -각, reshape=True, order=order) > 0.5
    겉r, mr = 돌(겉), 돌(m); cr = ndimage.rotate(crop, -각, reshape=True, order=1, cval=255)
    ys, xs = np.nonzero(겉r); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max(); L = y1 - y0 + 1
    겉r, mr, cr = 겉r[y0:y1 + 1, x0:x1 + 1], mr[y0:y1 + 1, x0:x1 + 1], cr[y0:y1 + 1, x0:x1 + 1]
    윤곽 = max(measure.find_contours(np.pad(겉r, 1).astype(float), 0.5), key=len) - 1
    cx = 겉r.shape[1] / 2
    정규 = np.c_[(윤곽[:, 1] - cx) / L, (L - 윤곽[:, 0]) / L]            # (u 좌우, v 아래 0 → 위 1) · 길이 = 1
    np.savez_compressed(os.path.join(D, 이름 + "_정답.npz"), 겉=겉r, 색=mr, 윤곽=정규, 각=각, L화소=L)
    k = 5; big = Image.fromarray(cr).resize((cr.shape[1] * k, cr.shape[0] * k), Image.LANCZOS); dr = ImageDraw.Draw(big)
    for t in np.arange(0, 1.001, 0.05):
        Y = (1 - t) * L * k; dr.line([(0, Y), (big.size[0], Y)], fill=(0, 0, 255) if round(t * 100) % 10 == 0 else (170, 170, 255))
        if round(t * 100) % 10 == 0: dr.text((2, Y + 1), "%.1f" % t, fill=(0, 0, 255))
    for u in np.arange(-0.3, 0.301, 0.05):
        X = (cx + u * L) * k; dr.line([(X, 0), (X, big.size[1])], fill=(0, 140, 0) if round(u * 100) % 10 == 0 else (170, 220, 170))
        if round(u * 100) % 10 == 0: dr.text((X + 2, 2), "%.1f" % u, fill=(0, 120, 0))
    big.save(os.path.join(D, 이름 + "_격자.png"))
    print("각 %.1f° · 길이 %d px · 폭/길이 %.3f · 구멍 넓이 몫 %.3f" % (각, L, 겉r.shape[1] / L, 1 - mr.sum() / 겉r.sum()))
