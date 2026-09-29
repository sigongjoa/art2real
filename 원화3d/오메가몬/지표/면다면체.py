# -*- coding: utf-8 -*-
"""면 다면체 — 「다른 방법」(2026-09-30): 셀화의 닫힌 면 = **평면 조각**, 선 = 조각이 맞닿는 모서리. 정면 면 그림을 선화 다면체로 읽고(Sugihara · Lipson–Shpitalni 식) 깊이는 옆 캡처의 면 경계에서 앵커로.
    python 면다면체.py -> out/오메가몬2/자료/다면체/정면.stl(면 = 정면 영역 번호) · 면다면체.png(정면 · 3/4 · 옆 오버레이 + 렌더) · 면다면체.json(꼭짓점 z · 앵커 · 시점별 IoU)
미지수: 꼭짓점 z(정면 그림의 x · y 는 안다) + 면마다 평면(a · b · c).  식: ① 꼭짓점이 닿는 모든 면의 평면 위에 있다(모서리 공유 = 옛 판 밀기와 다른 점) ② 옆 앵커(정면 꼭짓점 (x,y) 를 옆 자세로 찍어 ② 짝 면들의 경계에 닿는 z) ③ 좌우 거울 면은 거울 평면 ④ 약한 정면 우선(a · b ≈ 0).
정면 회전(5°)은 무시하고 정면 그림 = 정사영으로 둔다. 시각 껍질과 달리 **오목**(눈구멍 · 부리 능선)이 앵커 · 평면으로 생긴다. 판정은 3/4 오버레이 · 시점별 IoU.
"""
import os, sys, json
import numpy as np, cv2, trimesh
from shapely.geometry import Polygon
from trimesh.creation import triangulate_polygon
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기, 읽기
D = J(OUT, "..", "자료"); P = J(D, "다면체"); os.makedirs(P, exist_ok=True); S = 3
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]
자세 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); 자세.update({k: v for k, v in json.load(open(J(D, "면패치_자세.json"), encoding="utf-8")).items() if k in 자세}) if os.path.exists(J(D, "면패치_자세.json")) else None
시점 = {"02_정면": "정면 yt_172", "02_3-4": "3/4 M04", "02_옆": "옆 yt_235"}; 라벨 = {t: np.load(J(D, t + "_영역.npz"))["라벨"] for t in 시점}
F = 자세["정면 yt_172"]; L = 라벨["02_정면"]; H, W = L.shape
단위 = lambda p: np.stack([(p[..., 0] / S - F["t"][0]) / F["s"], (p[..., 1] / S - F["t"][1]) / F["s"]], -1)          # 정면 3× px → 정면 카메라 틀 x · y (k ≈ 0)
Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]
def 모델틀(x, y, z앞):
    """정면 카메라 틀 (x, y, z앞: 카메라 쪽 +) → 머리 단위 틀(찍기의 역: C = (U·(1,1,−1))·Rᵀ)"""
    C = np.stack([np.asarray(x, float), np.asarray(y, float), -np.asarray(z앞, float)], -1); return (C @ Rf) * (1, 1, -1)
