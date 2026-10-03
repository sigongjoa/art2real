# -*- coding: utf-8 -*-
"""처마 시험 (10-04 · 비즈니스 패널 권고 2 · 사용자 「모르겠으니까 해 보자고」).
좌우 처마(차양 날개)가 눈구멍(창) 앞으로 얼마나 내미나 — 두 길로 따로 재서 비교. 미리 적은 기준: 두 값이 ±20 % 안이면 「그림자로 깊이 재기」 채택.
 ① 옆 입면: 옆 처마 칸(6)의 가장 앞 끝과 옆 눈구멍 칸(4)의 가장 앞 끝 — 가로 차를 정면 화소로(B 맞춤 T)
 ② 음영도: 정면 처마 아래 그림자가 내려온 길이 drop → 내민 깊이 D = drop · Lz / (−Ly)
    빛 L = 정면 장의 추정 빛(각도접힌판 · 판.json · x 오른 · y 아래 · z 보는 쪽). 그림자 = 1.npz 칸별 오츠 그림자 · 검은 칠(밝기 < 50)은 그림자가 아니라 칠로 뺌
    재는 띠: 오른 처마 = 축 B~D · 왼 처마 = B'~D' · 처마 아랫선 = L6 아래에서 처음 만나는 밝은 판(처마)의 아래 끝
출력 각도데이터/처마시험.png · 처마시험.json"""
import os, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}; exec(open(G["__file__"], encoding="utf-8").read(), G)
T, 층, 정면축, s = G["T"], G["층"], G["정면축"], G["s"]
# ① 옆 입면
z2 = np.load(os.path.join(O, "2.npz")); L2 = z2["라벨"]; yy, xx = np.nonzero(L2 > 0); y0, x0 = yy.min(), xx.min()
def 앞끝(c):
    q = np.nonzero(L2 == c); i = q[1].argmin(); return ((q[1][i] - x0) / 2, (q[0][i] - y0) / 2)
p6, p4 = 앞끝(6), 앞끝(4); d6, d4 = T(*p6)[0], T(*p4)[0]; 옆깊이 = float(d4 - d6)
# ② 음영도(정면)
z1 = np.load(os.path.join(O, "1.npz")); 그림자 = z1["그림자"]; L1 = z1["라벨"]; yy1, xx1 = np.nonzero(L1 > 0); a0, b0_ = yy1.min(), xx1.min()
im = cv2.imdecode(np.fromfile(os.path.join(O, "판_1_원화.png"), np.uint8), 1); Lum = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[:, :, 0].astype(float); H, W = Lum.shape
sh = 그림자[np.clip(a0 + 2 * np.arange(H)[:, None], 0, 그림자.shape[0] - 1), np.clip(b0_ + 2 * np.arange(W)[None, :], 0, 그림자.shape[1] - 1)]
칠 = Lum < 50
빛 = json.load(open(os.path.join(O, "판.json"), encoding="utf-8"))["1 정면 · 02"]["빛(x오른,y아래,z앞)"]; Ly, Lz = 빛[1], 빛[2]
결과 = {"옆 입면 깊이": round(옆깊이, 1), "정면 빛": 빛, "처마": {}}
L6, L5 = 층["L6 처마"], 층["L5 눈"]
for 쪽, (a_, b_) in (("오른", ("B 눈구멍 안 R", "D 처마 끝 R")), ("왼", ("B' 눈구멍 안 L", "D' 처마 끝 L"))):
    xa, xb = sorted([정면축[a_], 정면축[b_]]); drops = []; 칠비 = []
    for x in range(int(xa), int(xb) + 1):
        col = Lum[:, x]; r0 = int(L6) - 15; r1 = int(L5) + 10
        bright = np.nonzero(col[r0:r1] > np.percentile(Lum, 60))[0]
        if not len(bright): continue
        edge = r0 + bright.max()                          # 처마 판의 아래 끝(띠 안에서 가장 아래 밝은 곳)
        run = 0
        for y in range(edge + 1, min(H, edge + 40)):
            if sh[y, x] and not 칠[y, x]: run += 1
            else: break
        drops.append(run); 칠비.append(float(칠[edge + 1:edge + 20, x].mean()))
    drop = float(np.median(drops)) if drops else 0.0
    D = drop * Lz / max(1e-3, -Ly) if Ly < 0 else float("inf")
    결과["처마"][쪽] = {"그림자 drop 중앙(화소)": round(drop, 1), "음영도 깊이": round(D, 1), "처마 바로 아래 검은 칠 비": round(float(np.mean(칠비)) if 칠비 else 0, 2),
                     "옆 입면과 비": round(D / 옆깊이, 2) if 옆깊이 > 0 and np.isfinite(D) else None}
결과["판정(±20 %)"] = {k_: (v["옆 입면과 비"] is not None and 0.8 <= v["옆 입면과 비"] <= 1.2) for k_, v in 결과["처마"].items()}
json.dump(결과, open(os.path.join(O, "처마시험.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
# 그림: 왼 = 정면(띠 · 그림자 빨강 · 검은 칠 파랑) · 오른 = 옆(처마 앞끝 · 눈구멍 앞끝 · 깊이 화살)
K = 3; a = im.copy(); a[sh & ~칠] = (0.4 * a[sh & ~칠] + 0.6 * np.array((40, 40, 230))).astype(np.uint8); a[칠] = (0.5 * a[칠] + 0.5 * np.array((230, 120, 40))).astype(np.uint8)
for 쪽, (a_, b_) in (("오른", ("B 눈구멍 안 R", "D 처마 끝 R")), ("왼", ("B' 눈구멍 안 L", "D' 처마 끝 L"))):
    xa, xb = sorted([정면축[a_], 정면축[b_]]); cv2.rectangle(a, (int(xa), int(L6) - 15), (int(xb), int(L5) + 10), (0, 230, 230), 1)
a = cv2.resize(a, None, fx=K, fy=K, interpolation=cv2.INTER_NEAREST)
b = cv2.imdecode(np.fromfile(os.path.join(O, "판_2_원화.png"), np.uint8), 1); b = cv2.convertScaleAbs(b, alpha=2.0, beta=10)
for c_, col in ((6, (40, 140, 230)), (4, (230, 120, 40))):
    cs, _ = cv2.findContours(((L2 == c_)[y0::2, x0::2][:b.shape[0], :b.shape[1]]).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(b, cs, -1, col, 1)
for p_, col in ((p6, (40, 140, 230)), (p4, (230, 120, 40))): cv2.circle(b, (int(p_[0]), int(p_[1])), 3, col, -1)
cv2.arrowedLine(b, (int(p4[0]), int(p6[1])), (int(p6[0]), int(p6[1])), (0, 255, 255), 1, tipLength=0.2)
b = cv2.resize(b, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
Hh = max(a.shape[0], b.shape[0]); a = cv2.copyMakeBorder(a, 0, Hh - a.shape[0], 0, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255)); b = cv2.copyMakeBorder(b, 0, Hh - b.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
cv2.imencode(".png", np.hstack([a, b]))[1].tofile(os.path.join(O, "처마시험.png"))
