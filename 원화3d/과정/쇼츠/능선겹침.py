# -*- coding: utf-8 -*-
"""능선 비교를 옆모습 원화 위에 겹친다(10-01 「빨강이랑 파랑 그냥 흰 배경이라 아무것도 안 보인다 · 배경 오버레이 해야지」).
    python 능선겹침.py [모델=da2b] -> out/깊이카드/겹침_능선_<모델>.png (02_옆 상자로 자름)
빨강 = 옆 캡처 실루엣의 맨 앞 윤곽(행마다 맨 왼쪽 화소 · 그대로) · 파랑 = 정면 깊이(모델) 가운데 열을 깊이카드 눈금으로 z 로 바꿔 옆 카메라로 다시 찍은 것.
계산은 실험_20260930/깊이카드.py 의 「자 1」과 같다."""
import os, sys, json, numpy as np, cv2
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(R, "오메가몬", "지표")); from 집합 import OUT, J
모델 = sys.argv[1] if len(sys.argv) > 1 else "da2b"
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); K = J(R, "out", "깊이카드"); S = 3
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); F = json.load(open(J(OUT, "자세3.json"), encoding="utf-8"))["정면 yt_172"]
c = {k["이름"]: k for k in json.load(open(J(B, "블록아웃.json"), encoding="utf-8"))["카메라"]}["02_옆"]
M = np.array(c["행렬"]); Rm, loc = M[:3, :3], M[:3, 3]; s_ = c["W"] / c["ortho_scale"]
d = np.load(J(K, "%s_정면.npy" % 모델))   # 눈금(a, b)은 아래서 다시 맞춘다 — json 의 눈금이 지금 npy 와 안 맞았다(10-01)
읽 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 옆에서(u, v):
    cx, cy = (u - c["W"] / 2) / s_, -(v - c["H"] / 2) / s_; base = loc + Rm[:, 0] * cx + Rm[:, 1] * cy; cz = -base[0] / Rm[0, 2]; p = base + Rm[:, 2] * cz; return float(-p[2]), float(-p[1])   # (y, z)
def 옆으로(y, z):
    q = Rm.T @ (np.array([0.0, -z, -y]) - loc); return q[0] * s_ + c["W"] / 2, -q[1] * s_ + c["H"] / 2
sil옆 = 읽(J(D, "02_옆_실루엣.png"), 0) > 127; 턱옆 = np.nonzero(np.load(J(D, "02_옆_영역.npz"))["라벨"] == 15)[0].max() // S
sil = 읽(J(D, "02_정면_실루엣.png"), 0) > 127; 빨, 파 = [], []
for v in range(20, 턱옆 + 1):
    xs = np.nonzero(sil옆[v])[0]
    if not len(xs): continue
    yy, zz = 옆에서(xs.min(), v); vf, uf = int(round(F["t"][1] + yy * F["s"])), int(round(F["t"][0]))
    if 0 <= vf < d.shape[0] and sil[vf, uf]:
        빨.append((xs.min(), v)); 파.append((yy, zz, float(d[vf, uf - 2:uf + 3].mean())))
q = np.array(파); a = q[:, 1].std() / max(1e-6, q[:, 2].std()); b = q[:, 1].mean() - a * q[:, 2].mean()
# 눈금: 모델 말 그대로(값 클수록 앞 · 기울기 +) 평균 · 폭만 맞춘다. 최소제곱으로 맞추면 da2b 는 기울기가 −(ρ −0.67)라 깊이를 뒤집어 맞는 것처럼 보인다(10-01)
파 = [옆으로(yy, a * dv + b) for yy, _, dv in 파]; print("눈금", round(a, 3), round(b, 2))
im = 읽(기록["02_옆"]["파일"]); x0, y0, x1, y1 = 기록["02_옆"]["상자"]; o = im.copy(); x0, x1 = x0 - 60, x0 + 360          # 얼굴 앞쪽만 · 세로 화면에 맞게 좁게
for pts, col in ((빨, (40, 40, 235)), (파, (235, 140, 30))):                          # BGR: 빨강 · 파랑
    p = np.round(np.array(pts)).astype(np.int32)
    cv2.polylines(o, [p], False, (0, 0, 0), 9, cv2.LINE_AA); cv2.polylines(o, [p], False, col, 5, cv2.LINE_AA)
out = J(K, "겹침_능선_%s.png" % 모델); cv2.imencode(".png", o[y0:y1, x0:x1])[1].tofile(out); print(out, "점", len(빨))
