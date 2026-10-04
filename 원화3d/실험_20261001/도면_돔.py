# -*- coding: utf-8 -*-
"""도면 v3 — 부재 하나(H01 투구 돔)를 「한 몸」으로 정하고, 거기서 정면 · 옆 · 평면 · 단면 · 3/4 를 투영해 그린다 (10-04 「여전히 도면이 개판」 → 「ㄱㄱ」).
뽑아낸 선이 아니라 정한 형상: 비대칭 반타원체(앞 반축 f · 뒤 반축 b · 좌우 반축 a · 높이 h) + 껍질 두께 t(레퍼런스 비율 0.012 × 머리 높이).
숫자는 원화에서만:
  a = 정면 몸통(가시 뗀 실루엣) L6 처마 높이 반폭 · h = L6 → 정면 몸통 꼭대기
  f · b = 옆 몸통(B 맞춤) L6 높이의 앞 끝 · 뒤 끝 − 눈 깊이 0 기준 가운데
세 도면은 같은 식에서 나오므로 구성상 서로 맞는다. 원화 위 겹침(빨강)은 검증용.
출력 out/오메가몬2/블렌더/도면_돔_v3.png · 도면_돔_v3.json"""
import os, json, numpy as np, cv2, contextlib, io
from PIL import Image, ImageDraw, ImageFont
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; xa = 축["A 중심"]
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Sa = 몸(m1), 몸(S2)
r6 = int(round(층["L6 처마"])); xs = np.nonzero(Fa[r6])[0]; ys = np.nonzero(Sa[r6])[0]
a = (xs.max() - xs.min()) / 2; cx_img = (xs.max() + xs.min()) / 2
top = np.nonzero(Fa[:, int(xa)])[0].min(); h = r6 - top
yf, yb = ys.min() + D0, ys.max() + D0; y0 = (yf + yb) / 2; f = y0 - yf; b = yb - y0
t = round(0.012 * (층["L2 턱 끝"] - 층["L7 뿔 뿌리"]), 2)
수 = {"a 좌우 반축": round(a, 1), "h 높이": round(float(h), 1), "앞 끝": round(float(yf), 1), "뒤 끝": round(float(yb), 1), "y0 가운데": round(float(y0), 1), "f 앞 반축": round(float(f), 1), "b 뒤 반축": round(float(b), 1), "t 껍질": t, "가운데 x": round(cx_img - xa, 1)}
def 단면(s, sc=1.0):   # 높이 비율 s(0 = 처마 · 1 = 꼭대기)에서 바깥 고리 (x, y) — 앞은 f, 뒤는 b
    k = np.sqrt(max(0.0, 1 - s * s)); th = np.linspace(0, 2 * np.pi, 180)
    x = (a * sc) * k * np.cos(th); y = np.where(np.sin(th) < 0, -(f * sc) * k * np.sin(th) * -1, (b * sc) * k * np.sin(th)); return np.c_[x, y0 + y]
안 = lambda s: 단면(s, 1 - t / min(a, f, b))
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
sheet = Image.new("RGB", (2400, 1500), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 20), "H01 투구 돔 · 도면 v3 (한 몸에서 투영)", font=F(42), fill="black")
d.text((30, 74), "형상: 비대칭 반타원체 + 껍질 · 숫자는 원화(정면 반폭 · 옆 앞뒤 · 높이), 껍질만 레퍼런스 비율 · 단위 = 정면 판 화소", font=F(22), fill=(80, 80, 80))
선 = (20, 20, 20); 숨은 = (150, 150, 150); 치수 = (200, 40, 40)
def 칸(x0, y0_, w, hh, 제목):
    d.rectangle([x0, y0_, x0 + w, y0_ + hh], outline=(200, 200, 200)); d.text((x0 + 8, y0_ + 6), 제목, font=F(22), fill="black")
