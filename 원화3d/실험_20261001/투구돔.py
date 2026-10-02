# -*- coding: utf-8 -*-
"""부조에 투구 돔(아모달 · 가장 단순한 모양)을 채워 옆 원형성 비교 (10-02 사용자 「측면에서도 어느 정도 원형성이 있어야 하는데 · 투구랑 비교는 해 봤어?」).
돔 = 초타원체(지수 2.5) · 폭 = 정면 투구 돔+이마+볼날개 칸 폭(눈 높이 위) · 높이 = 돔 꼭대기 ~ 턱 · 앞뒤 = 49 단위(옆 원화 숫자 하나) · 앞면 = 부조의 돔 칸 앞면 바로 뒤.
옆 실루엣 셋(부조만 · 돔+부조 · 옆 원화)을 각자 자기 틀(높이 맞춤 · 얼굴 왼쪽)에 겹쳐 IoU. 출력 out/오메가몬2/지표/부조/투구돔.ply · 옆실루엣_비교.png"""
import os, json, numpy as np, cv2, trimesh
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "부조")
rel = trimesh.load(os.path.join(O, "부조.ply"), process=False)
Lf = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; ys, xs = np.nonzero(Lf > 0); top, bot = ys.min(), ys.max(); k = 100 / (bot - top)
x0, y0, x1, y1 = json.load(open(os.path.join(K, "원화그림자", "그림자.json"), encoding="utf-8"))["자르기"]
그래프 = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8"))
def 칸(*이름): return [n for p in 그래프["부품"] if p["이름"].split("/")[0] in 이름 for n in p["칸"]]
dome_c = np.isin(Lf, 칸("투구 돔")); shell = np.isin(Lf, 칸("투구 돔", "이마판", "볼날개"))
# 부조 좌표: X = (px − 화면 가운데) · k · 블렌더 z = −(py − y0) · k · 블렌더 y = −깊이(앞이 음수)
def bx(px): return (px - Lf.shape[1] / 2) * k
def bz(py): return -(py - y0) * k
dy_, dx_ = np.nonzero(dome_c); sy, sx = np.nonzero(shell)
eye_row = int(np.median(np.nonzero(np.isin(Lf, 칸("눈")))[0])); band = sx[sy < eye_row]
xa, xb = bx(np.percentile(band, 2)), bx(np.percentile(band, 98)); za, zb = bz(dy_.min()), bz(bot)
V = rel.vertices; near = (V[:, 0] > xa) & (V[:, 0] < xb) & (V[:, 2] < za) & (V[:, 2] > za - 15); front = np.percentile(V[near, 1], 70)   # 돔 칸 앞면(블렌더 y · 작을수록 앞)
a, c = (xb - xa) / 2, (za - zb) / 2; b = 49 / 2; C = np.array([(xa + xb) / 2, front + 3 + b, (za + zb) / 2])
s = trimesh.creation.uv_sphere(1.0, count=[64, 64]); P = s.vertices; e = 2.5
r = (np.abs(P[:, 0]) ** e + np.abs(P[:, 1]) ** e + np.abs(P[:, 2]) ** e) ** (1 / e); s.vertices = P / r[:, None] * np.array([a, b, c]) + C
s.visual.vertex_colors = np.tile([205, 210, 225, 255], (len(s.vertices), 1)); s.export(os.path.join(O, "투구돔.ply"))
# 옆 실루엣(블렌더 y = 앞뒤 · z = 위) — 꼭짓점 · 면 칠하기
def 실루엣(meshes, n=400):
    pts = np.vstack([m.vertices for m in meshes]); y, z = pts[:, 1], pts[:, 2]; lo = np.array([y.min(), z.min()]); sc = (n - 1) / max(np.ptp(y), np.ptp(z))
    img = np.zeros((n, n), np.uint8)
    for m in meshes:
        T = ((m.vertices[:, [1, 2]] - lo) * sc).astype(np.int32)[m.faces]; T[:, :, 1] = n - 1 - T[:, :, 1]
        for t_ in T: cv2.fillConvexPoly(img, t_, 1)   # 한꺼번에 fillPoly 는 겹친 삼각형을 홀짝으로 지움(점무늬 원인)
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))   # 작은 면 칠하기 구멍 메움
def 틀(m, 얼굴왼=True):
    ys_, xs_ = np.nonzero(m); m = m[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
    if not 얼굴왼: m = m[:, ::-1]
    h = 200; w = max(1, int(m.shape[1] * h / m.shape[0])); m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST); c_ = np.zeros((h, 260), np.uint8); c_[:, :min(w, 260)] = m[:, :260]; return c_ > 0
부조만 = 실루엣([rel]); 돔부조 = 실루엣([rel, s])
# 머리만(뿔 · 안테나 빼고): 높이 범위를 돔 꼭대기 ~ 턱으로 자름
def 자름(img, meshes):
    pts = np.vstack([m.vertices for m in meshes]); z = pts[:, 2]; n = img.shape[0]; sc = (n - 1) / max(np.ptp(pts[:, 1]), np.ptp(z))
    r0 = int(n - 1 - (za - z.min()) * sc); out = img.copy(); out[:max(0, r0)] = 0; return out
부조만, 돔부조 = 자름(부조만, [rel]), 자름(돔부조, [rel, s])
Ls = np.load(os.path.join(K, "선파츠_옆.npz"))["라벨"]; 옆 = cv2.morphologyEx((Ls > 0).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
# 블렌더 y 는 앞이 작음 → 그림 왼쪽이 앞 · 옆 원화는 얼굴이 −x(왼쪽) (더미머리5_칸 확인)
A, B, S_ = 틀(부조만), 틀(돔부조), 틀(옆)
iou = lambda p, q: round(float((p & q).sum() / (p | q).sum()), 3)
res = {"부조만_vs_옆원화": iou(A, S_), "돔+부조_vs_옆원화": iou(B, S_)}
def 겹(p, q):
    v = np.full(p.shape + (3,), 255, np.uint8); v[p & ~q] = (230, 110, 60); v[q & ~p] = (60, 60, 230); v[p & q] = (150, 150, 150); return cv2.resize(v, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
out = np.hstack([겹(A, S_), np.full((400, 20, 3), 255, np.uint8), 겹(B, S_)]); cv2.imencode(".png", out)[1].tofile(os.path.join(O, "옆실루엣_비교.png"))
json.dump({**res, "돔": {"폭": round(2 * a, 1), "앞뒤": 49, "높이": round(2 * c, 1)}}, open(os.path.join(O, "투구돔.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(res, "돔 폭 · 앞뒤 · 높이", round(2 * a, 1), 49, round(2 * c, 1))
