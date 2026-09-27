# -*- coding: utf-8 -*-
"""EG RX-78-2 정강이 반쪽(흰 · B3/B4)을 부품 사진의 옆 실루엣에서 짓고, 거울 짝 부품(다른 실물)으로 잰다 (2026-09-27).

    python 정강이.py -> out/키트/EG_RX78/정강이/정강이.stl · 결과.json · 정강이_실물대조.png

입체 부품 첫 시험. 크기 임의(L = 60 mm) · 형태 보존.
  옆 실루엣 = 부품 나열 사진(옆면이 위) · 두께(좌우) = 완성 정면 사진에서 읽은 폭/길이 0.23 의 반 · 겉면 둥글림 · 종아리 돔은 사진 음영으로 읽은 물방울 윤곽 — 높이는 가정.
  껍질 두께 · 돔 높이 · 둥글림 반지름은 가정값(사진에 깊이가 없다)."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image
from scipy import ndimage
from skimage import measure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 키트부품 as KP, 방패 as B
import 디테일대조 as DD
from 메시출력 import 부채나누기

D = KP.D; OUT = os.path.join(D, "정강이"); os.makedirs(OUT, exist_ok=True)
L = 60.0
반두께, 벽, 가장자리몫, 둥글r, 돔높이, 돔r = 0.115, 0.025, 0.30, 0.07, 0.035, 0.09      # 정규(L 배)
물방울 = [(-0.05, 0.89), (0.05, 0.86), (0.095, 0.72), (0.08, 0.60), (0.0, 0.43), (-0.03, 0.41), (-0.12, 0.50), (-0.19, 0.64), (-0.18, 0.78), (-0.12, 0.87)]   # 종아리 돔 윤곽(사진 음영에서 읽음)
발목구멍 = (0.02, 0.072, 0.022); 무릎원 = (0.0, 0.925, 0.058)
K = 4   # 마스크 올림 배율

def 매끈마스크(겉):
    big = ndimage.zoom(겉.astype(float), K, order=1); return ndimage.gaussian_filter(big, 1.5 * K / 2) > 0.5
def 격자좌표(shape):
    H, W = shape; return H, W, W / 2
def 다각형(mask):
    """윤곽 → 닫힌 곡선을 둘레 방향으로 가우스(σ 5 점)로 펴고 → RDP. 136 px 마스크의 화소 계단을 그대로 따르면 윤곽이 들쭉날쭉했다(첫 판)."""
    H, W, cx = 격자좌표(mask.shape); c = max(measure.find_contours(np.pad(mask, 1).astype(float), 0.5), key=len) - 1
    c = ndimage.gaussian_filter1d(c[:-1], 5.0, axis=0, mode="wrap")
    P = np.c_[(c[:, 1] - cx) / H, (H - c[:, 0]) / H]; return B.rdp(np.vstack([P, P[:1]]), 0.003)[:-1]
def 잘게(P, n=3):
    """Chaikin 모서리 깎기 n 번 — 읽은 꼭짓점 다각형을 매끈한 닫힌 곡선으로."""
    P = np.asarray(P, float)
    for _ in range(n):
        Q = np.roll(P, -1, 0); P = np.vstack([np.c_[0.75 * P + 0.25 * Q], np.c_[0.25 * P + 0.75 * Q]]).reshape(2, -1, 2).transpose(1, 0, 2).reshape(-1, 2)
    return P
def 표본(장, mask_shape, u, v):
    H, W, cx = 격자좌표(mask_shape); r = np.clip((1 - v) * H - 0.5, 0, H - 1); c = np.clip(u * H + cx - 0.5, 0, W - 1)
    return ndimage.map_coordinates(장, [r, c], order=1, mode="nearest")
def 기둥x(poly, x0, x1):
    e = M.CrossSection([B.반시계(poly).tolist()]).extrude(x1 - x0)
    return e.transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
def 원(c, r, n=32): return np.array([(c[0] + r * np.cos(t), c[1] + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)])

def 짓기():
    g = np.load(os.path.join(D, "정강이_정답.npz")); mask = 매끈마스크(g["겉"]); H = mask.shape[0]
    P = 다각형(mask); 거리 = ndimage.distance_transform_edt(mask) / H                     # 윤곽까지 거리(L 배)
    mm = lambda q: np.asarray(q, float) * L
    a0, t = 반두께 * L, 벽 * L
    겉 = 기둥x(mm(P), 0.0, a0)
    안cs = M.CrossSection([B.반시계(mm(P)).tolist()]).offset(-t, M.JoinType.Round)
    안 = 안cs.extrude(a0 - t + 1.0).transform(np.array([[0, 0, 1, -1.0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
    m = 겉 - 안
    m = m - 기둥x(mm(원(발목구멍[:2], 발목구멍[2])), -1, a0 + 1)                              # 발목 축 구멍(관통)
    원판 = 기둥x(mm(원(무릎원[:2], 무릎원[2], 48)), a0 - 0.2, a0 + 0.018 * L)                    # 무릎 원판(0.018 L 솟음) + 일자 홈
    홈 = 기둥x(mm(np.array([(무릎원[0] - 0.045, 무릎원[1] - 0.007), (무릎원[0] + 0.045, 무릎원[1] - 0.007), (무릎원[0] + 0.045, 무릎원[1] + 0.007), (무릎원[0] - 0.045, 무릎원[1] + 0.007)])), a0 + 0.008 * L, a0 + 1)
    m = ((m + 원판) - 홈).refine_to_length(0.5)
    # 물방울 돔 거리장
    Hh, Ww = mask.shape; yy, xx = np.mgrid[0:Hh, 0:Ww]; uu = (xx + 0.5 - Ww / 2) / Hh; vv = 1 - (yy + 0.5) / Hh
    from matplotlib.path import Path
    안쪽 = Path(잘게(물방울)).contains_points(np.c_[uu.ravel(), vv.ravel()]).reshape(Hh, Ww)
    돔거리 = ndimage.gaussian_filter(ndimage.distance_transform_edt(안쪽) / Hh, 4.0); 돔최대 = float(돔거리.max())
    거리 = ndimage.gaussian_filter(거리, 3.0)
    def 둥근(d, r): return np.sqrt(np.clip(1 - (1 - np.clip(d / r, 0, 1)) ** 2, 0, 1))
    def 부풀림(V):
        u, v = V[:, 1] / L, V[:, 2] / L; d = 표본(거리, mask.shape, u, v); dd = 표본(돔거리, mask.shape, u, v)
        f = 가장자리몫 + (1 - 가장자리몫) * 둥근(d, 둥글r)                                     # 겉면 둥글림: 가장자리에서 벽 높이 0.3 → 안쪽 1
        x = V[:, 0] * f + np.clip(V[:, 0] / a0, 0, 1) * 돔높이 * L * 둥근(dd, 돔최대)          # 돔: 가장자리 0 → 가운데 최대(고원 없이)
        return np.c_[x, V[:, 1], V[:, 2]]
    return m.warp_batch(부풀림), P

def 옆실루엣(tm, H=400):
    """+x 에서 본 실루엣을 정규 격자로 (화면 X = u, Y = v)."""
    V = np.c_[tm.vertices[:, 1], tm.vertices[:, 2], tm.vertices[:, 0]]; s = L / H; W = int(0.7 * H)
    _, tid = DD.래스터(V, tm.faces, W / 2, H, s, max(W, H) + 2)
    return (tid >= 0)[:H, :W]
def 정답(이름, H=400):
    g = np.load(os.path.join(D, 이름 + "_정답.npz")); r = 매끈마스크(g["겉"]); k = H / r.shape[0]
    r = np.array(Image.fromarray((r * 255).astype(np.uint8)).resize((max(1, int(round(r.shape[1] * k))), H), Image.BILINEAR)) > 127
    W = int(0.7 * H); o = np.zeros((H, W), bool); c0 = (W - r.shape[1]) // 2; o[:, c0:c0 + r.shape[1]] = r
    return o
def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
def 맞춤(겉, 모):
    """좌우 뒤집힘 + ±6 화소 이동 중 가장 잘 맞는 것(사진마다 상자 · 중심이 조금 다르다)."""
    best = (0, None)
    for f in (lambda a: a, lambda a: a[:, ::-1]):
        for dx in range(-24, 25, 2):
            g = np.roll(f(겉), dx, 1); s1 = iou(g, 모)
            if s1 > best[0]: best = (s1, g)
    return best

if __name__ == "__main__":
    m, P = 짓기(); g = m.to_mesh(); tm = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
    fn = os.path.join(OUT, "정강이.stl"); tm.export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.04, 0.08):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    tm = trimesh.load(fn); 모 = ndimage.binary_fill_holes(옆실루엣(tm))
    결과 = dict(L_mm=L, 닫힘=닫힘, 부피mm3=round(m.volume(), 1), 무게g=round(m.volume() * 1.24e-3, 2), 윤곽꼭짓점=len(P), 크기mm=np.round(tm.extents, 1).tolist(),
              가정=dict(반두께=반두께, 벽=벽, 둥글r=둥글r, 돔높이=돔높이))
    그림 = []
    for 라벨, 이름 in (("짓는 데 쓴 부품", "정강이"), ("held-out(거울 짝 부품)", "정강이_짝")):
        s1, 겉 = 맞춤(정답(이름), 모); 결과[라벨] = dict(옆실루엣IoU=round(s1, 4))
        img = np.ones(겉.shape + (3,)); img[겉 & 모] = (0.6, 0.85, 0.6); img[겉 & ~모] = (0.9, 0.2, 0.2); img[~겉 & 모] = (0.2, 0.3, 0.9); 그림.append((img * 255).astype(np.uint8))
    Image.fromarray(np.concatenate(그림, 1)).save(os.path.join(OUT, "대조.png"))
    json.dump(결과, open(os.path.join(OUT, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(결과, ensure_ascii=False, indent=1))
