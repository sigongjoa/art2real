# -*- coding: utf-8 -*-
"""자세 3 — ② 면 짝으로 옆 · 3/4 자세를 정면과 **함께** 푼다 (2026-09-30 · 자세검사: 자세2 로는 정면 무게중심 광선이 옆 · 3/4 짝 면에 닿지도 않는다).
    python 자세3.py -> out/오메가몬2/지표/자세3.json (정면은 자세2 그대로 = 기준 틀 · 옆 · 3/4 새 자세 · 부품 3D 점) · 자세3.png
미지수: 부품마다 z(정면 무게중심의 x · y 는 정면 틀에서 앎) + 옆 · 3/4 자세(r · s · t). 식: 부품 3D 점을 그 자세로 찍으면 그 장의 짝 면 무게중심 (넓이 작을수록 가중 — 큰 면은 시점이 바뀌면 무게중심이 움직인다) + 자세2 에서 각 · 크기가 크게 안 벗어나는 약한 사전.
정답 없음: 무게중심은 같은 3D 점이 아니다(근사). 판정은 자세검사.py 겹침 수 · 껍질 기둥 · 3/4 패치 IoU 로."""
import os, sys, json
import numpy as np, cv2
from scipy.optimize import least_squares
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from 부품투영 import 찍기, 읽기
D = J(OUT, "..", "자료"); S = 3; 선택 = json.load(open(J(D, "면대응_선택.json"), encoding="utf-8"))["짝"]; 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8"))
라벨 = {t: np.load(J(D, t + "_영역.npz"))["라벨"] for t in ("02_정면", "02_3-4", "02_옆")}; 자세2 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8"))
F = 자세2["정면 yt_172"]; Rf = cv2.Rodrigues(np.asarray(F["r"], float))[0]
def 무게(t, ids):
    m = np.isin(라벨[t], ids); ys, xs = np.nonzero(m); return np.array([xs.mean(), ys.mean()]) / S, float(m.sum()) / S / S
부품 = [(n, 짝) for n, 짝 in 선택.items() if 짝.get("정면") and (짝.get("옆") or 짝.get("3-4")) and n not in ("볼L",)]     # 볼L 은 3/4 짝(5)이 의심스러워 뺌(z 129)
정 = {n: 무게("02_정면", 짝["정면"]) for n, 짝 in 부품}; 관측 = []                                          # (부품 번호, 장, 무게중심 px, 가중)
for k, (n, 짝) in enumerate(부품):
    for t, key in (("02_옆", "옆"), ("02_3-4", "3-4")):
        if 짝.get(key): c, a = 무게(t, 짝[key]); 관측.append((k, t, c, 1.0 / np.sqrt(a) * 30))
시점 = {"02_옆": "옆 yt_235", "02_3-4": "3/4 M04"}; p0 = {t: np.r_[자세2[n]["r"], 자세2[n]["s"], 자세2[n]["t"]] for t, n in 시점.items()}
def 풀기(x):
    z = x[:len(부품)]; P = {t: x[len(부품) + 6 * i: len(부품) + 6 * i + 6] for i, t in enumerate(시점)}; return z, P
def 점3D(z):
    C = np.array([[(정[n][0][0] - F["t"][0]) / F["s"], (정[n][0][1] - F["t"][1]) / F["s"], -z[k]] for k, (n, _) in enumerate(부품)]); return (C @ Rf) * (1, 1, -1)
def 잔차(x):
    z, P = 풀기(x); U = 점3D(z); r = []
    for k, t, c, w in 관측:
        p = P[t]; uv, _ = 찍기(U[k:k + 1], dict(r=p[:3], s=p[3], t=p[4:6], k=자세2[시점[t]].get("k", 0.0))); r += list((uv[0] - c) / p[3] * w)      # 단위 · 가중
    for t in 시점:                                                                                    # 약한 사전: 자세2 에서 각 · 크기
        p = P[t]; dR = cv2.Rodrigues(p[:3])[0] @ cv2.Rodrigues(p0[t][:3])[0].T; ang = np.degrees(np.arccos(np.clip((np.trace(dR) - 1) / 2, -1, 1)))
        r += [max(0.0, ang - 15) * 0.5, np.log(p[3] / p0[t][3]) * 20]
    r += [(zk - 20) * 0.02 for zk in z]                                                              # z 는 머리 안(대략 0..50)
    return np.array(r)
