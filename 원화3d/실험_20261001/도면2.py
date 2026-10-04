# -*- coding: utf-8 -*-
"""도면 묶음 v2 — 오메가몬 머리 (10-04 원형사 패널 도면 v1 피드백 → 「그러면 고쳐」).
v1 에서 고친 다섯 + 하나:
  ① 부재표 숫자: 엑시아 단면(눈 높이)에서 광선으로 잰 비율 — 속 공 반지름 / 머리 반폭 · 껍질 두께 / 머리 높이 · 틈 / 머리 높이
  ② 입면에 부재 윤곽 + 번호(부품ID.json 대응표 · 칸 묶음 → 부재) — 정면 · 옆 둘 다
  ③ 단면을 오메가몬 부재로 다시 그림: 바깥 = 레퍼런스 단면의 **가장 바깥 윤곽만**(속 상자 버림) · 껍질 = 그 안쪽으로 두께 · 속 공 = 비율 반지름 ·
     창 · 뿔 · 부리 자리 = 원화 값 · **오른쪽 반만 그리고 거울**
  ④ 부리 단면 두 판(L3): A 박공 V / B 둥근 V — 앞 끝 = 옆 원화 그 행 가장 앞 · 뒤 = 단면 바깥
  ⑤ 3/4 검증 칸: 단면 윤곽을 3/4 투시(yaw −35° · pitch 10°)로 쌓은 퍼스 + 원화 3/4
  ⑥ 과장 · 잔차 목록
출력 out/오메가몬2/블렌더/도면_머리_v2.png · 도면_머리_v2.json(부재표 숫자)"""
import os, json, numpy as np, cv2, trimesh, contextlib, io
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축, 옆축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"], J["옆 축(눈 = 0 · 정면 화소 · 앞 −)"]
깊 = json.load(open(os.path.join(A, "창깊이.json"), encoding="utf-8")); D = round((깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1)
대응 = json.load(open(os.path.join(A, "부품ID.json"), encoding="utf-8"))["대응표"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2; xa = 축["A 중심"]
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
art1 = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1)[:, :, ::-1]
art2w = cv2.warpAffine(cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1), Ma, (ND, H), borderValue=(255, 255, 255))[:, :, ::-1]
art3 = cv2.imdecode(np.fromfile(os.path.join(A, "판_3_원화.png"), np.uint8), 1)[:, :, ::-1]
def 칸지도(n):
    z = np.load(os.path.join(A, f"{n}.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
    m = np.load(os.path.join(A, f"판_{n}_Z.npz"))["m"]; h, w = m.shape; py, px = np.mgrid[0:h, 0:w]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m
C1, C2 = 칸지도("1"), cv2.warpAffine(칸지도("2").astype(np.float32), Ma, (ND, H), flags=cv2.INTER_NEAREST).astype(int)
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Sa = 몸(m1), 몸(S2)
ref = trimesh.load(os.path.join(B, "엑시아_격자.ply"), process=False); T = ref.triangles
def 자르기(z):
    dz = T[:, :, 2] - z; seg = []
    sel = (dz.min(1) <= 0) & (dz.max(1) >= 0)
    for tri, dd in zip(T[sel], dz[sel]):
        pts = [p + (q - p) * dp / (dp - dq) for p, q, dp, dq in ((tri[0], tri[1], dd[0], dd[1]), (tri[1], tri[2], dd[1], dd[2]), (tri[2], tri[0], dd[2], dd[0])) if dp * dq < 0]
        if len(pts) == 2: seg.append(np.array(pts)[:, :2])
    return np.array(seg)
# ① 비율 재기 — 눈 높이 엑시아 단면, 중심에서 광선 36 개 → 교차 거리 바깥부터 r1(겉) · r2(껍질 속면) · 공(가장 둥근 일정 반지름)
seg = 자르기(-층["L5 눈"]); P = seg.reshape(-1, 2); c = np.array([np.median(P[:, 0]), np.median(P[:, 1])])
겉, 두께, 공 = [], [], []
for a in np.linspace(0, 2 * np.pi, 72, endpoint=False):
    dvec = np.array([np.cos(a), np.sin(a)]); hits = []
    for p, q in seg:
        e = q - p; M_ = np.array([dvec, -e]).T
        if abs(np.linalg.det(M_)) < 1e-9: continue
        t, s = np.linalg.solve(M_, p - c)
        if t > 0 and 0 <= s <= 1: hits.append(t)
    h = sorted(hits, reverse=True)
    if len(h) >= 2: 겉.append(h[0]); 두께.append(h[0] - h[1])
    if len(h) >= 1: 공.append(h)
r_out = np.median(겉); th = float(np.median([t for t in 두께 if t < 0.15 * r_out]))
# 공: 모든 광선에 공통으로 있는 반지름(히스토그램 최빈)
allh = np.concatenate([np.array(h) for h in 공]); hist, ed = np.histogram(allh[(allh > 0.3 * r_out) & (allh < 0.95 * r_out)], bins=40); r_core = float((ed[hist.argmax()] + ed[hist.argmax() + 1]) / 2)
head_h = 층["L2 턱 끝"] - 층["L7 뿔 뿌리"]
비율 = {"속 공 반지름 / 단면 반폭": round(r_core / r_out, 3), "껍질 두께 / 머리 높이": round(th / head_h, 3), "껍질-공 틈 / 머리 높이": round(max(0.0, (r_out - th - r_core)) / head_h, 3)}
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
sheet = Image.new("RGB", (2600, 2050), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 20), "오메가몬 머리 · 도면 묶음 v2", font=F(44), fill="black")
d.text((30, 78), "단위: 정면 판 화소(머리 높이 약 150 = 뿔 뿌리 → 턱 끝) · 앞 = 위쪽(-y) · v1 피드백 반영(원형사 패널 10-04)", font=F(22), fill=(80, 80, 80))
층색 = [(200, 40, 40), (230, 120, 0), (40, 90, 220), (30, 150, 70), (0, 150, 150), (130, 60, 180)]
부재색 = {"H01": (40, 110, 230), "H02": (230, 60, 60), "H03": (20, 20, 20), "H04": (210, 170, 0), "H06": (150, 60, 200), "H09": (0, 160, 90), "F01": (0, 170, 220)}
ofs, c1 = 90, 306
def 입면(img, cell, 표, x0, sc, 제목, 축들):
    im = Image.fromarray(img[ofs:c1]).convert("RGB"); im = Image.blend(im, Image.new("RGB", im.size, "white"), 0.35)
    im = im.resize((int(im.width * sc), int(im.height * sc))); sheet.paste(im, (x0, 170)); dd = ImageDraw.Draw(sheet)
    부재 = {}
    for e in 표:
        key = e["부품"].split()[0]; 부재.setdefault(key, []).extend(e["칸"])
    for key, cs in 부재.items():
        mk = cv2.dilate(np.isin(cell, cs).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)[ofs:c1]
        cnts, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        col = 부재색.get(key, (90, 90, 90))
        for cn in cnts:
            if cv2.contourArea(cn) < 12: continue
            pts = [(x0 + p[0][0] * sc, 170 + p[0][1] * sc) for p in cn]; dd.line(pts + [pts[0]], fill=col, width=3)
        ys, xs = np.nonzero(mk)
        if len(xs): dd.text((x0 + np.median(xs) * sc - 18, 170 + np.median(ys) * sc - 10), key, font=F(18), fill=col, stroke_width=2, stroke_fill="white")
    for (nm, r), cc in zip(층.items(), 층색):
        y = 170 + (r - ofs) * sc; dd.line([(x0, y), (x0 + im.width, y)], fill=cc, width=1); dd.text((x0 + im.width + 6, y - 12), nm, font=F(17), fill=cc)
    for nm, x in 축들: dd.line([(x0 + x * sc, 170), (x0 + x * sc, 170 + im.height)], fill=(150, 150, 150), width=1); dd.text((x0 + x * sc + 2, 170 + im.height + 2), nm, font=F(14), fill=(110, 110, 110))
    dd.text((x0, 132), 제목, font=F(26), fill="black"); return im.size
w1, h1 = 입면(art1, C1, 대응["1"], 30, 1.7, "① 입면 · 정면 + 부재 윤곽", [(k.split()[0], v) for k, v in 축.items()])
w2, h2 = 입면(art2w, C2, 대응["2"], 30 + w1 + 150, 1.35, "② 입면 · 옆 + 부재 윤곽 (정면에 맞춰 돌림)", [(f"{k.split()[0]}{v:+.0f}", v - D0) for k, v in 옆축.items()])
# 부재 범례
lx = 30 + w1 + 150 + w2 + 130; d.text((lx, 132), "부재 번호", font=F(24), fill="black")
for i, (k, nm) in enumerate([("H01", "투구 껍질(돔 · 이마 · 차양)"), ("H02", "마스크(코판 · 미늘2 · 턱판 · 볼판)"), ("H03", "눈 조립(눈구멍 · 테 · 눈)"), ("H04", "안테나"), ("H06", "볼날개"), ("H09", "뿔"), ("F01", "번개 무늬(칠)")]):
    d.rectangle([lx, 176 + i * 34, lx + 22, 196 + i * 34], fill=부재색[k]); d.text((lx + 30, 172 + i * 34), f"{k} {nm}", font=F(19), fill=(30, 30, 30))
# ③ 단면 — 바깥 윤곽만 → 원화 폭 · 앞뒤 맞춤 → 껍질 · 공 · 원화 부재 자리 · 오른쪽 반 + 거울
by = 170 + max(h1, h2) + 90; S = 380
d.text((30, by - 44), "③ 단면 (오른쪽 반 그리고 거울 · 바깥 = 레퍼런스 가장 바깥 윤곽만 · 껍질 두께 · 속 공 = ① 비율 · 빨강 = 원화 잰 자리)", font=F(24), fill="black")
단 = [("L6 처마", 층["L6 처마"]), ("L5 눈", 층["L5 눈"]), ("L4 코판 끝", 층["L4 코판 끝"])]
퍼스 = []
def 바깥윤곽(seg, rr):
    xa_ = np.nonzero(Fa[rr])[0]; ya_ = np.nonzero(Sa[rr])[0]
    P = seg.reshape(-1, 2); ex0, ex1 = np.percentile(P[:, 0], 1), np.percentile(P[:, 0], 99); ey0, ey1 = np.percentile(P[:, 1], 1), np.percentile(P[:, 1], 99)
    ax0, ax1 = xa_.min() - cu, xa_.max() - cu; ay0, ay1 = ya_.min() + D0, ya_.max() + D0
    Q = np.stack([ax0 + (seg[:, :, 0] - ex0) * (ax1 - ax0) / (ex1 - ex0), ay0 + (seg[:, :, 1] - ey0) * (ay1 - ay0) / (ey1 - ey0)], -1)
    img = np.zeros((600, 600), np.uint8); o = 300
    for p, q in Q: cv2.line(img, (int(p[0] + o), int(p[1] + o)), (int(q[0] + o), int(q[1] + o)), 255, 2)
    ff = img.copy(); m_ = np.zeros((602, 602), np.uint8); cv2.floodFill(ff, m_, (0, 0), 128); 안 = (ff != 128).astype(np.uint8)
    cnts, _ = cv2.findContours(안, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cn = max(cnts, key=cv2.contourArea).reshape(-1, 2).astype(float) - o
    # 오른쪽 반(x ≥ 축 A) → 거울
    axc = xa - cu; 오른 = cn[cn[:, 0] >= axc]; 왼 = 오른.copy(); 왼[:, 0] = 2 * axc - 왼[:, 0]
    return 오른, 왼, (ax0, ax1, ay0, ay1)
for i, (nm, r) in enumerate(단):
    rr = int(round(r)); x0 = 30 + i * (S + 30); seg = 자르기(-r)
    d.rectangle([x0, by, x0 + S, by + S], outline=(190, 190, 190)); d.text((x0 + 6, by + 4), f"{nm} (행 {r:.0f})", font=F(20), fill=층색[i + 1])
    오른, 왼, (ax0, ax1, ay0, ay1) = 바깥윤곽(seg, rr); k = 0.85; cx, cy = x0 + S / 2 - (xa - cu) * k, by + S / 2 + 20
    def 선(pts, col, w=2):
        o_ = np.argsort(np.arctan2(pts[:, 1] - pts[:, 1].mean(), pts[:, 0] - pts[:, 0].mean())); pp = pts[o_]
        d.line([(cx + p[0] * k, cy + p[1] * k) for p in pp], fill=col, width=w)
    겉 = np.r_[오른, 왼[::-1]]; d.polygon([(cx + p[0] * k, cy + p[1] * k) for p in np.r_[오른, 왼[::-1]]], outline=(40, 110, 230))
    cen = 겉.mean(0); 속 = cen + (겉 - cen) * (1 - th / max(1e-6, np.linalg.norm(겉 - cen, axis=1).mean()))
    d.polygon([(cx + p[0] * k, cy + p[1] * k) for p in 속], outline=(120, 160, 240))
    rc = 비율["속 공 반지름 / 단면 반폭"] * (ax1 - ax0) / 2; d.ellipse([cx + (cen[0] - rc) * k, cy + (cen[1] - rc) * k, cx + (cen[0] + rc) * k, cy + (cen[1] + rc) * k], outline=(20, 20, 20), width=2)
    d.line([(cx + (xa - cu) * k, by + 30), (cx + (xa - cu) * k, by + S - 8)], fill=(200, 200, 255)); d.text((cx + (xa - cu) * k - 10, by + 30), "앞", font=F(16), fill=(0, 0, 200))
    if nm.startswith("L5"):
        for side in (1, -1):
            xb, xc_ = 축["B 눈구멍 안 R"] - cu, 축["C 눈구멍 바깥 R"] - cu
            if side < 0: xb, xc_ = 2 * (xa - cu) - xb, 2 * (xa - cu) - xc_
            d.rectangle([cx + min(xb, xc_) * k, cy - D * k - 3, cx + max(xb, xc_) * k, cy + 3], outline=(220, 0, 0), width=2)
        d.text((x0 + 8, by + S - 60), f"창(H03) 입구 -{D} → 눈 0", font=F(16), fill=(220, 0, 0))
    if nm.startswith("L6"): d.polygon([(cx + (xa - cu) * k, cy + (ay0 - 4) * k), (cx + (xa - cu - 8) * k, cy + (ay0 + 12) * k), (cx + (xa - cu + 8) * k, cy + (ay0 + 12) * k)], outline=(0, 160, 90)); d.text((x0 + 8, by + S - 60), "뿔(H09) 뿌리 = 앞 가운데", font=F(16), fill=(0, 160, 90))
    if nm.startswith("L4"): d.text((x0 + 8, by + S - 60), f"코판(H02) 앞 {옆축['2 코판 앞']:.0f}", font=F(16), fill=(230, 60, 60)); d.ellipse([cx + (xa - cu) * k - 4, cy + 옆축["2 코판 앞"] * k - 4, cx + (xa - cu) * k + 4, cy + 옆축["2 코판 앞"] * k + 4], fill=(230, 60, 60))
    d.text((x0 + 8, by + S - 34), f"폭 {ax1 - ax0:.0f} · 앞뒤 {ay1 - ay0:.0f} · 껍질 {th:.1f}", font=F(16), fill=(70, 70, 70))
    퍼스.append((-r, 겉))
# ④ 부리 단면 두 판 (L3)
r3 = 층["L3 미늘2 아래"]; rr = int(round(r3)); ya_ = np.nonzero(S2[rr])[0]; xa_ = np.nonzero(Fa[rr])[0]
앞끝 = ya_.min() + D0; 뒤 = np.nonzero(Sa[rr])[0].max() + D0 if np.nonzero(Sa[rr])[0].size else 60; hw = (xa_.max() - xa_.min()) / 2 if xa_.size else 30; axc = xa - cu
for j, (lab, 둥) in enumerate((("A 박공 V", False), ("B 둥근 V", True))):
    x0 = 30 + (3 + j) * (S + 30); d.rectangle([x0, by, x0 + S, by + S], outline=(190, 190, 190)); d.text((x0 + 6, by + 4), f"④ L3 부리 단면 {lab}", font=F(20), fill=(230, 60, 60))
    k = 0.85; cx, cy = x0 + S / 2 - axc * k, by + S / 2 + 20
    pts = [(axc, 앞끝)]
    for t in np.linspace(0, 1, 9)[1:]:
        x = axc + hw * t; y = 앞끝 + (뒤 - 앞끝) * (t if not 둥 else (1 - np.cos(t * np.pi / 2)))
        pts.append((x, min(y, 뒤)))
    pts += [(axc + hw, 뒤)]; full = pts + [(2 * axc - x, y) for x, y in reversed(pts)]
    d.polygon([(cx + x * k, cy + y * k) for x, y in full], outline=(230, 60, 60), width=3)
    d.text((x0 + 8, by + S - 34), f"앞 끝 {앞끝:.0f}(옆 원화) · 폭 {2 * hw:.0f}", font=F(16), fill=(70, 70, 70)); 퍼스.append((-r3, np.array(full)))
# ⑤ 3/4 검증: 단면 윤곽을 3/4 투시로 쌓음 + 원화 3/4
vy = by + S + 70; d.text((30, vy - 40), "⑤ 3/4 검증 (단면을 쌓은 퍼스 · yaw -35° · pitch 28° · 빨강 = 부리 단면 A) 대 원화 3/4", font=F(24), fill="black")
yaw, pit = np.radians(-35), np.radians(28); Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, np.cos(pit), -np.sin(pit)], [0, np.sin(pit), np.cos(pit)]])
cv_ = Image.new("RGB", (520, 420), "white"); dv = ImageDraw.Draw(cv_)
for i_, (z, ring) in enumerate(퍼스[:4]):
    v3 = np.c_[ring[:, 0] - (xa - cu), ring[:, 1], np.full(len(ring), (z + 205) * 1.6)] @ Rz.T @ Rx.T
    dv.line([(260 + p[0] * 1.3, 200 - p[2] * 1.3) for p in np.r_[v3, v3[:1]]], fill=(220, 40, 40) if i_ == 3 else (40, 110, 230), width=2)
