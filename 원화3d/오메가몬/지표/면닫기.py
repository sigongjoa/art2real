# -*- coding: utf-8 -*-
"""면 닫기 — 끊긴 선의 끝점을 접선 방향으로 이어 면을 닫는다 (09-29 「면을 닫는 알고리즘을 돌려봐」).
    python 면닫기.py -> out/오메가몬2/자료/<이름>_선닫힘.png · <이름>_닫기_보기.png(선 검정 · 이은 선 빨강) · 자료영역.py 가 _선닫힘 이 있으면 그것을 쓴다.
알고리즘(3 배 그림 · 반경 R = 머리 높이의 3 %):
  1 세선화  2 끝점 = 8-이웃이 1 개인 화소  3 끝점마다 접선 = 마지막 6 화소의 방향 · 접선 ±35° 부채꼴 안 R 이내의 가장 가까운 선 화소로 잇는다
  4 못 이은 끝점끼리 R 이내면 잇는다  5 두 번 반복(이은 선이 새 접점을 만든다).
"""
import os, sys, json, math
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 소벨 import 세선
D = J(OUT, "..", "자료"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 끝점(sk):
    nb = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.float32)) - sk; return np.argwhere((sk > 0) & (nb == 1))
def 접선(sk, y, x, n=6):
    """끝점에서 선을 따라 n 화소 거슬러 간 점 → 끝점 방향 단위 벡터"""
    seen = {(y, x)}; cy, cx = y, x
    for _ in range(n):
        nxt = [(cy + dy, cx + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and 0 <= cy + dy < sk.shape[0] and 0 <= cx + dx < sk.shape[1] and sk[cy + dy, cx + dx] and (cy + dy, cx + dx) not in seen]
        if not nxt: break
        cy, cx = nxt[0]; seen.add((cy, cx))
    v = np.array([y - cy, x - cx], float); n_ = np.linalg.norm(v); return v / n_ if n_ > 0 else None
def 닫기(선, R, 각도=35, 가지=4):
    sk = 세선(cv2.dilate((선 > 0).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))) > 0                 # 이중선 합침
    for _ in range(가지):                                                                              # 잔가지 치기: 끝점을 가지 길이만큼 깎는다(진짜 끝도 깎이지만 R 로 다시 잇는다)
        e = 끝점(sk)
        if len(e) == 0: break
        sk[e[:, 0], e[:, 1]] = False
    이음 = np.zeros(sk.shape, np.uint8); 원 = sk.copy()
    for 회 in range(2):
        pts = 끝점(sk); 안됨 = []
        ys, xs = np.nonzero(sk); 전체 = np.stack([ys, xs], 1)
        for y, x in pts:
            d = 접선(sk, y, x)
            if d is None: 안됨.append((y, x)); continue
            v = 전체 - (y, x); dist = np.linalg.norm(v, axis=1); ok = (dist > 3) & (dist <= R)
            if not ok.any(): 안됨.append((y, x)); continue
            cos = (v[ok] @ d) / dist[ok]; cand = np.nonzero(cos >= math.cos(math.radians(각도)))[0]
            if len(cand) == 0: 안됨.append((y, x)); continue
            j = cand[np.argmin(dist[ok][cand])]; ty, tx = 전체[ok][j]; cv2.line(이음, (int(x), int(y)), (int(tx), int(ty)), 1, 1)
        if 안됨:
            P = np.array(안됨)
            for i, (y, x) in enumerate(P):
                dd = np.linalg.norm(P - (y, x), axis=1); dd[i] = 1e9; j = int(np.argmin(dd))
                if dd[j] <= R: cv2.line(이음, (int(x), int(y)), (int(P[j][1]), int(P[j][0])), 1, 1)
        sk = sk | (이음 > 0)
    return sk, 이음 > 0, 원
if __name__ == "__main__":
    for n in ("02_정면", "02_3-4", "02_옆"):
        선 = 읽기(J(D, n + "_선.png"), cv2.IMREAD_GRAYSCALE) < 128; sil = 읽기(J(D, n + "_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; ys, _ = np.nonzero(sil); R = int(0.03 * (ys.max() - ys.min()) * 3)
        sk, 이음, 원 = 닫기(선, R); cv2.imencode(".png", (~sk).astype(np.uint8) * 255)[1].tofile(J(D, n + "_선닫힘.png"))
        x0, y0, x1, y1 = [v * 3 for v in 기록[n]["상자"]]; vis = np.full(선.shape + (3,), 255, np.uint8); vis[원] = (0, 0, 0); vis[cv2.dilate(이음.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0] = (0, 0, 255)
        cv2.imencode(".png", vis[y0:y1, x0:x1])[1].tofile(J(D, n + "_닫기_보기.png")); print(n, "R", R, "px · 끝점", len(끝점(원)), "→ 남은 끝점", len(끝점(sk)), "· 이은 화소", int(이음.sum()))
