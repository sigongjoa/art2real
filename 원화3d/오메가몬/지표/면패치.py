# -*- coding: utf-8 -*-
"""⑤ 면 패치 — 바탕(세 시점 실루엣의 시각 껍질) 위에 ② 에서 짝지은 면을 **표면 라벨**로 얹는다 (2026-09-30 · 외부 패널 「2D 면 → 3D 표면 패치」 · 사용자 「베이스 모델에 대해 다시점으로 수정」).
    python 면패치.py -> out/오메가몬2/자료/패치/바탕.stl · 패치_<부품>.stl · 면패치.png(세 시점 오버레이 + 라벨 렌더) · 면패치.json(부품 · 시점별 IoU · 충돌)
바탕: 머리 단위 격자(1 단위) → 시점마다 자세2 자세로 찍어 실루엣 밖이면 깎는다(그림 밖 · 3/4 의 뿔 띠 = 모름 → 안 깎음) → 남은 복셀 = 시각 껍질.
패치: 시점마다 그 카메라에서 **보이는** 표면 복셀(같은 픽셀에서 가장 가까운 것)에 그 시점의 면 라벨(면대응_선택 으로 부품 이름)을 붙인다. 시점끼리 다르면 「충돌」. 부품 = 그 이름의 복셀 덩어리(깊이는 껍질에서 온다 · 지어내지 않음).
잰 것: 부품마다 시점마다 라벨 복셀 투영 vs 캡처 면 마스크 IoU (0.5 밑이면 그 시점에서 그 면이 껍질 위에 안 얹힘).
"""
import os, sys, json
import numpy as np, cv2, trimesh
from skimage.measure import marching_cubes
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기, 읽기
D = J(OUT, "..", "자료"); P = J(D, "패치"); os.makedirs(P, exist_ok=True); S = 3
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]
자세 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); 시점 = {"02_정면": "정면 yt_172", "02_3-4": "3/4 M04", "02_옆": "옆 yt_235"}
# 시점마다 면 번호 → 부품 이름 (② 에서 고른 짝 · 눈구멍R 은 정면에서만 · 거울)
이름 = {t: {} for t in 시점}
for 부품, 짝 in 선택.items():
    for t, 열 in (("02_정면", "정면"), ("02_3-4", "3-4"), ("02_옆", "옆")):
        for i in (짝.get(열) or []): 이름[t][i] = 부품
