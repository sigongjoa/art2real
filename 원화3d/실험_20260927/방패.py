# -*- coding: utf-8 -*-
"""EG RX-78-2 방패(빨강 A4-30)를 사진 한 장(부품 나열)에서 짓고, 다른 사진(런너)으로 잰다 (2026-09-27).

    python 방패.py
      -> out/키트/EG_RX78/방패/방패.stl · 대조.png · 결과.json

크기는 임의(길이 L = 70 mm) · 형태는 보존. 짓는 데 쓴 것: d_egx01_j1.jpg 의 방패 실루엣(좌우 대칭화) + 눈으로 읽은 창 · 십자 슬롯 · 꺾임선(정규 좌표).
재는 데 쓴 것(held-out): d_egx01_runner.jpg 의 같은 방패 실루엣 — 다른 촬영. 두께 · 꺾임 깊이는 사진에 없어 가정값(설명서 등각도 눈대중)."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image
from scipy import ndimage
from skimage import measure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 키트부품 as KP
import 디테일대조 as DD

D = KP.D; OUT = os.path.join(D, "방패"); os.makedirs(OUT, exist_ok=True)
L = 70.0                                   # 임의 척도 (mm)
꺾임u, 낙차, 두께, 윗면z, 홈깊이 = 0.125, 0.030, 0.022, 0.050, 0.45     # 정규(L 배) — 옆 면이 꺾이는 u · 가장자리까지 내려가는 양 · 판 두께 (가정)
창 = dict(u=0.093, v0=0.880, v1=0.955)      # 사진에서 읽음(좌우 평균)
십자 = dict(세로=(0.035, 0.578), 가로v=0.352, 가로u=0.110, 폭=0.013)

def 반폭곡선(겉):
    """행마다 좌우 반폭 → v(아래 0 → 위 1) 의 함수. 대칭 부품: 좌우가 0.015 넘게 다르면 한쪽이 덜 잡힌 것(반사광 · 그림자) → 큰 쪽, 아니면 평균."""
    H, W = 겉.shape; cx = W / 2; v, w = [], []
    for r in range(H):
        xs = np.nonzero(겉[r])[0]
        if len(xs) == 0: continue
        a, b = (cx - xs.min()) / H, (xs.max() + 1 - cx) / H
        if min(a, b) < 0.05: continue                                  # 맨 위 · 아래 끝 줄(한쪽만 걸린 줄)
        v.append(1 - (r + 0.5) / H); w.append(max(a, b) if abs(a - b) > 0.015 else (a + b) / 2)
    v, w = np.array(v)[::-1], np.array(w)[::-1]
    return np.r_[0.0, v, 1.0], np.r_[w[0], w, w[-1]]
def rdp(P, tol):
    if len(P) < 3: return P
    a, b = P[0], P[-1]; d = b - a; n = np.linalg.norm(d)
    e = np.abs(np.cross(d, P - a)) / n if n > 0 else np.linalg.norm(P - a, axis=1)
    k = int(np.argmax(e))
    return np.vstack([rdp(P[:k + 1], tol)[:-1], rdp(P[k:], tol)]) if e[k] > tol else np.array([a, b])
def 반시계(q):
    q = np.asarray(q, float); a = 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]); return q if a > 0 else q[::-1]
def 기둥z(poly, z0, z1): return M.CrossSection([반시계(poly).tolist()]).extrude(z1 - z0).translate([0, 0, z0])

def 짓기():
    g = np.load(os.path.join(D, "방패_정답.npz")); v, w = 반폭곡선(g["겉"])
    P = rdp(np.c_[w, v], 0.008)                                      # 직선 다각형
    윤곽 = np.vstack([P, (P * [-1, 1])[::-1]]) * L                   # (x, y) mm · y = 길이 방향
    t, zt = 두께 * L, 윗면z * L
    판 = 기둥z(윤곽, 0.0, t)
    사각 = lambda u0, v0, u1, v1, z0, z1: 기둥z(np.array([(u0, v0), (u1, v0), (u1, v1), (u0, v1)]) * L, z0, z1)
    h = 십자["폭"] / 2; zg = (1 - 홈깊이) * t
    홈 = [사각(-h, 십자["세로"][0], h, 십자["세로"][1], zg, t + 1), 사각(-십자["가로u"], 십자["가로v"] - h, 십자["가로u"], 십자["가로v"] + h, zg, t + 1),
         기둥z(np.array([(0, 십자["가로v"] - 0.03), (0.022, 십자["가로v"]), (0, 십자["가로v"] + 0.03), (-0.022, 십자["가로v"])]) * L, zg, t + 1)]
    홈 += [사각(sx * 십자["가로u"] - 0.012, 십자["가로v"] - 0.009, sx * 십자["가로u"] + 0.012, 십자["가로v"] + 0.009, zg, t + 1) for sx in (-1, 1)]   # 가로 끝 작은 네모
    보스 = [M.Manifold.cylinder(0.35, 0.02 * L, 0.02 * L, 32).translate([sx * 0.128 * L, 0.805 * L, t - 0.05]) for sx in (-1, 1)]
    m = (판 - 사각(-창["u"], 창["v0"], 창["u"], 창["v1"], -1, t + 1) - M.Manifold.batch_boolean(홈, M.OpType.Add)) + M.Manifold.batch_boolean(보스, M.OpType.Add)
    m = m.refine_to_length(0.7)                                       # 홈 · 구멍 · 보스를 판 상태에서 넣고 → 잘게 나눈 뒤 → 한꺼번에 꺾는다
    # 꺾임선은 가운데 축과 나란한 곧은 선(|u| = 꺾임u) · 옆 면은 평면(설명서 그림 · 실물 사진으로 확인 — 「가장자리와 나란」은 내가 잘못 읽은 것)
    a_ = 꺾임u * L; 기울기 = 낙차 / (0.2 - 꺾임u)
    def 꺾기(V):
        위 = np.clip((0.78 * L - V[:, 1]) / (0.03 * L), 0, 1)             # 윗 블록(v > 0.78)은 평평
        return np.c_[V[:, 0], V[:, 1], V[:, 2] + zt - 기울기 * np.maximum(np.abs(V[:, 0]) - a_, 0) * 위]
    return m.warp_batch(꺾기), P
def 위실루엣(tm, H=400):
    """위에서 본 실루엣을 정규 격자(H 행 = 길이 1)로."""
    V = tm.vertices[:, [0, 1, 2]]; F = tm.faces; s = L / H; W = int(0.6 * L / s)
    scr = np.c_[V[:, 0], V[:, 1], V[:, 2]]
    _, tid = DD.래스터(scr, F, W / 2, H, s, max(W, H) + 2)
    return (tid >= 0)[:H, :W]
def 정답실루엣(사진, 상자, H=400):
    im = np.array(Image.open(os.path.join(D, 사진)).convert("RGB")); x0, y0, x1, y1 = 상자
    m = ndimage.binary_closing(KP.색마스크(im[y0:y1, x0:x1], "빨강"), iterations=2)
    # 런너 사진: 부품이 런너 틀에 게이트로 붙어 있다 → 반지름 7 px 열기로 가는 틀 · 게이트를 떼고 가장 큰 덩이(부품)만, 그 덩이를 7 px 되불려 원래 마스크와 교집합
    r_ = 3; disk = np.hypot(*np.mgrid[-r_:r_ + 1, -r_:r_ + 1]) <= r_
    core = ndimage.binary_opening(ndimage.binary_fill_holes(m), disk); lab, n = ndimage.label(core); core = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
    영역 = ndimage.binary_dilation(core, iterations=2)
    겉 = ndimage.binary_fill_holes(m) & 영역; m = m & 영역
    ys, xs = np.nonzero(겉); P = np.c_[xs, ys] - [xs.mean(), ys.mean()]
    w_, v_ = np.linalg.eigh(np.cov(P.T)); 각 = np.degrees(np.arctan2(v_[0, 1], v_[1, 1]))
    out = []
    for mask in (겉, m):
        r = ndimage.rotate(mask.astype(float), -각, reshape=True, order=1) > 0.5
        if mask is 겉: ys, xs = np.nonzero(r); bb = (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)
        r = r[bb[0]:bb[1], bb[2]:bb[3]]; k = H / r.shape[0]
        r = np.array(Image.fromarray((r * 255).astype(np.uint8)).resize((max(1, int(round(r.shape[1] * k))), H), Image.NEAREST)) > 127
        W = int(0.6 * H); o = np.zeros((H, W), bool); c0 = (W - r.shape[1]) // 2; o[:, c0:c0 + r.shape[1]] = r[:, :W - c0] if r.shape[1] <= W else r[:, :W]
        out.append(o)
    return out          # [겉, 색(구멍 뚫린)]
def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))

if __name__ == "__main__":
    m, P = 짓기(); g = m.to_mesh(); tm = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
    fn = os.path.join(OUT, "방패.stl"); tm.export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    if not 닫힘:
        from 메시출력 import 부채나누기
        for 양 in (0.02, 0.04, 0.08):
            부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
            if 닫힘: tm = trimesh.load(fn); break
    모 = 위실루엣(tm); 모겉 = ndimage.binary_fill_holes(모)
    결과 = dict(L_mm=L, 닫힘=닫힘, 부피mm3=round(m.volume(), 1), 윤곽꼭짓점=len(P) * 2, 가정=dict(꺾임u=꺾임u, 낙차=낙차, 두께=두께, 홈깊이=홈깊이))
    그림 = []
    for 이름, 사진, 상자 in (("짓는 데 쓴 사진(j1)", "d_egx01_j1.jpg", KP.부품표["방패"]["상자"]), ("held-out(런너 사진 · 비스듬)", "d_egx01_runner.jpg", (56, 58, 224, 132))):
        겉, 색 = 정답실루엣(사진, 상자); best = None
        for f in (lambda a: a, lambda a: a[::-1], lambda a: a[:, ::-1], lambda a: a[::-1, ::-1]):      # 위아래 · 좌우 뒤집힘 모름 → 가장 잘 맞는 쪽
            s1 = iou(f(겉), 모겉)
            if best is None or s1 > best[0]: best = (s1, f)
        겉, 색 = best[1](겉), best[1](색)
        결과[이름] = dict(실루엣IoU=round(iou(겉, 모겉), 4), 구멍포함IoU=round(iou(색, 모), 4), 정답구멍몫=round(1 - 색.sum() / 겉.sum(), 4), 모델구멍몫=round(1 - 모.sum() / 모겉.sum(), 4))
        img = np.ones(겉.shape + (3,)); img[색 & 모] = (0.6, 0.85, 0.6); img[색 & ~모] = (0.9, 0.2, 0.2); img[~색 & 모] = (0.2, 0.3, 0.9)
        그림.append((img * 255).astype(np.uint8))
    Image.fromarray(np.concatenate(그림, 1)).resize((그림[0].shape[1] * 4, 그림[0].shape[0] * 2)).save(os.path.join(OUT, "대조.png"))
    json.dump(결과, open(os.path.join(OUT, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(결과, ensure_ascii=False, indent=1))
