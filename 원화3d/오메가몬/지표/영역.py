# -*- coding: utf-8 -*-
"""선으로 닫힌 면(영역) — 점 대신 영역 · 색으로 (09-29 「점으로는 정보를 알기 어려워 영역이나 색상으로」).
    python 영역.py -> out/오메가몬2/지표/영역_<캡처>.png (왼쪽 면 색칠 + 번호 / 오른쪽 캡처 겹침) · 영역_<캡처>.npz(라벨 · 면 표)
방법(3 배): 실루엣(윤곽.py) 안에서 먹선(선화.py 블랙햇 ∪ 적응 문턱) ∪ Sobel 선(소벨.py) → 틈 메움(닫힘 k) → 선 아닌 곳의 4-연결 성분 = 면 → 작은 면(< 최소) 은 이웃 큰 면에 합침 · 검은 면(눈구멍 · 번개)은 따로 라벨.
09-29 아침의 연결성분 분할이 실패한 이유는 실루엣 없이 · 선 하나로 · 원본 해상도였기 때문. 이번엔 실루엣 안 · 두 선 지도 · 3 배.
"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 윤곽 import 캡처, 실루엣, 읽기; from 선화 import 선따기, S; from 소벨 import 소벨선
닫힘, 최소 = 5, 400
def 영역(im, full):
    im3, m3, thin, 검면 = 선따기(im, full); _, sob = 소벨선(cv2.bilateralFilter(cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), 7, 30, 7))
    선 = ((thin > 0) | (sob > 0)) & m3; 선 = cv2.morphologyEx(선.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((닫힘, 닫힘), np.uint8)) > 0
    빈 = (m3 & ~선 & (검면 == 0)).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(빈, connectivity=4)
    # 작은 면은 이웃 중 가장 긴 경계를 공유하는 큰 면에 합친다(선 화소는 나중에 가장 가까운 면으로)
    큰 = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 최소]; 라벨 = np.where(np.isin(lab, 큰), lab, 0).astype(np.int32)
    for i in range(1, n):
        if i in 큰: continue
        m = lab == i; ring = cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0; nb = 라벨[ring & (라벨 > 0)]
        if nb.size: 라벨[m] = np.bincount(nb).argmax()
    # 선 · 남은 빈 화소를 가장 가까운 면으로 채운다(면이 선을 반씩 나눠 가짐)
    _, idx = cv2.distanceTransformWithLabels((라벨 == 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(라벨 > 0); 값 = np.zeros(idx.max() + 1, np.int32); 값[idx[ys, xs]] = 라벨[ys, xs]; 채움 = 값[idx]; 채움[~m3] = 0; 채움[검면 > 0] = -1
    return im3, 채움, 선, 검면
if __name__ == "__main__":
    for n, (f, 상자, k) in 캡처.items():
        im = 읽기(J(장면, f)); full = 실루엣(im, 상자); im3, 라벨, 선, 검면 = 영역(im, full); ids = [i for i in np.unique(라벨) if i > 0]
        rng = np.random.RandomState(5); 색 = {i: tuple(int(c) for c in rng.randint(60, 240, 3)) for i in ids}; 색[-1] = (30, 30, 30)
        면 = np.full(im3.shape, 255, np.uint8)
        for i, c in 색.items(): 면[라벨 == i] = c
        면[선 & (라벨 != 0)] = (0, 0, 0); 겹 = cv2.addWeighted(im3, 0.45, 면, 0.55, 0)
        for i in ids:
            ys, xs = np.nonzero(라벨 == i); cv2.putText(면, str(i), (int(np.median(xs)) - 6, int(np.median(ys)) + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 3); cv2.putText(면, str(i), (int(np.median(xs)) - 6, int(np.median(ys)) + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
        x0, y0, x1, y1 = [v * S for v in 상자]; out = np.concatenate([면[y0:y1, x0:x1], 겹[y0:y1, x0:x1]], 1)
        p = J(OUT, "영역_%s.png" % n); cv2.imencode(".png", out)[1].tofile(p); np.savez_compressed(p[:-4] + ".npz", 라벨=라벨); print(p, "면", len(ids), "검은 면", int((라벨 == -1).sum() > 0))
