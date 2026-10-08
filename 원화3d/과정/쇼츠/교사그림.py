# -*- coding: utf-8 -*-
"""쇼츠 33 · 34 그림 (10-08) — 전부 실제 데이터에서: 부품 렌더 · AI 답안 8 장 · O/X · 코드 화면.
venv/Scripts/python.exe(trail10_cadrille) 로 실행 → G:/art2real/원화3d/out/쇼츠/교사/*.png"""
import os, sys, json, glob, tempfile, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
T = "G:/art2real/트레일/trail10_cadrille"; sys.path[:0] = [T, T + "/s0", T + "/s0/stub"]
import cadquery as cq, s0 as S
from render import render
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; O = "G:/art2real/원화3d/out/쇼츠/교사/"; os.makedirs(O, exist_ok=True)
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); M = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)   # consola 는 한글이 네모
BG = (18, 18, 22); W, H = 1000, 860

def gt(p): return S.unit(trimesh.load(R + p, force="mesh"))
def code_mesh(c):
    try:
        ns = {"cq": cq}; exec(c, ns); o = ns.get("r") or next(v for v in ns.values() if isinstance(v, cq.Workplane))
        p = os.path.join(tempfile.gettempdir(), "교사그림.stl"); cq.exporters.export(o, p); return S.unit(trimesh.load(p))
    except Exception: return None
