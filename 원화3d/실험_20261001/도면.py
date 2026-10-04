# -*- coding: utf-8 -*-
"""도면 묶음 v1 — 오메가몬 머리 (10-04 사용자 「왜 도면 안 만든 건데? 도면 만들어라」).
건축 도면 셋을 한 장에: 입면도(정면 · 옆) · 단면도(층 L6 · L5 · L4 · L3) · 평면도(단면을 위에서 겹침) + 부재표 · 출처.
  입면도 = 원화(정면 판 · 옆은 B 맞춤으로 옮긴 것) + 층선 + 축선 + 잰 깊이(창 17.2 · 부리 앞 −102 · 뒤통수 +157)
  단면도 = 원화에 없는 정보 → 레퍼런스(엑시아 머리 · Power Jojo · CC BY · 격자 변형 판)를 그 층에서 자른 모양을
           원화 몸통 폭(정면) · 앞뒤 길이(옆)에 맞춰 늘이고 줄임 · 원화 잰 값(창 입구 −17 · 부리 앞)을 빨강으로 겹침
  단위 = 정면 판 화소(머리 높이 약 150 = 뿔 뿌리 → 턱 끝) · 앞 = 위쪽(−y)
출력 out/오메가몬2/블렌더/도면_머리_v1.png"""
import os, json, numpy as np, cv2, trimesh, contextlib, io
from PIL import Image, ImageDraw, ImageFont
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축, 옆축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"], J["옆 축(눈 = 0 · 정면 화소 · 앞 −)"]
깊 = json.load(open(os.path.join(A, "창깊이.json"), encoding="utf-8")); D = round((깊["창 깊이(옆 · 입구 → 눈)"] + 깊["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
art1 = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1)[:, :, ::-1]
art2 = cv2.warpAffine(cv2.imdecode(np.fromfile(os.path.join(A, "판_2_원화_밝게.png"), np.uint8), 1), Ma, (ND, H), borderValue=(255, 255, 255))[:, :, ::-1]
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Sa = 몸(m1), 몸(S2)
ref = trimesh.load(os.path.join(B, "엑시아_격자.ply"), process=False); T = ref.triangles
def 자르기(z):
    dz = T[:, :, 2] - z; seg = []
    for tri, dd in zip(T, dz):
        if dd.min() > 0 or dd.max() < 0: continue
        pts = [p + (q - p) * dp / (dp - dq) for p, q, dp, dq in ((tri[0], tri[1], dd[0], dd[1]), (tri[1], tri[2], dd[1], dd[2]), (tri[2], tri[0], dd[2], dd[0])) if dp * dq < 0]
        if len(pts) == 2: seg.append(np.array(pts)[:, :2])
    return np.array(seg)
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
sheet = Image.new("RGB", (2400, 1700), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 20), "오메가몬 머리 · 도면 묶음 v1", font=F(44), fill="black"); d.text((30, 78), "단위: 정면 판 화소(머리 높이 약 150) · 앞 = 위쪽(-y) · 2026-10-04", font=F(24), fill=(80, 80, 80))
층색 = [(200, 40, 40), (230, 120, 0), (40, 90, 220), (30, 150, 70), (0, 150, 150), (130, 60, 180)]
def 입면(img, x0, y0, sc, 제목, 세로축):
    im = Image.fromarray(img).convert("RGB").resize((int(img.shape[1] * sc), int(img.shape[0] * sc))); sheet.paste(im, (x0, y0)); dd = ImageDraw.Draw(sheet)
    for (nm, r), c in zip(층.items(), 층색):
        y = y0 + r * sc; dd.line([(x0, y), (x0 + im.width, y)], fill=c, width=2); dd.text((x0 + im.width + 6, y - 12), nm, font=F(18), fill=c)
    for nm, x in 세로축: dd.line([(x0 + x * sc, y0), (x0 + x * sc, y0 + im.height)], fill=(60, 60, 60), width=1); dd.text((x0 + x * sc + 2, y0 + 2), nm, font=F(14), fill=(60, 60, 60))
    dd.text((x0, y0 - 34), 제목, font=F(26), fill="black"); return im.size
# 입면도
sc = 1.6; c0, c1 = 100, 301
입면(art1[c0 - 10:c1 + 5], 30, 150, sc, "입면도 · 정면 (원화)", [])
for nm, x in 축.items():
    pass
y0e = 150; ofs = (c0 - 10)
# 층선이 잘린 그림 기준이 되게 다시 그림(행 − ofs)
sheet.paste((255, 255, 255), (0, 120, 2400, 700)); d = ImageDraw.Draw(sheet)
def 입면2(img, x0, sc, 제목, 축들):
    im = Image.fromarray(img[ofs:c1 + 5]).convert("RGB"); im = im.resize((int(im.width * sc), int(im.height * sc))); sheet.paste(im, (x0, 160)); dd = ImageDraw.Draw(sheet)
    for (nm, r), c in zip(층.items(), 층색):
        y = 160 + (r - ofs) * sc; dd.line([(x0, y), (x0 + im.width, y)], fill=c, width=2); dd.text((x0 + im.width + 6, y - 12), nm, font=F(18), fill=c)
    for nm, x in 축들: dd.line([(x0 + x * sc, 160), (x0 + x * sc, 160 + im.height)], fill=(90, 90, 90), width=1); dd.text((x0 + x * sc + 2, 160 + im.height + 2), nm, font=F(14), fill=(90, 90, 90))
    dd.text((x0, 126), 제목, font=F(26), fill="black"); return im.size
w1, h1 = 입면2(art1, 30, 1.6, "① 입면도 · 정면 (원화)", [(k.split()[0], v) for k, v in 축.items()])
w2, h2 = 입면2(art2, 30 + w1 + 160, 1.25, "② 입면도 · 옆 (원화 · 정면에 맞춰 돌림)", [(f"{k.split()[0]} {v:+.0f}", v - D0) for k, v in 옆축.items()])
xs2 = 30 + w1 + 160
d.text((xs2, 160 + h2 + 26), f"잰 값: 창(눈구멍) 깊이 {D} (옆 17.1 · 3/4 17.4) · 부리 앞 {옆축['1 부리 앞']:.0f} · 뒤통수 +{옆축['5 뒤통수']:.0f}", font=F(20), fill=(200, 0, 0))
# 단면도
단 = [("L6 처마", 층["L6 처마"]), ("L5 눈", 층["L5 눈"]), ("L4 코판 끝", 층["L4 코판 끝"]), ("L3 미늘2 아래", 층["L3 미늘2 아래"])]
겉선 = []; bx = 30; by = 760; S = 330
d.text((bx, by - 40), "③ 단면도 (원화에 없는 정보 → 레퍼런스 단면을 원화 폭 · 앞뒤 길이에 맞춤 · 빨강 = 원화에서 잰 값)", font=F(26), fill="black")
for i, ((nm, r), c) in enumerate(zip(단, 층색[1:])):
    seg = 자르기(-r); x0 = bx + i * (S + 40)
    d.rectangle([x0, by, x0 + S, by + S], outline=(180, 180, 180)); d.text((x0 + 6, by + 4), f"{nm} (행 {r:.0f})", font=F(20), fill=c)
    rr = int(round(r)); xa = np.nonzero(Fa[rr])[0]; ya = np.nonzero(Sa[rr])[0]
    if len(seg) == 0 or len(xa) < 2 or len(ya) < 2: continue
    P = seg.reshape(-1, 2); big = P  # 레퍼런스 단면 범위
    ex0, ex1 = np.percentile(big[:, 0], 1), np.percentile(big[:, 0], 99); ey0, ey1 = np.percentile(big[:, 1], 1), np.percentile(big[:, 1], 99)
    ax0, ax1 = xa.min() - cu, xa.max() - cu; ay0, ay1 = ya.min() + D0, ya.max() + D0
    sx = (ax1 - ax0) / max(1e-6, ex1 - ex0); sy = (ay1 - ay0) / max(1e-6, ey1 - ey0)
    Q = np.c_[ax0 + (seg[:, :, 0] - ex0) * sx, ay0 + (seg[:, :, 1] - ey0) * sy].reshape(-1, 2, 2) if False else np.stack([ax0 + (seg[:, :, 0] - ex0) * sx, ay0 + (seg[:, :, 1] - ey0) * sy], -1)
    겉선.append((c, Q))
    k = 0.75; cx, cy = x0 + S / 2, by + S / 2 + 10
    for p, q in Q: d.line([(cx + p[0] * k, cy + p[1] * k), (cx + q[0] * k, cy + q[1] * k)], fill=(30, 30, 30), width=1)
    d.line([(cx - S / 2 + 10, cy), (cx + S / 2 - 10, cy)], fill=(210, 210, 255)); d.line([(cx, by + 30), (cx, by + S - 10)], fill=(210, 210, 255))
    d.text((cx - 12, by + 26), "앞", font=F(16), fill=(0, 0, 200))
    if nm.startswith("L5"):   # 창 입구 깊이 −17 · 눈 0
        d.line([(cx - 80, cy - D * k), (cx + 80, cy - D * k)], fill=(220, 0, 0), width=2); d.text((cx + 84, cy - D * k - 10), f"창 입구 -{D}", font=F(16), fill=(220, 0, 0))
    d.text((x0 + 6, by + S - 52), f"폭 {ax1 - ax0:.0f} · 앞뒤 {ay1 - ay0:.0f}", font=F(16), fill=(60, 60, 60)); d.text((x0 + 6, by + S - 30), f"레퍼런스 늘임 x{sx:.2f} · y{sy:.2f}", font=F(16), fill=(120, 120, 120))
# 평면도(단면 겹침)
x0 = bx + 4 * (S + 40); d.rectangle([x0, by, x0 + S + 120, by + S], outline=(180, 180, 180)); d.text((x0 + 6, by + 4), "④ 평면도 (단면 겹침 · 위에서)", font=F(20), fill="black")
cx, cy = x0 + (S + 120) / 2, by + S / 2 + 10
for c, Q in 겉선:
    for p, q in Q: d.line([(cx + p[0] * 0.75, cy + p[1] * 0.75), (cx + q[0] * 0.75, cy + q[1] * 0.75)], fill=c, width=1)
# 부재표
ty = by + S + 50
d.text((30, ty), "⑤ 부재표 (겹 순서 안 → 밖 · 위키 머리 카드)", font=F(26), fill="black")
rows = [("속머리", "검정 · 둥근 공(레퍼런스 단면의 속 원)", "눈 · 창 바닥이 여기 붙음", "레퍼런스"),
        ("마스크", "흰 · V 미늘 3 장(코판 · 미늘2 · 턱판) · 볼 옆까지", f"부리 앞 {옆축['1 부리 앞']:.0f} · 코판 앞 {옆축['2 코판 앞']:.0f}", "원화 잰 값"),
        ("투구", "흰 · 돔 + 차양(마스크 윗변을 덮음) · 가운데 뿔", "두께 · 틈 = 레퍼런스 비율(다음 판에서 잼)", "레퍼런스"),
        ("창(눈구멍)", "각진 검은 구멍 + 둥근 파란 눈", f"깊이 {D}", "원화 잰 값(두 장 일치)"),
        ("안테나 · 번개", "노랑 막대 둘 · 관자놀이 파란 번개", "원화 정면 자리", "원화")]
for i, r in enumerate(rows):
    for j, (t, w) in enumerate(zip(r, (180, 640, 560, 300))):
        d.text((30 + sum((180, 640, 560, 300)[:j]), ty + 44 + i * 30), t, font=F(19), fill=(30, 30, 30))
d.text((30, 1660), "출처: 원화 = 디지몬 어드벤처 02 극장판 캡처(분석용) · 단면 레퍼런스 = 「Dummy 13 Gundam Head」 Power Jojo · Printables 870763 · CC BY", font=F(18), fill=(90, 90, 90))
sheet.save(os.path.join(B, "도면_머리_v1.png")); print("ok", len(겉선))