# ── 바탕: 복셀 깎기 ──
xs, ys, zs = np.arange(-55, 56.0), np.arange(-40, 101.0), np.arange(-60, 71.0); G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3); 살 = np.ones(len(G), bool)      # y 100 = 턱 · 그 밑(목 · 깃)은 머리가 아니다 · 옆 뿔은 x ±55 · z 70 까지
추가 = json.load(open(J(D, "시점추가.json"), encoding="utf-8")) if os.path.exists(J(D, "시점추가.json")) and "--3장" not in sys.argv else {}
for t, v in 추가.items(): 시점[t] = t; 자세[t] = v["자세"]; 기록[t] = dict(파일=v["파일"], 상자=v["상자"])
실루엣 = {}; 모름 = {}
for t, 자이름 in 시점.items():
    sil = 읽기(J(D, t + "_실루엣.png"))[:, :, 0] > 127; 실루엣[t] = sil; m = np.zeros_like(sil)
    if t == "02_3-4":                                                                              # 3/4 실루엣은 뿔이 잘려 있다(배경 성분에 붙음) → 눈 위는 모름
        L = np.load(J(D, t + "_영역.npz"))["라벨"]; r = np.nonzero(np.isin(L, [7, 8]).any(1))[0].min() // S; m[:r] = True
    if t in 추가: m |= 읽기(J(D, t + "_모름.png"))[:, :, 0] > 127; r = max(3, int(0.03 * 100 * 자세[t]["s"])); sil = cv2.dilate(sil.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0; 실루엣[t] = sil
    x0, y0, x1, y1 = 기록[t]["상자"]; b = np.ones_like(m); b[y0:y1, x0:x1] = False; m |= b                    # 상자 밖 = 모름(장마다 실루엣이 덮는 범위가 다르다 · 옆은 턱 밑이 잘림)
    모름[t] = m
def 깎기():
    살 = np.ones(len(G), bool); 거부 = np.zeros(len(G), np.int8)                                       # 추가 장은 표결: 둘 이상이 「밖」이라야 깎는다(자세가 실루엣만으로 잡혀 하나는 틀릴 수 있다)
    for t, 자이름 in 시점.items():                                                                    # 상자 = 머리가 있는 범위(옆은 가로만 · 세로는 턱이 잘려 모름 · 추가 장은 망토 · 프레임에 잘려 안 씀)
        if t in 추가: continue
        x0, y0, x1, y1 = 기록[t]["상자"]; uv, _ = 찍기(G, 자세[자이름]); 살 &= (uv[:, 0] >= x0) & (uv[:, 0] < x1)
        if t != "02_옆": 살 &= (uv[:, 1] >= y0) & (uv[:, 1] < y1)
    for t, 자이름 in 시점.items():
        sil, m = 실루엣[t], 모름[t]; H, W = sil.shape; uv, _ = 찍기(G, 자세[자이름]); u, v = np.round(uv).astype(int).T; 안 = (u >= 0) & (u < W) & (v >= 0) & (v < H)
        밖 = 안.copy(); 밖[안] = ~sil[v[안], u[안]] & ~m[v[안], u[안]]
        if t in 추가: 거부 += 밖
        else: 살 &= ~밖
    return 살 & (거부 < 1)                                                                     # 상자 버그 고친 뒤(09-30) 표결은 안 쓴다 · 장마다 혼자 깎는다
def 겉(살):
    V = 살.reshape(len(xs), len(ys), len(zs)); 속 = V.copy()
    for ax in (0, 1, 2):
        for d in (1, -1): 속 &= np.roll(V, d, axis=ax)
    return (V & ~속).reshape(-1)
def 재투영(t, 자, 점):
    sil = 실루엣[t]; H, W = sil.shape; uv, _ = 찍기(점, 자); p = np.round(uv).astype(int); ok = (p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H)
    m = np.zeros((H, W), np.uint8); m[p[ok, 1], p[ok, 0]] = 1; m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0; roi = ~모름[t]; a, b = m & roi, sil & roi
    return float((a & b).sum() / max(1, (a | b).sum()))
from scipy.optimize import minimize
살 = 깎기(); print("첫 깎기 · 남은 복셀", 살.sum())
for 바퀴 in range(3):                                                                              # ① 재등록: 정면 자세는 고정(기준 틀) · 3/4 · 옆 자세를 껍질 재투영 IoU 로 다시 맞추고 다시 깎는다
    점 = G[겉(살)]
    for t, 자이름 in 시점.items():
        if t == "02_정면" or t in 추가: print("  %s 재투영 IoU %.3f (고정)" % (t, 재투영(t, 자세[자이름], 점))); continue
        자 = 자세[자이름]; p0 = np.r_[자["r"], 자["s"], 자["t"]]; 전 = 재투영(t, 자, 점)
        f = lambda p: -재투영(t, dict(r=p[:3], s=p[3], t=p[4:6], k=자.get("k", 0)), 점)
        best = minimize(f, p0, method="Nelder-Mead", options=dict(maxiter=150, xatol=1e-3, fatol=1e-4, initial_simplex=np.r_[[p0], p0 + np.diag([0.04, 0.04, 0.04, 0.15, 8, 8])]))
        자.update(r=best.x[:3].tolist(), s=float(best.x[3]), t=best.x[4:6].tolist()); print("  %s 재투영 IoU %.3f → %.3f" % (t, 전, -best.fun))
    살 = 깎기(); print("바퀴 %d · 남은 복셀 %d" % (바퀴 + 1, 살.sum()))
json.dump(자세, open(J(D, "면패치_자세.json"), "w", encoding="utf-8"), indent=1); np.savez_compressed(J(D, "면패치_살.npz"), 살=살, xs=xs, ys=ys, zs=zs)
V = 살.reshape(len(xs), len(ys), len(zs))
# ── 패치: 시점마다 보이는 표면 복셀에 라벨 ──
idx = np.nonzero(살)[0]; 라벨 = {t: np.zeros(len(G), np.int32) for t in 시점}; 부품목록 = sorted({n for d in 이름.values() for n in d.values()}); 번호 = {n: i + 1 for i, n in enumerate(부품목록)}
for t, 자이름 in 시점.items():
    if t in 추가: continue
    자 = 자세[자이름]; L = np.load(J(D, t + "_영역.npz"))["라벨"]; uv, cz = 찍기(G[idx], 자); q = np.round(uv / 자["s"]).astype(np.int64)     # 1 단위 픽셀 통
    key = (q[:, 0] - q[:, 0].min()) * 100000 + (q[:, 1] - q[:, 1].min()); order = np.lexsort((cz, key)); k_sorted = key[order]; first = np.ones(len(order), bool); first[1:] = k_sorted[1:] != k_sorted[:-1]
    보임 = idx[order[first]]; uvb = np.round(uv[order[first]] * S).astype(int); H, W = L.shape; 안 = (uvb[:, 0] >= 0) & (uvb[:, 0] < W) & (uvb[:, 1] >= 0) & (uvb[:, 1] < H)
    f = np.zeros(len(보임), np.int32); f[안] = L[uvb[안, 1], uvb[안, 0]]
    for i, n in 이름[t].items(): 라벨[t][보임[f == i]] = 번호[n]
    print("%-7s 보이는 표면 복셀 %d · 라벨 붙은 것 %d" % (t, len(보임), (라벨[t][보임] > 0).sum()))
합 = np.zeros(len(G), np.int32); 충돌 = np.zeros(len(G), bool)
for t in 시점:
    a = 라벨[t]; 새 = (a > 0) & (합 == 0); 합[새] = a[새]; 충돌 |= (a > 0) & (합 > 0) & (a != 합)
# 라벨을 표면에서 안쪽 3 단위까지 번지게(부품 = 껍질 위 얇은 덩어리) — 복셀 라벨 그대로 STL
def 복셀메시(mask3):
    if mask3.sum() < 8: return None
    v, f, _, _ = marching_cubes(np.pad(mask3.astype(np.float32), 1), 0.5); v = v - 1 + (xs[0], ys[0], zs[0]); t = trimesh.Trimesh(v, f, process=False)
    if t.volume < 0: t.invert()
    return t
바탕 = 복셀메시(V); 바탕.export(J(P, "바탕.stl")); 부품메시 = {}
for n, i in 번호.items():
    m = (합 == i).reshape(V.shape); m = cv2.dilate(m.astype(np.uint8).reshape(len(xs), -1), np.ones((1, 1), np.uint8)).reshape(V.shape) > 0     # (두께는 안 지어낸다 · 표면 복셀 그대로)
    t = 복셀메시(m)
    if t is not None: t.export(J(P, "패치_%s.stl" % n)); 부품메시[n] = t
# ── 잰 것: 시점마다 부품 라벨 복셀 투영 vs 캡처 면 마스크 ──
결과 = {}
for t, 자이름 in 시점.items():
    if t in 추가: continue
    L = np.load(J(D, t + "_영역.npz"))["라벨"]; H, W = L.shape; 자 = 자세[자이름]; 결과[t] = {}
    for n, i in 번호.items():
        ids = [k for k, v in 이름[t].items() if v == n]
        if not ids: continue
        h, w = H // S, W // S; uv, _ = 찍기(G[합 == i], 자); m = np.zeros((h, w), np.uint8); p = np.round(uv).astype(int); ok = (p[:, 0] >= 0) & (p[:, 0] < w) & (p[:, 1] >= 0) & (p[:, 1] < h); m[p[ok, 1], p[ok, 0]] = 1
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0; c = cv2.resize(np.isin(L, ids).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0; 결과[t][n] = round(float((m & c).sum() / max(1, (m | c).sum())), 3)
json.dump(dict(부품=부품목록, 복셀=int(살.sum()), 충돌=int(충돌.sum()), 시점별IoU=결과, 승인="Claude(사용자 미확인) · 오버레이로 판정"), open(J(D, "면패치.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for t in 결과: print(t, " ".join("%s %.2f" % kv for kv in 결과[t].items()))
# ── 그림: 시점마다 캡처 위에 라벨 복셀(부품 색) + 캡처 면 경계(흰) | 오른쪽 렌더(바탕 회 + 부품 색) ──
ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 20); 색0 = {"눈구멍L": (30, 90, 220), "눈구멍R": (30, 180, 230), "볼L": (60, 170, 60), "부리1": (240, 200, 40), "부리2": (240, 130, 30), "부리3": (220, 40, 40), "뿔": (150, 60, 200), "투구이마": (120, 120, 40)}; rng = np.random.RandomState(3); 색 = {n: 색0.get(n, tuple(int(c) for c in rng.randint(60, 230, 3))) for n in 부품목록}
def 렌더(yaw, W=600, H=600, s=3.8):
    th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); g = 겉(살); Pv = G[g] @ R.T; lab = 합[g]
    o = np.argsort(-Pv[:, 2]); im = np.full((H, W, 3), 245, np.uint8); z0, z1 = Pv[:, 2].min(), Pv[:, 2].max()
    for j in o:
        x, y = int(Pv[j, 0] * s + W / 2), int((Pv[j, 1] - ys[0]) * s + 20); sh = 0.45 + 0.55 * (z1 - Pv[j, 2]) / (z1 - z0 + 1e-6)          # 가까울수록 밝게
        c = 색[부품목록[lab[j] - 1]] if lab[j] > 0 else (200, 200, 200); cv2.rectangle(im, (x - 2, y - 2), (x + 2, y + 2), tuple(int(v * sh) for v in c[::-1]), -1)
    return Image.fromarray(im[:, :, ::-1])
판 = []
for t, 자이름 in 시점.items():
    if t in 추가: continue
    im = 읽기(기록[t]["파일"]); x0, y0, x1, y1 = 기록[t]["상자"]; L = np.load(J(D, t + "_영역.npz"))["라벨"]; 자 = 자세[자이름]; ov = im.copy()
    uv, _ = 찍기(G[합 > 0], 자); p = np.round(uv).astype(int); lab = 합[합 > 0]; H, W = im.shape[:2]; ok = (p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H)
    for n, i in 번호.items():
        q = p[ok & (lab == i)]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1): ov[np.clip(q[:, 1] + dy, 0, H - 1), np.clip(q[:, 0] + dx, 0, W - 1)] = 색[n][::-1]
    vis = cv2.addWeighted(im, 0.4, ov, 0.6, 0); e = cv2.resize((cv2.Laplacian(L.astype(np.float32), cv2.CV_32F) != 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_AREA) > 0; vis[e & (cv2.resize(L, (W, H), interpolation=cv2.INTER_NEAREST) > 0)] = (255, 255, 255)
    a = Image.fromarray(vis[y0:y1, x0:x1, ::-1]); a = a.resize((int(a.width * 600 / a.height), 600)); ImageDraw.Draw(a).text((6, 6), t + " 오버레이(색 = 라벨 복셀 · 흰 = 캡처 면)", font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255)); 판.append(a)
for 이름_, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
    r = 렌더(yaw); ImageDraw.Draw(r).text((6, 6), "바탕 + 패치 · " + 이름_, font=ft, fill=(0, 0, 0)); 판.append(r)
W_ = sum(p_.width for p_ in 판[:3]) + 20; 시트 = Image.new("RGB", (max(W_, 3 * 610), 1210), (250, 250, 248)); x = 0
for p_ in 판[:3]: 시트.paste(p_, (x, 0)); x += p_.width + 10
for k, p_ in enumerate(판[3:]): 시트.paste(p_, (k * 610, 610))
d = ImageDraw.Draw(시트); y = 1180
for n in 부품목록: d.rectangle((x := 8 + 130 * 부품목록.index(n), y, x + 18, y + 18), fill=색[n]); d.text((x + 24, y - 3), n, font=ft, fill=(0, 0, 0))
시트.save(J(D, "면패치.png")); print(J(D, "면패치.png"), "· 충돌 복셀", int(충돌.sum()))