def 치수선(p, q, 글, off=(0, 0)):
    d.line([p, q], fill=치수, width=1)
    for e in (p, q): d.ellipse([e[0] - 3, e[1] - 3, e[0] + 3, e[1] + 3], fill=치수)
    d.text(((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1]), 글, font=F(18), fill=치수)
S = 2.2; ss = np.linspace(0, 1, 60)
# ① 정면 입면: x = ±a√(1−s²) , 높이 s·h
x0, by = 40, 140; 칸(x0, by, 520, 420, "① 정면"); cx, cy = x0 + 260, by + 360
pts = [(cx + a * np.sqrt(1 - s * s) * S, cy - s * h * S) for s in ss]; d.line(pts, fill=선, width=3); d.line([(2 * cx - p[0], p[1]) for p in pts], fill=선, width=3)
pi = [(cx + (a - t) * np.sqrt(1 - s * s) * S, cy - s * (h - t) * S) for s in ss]; d.line(pi, fill=숨은, width=1); d.line([(2 * cx - p[0], p[1]) for p in pi], fill=숨은, width=1)
d.line([(cx - a * S - 10, cy), (cx + a * S + 10, cy)], fill=선, width=2); d.line([(cx, cy + 10), (cx, cy - h * S - 20)], fill=(120, 120, 255))
치수선((cx - a * S, cy + 30), (cx + a * S, cy + 30), f"폭 {2 * a:.0f}", (-30, 4)); 치수선((cx + a * S + 30, cy), (cx + a * S + 30, cy - h * S), f"높이 {h:.0f}", (6, 0))
# ② 옆 입면: 앞 −f · 뒤 +b
x0 = 600; 칸(x0, by, 620, 420, "② 옆 (왼쪽 = 앞)"); cx2, cy2 = x0 + 320, by + 360
pf = [(cx2 + (y0 - f * np.sqrt(1 - s * s)) * S * 0.9, cy2 - s * h * S) for s in ss]; pb = [(cx2 + (y0 + b * np.sqrt(1 - s * s)) * S * 0.9, cy2 - s * h * S) for s in ss]
d.line(pf + pb[::-1], fill=선, width=3); d.line([(cx2 + yf * S * 0.9 - 10, cy2), (cx2 + yb * S * 0.9 + 10, cy2)], fill=선, width=2)
d.line([(cx2, by + 40), (cx2, cy2 + 10)], fill=(120, 120, 255)); d.text((cx2 + 4, by + 40), "눈 깊이 0", font=F(16), fill=(80, 80, 255))
치수선((cx2 + yf * S * 0.9, cy2 + 30), (cx2 + yb * S * 0.9, cy2 + 30), f"앞 {yf:.0f} ~ 뒤 +{yb:.0f}", (-60, 4))
# ③ 평면 (위에서) + 단면 높이선
x0 = 1260; 칸(x0, by, 520, 420, "③ 평면 (위 = 앞)"); cx3, cy3 = x0 + 260, by + 230
for s, col, w in ((0.0, 선, 3), (0.5, 숨은, 1), (0.8, 숨은, 1)):
    r = 단면(s); d.line([(cx3 + p[0] * S * 0.9, cy3 + (p[1] - y0) * S * 0.9) for p in np.r_[r, r[:1]]], fill=col, width=w)
r = 안(0.0); d.line([(cx3 + p[0] * S * 0.9, cy3 + (p[1] - y0) * S * 0.9) for p in np.r_[r, r[:1]]], fill=숨은, width=1)
d.text((cx3 - 10, by + 40), "앞", font=F(18), fill=(0, 0, 200))
# ④ 단면 셋 (껍질 두께 보임 · 확대)
d.text((40, 590), "④ 단면 (바깥 굵은 선 · 안쪽 = 껍질 속면 · 두께 t)", font=F(24), fill="black")
for i, s in enumerate((0.0, 0.4, 0.75)):
    x0 = 40 + i * 420; 칸(x0, 630, 400, 380, f"높이 {s * h:.0f} (s={s})"); cx4, cy4 = x0 + 200, 630 + 200
    for r, col, w in ((단면(s), 선, 3), (안(s), (90, 90, 90), 2)):
        d.line([(cx4 + p[0] * S, cy4 + (p[1] - y0) * S * 0.8) for p in np.r_[r, r[:1]]], fill=col, width=w)
    d.text((x0 + 8, 630 + 350), f"좌우 {2 * a * np.sqrt(1 - s * s):.0f} · 앞뒤 {(f + b) * np.sqrt(1 - s * s):.0f} · 껍질 {t}", font=F(16), fill=(70, 70, 70))