# ── 면 다각형 · 꼭짓점 ──
전체 = float((L > 0).sum()); ids = [int(i) for i in np.unique(L) if i > 0 and (L == i).sum() > 0.002 * 전체]
다각 = {}
for i in ids:
    cs, _ = cv2.findContours((L == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea)
    다각[i] = cv2.approxPolyDP(c, 5.0, True)[:, 0, :].astype(float)
점 = np.concatenate(list(다각.values())); 대표 = -np.ones(len(점), int); V = []
for k in range(len(점)):                                                                             # 15 px(3×) 안 꼭짓점은 하나로(모서리 공유 · 이웃 면 윤곽은 먹선만큼 떨어져 있다)
    if 대표[k] >= 0: continue
    근 = np.nonzero((대표 < 0) & (np.linalg.norm(점 - 점[k], axis=1) < 15))[0]; 대표[근] = len(V); V.append(점[근].mean(0))
V = np.array(V); 면꼭 = {}; k = 0
for i in ids: n = len(다각[i]); 면꼭[i] = [int(v) for v in 대표[k:k + n]]; k += n
닿음 = {v: set() for v in range(len(V))}                                                            # 꼭짓점이 닿는 면(3 px 불린 면 안) — T 자 접점도 잡힌다
for i in ids:
    m = cv2.dilate((L == i).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    for v in range(len(V)):
        x, y = np.round(V[v]).astype(int)
        if m[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]: 닿음[v].add(i)
U = 단위(V); print("면 %d · 꼭짓점 %d · 닿음 평균 %.2f" % (len(ids), len(V), np.mean([len(s) for s in 닿음.values()])))
# ── 이름 → 옆 · 3/4 면 ──
부품 = {}
for n, 짝 in 선택.items():
    for i in (짝.get("정면") or []): 부품[i] = n
옆ids = {n: 짝.get("옆") for n, 짝 in 선택.items()}; 옆이름 = json.load(open(J(D, "자료3D3_옆이름.json"), encoding="utf-8")); 옆ids["눈구멍L"] = 옆이름["눈"]; 삼사ids = {n: 짝.get("3-4") for n, 짝 in 선택.items()}
# ── 옆 앵커: 정면 꼭짓점 (x,y) 를 z 를 바꿔 가며 옆 자세로 찍어, 짝 면들의 경계(또는 가운데 줄이면 옆 실루엣 앞선)에 닿는 z ──
Ls = 라벨["02_옆"]; 옆자 = 자세["옆 yt_235"]; 옆sil = 읽기(J(D, "02_옆_실루엣.png"))[:, :, 0] > 127
거리 = lambda m: cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 3)
def 경계(a_ids, b_ids):
    k7 = np.ones((7, 7), np.uint8); return 거리((cv2.dilate(np.isin(Ls, a_ids).astype(np.uint8), k7) > 0) & (cv2.dilate(np.isin(Ls, b_ids).astype(np.uint8), k7) > 0))
def 앞선(sil):
    e = sil & ~(cv2.erode(sil.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0); return 거리(cv2.resize(e.astype(np.uint8), (Ls.shape[1], Ls.shape[0]), interpolation=cv2.INTER_NEAREST) > 0)
zs = np.arange(-60, 71, 0.5); 앵커 = {}; 앵커출처 = {}
def z찾기(v, 표적, 허용=36):
    """표적(경계 화소 집합)까지의 거리 변환에서 가장 가까운 z · 허용(3× px) 밖이면 없음. 같은 거리면 앞쪽(z 큰) 것"""
    P3 = 모델틀(np.full_like(zs, U[v, 0]), np.full_like(zs, U[v, 1]), zs); uv, _ = 찍기(P3, 옆자); p = np.round(uv * S).astype(int)
    ok = (p[:, 0] >= 0) & (p[:, 0] < Ls.shape[1]) & (p[:, 1] >= 0) & (p[:, 1] < Ls.shape[0]); d = np.full(len(zs), 1e9); d[ok] = 표적[p[ok, 1], p[ok, 0]]
    if d.min() > 허용: return None
    near = np.nonzero(d <= d.min() + 1.5)[0]; return float(zs[near].max())
캐시 = {}
for v in range(len(V)):
    parts = sorted({부품[i] for i in 닿음[v] if i in 부품 and 옆ids.get(부품[i])})
    if len(parts) >= 2:
        key = tuple(parts[:2]); 캐시.setdefault(key, 경계(옆ids[parts[0]], 옆ids[parts[1]])); z = z찾기(v, 캐시[key])
        if z is not None: 앵커[v] = z; 앵커출처[v] = "경계 %s|%s" % key; continue
    if abs(U[v, 0]) < 3.0 and len(닿음[v]) >= 1:
        캐시.setdefault("앞선", 앞선(옆sil)); z = z찾기(v, 캐시["앞선"])
        if z is not None: 앵커[v] = z; 앵커출처[v] = "가운데 앞선"
print("앵커 %d / %d" % (len(앵커), len(V)), {k: sum(1 for s in 앵커출처.values() if s == k or s.startswith(k[:2])) for k in ("경계", "가운데")})
# ── 거울 짝(정면 x 부호) ──
cx0 = float(np.mean([U[v, 0] for i in ids if i in 부품 and 부품[i] == "뿔" for v in 면꼭[i]])) if any(부품.get(i) == "뿔" for i in ids) else 0.0
중심 = {i: U[면꼭[i]].mean(0) for i in ids}; 거울 = {}
for i in ids:
    mx, my = 2 * cx0 - 중심[i][0], 중심[i][1]
    if abs(mx - cx0) < 3: continue
    cand = [j for j in ids if j != i and abs(중심[j][0] - mx) < 4 and abs(중심[j][1] - my) < 4]
    if cand: 거울[i] = cand[0]
# ── 최소제곱: 미지수 [z_v (N) | a_f b_f c_f (3F)] ──
N, Fn = len(V), len(ids); fi = {i: k for k, i in enumerate(ids)}; rows, rhs, w = [], [], []
def 식(계수, b, 가중):
    r = np.zeros(N + 3 * Fn); [r.__setitem__(k, c) for k, c in 계수]; rows.append(r); rhs.append(b); w.append(가중)
for v in range(N):
    for i in 닿음[v]: 식([(v, 1.0), (N + 3 * fi[i], -U[v, 0]), (N + 3 * fi[i] + 1, -U[v, 1]), (N + 3 * fi[i] + 2, -1.0)], 0.0, 1.0)      # ① 평면 위
for v, z in 앵커.items(): 식([(v, 1.0)], z, 3.0)                                                                                        # ② 옆 앵커
for i, j in 거울.items(): 식([(N + 3 * fi[i], 1.0), (N + 3 * fi[j], 1.0)], 0.0, 1.0); 식([(N + 3 * fi[i] + 1, 1.0), (N + 3 * fi[j] + 1, -1.0)], 0.0, 1.0); 식([(N + 3 * fi[i] + 2, 1.0), (N + 3 * fi[j] + 2, -1.0)], 0.0, 1.0)   # ③ 거울(c 는 x 원점 cx0 기준이라 근사)
for i in ids: 식([(N + 3 * fi[i], 1.0)], 0.0, 0.05); 식([(N + 3 * fi[i] + 1, 1.0)], 0.0, 0.05)                                           # ④ 약한 정면 우선
껍질z = {}
if os.path.exists(J(D, "면패치_살.npz")):                                                              # ⑤ 시각 껍질 앞면 = 약한 깊이 사전(바탕) · 앵커 · 평면이 이긴다
    Z = np.load(J(D, "면패치_살.npz")); 살 = Z["살"].reshape(len(Z["xs"]), len(Z["ys"]), len(Z["zs"])); zi = np.where(살, Z["zs"][None, None, :], -1e9).max(2)
    for v in range(N):
        ix, iy = min(max(int(round(U[v, 0] - Z["xs"][0])), 0), 살.shape[0] - 1), min(max(int(round(U[v, 1] - Z["ys"][0])), 0), 살.shape[1] - 1)     # 격자 밖은 가장자리 기둥
        if zi[ix, iy] > -1e8: 껍질z[v] = float(zi[ix, iy]); 식([(v, 1.0)], 껍질z[v], float(os.environ.get("껍질가중", "1.0")))
print("껍질 사전 %d" % len(껍질z))
A = np.array(rows) * np.array(w)[:, None]; b = np.array(rhs) * np.array(w); x, *_ = np.linalg.lstsq(A, b, rcond=None); z = x[:N]; 평면 = {i: x[N + 3 * fi[i]:N + 3 * fi[i] + 3] for i in ids}
잔차 = A @ x - b; print("잔차 RMS %.2f 단위 · z 범위 %.0f..%.0f · 거울 짝 %d" % (np.sqrt(np.mean(잔차 ** 2)), z.min(), z.max(), len(거울)))
# ── 메시 ──
Vs, Fs, 면라벨 = [], [], []
for i in ids:
    poly = U[면꼭[i]]; a, b_, c = 평면[i]
    try: pv, pf = triangulate_polygon(Polygon(poly).buffer(0))
    except Exception: continue
    if len(pf) == 0: continue
    p3 = 모델틀(pv[:, 0], pv[:, 1], a * pv[:, 0] + b_ * pv[:, 1] + c); Fs.append(pf + len(np.concatenate(Vs)) if Vs else pf); Vs.append(p3); 면라벨 += [i] * len(pf)
Vm, Fm = np.concatenate(Vs), np.concatenate(Fs); 면라벨 = np.array(면라벨); 메시 = trimesh.Trimesh(Vm, Fm, process=False); 메시.export(J(P, "정면.stl"))
json.dump(dict(꼭짓점=[[round(float(a), 1) for a in (U[v, 0], U[v, 1], z[v])] for v in range(N)], 앵커={str(v): [round(a, 1), s] for (v, a), s in zip(앵커.items(), 앵커출처.values())}, 평면={str(i): [round(float(a), 3) for a in 평면[i]] for i in ids}, 거울={str(a): b for a, b in 거울.items()}), open(J(D, "면다면체.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# ── 오버레이 · 시점별 IoU ──
ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); rng = np.random.RandomState(5); 색 = {i: tuple(int(c) for c in rng.randint(50, 230, 3)) for i in ids}
def 투영마스크(t, 자, h, w, 축소=1):
    uv, cz = 찍기(Vm, 자); uv = uv / 축소; ID = np.zeros((h, w), np.int32); 삼 = sorted(((cz[f].mean(), k) for k, f in enumerate(Fm)), key=lambda a: -a[0])
    for _, k in 삼: cv2.fillPoly(ID, [np.round(uv[Fm[k]]).astype(np.int32)], int(면라벨[k]))
    return ID
결과 = {}; 판 = []
for t, 자이름 in 시점.items():
    자 = 자세[자이름]; im = 읽기(기록[t]["파일"]); h, w = im.shape[:2]; x0, y0, x1, y1 = 기록[t]["상자"]; ID = 투영마스크(t, 자, h, w); Lt = cv2.resize(라벨[t], (w, h), interpolation=cv2.INTER_NEAREST); 결과[t] = {}
    for n, 짝 in 선택.items():
        f_ids = 짝.get("정면") or []; g_ids = {"02_정면": f_ids, "02_3-4": 짝.get("3-4"), "02_옆": 짝.get("옆")}[t]
        if not f_ids or not g_ids: continue
        a, b_ = np.isin(ID, f_ids), np.isin(Lt, g_ids); 결과[t][n] = round(float((a & b_).sum() / max(1, (a | b_).sum())), 3)
    ov = im.copy()
    for i in ids: ov[ID == i] = 색[i][::-1]
    vis = cv2.addWeighted(im, 0.45, ov, 0.55, 0); vis[(cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0) & (ID > 0)] = (0, 0, 0)
    e = (cv2.Laplacian(Lt.astype(np.float32), cv2.CV_32F) != 0) & (Lt > 0); vis[e] = (255, 255, 255)
    p_ = Image.fromarray(vis[y0:y1, x0:x1, ::-1]); p_ = p_.resize((int(p_.width * 600 / p_.height), 600)); ImageDraw.Draw(p_).text((6, 6), "%s 다면체(색 · 검은 모서리) vs 캡처 면(흰)" % t, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255)); 판.append(p_)
    print(t, " ".join("%s %.2f" % kv for kv in 결과[t].items()))
json.dump(dict(시점별IoU=결과, 앵커수=len(앵커), 승인="Claude(사용자 미확인) · 오버레이로 판정"), open(J(D, "면다면체_점수.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def 렌더(yaw, Wd=600, Hd=600, s=4.2):
    th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); Vv = Vm @ R.T; uv = np.stack([Vv[:, 0] * s + Wd / 2, (Vv[:, 1] + 40) * s + 20], 1); zc = Vv[:, 2]
    Nn = 메시.face_normals @ R.T; sh = np.clip(0.5 + 0.5 * (Nn @ np.array([-0.4, -0.5, 0.75])), 0.25, 1); im = np.full((Hd, Wd, 3), 245, np.uint8)
    for k in sorted(range(len(Fm)), key=lambda k: -zc[Fm[k]].mean()): cv2.fillPoly(im, [np.round(uv[Fm[k]]).astype(np.int32)], tuple(int(c * sh[k]) for c in (200, 200, 200)))
    ID = np.zeros((Hd, Wd), np.int32)
    for k in sorted(range(len(Fm)), key=lambda k: -zc[Fm[k]].mean()): cv2.fillPoly(ID, [np.round(uv[Fm[k]]).astype(np.int32)], int(면라벨[k]))
    im[(cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0) & (ID > 0)] = (40, 40, 40); return Image.fromarray(im)
for 이름_, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
    r = 렌더(yaw); ImageDraw.Draw(r).text((6, 6), "다면체 · " + 이름_, font=ft, fill=(0, 0, 0)); 판.append(r)
W_ = sum(p_.width for p_ in 판[:3]) + 20; 시트 = Image.new("RGB", (max(W_, 3 * 610), 1210), (250, 250, 248)); x = 0
for p_ in 판[:3]: 시트.paste(p_, (x, 0)); x += p_.width + 10
for k, p_ in enumerate(판[3:]): 시트.paste(p_, (k * 610, 610))
시트.save(J(D, "면다면체.png")); print(J(D, "면다면체.png"))
