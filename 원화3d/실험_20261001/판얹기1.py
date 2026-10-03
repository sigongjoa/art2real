# -*- coding: utf-8 -*-
"""판 얹기 1 판 (10-03 사용자 「ㄱㄱ · 그리고 뽑은 데이터를 활용하는 거야?」 · 깎기 1 판 실패 → 메카는 깎기 말고 판 얹기).
뽑은 데이터를 그대로 쓴다 — 어디서 무엇을:
  판 모양 = 정면 원화 먹선 칸(각도데이터/1.npz) + 칸 이름 → 부품 ID(부품ID.json 대응표: 마스크 · 차양 · 이마 · 눈구멍)
  판 위의 꺾임 = 정면 접힌 판(판_1_Z · 셀 그림자 → 면 방향)의 잔 꺾임(− 흐림 σ 10)
  판의 앞뒤 자리 = 블록아웃 B(옆 원화 다섯 점 맞춤 0.745 · −22.3° 에서 나온 부리 쐐기 · 투구 타원체)의 앞면
       마스크 판은 부리 쐐기 앞면에(옆의 부리 돌출) · 차양 · 이마 판은 투구 겉면보다 앞에(처마 12 · 가정) · 눈구멍 칸은 판을 비움(속머리 · 눈이 보임)
  뿔 · 안테나 · 투구 · 속머리 · 눈 · 볼날개 = 디테일 1 판 그대로
색 = 정면 원화 색(판이 칸 그대로라 무늬 · 그림자가 판 위에 맞음).
출력 out/오메가몬2/블렌더/판얹기1.ply · 판얹기1_비교.png"""
import os, json, numpy as np, trimesh, cv2
from scipy import ndimage
from scipy.spatial import ConvexHull
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "디테일1.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)                  # 디테일 1 판(블록아웃 B 포함) — parts · cen · rad · beak · f · cu · O · B
GG = G["G"]   # 디테일1 안의 블록아웃 B 이름공간
O, B, cu, cen, rad, beak = GG["O"], G["B"], GG["cu"], G["cen"], G["rad"], G["beak"]
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]["1"]
z = np.load(os.path.join(O, "1.npz")); L = z["라벨"]; ys_, xs_ = np.nonzero(L > 0); y0, x0 = ys_.min(), xs_.min()
m1 = np.load(os.path.join(O, "판_1_Z.npz")); M, Z1 = m1["m"], m1["Z"]; H, W = M.shape
py, px = np.mgrid[0:H, 0:W]; cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * M
def 칸(부품, 표면=None):
    cs = [c for e in 대응 if e.get("부품") == 부품 and (표면 is None or e.get("표면") in 표면) for c in e["칸"]]; return np.isin(cell, cs) & M
마스크 = 칸("H02 마스크"); 차양 = 칸("H01 투구 껍질", ("차양", "이마")); 구멍 = 칸("H03 눈 조립")
Zf = np.where(np.isfinite(Z1), Z1, np.nanmean(Z1[M])); rel = Zf - ndimage.gaussian_filter(Zf, 10)        # + = 보는 쪽으로
X = px - cu; Zw = -py.astype(float)
# 부리 쐐기 앞면 깊이(정면에서 쏜 광선이 처음 닿는 곳)
h = ConvexHull(beak.vertices); A_, b_ = h.equations[:, :3], h.equations[:, 3]; ds = np.arange(-140, 80, 1.0)
def 쐐기앞(xv, zv):
    out = np.full(xv.shape, np.nan)
    for d in ds[::-1]:
        inside = np.all(np.stack([xv, np.full(xv.shape, d), zv], -1) @ A_.T + b_ <= 1.0, axis=-1); out[inside] = d
    return out
def 겉(xv, zv):
    q = 1 - ((xv - cen[0]) / rad[0]) ** 2 - ((zv - cen[2]) / rad[2]) ** 2; return cen[1] - rad[1] * np.sqrt(np.clip(q, 0.02, 1))
깊이 = np.full((H, W), np.nan)
wm = 쐐기앞(X, Zw); 깊이[마스크] = wm[마스크]
깊이[마스크 & np.isnan(wm)] = 겉(X, Zw)[마스크 & np.isnan(wm)] - 4          # 쐐기 밖 마스크 칸(볼판 등)은 투구 겉면 조금 앞
깊이[차양] = 겉(X, Zw)[차양] - 12
쓸 = (마스크 | 차양) & ~구멍 & np.isfinite(깊이)
깊이 = 깊이 - np.clip(rel, -6, 6) * 1.2                                   # 판 위 꺾임(접힌 판)
art = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1)[:, :, ::-1]
def 판메시(sel, dep, 두께=4):
    yy, xx = np.nonzero(sel); vid = -np.ones(sel.shape, int); vid[yy, xx] = np.arange(len(yy)); n = len(yy)
    Vf = np.c_[xx - cu, dep[yy, xx], -yy]; Vb = Vf + [0, 두께, 0]
    a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    F = np.r_[np.c_[a[ok], b[ok], c[ok]], np.c_[b[ok], d[ok], c[ok]]]; F = np.r_[F, F[:, ::-1] + n]
    m = trimesh.Trimesh(np.r_[Vf, Vb], F, process=False); col = np.clip(art[yy, xx].astype(float) * 1.3, 0, 255).astype(np.uint8)
    m.visual.vertex_colors = np.c_[np.r_[col, col], np.full(2 * n, 255)].astype(np.uint8); return m
판들 = 판메시(쓸, 깊이)
# 디테일 1 판에서: 마스크 계단 · 차양 판 · 번개 판은 빼고(이번 판이 대신) 나머지 유지
keep = [p for p in G["parts"] if not (np.allclose(p.visual.vertex_colors[0, :3], (225, 228, 238)) and len(p.vertices) < 60) and not np.allclose(p.visual.vertex_colors[0, :3], (180, 184, 196))]
keep = [p for p in G["parts"] if len(p.vertices) > 60 or np.allclose(p.visual.vertex_colors[0, :3], (60, 120, 230)) and len(p.vertices) > 40]   # 투구 · 속머리 · 뿔 · 안테나 · 눈(원판)
all_ = trimesh.util.concatenate(keep + [판들]); all_ = trimesh.Trimesh(all_.vertices, all_.faces, vertex_colors=all_.visual.vertex_colors, process=False)
all_.export(os.path.join(B, "판얹기1.ply"), encoding="ascii")
print({"마스크 칸 화소": int(마스크.sum()), "차양 · 이마": int(차양.sum()), "눈구멍(비움)": int(구멍.sum()), "판 화소": int(쓸.sum()), "남긴 디테일1 부품": len(keep)})
