# -*- coding: utf-8 -*-
"""Zero-To-CAD 입력 그림 흉내: 정사영 · 8 팔분면 방향 · 갈색 평면 음영 · 날카로운 모서리 검은 선 · 흰 바탕 · 256 px (데이터셋 그림을 보고 맞춤)"""
import numpy as np, trimesh
from PIL import Image, ImageDraw
BASE = np.array([150, 112, 72]) / 255.0
def render(m, d, S=256, pad=0.06, up=(0, 0, 1)):
    d = np.asarray(d, float); d /= np.linalg.norm(d); up = np.asarray(up, float)
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    V = m.vertices - m.bounds.mean(0); P = np.c_[V @ r, V @ u]; z = V @ d
    ext = np.abs(P).max() * (1 + pad) or 1; px = (P / ext * 0.5 + 0.5) * S; px[:, 1] = S - px[:, 1]
    img = np.ones((S, S, 3)); zb = np.full((S, S), np.inf); F = m.faces; n = m.face_normals
    L = -d + 0.6 * up - 0.3 * r; L /= np.linalg.norm(L); sh = 0.55 + 0.45 * np.clip(n @ L, 0, 1)
    for t in np.where(n @ d < 0)[0]:
        a = px[F[t]]; zs = z[F[t]]
        x0, x1 = int(max(a[:, 0].min(), 0)), int(min(a[:, 0].max() + 1, S - 1)); y0, y1 = int(max(a[:, 1].min(), 0)), int(min(a[:, 1].max() + 1, S - 1))
        if x0 > x1 or y0 > y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (a[1, 1] - a[2, 1]) * (a[0, 0] - a[2, 0]) + (a[2, 0] - a[1, 0]) * (a[0, 1] - a[2, 1])
        if abs(den) < 1e-12: continue
        w0 = ((a[1, 1] - a[2, 1]) * (gx - a[2, 0]) + (a[2, 0] - a[1, 0]) * (gy - a[2, 1])) / den; w1 = ((a[2, 1] - a[0, 1]) * (gx - a[2, 0]) + (a[0, 0] - a[2, 0]) * (gy - a[2, 1])) / den; w2 = 1 - w0 - w1
        k = (w0 >= 0) & (w1 >= 0) & (w2 >= 0); zz = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]; sub = zb[y0:y1 + 1, x0:x1 + 1]; k &= zz < sub
        sub[k] = zz[k]; img[y0:y1 + 1, x0:x1 + 1][k] = BASE * sh[t]
    im = Image.fromarray((img * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    ang = m.face_adjacency_angles; E = m.face_adjacency_edges[ang > np.radians(25)]
    fa = m.face_adjacency[ang > np.radians(25)]; vis = (n[fa[:, 0]] @ d < 0) | (n[fa[:, 1]] @ d < 0)
    for (i, j), v in zip(E, vis):   # 보이는 모서리만(깊이 버퍼로 가려짐 확인)
        if not v: continue
        p, q = px[i], px[j]; zm = (z[i] + z[j]) / 2; c = ((p + q) / 2).astype(int)
        if 0 <= c[0] < S and 0 <= c[1] < S and zm > zb[c[1], c[0]] + 0.01 * ext * 2: continue
        dr.line([tuple(p), tuple(q)], fill=(0, 0, 0), width=1)
    return im
DIRS = [(1, -1, 1), (-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1), (-1, -1, -1), (-1, 1, -1)]   # 데이터셋 시험 표본 6 개 회색 차 투표로 맞춤(10-06)
def views(m, dirs=DIRS): return [render(m, d) for d in dirs]
