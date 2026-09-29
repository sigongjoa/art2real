# -*- coding: utf-8 -*-
"""도안 3D 랜드마크를 캡처 셋(정면 · 3/4 · 옆)에 **동시에** 맞춘다 — 자세(캡처마다 회전 · 이동 · 축척)와 3D 점을 같이 풀어 재투영 잔차를 줄인다.
    python 맞춤.py -> 표(점마다 도안 → 맞춤 · 옮긴 거리) · out/오메가몬2/지표/랜드마크3D.json(자세.py · 후보 비교가 이걸 쓴다) · 맞춤_<캡처>.png
제약: 좌우 대칭(L = R 거울) · 가운데 점 x = 0 · 한 캡처에만 보이는 점은 도안 값으로 약하게 잡음(λ) — 깊이가 안 정해지기 때문.
투영: 약원근  u = s · (R p)[:2] + t. 잔차 단위 = 머리 높이 100.
"""
import os, json, math
import numpy as np, cv2
from scipy.optimize import least_squares
from PIL import Image, ImageDraw
from 자세 import 반쪽, 가운데, 캡처, 읽기, 장면, J, OUT
λ = 1.0                                                       # 도안 값으로 잡아 두는 힘(잔차 단위와 같은 눈금). 0.3 이면 폭이 1/3 로 무너지고 고도가 30° 로 도망간다(부조 모호성)
고정 = {"돔꼭대기": (0.0, 0.0), "턱끝": None}                       # 게이지: 돔꼭대기 (y,z) = (0,0) · 턱끝 y = 100 은 안 푼다(머리 높이 = 100 눈금)
반이름, 중이름 = list(반쪽), list(가운데); 캡이름 = list(캡처)
def 펼치기(x):
    """x → (3D 점 사전, 자세 사전)"""
    P = {}; i = 0
    for k in 반이름: v = x[i:i + 3]; P[k + "R"] = np.array(v); P[k + "L"] = np.array((-v[0], v[1], v[2])); i += 3
    for k in 중이름:
        if k == "돔꼭대기": P[k] = np.array((0.0, 0.0, 0.0))
        elif k == "턱끝": P[k] = np.array((0.0, 100.0, x[i])); i += 1
        else: P[k] = np.array((0.0, x[i], x[i + 1])); i += 2
    자세 = {}
    for n in 캡이름: 자세[n] = dict(r=x[i:i + 3], t=x[i + 3:i + 5], s=x[i + 5]); i += 6
    return P, 자세
def 찍기(p3, 자):
    R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); q = R @ (np.asarray(p3, float) * (1, 1, -1)); return 자["s"] * q[:2] + np.asarray(자["t"])
def 잔차(x):
    P, 자세 = 펼치기(x); out = []
    for n in 캡이름:
        f, pts = 캡처[n]; 자 = 자세[n]; u = 자["s"]                      # px / 단위
        for k, uv in pts.items():
            if k in P: out.extend((찍기(P[k], 자) - np.array(uv, float)) / u)
    for k in 반이름: out.extend(λ * (P[k + "R"] - np.array(반쪽[k], float)) / 1.0)
    for k in 중이름: out.extend(λ * (P[k][1:] - np.array(가운데[k][1:], float)))   # 고정점은 0 이 나온다
    return np.array(out)
