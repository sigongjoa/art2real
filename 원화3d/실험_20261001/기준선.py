# -*- coding: utf-8 -*-
"""건축 관점 1 단계: 기준선(층 × 축) 확정용 그림 (10-04 · 비즈니스 패널 권고 1 → 「ㄱㄱ」).
층(가로) = 정면 · 옆 공통 · 정면 특징점 높이에서: L7 뿔 뿌리 · L6 처마(차양 날개) · L5 눈 · L4 코판 끝 · L3 미늘2 아래 · L2 턱 끝(+ L1 목 깃 위 = 옆 머리 아래 끝)
   L3 은 정면 미늘2 칸(30 · 32 · 33 · 34 · 37)의 아래 끝 — 칸 묶음은 부품짝_초안(사람 확인 전)
축(세로) 정면 = 중심 · 눈구멍 안 R/L · 눈구멍 바깥 R/L · 처마 끝 R/L · 볼날개 끝 R/L
축(세로) 옆 = 부리 앞 · 코판 앞(옆 5 번 칸 앞끝) · 눈 · 안테나 뿌리 · 뒤통수(옆 머리 실루엣 눈 높이의 뒤끝)
옆 원화는 B 맞춤(정면 턱 ↔ 옆 부리 앞끝 · 배율 0.745 · 기울기 −22.3°)으로 정면 층에 맞춰 돌림. 층선 위 옆 특징점(흰 점)이 줄에서 얼마나 벗어나나 = 옆 컷 원근 휨.
출력 각도데이터/기준선.png · 기준선.json"""
import os, json, numpy as np, cv2
from scipy.optimize import least_squares
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8")); f, s = P["1"], P["2"]; avg = lambda a, b: (f[a][1] + f[b][1]) / 2
쌍 = [(avg("눈/왼", "눈/오른"), s["눈/오른"]), (f["뿔 뿌리"][1], s["뿔 뿌리"]), (f["턱 끝"][1], s["턱 끝" if os.environ.get("PAIR") == "A" else "부리 앞끝"]), (avg("번개/왼", "번개/오른"), s["번개/오른"]), (avg("안테나 뿌리/왼", "안테나 뿌리/오른"), s["안테나 뿌리/오른"])]   # PAIR=A: 정면 턱 끝 ↔ 옆 아래턱 끝 (10-04 「둘 다 보여줘」)
yf = np.array([a for a, _ in 쌍]); xs = np.array([b[0] for _, b in 쌍], float); ys = np.array([b[1] for _, b in 쌍], float); xm = xs.mean()
r = lambda q: q[0] * (ys * np.cos(q[1]) + (xs - xm) * np.sin(q[1])) + q[2] - yf
k, t, c = least_squares(r, [0.8, 0, 0], bounds=([0.3, -0.6, -500], [2, 0.6, 500])).x; ex, ey = s["눈/오른"]; ct, st = np.cos(t), np.sin(t)
T = lambda x, y: (k * ((x - ex) * ct - (y - ey) * st), k * (y * ct + (x - xm) * st) + c)       # 옆 화소 → (눈 기준 가로, 정면 행)
# 정면 칸 → 판 틀
z = np.load(os.path.join(O, "1.npz")); Lb = z["라벨"]; yy, xx = np.nonzero(Lb > 0); y0, x0 = yy.min(), xx.min()
m2 = np.isin(Lb, [30, 32, 33, 34, 37]); L3 = (np.nonzero(m2.any(1))[0].max() - y0) / 2
z2 = np.load(os.path.join(O, "2.npz")); L2b = z2["라벨"]; yy2, xx2 = np.nonzero(L2b > 0); y02, x02 = yy2.min(), xx2.min()
c5 = np.nonzero(L2b == 5); 코판앞 = ((c5[1].min() - x02) / 2, (c5[0][c5[1].argmin()] - y02) / 2)
m2s = np.load(os.path.join(O, "판_2_Z.npz"))["m"]; row = int(round(ey)); 뒤 = (np.nonzero(m2s[row])[0].max(), row)
층 = {"L7 뿔 뿌리": f["뿔 뿌리"][1], "L6 처마": (f["차양 날개/왼"][1] + f["차양 날개/오른"][1]) / 2, "L5 눈": avg("눈/왼", "눈/오른"),
      "L4 코판 끝": f["코판 끝"][1], "L3 미늘2 아래": float(L3), "L2 턱 끝": f["턱 끝"][1]}
정면축 = {"A 중심": f["차양 V"][0], "B 눈구멍 안 R": f["눈구멍 안/오른"][0], "B' 눈구멍 안 L": f["눈구멍 안/왼"][0], "C 눈구멍 바깥 R": f["눈구멍 바깥/오른"][0], "C' 눈구멍 바깥 L": f["눈구멍 바깥/왼"][0],
         "D 처마 끝 R": f["차양 날개/오른"][0], "D' 처마 끝 L": f["차양 날개/왼"][0], "E 볼날개 끝 R": f["볼날개 끝/오른"][0], "E' 볼날개 끝 L": f["볼날개 끝/왼"][0]}