from 자세2 import R_of, 각
def 시작(t, 부호):                                                                                  # 약원근 무게중심 맞춤은 앞뒤가 뒤집힌 해(네커)도 잘 맞는다 → yaw 부호 둘 다에서 출발
    r0 = p0[t]; R = cv2.Rodrigues(r0[:3])[0]
    if 부호 < 0: D = np.diag([1.0, 1.0, -1.0]); R = D @ R @ D                                        # 앞뒤 뒤집힌 짝 해(약원근 네커 반전)
    return np.r_[cv2.Rodrigues(R)[0].ravel(), r0[3:]]
res = None
for a in (-1, 1):
    for b in (-1, 1):
        x0 = np.r_[np.full(len(부품), 20.0), 시작("02_옆", a), 시작("02_3-4", b)]; r_ = least_squares(잔차, x0, method="trf", max_nfev=4000)
        print("  시작 옆 yaw %s · 3/4 yaw %s → 잔차 RMS %.2f" % ("−" if a < 0 else "+", "−" if b < 0 else "+", np.sqrt(np.mean(r_.fun ** 2))))
        if res is None or r_.cost < res.cost: res = r_; x0best = x0
x0 = x0best
z, P = 풀기(res.x); print("잔차 RMS %.2f → %.2f 단위" % (np.sqrt(np.mean(잔차(x0) ** 2)), np.sqrt(np.mean(res.fun ** 2))))
자세3 = dict(자세2); 
for t, n in 시점.items():
    p = P[t]; 자세3[n] = dict(자세2[n], r=p[:3].tolist(), s=float(p[3]), t=p[4:6].tolist()); R = cv2.Rodrigues(p[:3])[0]; 앞 = R @ np.array([0, 0, -1.0])
    print("%s: s %.2f → %.2f · t (%.0f,%.0f) → (%.0f,%.0f) · yaw %.1f°" % (n, 자세2[n]["s"], p[3], *자세2[n]["t"], *p[4:6], np.degrees(np.arctan2(앞[0], -앞[2]))))
자세3["부품3D"] = {n: [round(float(v), 1) for v in 점3D(z)[k]] for k, (n, _) in enumerate(부품)}; json.dump(자세3, open(J(OUT, "자세3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, (n, _) in enumerate(부품): print("  %-6s z %.0f" % (n, z[k]))
# 그림: 장마다 관측 무게중심(흰 +) vs 새 자세 투영(색 ×) · 자세2 투영(회 ×)
ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18); U = 점3D(z); 판 = []
for t, n in 시점.items():
    im = 읽기(기록[t]["파일"]); x0_, y0_, x1_, y1_ = 기록[t]["상자"]
    for k, tt, c, w in 관측:
        if tt != t: continue
        a = 찍기(U[k:k + 1], 자세3[n])[0][0]; b = 찍기(U[k:k + 1], 자세2[n])[0][0]
        cv2.drawMarker(im, tuple(np.round(c).astype(int)), (255, 255, 255), cv2.MARKER_CROSS, 18, 2); cv2.drawMarker(im, tuple(np.round(a).astype(int)), (0, 200, 0), cv2.MARKER_TILTED_CROSS, 16, 2); cv2.drawMarker(im, tuple(np.round(b).astype(int)), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 12, 1); cv2.line(im, tuple(np.round(c).astype(int)), tuple(np.round(a).astype(int)), (0, 200, 0), 1)
        cv2.putText(im, 부품[k][0], tuple(np.round(c).astype(int) + (6, -6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
    p_ = Image.fromarray(im[y0_:y1_, x0_:x1_, ::-1]); p_ = p_.resize((int(p_.width * 500 / p_.height), 500)); ImageDraw.Draw(p_).text((4, 4), "%s  흰+ 관측 · 초× 자세3 · 빨× 자세2" % t, font=ft, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0)); 판.append(p_)
시트 = Image.new("RGB", (sum(p.width for p in 판) + 10, 500), (30, 30, 30)); x = 0
for p_ in 판: 시트.paste(p_, (x, 0)); x += p_.width + 10
시트.save(J(OUT, "자세3.png")); print(J(OUT, "자세3.png"))
