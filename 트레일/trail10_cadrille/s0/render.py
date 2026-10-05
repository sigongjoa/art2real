# -*- coding: utf-8 -*-
"""open3d Visualizer 가 이 PC 에서 세그폴트 → 같은 카메라(앞 방향 · 거리 0.9 · 바라보는 점 0.5 · 시야 60°)로 numpy 래스터라이저.
색은 cadrille 학습 렌더와 같은 (255,255,136) · 흰 바탕 · 카메라 쪽 빛(디퓨즈 0.7 + 앰비언트 0.3)."""
import numpy as np
from PIL import Image
def render(V, F, front, dist=-0.9, W=500, img_size=128, fov=60.0):
    lookat = np.array([0.5, 0.5, 0.5]); f = np.array(front, float); up = np.array([0, 1.0, 0])
    eye = lookat + f * dist; right = np.cross(up, f); right /= np.linalg.norm(right); tup = np.cross(f, right)
    Rm = np.stack([right, tup, f]); P = (V - eye) @ Rm.T            # 카메라 좌표: z = 앞(+f 방향이 화면 안쪽)
    P[:, 2] = P[:, 2] / np.linalg.norm(f)
    fpx = (W / 2) / np.tan(np.radians(fov / 2))
    z = P[:, 2]; x = fpx * P[:, 0] / z + W / 2; y = -fpx * P[:, 1] / z + W / 2
    img = np.ones((W, W, 3)); zb = np.full((W, W), np.inf); base = np.array([255, 255, 136]) / 255.0
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    ldir = -f / np.linalg.norm(f); shade = 0.3 + 0.7 * np.abs(n @ ldir)
    for t in range(len(F)):
        i0, i1, i2 = F[t]; xs = np.array([x[i0], x[i1], x[i2]]); ys = np.array([y[i0], y[i1], y[i2]]); zs = np.array([z[i0], z[i1], z[i2]])
        if (zs <= 0).any(): continue
        x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1); y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, W - 1)
        if x0 > x1 or y0 > y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12: continue
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d; b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d; c = 1 - a - b
        m = (a >= 0) & (b >= 0) & (c >= 0)
        if not m.any(): continue
        zz = a * zs[0] + b * zs[1] + c * zs[2]; sub = zb[y0:y1 + 1, x0:x1 + 1]; w = m & (zz < sub)
        sub[w] = zz[w]; img[y0:y1 + 1, x0:x1 + 1][w] = base * shade[t]
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((img_size, img_size), Image.LANCZOS)
    return im