옆축 = {"1 부리 앞": T(*s["부리 앞끝"])[0], "2 코판 앞": T(*코판앞)[0], "3 눈": 0.0, "4 안테나 뿌리": T(*s["안테나 뿌리/오른"])[0], "5 뒤통수": T(*뒤)[0]}
# 그림
K = 2; fr = Image.open(os.path.join(O, "판_1_원화.png")).convert("RGB"); sd = ImageEnhance.Brightness(Image.open(os.path.join(O, "판_2_원화.png")).convert("RGB")).enhance(2.2)
a = np.array(sd); Hs, Ws = a.shape[:2]; Lft = 230; Wside = Lft + 260; top = 60; gap = 60; LM = 150
H = K * 330; W = LM + K * fr.width + gap + K * Wside + 20
cv = Image.new("RGB", (W, top + H + 230), "white"); cv.paste(fr.resize((fr.width * K, fr.height * K)), (LM, top)); ox = LM + K * fr.width + gap
X, Y = np.meshgrid(np.arange(K * Wside), np.arange(H)); u = X / K - Lft; v = Y / K
Ai = np.linalg.inv(np.array([[k * ct, -k * st], [k * st, k * ct]])); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c])
q = np.einsum("ij,jhw->ihw", Ai, np.stack([u - b0[0], v - b0[1]])); xi = np.round(q[0]).astype(int); yi = np.round(q[1]).astype(int)
ok = (xi >= 0) & (xi < Ws) & (yi >= 0) & (yi < Hs); img = np.full((H, K * Wside, 3), 255, np.uint8); img[ok] = a[yi[ok], xi[ok]]; cv.paste(Image.fromarray(img), (ox, top))
d = ImageDraw.Draw(cv); F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); Fb = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
층색 = [(200, 40, 40), (230, 130, 0), (30, 90, 230), (40, 150, 60), (0, 150, 150), (120, 60, 180)]
for (nm, yv), col in zip(층.items(), 층색):
    y = top + K * yv; d.line([(LM - 10, y), (W, y)], fill=col, width=2); d.text((6, y - 12), nm, font=F, fill=col)
for i, (nm, xv) in enumerate(정면축.items()):
    x_ = LM + K * xv; d.line([(x_, top), (x_, top + H)], fill=(0, 0, 0), width=1); d.text((x_ - 8, top + H + 4 + 24 * (i % 2)), nm.split()[0], font=F, fill="black")
for nm, uv in 옆축.items():
    x_ = ox + K * (uv + Lft); d.line([(x_, top), (x_, top + H)], fill=(0, 0, 0), width=1); d.text((x_ - 6, top + H + 4), nm.split()[0], font=F, fill="black")
# 옆 특징점이 층선에서 벗어난 정도(흰 점)
휨 = {}
for nm, (yf_, p_) in zip(["눈", "뿔 뿌리", "턱 끝(=부리 앞)", "번개", "안테나 뿌리"], 쌍):
    uu, vv = T(*p_); d.ellipse([ox + K * (uu + Lft) - 7, top + K * vv - 7, ox + K * (uu + Lft) + 7, top + K * vv + 7], outline=(255, 255, 255), width=3); 휨[nm] = round(float(vv - yf_), 1)
d.text((8, 12), "기준선 — 층(가로 · 정면 · 옆 공통) × 축(세로) · 흰 점 = 옆 특징점(층선에서 벗어난 만큼 = 옆 컷 원근 휨)", font=Fb, fill="black")
leg = "정면 축: " + " · ".join(정면축) + "\n옆 축: " + " · ".join(옆축) + f"\n옆 맞춤 B: 배율 {k:.3f} · 기울기 {np.degrees(t):.1f}° · 휨(정면 화소) " + " · ".join(f"{a_} {b_:+}" for a_, b_ in 휨.items())
d.multiline_text((8, top + H + 60), leg, font=F, fill="black", spacing=8)
cv.save(os.path.join(O, "기준선" + ("_A" if os.environ.get("PAIR") == "A" else "") + ".png"))
json.dump({"층(정면 판 화소 행)": {a_: round(float(b_), 1) for a_, b_ in 층.items()}, "정면 축(판 화소 열)": {a_: round(float(b_), 1) for a_, b_ in 정면축.items()},
           "옆 축(눈 = 0 · 정면 화소 · 앞 −)": {a_: round(float(b_), 1) for a_, b_ in 옆축.items()}, "옆 휨": 휨, "옆 맞춤": [round(float(k), 3), round(float(np.degrees(t)), 1)]},
          open(os.path.join(O, "기준선" + ("_A" if os.environ.get("PAIR") == "A" else "") + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(휨, {a_: round(float(b_), 1) for a_, b_ in 옆축.items()})
