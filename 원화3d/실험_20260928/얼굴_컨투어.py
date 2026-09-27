"""오메가몬 얼굴 컨투어 비교 — 원화 · FRA · 우리(새) · 우리(옛). 손 좌표는 얼굴_컨투어.json.
정규화: 대칭축 x → 0, 투구 돔 꼭대기(뿔 제외) → 0, 턱 끝 → 1 (높이 한 단위). 반쪽을 찍어 거울."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(H, "얼굴_컨투어.json"), encoding="utf-8"))
OUT = r"G:\art2real\원화3d\out\출력\오메가몬_PG\멋\얼굴_컨투어.jpg"
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
COL = {"원화": (220, 30, 30), "FRA": (20, 120, 230), "우리_새": (20, 160, 60), "우리_옛": (200, 140, 0)}
NAMES = list(COL)

def mirror(pts, ax):  # 반쪽 → 온쪽(닫힌 윤곽이면 역순으로 이어 붙임)
    return pts + [[2 * ax - x, y] for x, y in reversed(pts)]
def norm(d, pts):
    s = d["chin"] - d["top"]; return [((x - d["axis"]) / s, (y - d["top"]) / s) for x, y in pts]
def shapes(d):
    body = norm(d, mirror(d["외곽"], d["axis"]))
    horns = [norm(d, h) for h in d["뿔"]] + [norm(d, [[2 * d["axis"] - x, y] for x, y in d["뿔"][1]])]
    lines = []
    for k, l in d["선"].items():
        lines.append(norm(d, l)); lines.append(norm(d, [[2 * d["axis"] - x, y] for x, y in l]))
    return body, horns, lines

def raster(polys, N=600, ox=0.8, oy=1.4):  # 정규화 좌표 → 마스크(x −ox..ox · y −oy..1.2)
    im = Image.new("L", (N, N)); dr = ImageDraw.Draw(im); sc = N / (2 * ox) if False else N / 2.6
    for p in polys: dr.polygon([((x + 1.3) * sc, (y + oy) * sc) for x, y in p], fill=1)
    return np.array(im, bool)
def iou(a, b): return (a & b).sum() / max((a | b).sum(), 1)

S = {n: shapes(D[n]) for n in NAMES}
M0 = {n: raster([S[n][0]]) for n in NAMES}
M1 = {n: raster([S[n][0]] + S[n][1]) for n in NAMES}
rows = []
for a, b in [("원화", "FRA"), ("원화", "우리_새"), ("FRA", "우리_새"), ("원화", "우리_옛"), ("FRA", "우리_옛"), ("우리_새", "우리_옛")]:
    rows.append((a, b, iou(M0[a], M0[b]), iou(M1[a], M1[b])))
# 모양 수치: 최대 폭 / 높이 · 눈 높이 · 눈 폭 · 이마 V
def stats(n):
    body = np.array(S[n][0]); d = D[n]; s = d["chin"] - d["top"]
    e = np.array(d["선"]["눈"]); ey = (e[:, 1].mean() - d["top"]) / s; ew = (e[:, 0].max() - e[:, 0].min()) / s
    eh = (e[:, 1].max() - e[:, 1].min()) / s
    return dict(폭=body[:, 0].max() * 2, 눈높이=ey, 눈폭=ew, 눈두께=eh)
ST = {n: stats(n) for n in NAMES}

# ── 그림 ──
W = 2400; P = 580; img = Image.new("RGB", (W, 1560), "white"); dr = ImageDraw.Draw(img)
def to_px(p, cx, cy, sc): return [(cx + x * sc, cy + y * sc) for x, y in p]
def draw_shape(dr, n, cx, cy, sc, w=3, horns=True):
    body, hs, ls = S[n]; c = COL[n]
    dr.line(to_px(body + body[:1], cx, cy, sc), fill=c, width=w)
    if horns:
        for h in hs: dr.line(to_px(h + h[:1], cx, cy, sc), fill=c, width=max(1, w - 1))
    for l in ls: dr.line(to_px(l, cx, cy, sc), fill=c, width=max(1, w - 1))
# 칸 ①: 이미지 조각 + 윤곽
for i, n in enumerate(NAMES):
    d = D[n]; im = Image.open(d["file"]).convert("RGBA")
    bg = Image.new("RGBA", im.size, (235, 235, 235, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
    if d["flip"]: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    s = d["chin"] - d["top"]; x0 = d["axis"] - 1.2 * s; y0 = d["top"] - 1.25 * s
    crop = im.crop((int(x0), int(y0), int(x0 + 2.4 * s), int(y0 + 2.4 * s))).resize((P, P), Image.LANCZOS)
    crop = Image.blend(crop, Image.new("RGB", crop.size, "white"), 0.35)
    ox = 10 + i * (P + 10); img.paste(crop, (ox, 50)); sc = P / 2.4
    draw_shape(ImageDraw.Draw(img), n, ox + P / 2, 50 + 1.25 * sc, sc, w=2)
    dr.text((ox + 6, 8), f"① {n}", fill=COL[n], font=F(30))
# 칸 ②: 넷 겹침 · 칸 ③: 원화 vs 새
sc = 330; cx2, cy = 600, 700 + 1.35 * sc
for n in NAMES: draw_shape(dr, n, cx2, cy, sc, w=3)
dr.text((20, 650), "② 넷 겹침 (정규화: 돔 꼭대기→턱 끝 = 1 · 대칭축 정렬)", fill="black", font=F(28))
for j, n in enumerate(NAMES): dr.text((20 + j * 250, 1510), "■ " + n, fill=COL[n], font=F(28))
cx3 = 1800
for n in ["원화", "우리_새"]: draw_shape(dr, n, cx3, cy, sc, w=4)
dr.text((1220, 650), "③ 원화(빨강) vs 우리 새(초록)", fill="black", font=F(28))
t = ["실루엣 IoU  뿔 뺌 / 뿔 포함"] + [f"{a}↔{b}: {x:.2f} / {y:.2f}" for a, b, x, y in rows[:3]]
for k, s_ in enumerate(t): dr.text((1220, 1330 + k * 34), s_, fill="black", font=F(24))
os.makedirs(os.path.dirname(OUT), exist_ok=True); img.save(OUT, quality=90)
for r in rows: print("IoU %s↔%s  뿔뺌 %.3f  뿔포함 %.3f" % r)
for n in NAMES: print(n, {k: round(v, 3) for k, v in ST[n].items()})
assert 0.3 < rows[0][2] <= 1  # 원화↔FRA 기준선이 있다(좌표 파일이 망가지면 깨짐)