def pic(m, size, front=(1, 1, 1)):
    if m is None:
        im = Image.new("RGB", (size, size), (60, 60, 66)); d = ImageDraw.Draw(im); d.text((size // 2, size // 2), "실행 실패", font=F(size // 8), fill=(200, 200, 200), anchor="mm"); return im
    return render(np.asarray(m.vertices), np.asarray(m.faces), list(front), img_size=size)
def mark(im, ok, s=None):
    d = ImageDraw.Draw(im); s = s or im.width // 3; c = (40, 200, 90) if ok else (230, 50, 50)
    if ok: d.ellipse((im.width - s - 8, 8, im.width - 8, 8 + s), outline=c, width=max(6, s // 9))
    else: d.line((im.width - s - 8, 8, im.width - 8, 8 + s), fill=c, width=max(6, s // 9)); d.line((im.width - 8, 8, im.width - s - 8, 8 + s), fill=c, width=max(6, s // 9))
    return im
def canvas(): return Image.new("RGB", (W, H), BG)
def grid(ims, cols, cell, gap=10):
    rows = (len(ims) + cols - 1) // cols; c = canvas(); x0 = (W - cols * cell - (cols - 1) * gap) // 2; y0 = (H - rows * cell - (rows - 1) * gap) // 2
    for i, im in enumerate(ims): c.paste(im.resize((cell, cell)), (x0 + (i % cols) * (cell + gap), y0 + (i // cols) * (cell + gap)))
    return c
def pair(a, b, la, lb, ok=None):
    c = canvas(); d = ImageDraw.Draw(c); s = 470
    for i, (im, lab) in enumerate(((a, la), (b, lb))):
        x = 20 + i * (s + 20); c.paste(im.resize((s, s)), (x, 200)); d.text((x + s // 2, 150), lab, font=F(44), fill=(255, 255, 255), anchor="mm")
    if ok is not None: mark(c.crop((530, 200, 1000, 670)), ok); sub = mark(c.crop((510, 200, 980, 670)).copy(), ok); c.paste(sub, (510, 200))
    return c
def code_img(txt, hi=None, size=30):
    c = canvas(); d = ImageDraw.Draw(c); y = 40
    for line in txt.split("\n")[:22]:
        col = (255, 232, 58) if hi and hi in line else (210, 220, 230); d.text((30, y), line[:58], font=M(size), fill=col); y += size + 8
    return c

# ---------- 33 ----------
# 문제 = AI 가 보는 그림(학습 때와 같은 2×2 회색 4 장)
P8 = "46446_G1클리프점퍼/21_cliff_gunlong_grey.stl"
S.item_img(gt(P8))[1].convert("RGB").resize((860, 860)).save(O + "33_문제.png")
B = {r["부품"]: r for r in json.load(open(T + "/runs/자가3/평가67e_바탕.json", encoding="utf-8"))["부품별"]}[P8]
ms = [code_mesh(c) for c in B["코드"]]; tiles = [pic(m, 300) for m in ms]
grid([t.copy() for t in tiles], 4, 230).save(O + "33_답안8.png")
grid([mark(t.copy(), e >= 0.42) for t, e in zip(tiles, B["모서리"])], 4, 230).save(O + "33_채점.png")
# 맞은 답 → 교과서(그림 + 코드 한 쌍)
k = int(np.argmax(B["모서리"])); c = canvas(); d = ImageDraw.Draw(c)
c.paste(S.item_img(gt(P8))[1].convert("RGB").resize((420, 420)), (30, 220)); d.text((240, 170), "문제 그림", font=F(40), fill="white", anchor="mm")
d.text((500, 430), "→", font=F(90), fill=(255, 232, 58), anchor="mm")
for i, l in enumerate(B["코드"][k].split("\n")[:12]): d.text((560, 200 + i * 34), l[:26], font=M(28), fill=(210, 220, 230))
d.text((760, 170), "맞은 답 코드", font=F(40), fill="white", anchor="mm"); d.text((500, 760), "= 교과서 한 쪽", font=F(56), fill=(255, 232, 58), anchor="mm"); c.save(O + "33_교과서.png")
# 공부한 문제를 다시 냈더니(교사1 · 학습 부품)
L = json.load(open(T + "/runs/교사1/평가_학습부품.json", encoding="utf-8"))["부품별"]
r0 = next(r for r in L if max(r["모서리"]) < 0.42 and any(e >= 0 for e in r["모서리"]))
key = next(f"{i}_{j:02d}" for i in "012" for j, x in enumerate(json.load(open(T + f"/runs/교사1/결과{i}.json", encoding="utf-8"))) if x["부품"] == r0["부품"])
ans = code_mesh(open(T + f"/runs/교사1/{key}.py", encoding="utf-8").read()); out = code_mesh(r0["코드"][int(np.argmax(r0["모서리"]))])
pair(pic(ans, 470), pic(out, 470), "공부한 정답", "다시 냈더니", ok=False).save(O + "33_재시험.png")
code_img("for step in range(1, STEPS + 1):\n    t = random.choice(tr)   # 문제 하나\n    loss = model(**b).loss\n    loss.backward()\n\n\nSTEPS = 150", hi="150", size=38).save(O + "33_150코드.png")
c = canvas(); d = ImageDraw.Draw(c)
for i in range(471):
    x, y = 40 + (i % 27) * 34, 120 + (i // 27) * 34; d.rectangle((x, y, x + 28, y + 28), fill=(255, 232, 58) if i < 150 else (70, 70, 78))
d.text((500, 60), "문제 471개 중 본 건 150개", font=F(48), fill="white", anchor="mm"); c.save(O + "33_471.png")
c = canvas(); d = ImageDraw.Draw(c); d.text((500, 300), "1,500번", font=F(150), fill=(255, 232, 58), anchor="mm"); d.text((500, 520), "맞힘 34 % → 28 %", font=F(80), fill="white", anchor="mm"); mark(c, False, 200); c.save(O + "33_1500.png")
c = canvas(); d = ImageDraw.Draw(c); d.text((500, 330), "150", font=F(320), fill=(255, 232, 58), anchor="mm"); d.text((500, 620), "범인은 숫자 하나", font=F(70), fill="white", anchor="mm"); c.save(O + "33_범인.png")

# ---------- 34 ----------
K = json.load(open(T + "/runs/교사시험/결과.json", encoding="utf-8"))["기록"]; EYE = {0: 1, 1: 1, 2: 0, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 1, 9: 0}
G = [gt(r["부품"]) for r in K]; C = [code_mesh(open(T + "/runs/교사시험/%02d.py" % i, encoding="utf-8").read()) for i in range(10)]
grid([mark(pic(g, 300), False) for g in G], 5, 180).save(O + "34_실패10.png")
code_img("$ claude\n> 이 부품 사진 보고 CadQuery 코드로 짜 줘\n\n" + open(T + "/runs/교사시험/07.py", encoding="utf-8").read(), size=26).save(O + "34_터미널.png")
for i, nm in ((0, "공막대"), (7, "허리"), (8, "통"), (2, "엉덩이"), (9, "C소켓"), (5, "팔연결")):
    pair(pic(G[i], 470), pic(C[i], 470), "사람이 만든 부품", "Claude Code", ok=bool(EYE[i])).save(O + f"34_{nm}.png")
grid([mark(pic(c_, 300), bool(EYE[i])) for i, c_ in enumerate(C)], 5, 180).save(O + "34_7of10.png")
c = canvas(); d = ImageDraw.Draw(c); a = open(T + "/runs/교사시험/00.py", encoding="utf-8").read().split("\n")[:14]
b = open(T + "/runs/자가3/data/train/0000.py", encoding="utf-8").read().split("\n")[:14]
d.text((250, 40), "Claude 코드", font=F(40), fill=(255, 232, 58), anchor="mm"); d.text((750, 40), "AI 가 쓰던 코드", font=F(40), fill=(120, 200, 255), anchor="mm")
for i, (x, y) in enumerate(zip(a + [""] * 14, b + [""] * 14)): d.text((10, 90 + i * 36), x[:33], font=M(25), fill=(230, 220, 160)); d.text((510, 90 + i * 36), y[:33], font=M(25), fill=(170, 210, 240))
d.line((500, 70, 500, 840), fill=(90, 90, 100), width=3); c.save(O + "34_두코드.png")
GR = []
for i in "012":
    for j, x in enumerate(json.load(open(T + f"/runs/교사1/문법/결과{i}.json", encoding="utf-8"))):
        if x.get("통과") and x.get("눈판정") == "O": GR.append(code_mesh(open(T + f"/runs/교사1/문법/{i}_{j:02d}.py", encoding="utf-8").read()))
grid([pic(m, 200) for m in GR[:36]], 6, 140, gap=8).save(O + "34_36개.png")
print("ok", len(os.listdir(O)))