def 초기():
    x = []
    for k in 반이름: x.extend(반쪽[k])
    for k in 중이름:
        if k == "돔꼭대기": continue
        x.extend([가운데[k][2]] if k == "턱끝" else 가운데[k][1:])
    자 = json.load(open(J(OUT, "자세.json"), encoding="utf-8"))
    for n in 캡이름:
        f, pts = 캡처[n]; im = 읽기(J(장면, f)); h, w = im.shape[:2]
        # 자세.py 의 각도에서 회전을 다시 만들고, 축척 · 이동은 점들로 최소제곱
        yaw, pitch, roll = (math.radians(자[n][k]) for k in ("yaw", "pitch", "roll"))
        Ry = cv2.Rodrigues(np.array([0, -yaw, 0.0]))[0]; Rx = cv2.Rodrigues(np.array([pitch, 0, 0.0]))[0]; Rz = cv2.Rodrigues(np.array([0, 0, roll]))[0]
        r = cv2.Rodrigues(Rz @ Rx @ Ry)[0].ravel()
        P0 = {**{k + "R": np.array(반쪽[k], float) for k in 반이름}, **{k + "L": np.array((-반쪽[k][0], 반쪽[k][1], 반쪽[k][2])) for k in 반이름}, **{k: np.array(가운데[k], float) for k in 중이름}}
        A = np.array([찍기(P0[k], dict(r=r, t=(0, 0), s=1.0)) for k in pts if k in P0]); B = np.array([pts[k] for k in pts if k in P0], float)
        s = np.std(B) / np.std(A); t = B.mean(0) - s * A.mean(0); x.extend(r); x.extend(t); x.append(s)
    return np.array(x, float)
if __name__ == "__main__":
    x0 = 초기(); r0 = 잔차(x0); sol = least_squares(잔차, x0, method="trf", max_nfev=2000); P, 자세 = 펼치기(sol.x)
    n관측 = sum(len([k for k in pts if k in P]) for _, pts in 캡처.values())
    norm = lambda r: float(np.mean(np.linalg.norm(r[:2 * n관측].reshape(-1, 2), axis=1)))
    print("재투영 잔차(단위 · 관측점 평균)  전 %.1f → 후 %.1f" % (norm(r0), norm(sol.fun)))
    print("%-10s %-22s %-22s %5s" % ("점", "도안 (x,y,z)", "맞춤 (x,y,z)", "옮김"))
    표 = {}
    for k in 반이름 + 중이름:
        a = np.array(반쪽[k] if k in 반쪽 else 가운데[k], float); b = P[k + "R"] if k in 반쪽 else P[k]; d = float(np.linalg.norm(a - b)); 표[k] = dict(도안=a.round(1).tolist(), 맞춤=b.round(1).tolist(), 옮김=round(d, 1))
        print("%-10s %-22s %-22s %5.1f" % (k, tuple(map(float, a.round(1))), tuple(map(float, b.round(1))), d))
    for n in 캡이름:
        f, pts = 캡처[n]; 자 = 자세[n]; u = 자["s"]; R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); 앞 = R @ np.array([0, 0, -1.0])
        e = np.mean([np.linalg.norm(찍기(P[k], 자) - np.array(uv, float)) / u for k, uv in pts.items() if k in P])
        print("%-12s yaw %6.1f pitch %6.1f  잔차 %.1f" % (n, math.degrees(math.atan2(앞[0], -앞[2])), math.degrees(math.asin(max(-1, min(1, -앞[1])))), e))
        im = Image.fromarray(읽기(J(장면, f))[:, :, ::-1]); d = ImageDraw.Draw(im)
        for k, uv in pts.items():
            if k not in P: continue
            x, y = uv; x2, y2 = 찍기(P[k], 자); d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 0, 0), width=2); d.ellipse((x2 - 4, y2 - 4, x2 + 4, y2 + 4), outline=(0, 90, 255), width=2); d.line((x, y, x2, y2), fill=(255, 255, 0))
        im.save(J(OUT, "맞춤_%s.png" % n.replace("/", "-").replace(" ", "_")))
    json.dump(dict(반쪽={k: 표[k]["맞춤"] for k in 반이름}, 가운데={k: 표[k]["맞춤"] for k in 중이름}, 표=표, λ=λ, 자세={n: dict(r=list(map(float, 자세[n]["r"])), t=list(map(float, 자세[n]["t"])), s=float(자세[n]["s"])) for n in 캡이름}), open(J(OUT, "랜드마크3D.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장", J(OUT, "랜드마크3D.json"))