sheet.paste(cv_, (30, vy)); a3 = Image.fromarray(art3).resize((int(art3.shape[1] * 420 / art3.shape[0]), 420)); sheet.paste(a3, (580, vy))
# ⑥ 부재표 · 비율 · 과장 목록
tx = 580 + a3.width + 50; d.text((tx, vy - 40), "⑥ 부재표 · 비율 · 과장", font=F(24), fill="black")
rows = [f"속 공 반지름 = 단면 반폭 × {비율['속 공 반지름 / 단면 반폭']}  (레퍼런스 · 눈 높이 광선 72)",
        f"껍질 두께 = 머리 높이 × {비율['껍질 두께 / 머리 높이']}  → {th:.1f}",
        f"껍질-공 틈 = 머리 높이 × {비율['껍질-공 틈 / 머리 높이']}",
        f"창(H03) 깊이 {D} (원화 옆 17.1 · 3/4 17.4)",
        f"마스크(H02) 부리 앞 {옆축['1 부리 앞']:.0f} · 코판 앞 {옆축['2 코판 앞']:.0f} (원화 옆)",
        f"뒤통수 +{옆축['5 뒤통수']:.0f} · 안테나 뿌리 +{옆축['4 안테나 뿌리']:.0f} (원화 옆)",
        "과장: 옆 원화 원근 휨 최대 22 (층선에서 벗어남)",
        f"과장: 옆 맞춤 배율 {K['k']:.3f} · 기울기 {np.degrees(K['t']):.1f}° (정면 턱 끝 = 옆 부리 앞끝)",
        "빈칸: 부리 단면은 A/B 중 사람이 고름 · 뿔 · 안테나 단면 없음"]
for i, t in enumerate(rows): d.text((tx, vy + i * 34), t, font=F(19), fill=(200, 0, 0) if t.startswith("과장") else (30, 30, 30))
d.text((30, 2010), "출처: 원화 = 디지몬 어드벤처 02 극장판 캡처(분석용) · 단면 레퍼런스 = 「Dummy 13 Gundam Head」 Power Jojo · Printables 870763 · CC BY", font=F(18), fill=(90, 90, 90))
sheet.save(os.path.join(B, "도면_머리_v2.png"))
json.dump({"비율": 비율, "껍질 두께": round(th, 2), "창 깊이": D, "부리 앞": 옆축["1 부리 앞"]}, open(os.path.join(B, "도면_머리_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(비율, round(th, 2), round(r_core, 1), round(r_out, 1))