# ⑤ 3/4 (위도 고리 + 경선 와이어)
x0 = 1320; 칸(x0, 590, 460, 420, "⑤ 3/4 (yaw -35° · pitch 20°)"); cx5, cy5 = x0 + 230, 590 + 300
yaw, pit = np.radians(-35), np.radians(20); Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, np.cos(pit), -np.sin(pit)], [0, np.sin(pit), np.cos(pit)]])
def 투(P): v = P @ Rz.T @ Rx.T; return [(cx5 + p[0] * 1.6, cy5 - p[2] * 1.6) for p in v]
for s in np.linspace(0, 0.95, 6):
    r = 단면(s); d.line(투(np.c_[r[:, 0], r[:, 1] - y0, np.full(len(r), s * h)]), fill=선 if s == 0 else 숨은, width=2 if s == 0 else 1)
for th in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    P = []
    for s in ss:
        k = np.sqrt(1 - s * s); x = a * k * np.cos(th); y = (b if np.sin(th) > 0 else f) * k * np.sin(th); P.append((x, y, s * h))
    d.line(투(np.array(P)), fill=숨은, width=1)
# ⑥ 원화 겹침 검증 (정면 · 옆) — 이 도면의 윤곽이 원화 위에 놓이나
art1 = Image.open(os.path.join(A, "판_1_원화.png")).convert("RGB"); d1 = ImageDraw.Draw(art1)
pts = [(cx_img + a * np.sqrt(1 - s * s), r6 - s * h) for s in ss]; d1.line(pts, fill=(255, 0, 0), width=2); d1.line([(2 * cx_img - p[0], p[1]) for p in pts], fill=(255, 0, 0), width=2)
art2 = Image.fromarray(cv2.warpAffine(cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1), Ma, (ND, H), borderValue=(255, 255, 255))[:, :, ::-1]); d2 = ImageDraw.Draw(art2)
pf = [(y0 - f * np.sqrt(1 - s * s) - D0, r6 - s * h) for s in ss]; pb = [(y0 + b * np.sqrt(1 - s * s) - D0, r6 - s * h) for s in ss]; d2.line(pf + pb[::-1], fill=(255, 0, 0), width=2)
d.text((40, 1040), "⑥ 검증: 이 도면의 돔 윤곽(빨강)을 원화 위에", font=F(24), fill="black")
g1 = art1.crop((0, 60, W, r6 + 30)).resize((int(W * 1.6), int((r6 - 30) * 1.6))); sheet.paste(g1, (40, 1080))
g2 = art2.crop((0, 60, ND, r6 + 30)).resize((int(ND * 1.2), int((r6 - 30) * 1.2))); sheet.paste(g2, (80 + g1.width, 1080))
d.text((1800, 140), "숫자 (원화에서)", font=F(24), fill="black")
for i, (kk, v) in enumerate(수.items()): d.text((1800, 180 + i * 32), f"{kk} = {v}", font=F(20), fill=(30, 30, 30))
d.text((1800, 180 + len(수) * 32 + 10), "t 만 레퍼런스 비율(0.012 × 머리 높이)", font=F(18), fill=(120, 120, 120))
sheet.save(os.path.join(B, "도면_돔_v3.png")); json.dump(수, open(os.path.join(B, "도면_돔_v3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(수)
