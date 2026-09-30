# -*- coding: utf-8 -*-
"""부리 손 — 원형사 순서로 부리 하나 (2026-09-30 「제가 원형사의 손이 될 수 있는가」 시험).
    python 부리손.py [읽기|짓기]   읽기: 옆 캡처 능선(맨 앞 z) · 부리 뒤 가장자리 z · 정면 반폭을 높이 9 줄로 읽어 부리점.json 초안 → 사람(Claude)이 값을 고친다
                                  짓기: 부리점.json 으로 쐐기 메시(능선 앞 · 좌우 뒤 가장자리) → 블렌더 npz
afherocrash 순서: 옆 뷰 능선 점 → 정면 폭 점 → 면 잇기 → 서브디비전(블렌더) → 3/4 보고 고침. 점은 적게(9 줄 × 3 점)."""
import os, sys, json
import numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); K = J(R, "out", "깊이카드"); S = 3; 파일 = J(B, "부리점.json")
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); F = 자세["정면 yt_172"]
스펙 = json.load(open(J(B, "블록아웃.json"), encoding="utf-8")); 카 = {c["이름"]: c for c in 스펙["카메라"]}
읽 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
c = 카["02_옆"]; M = np.array(c["행렬"]); Rm, loc = M[:3, :3], M[:3, 3]; s_ = c["W"] / c["ortho_scale"]
def 옆에서(u, v):
    cx, cy = (u - c["W"] / 2) / s_, -(v - c["H"] / 2) / s_; base = loc + Rm[:, 0] * cx + Rm[:, 1] * cy; cz = -base[0] / Rm[0, 2]; b = base + Rm[:, 2] * cz; return float(-b[2]), float(-b[1])   # (y, z)
def 옆으로(y, z):                                                                                    # U (0,y,z) → 옆 px (u,v)
    Ub = np.array([0.0, -z, -y]); C = Rm.T @ (Ub - loc); return C[0] * s_ + c["W"] / 2, -C[1] * s_ + c["H"] / 2
줄 = [40, 48, 56, 64, 72, 80, 88, 95, 100]
if sys.argv[1:2] == ["읽기"] or not os.path.exists(파일):
    sil옆 = 읽(J(D, "02_옆_실루엣.png"), 0) > 127; L옆 = np.load(J(D, "02_옆_영역.npz"))["라벨"]; L옆s = cv2.resize(L옆, (sil옆.shape[1], sil옆.shape[0]), interpolation=cv2.INTER_NEAREST); 부리옆 = np.isin(L옆s, [5, 12, 13, 14, 15])
    L정 = np.load(J(D, "02_정면_영역.npz"))["라벨"]; 부리정 = np.isin(L정, [17, 24, 31]); sil정 = 읽(J(D, "02_정면_실루엣.png"), 0) > 127
    점 = []
    for y in 줄:
        u, v = 옆으로(y, 40.0); v = int(round(v)); row = sil옆[v]; xs = np.nonzero(row)[0]; z앞 = 옆에서(xs.min(), v)[1] if len(xs) else None      # 능선 = 그 높이 맨 앞
        xb = np.nonzero(부리옆[v])[0]; z뒤 = 옆에서(xb.max(), v)[1] if len(xb) else None                                                        # 부리 뒤 가장자리(볼과 만나는 곳)
        vr = int(round(F["t"][1] + y * F["s"])) * S; xr = np.nonzero(부리정[vr])[0]; xs2 = np.nonzero(cv2.resize(sil정.astype(np.uint8), (L정.shape[1], L정.shape[0]))[vr])[0]
        반폭 = float((xr.max() - xr.min()) / 2 / S / F["s"]) if len(xr) else None; 중심 = float(((xr.max() + xr.min()) / 2 / S - F["t"][0]) / F["s"]) if len(xr) else 0.0
        점.append(dict(y=y, z앞=None if z앞 is None else round(z앞, 1), z뒤=None if z뒤 is None else round(z뒤, 1), 반폭=None if 반폭 is None else round(반폭, 1), x중심=round(중심, 1), 읽은것="옆 실루엣 맨 앞 · 옆 부리 면 뒤끝 · 정면 부리 면 폭"))
    json.dump(dict(줄=점, 손질="초안 · 사람이 고친다", 능선각=0.6), open(파일, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for p in 점: print(p)
    sys.exit()
P = json.load(open(파일, encoding="utf-8")); 점 = P["줄"]
# 쐐기: 줄마다 앞 능선점 (x중심, y, z앞) · 좌우 뒤 가장자리 (x중심 ± 반폭, y, z뒤) · 사이 중간점(능선각으로 볼록) → 5 점 단면
V, Fs = [], []; n단 = 3                                                                        # 용골: 능선 + 좌우 가장자리(키트 = 날카로운 쐐기 · 서브디비전 없이 각지게)
for p in 점:
    x0, y, zf, zb, w = p["x중심"], p["y"], p["z앞"], p["z뒤"], p["반폭"]; a = P.get("능선각", 0.6)
    ts = np.linspace(-1, 1, n단); xs = x0 + w * ts; zs = zb + (zf - zb) * (1 - np.abs(ts) ** (1 / a))          # 가운데가 앞으로 나온 볼록 단면
    for x, z in zip(xs, zs): V.append((float(x), float(-z), float(-y)))                                     # 블렌더 (x, −z, −y)
for i in range(len(점) - 1):
    for j in range(n단 - 1):
        a, b, c_, d = i * n단 + j, i * n단 + j + 1, (i + 1) * n단 + j + 1, (i + 1) * n단 + j; Fs += [(a, b, c_), (a, c_, d)]
V = np.array(V, np.float32); Fs = np.array(Fs, np.int32); np.savez(J(B, "부리손.npz"), V=V, F=Fs); print("부리 점", len(V), "면", len(Fs), "→", J(B, "부리손.npz"))
