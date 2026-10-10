# -*- coding: utf-8 -*-
"""선 고리 단계 GIF — 선고리.py <번호> gif 가 남긴 단계_NN.pkl 로 0~6 단계를 한 장씩 · python runs/선고리/단계gif.py 10"""
import os, sys, json, pickle, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [H, os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
from 선고리 import 부스러기
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); W, HH = 1000, 820
i = int(sys.argv[1]); D = pickle.load(open(os.path.join(H, "단계_%02d.pkl" % i), "rb")); X, P, fs = D["X"], D["P"], D["fs"]; S, L, Dh, Dt = X
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; 쪽이름 = {0: "앞", 2: "옆", 4: "위"}
def 판(n, t, sub=""):
    im = Image.new("RGB", (W, HH), "white"); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, 70), fill=(24, 32, 52))
    d.text((24, 35), "%d" % n, font=F(40), fill=(120, 190, 255), anchor="lm"); d.text((70, 35), t, font=F(32), fill="white", anchor="lm")
    if sub: d.text((W - 20, 35), sub, font=F(20), fill=(190, 200, 220), anchor="rm")
    return im, d
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, a, c=320, 색=(0.45, 0.68, 0.98)):
    v = [np.cos(a), np.sin(a), .7]; return render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=c, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))
def 키움(a, s=300): return Image.fromarray(a).resize((s, s), Image.NEAREST)
def 선판(k):   # 선 그림 회색 배경 (흰 바탕에 검은 선)
    a = np.full((N, N, 3), 255, np.uint8); a[S[k] > .5] = (238, 240, 245); a[L[k] > .5] = (40, 40, 40); return a
N = S.shape[-1]; fr = []
def 넣(im, n=1): fr.extend([im] * n)
xs = [35, 350, 665]
# 0 입력
im, d = 판(0, "입력: 앞 · 옆 · 위 선 그림", "부품 #%d" % i)
for x, k in zip(xs, (0, 2, 4)): im.paste(키움(선판(k)), (x, 150)); d.text((x + 150, 120), 쪽이름[k], font=F(28), fill="black", anchor="mm")
d.text((W // 2, 520), "그림이 주는 것: 바깥 윤곽 + 안쪽 선(홈 · 구멍 · 꺾임 테두리)", font=F(24), fill=(60, 60, 60), anchor="mm"); 넣(im, 14)
# 1 바탕
mb = 정(trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)))
for t in range(16):
    im, d = 판(1, "바탕: 세 윤곽을 밀어 겹친 덩어리", "바탕 점수 %.2f" % json.load(open(os.path.join(R, "윤곽0", "결과", "%02d.json" % i), encoding="utf-8"))["B"])
    for x, k in zip((40, 40, 40), (0, 2, 4)): pass
    for j, k in enumerate((0, 2, 4)): a = np.full((N, N, 3), 255, np.uint8); a[S[k] > .5] = (120, 160, 220); im.paste(키움(a, 150), (40, 110 + j * 170)); d.text((200, 185 + j * 170), 쪽이름[k], font=F(22), fill="black", anchor="lm")
    im.paste(Image.fromarray(그(mb, 2 * np.pi * t / 16, 560)) if not isinstance(그(mb, 0, 10), Image.Image) else 그(mb, 2 * np.pi * t / 16, 560), (360, 120)); fr.append(im)
# 2 선 → 벡터 (고리 테두리를 하나씩 그림)
고 = [f for f in fs if f["종"] == "고리"]
def 벡터그림(d, f, x0, s=300, 색=(30, 110, 230)):
    k = s / N; 종, v = f["벡터"]
    if 종 == "원": r, c, rad = v; d.ellipse((x0 + (c - rad) * k, 150 + (r - rad) * k, x0 + (c + rad) * k, 150 + (r + rad) * k), outline=(240, 140, 30), width=4)
    else: d.line([(x0 + c * k, 150 + r * k) for r, c in v] + [(x0 + v[0][1] * k, 150 + v[0][0] * k)], fill=색, width=3)
for t in range(len(고) + 6):
    im, d = 판(2, "선 → 벡터: 직선(파랑) · 원(주황) · 수평/수직 스냅", "고리 %d 개" % len(고))
    for x, k in zip(xs, (0, 2, 4)): a = 선판(k); a[L[k] > .5] = (190, 190, 190); im.paste(키움(a), (x, 150)); d.text((x + 150, 120), 쪽이름[k], font=F(28), fill="black", anchor="mm")
    for f in 고[:t]: 벡터그림(d, f, xs[(0, 2, 4).index(f["쪽"])])
    fr.append(im)
# 3 닫힌 고리
rng = np.random.default_rng(3); 색 = {id(f): tuple(int(c) for c in rng.integers(90, 235, 3)) for f in fs}
im, d = 판(3, "닫힌 고리 = 면 하나 (회색 = 너무 작아 뺌)")
for x, k in zip(xs, (0, 2, 4)):
    a = 선판(k)
    for f in fs:
        if f["쪽"] == k: a[f["m"] > 0] = (200, 200, 200) if f["종"] == "작음" else 색[id(f)]
    a[L[k] > .5] = (40, 40, 40); im.paste(키움(a), (x, 150)); d.text((x + 150, 120), 쪽이름[k], font=F(28), fill="black", anchor="mm")
d.text((W // 2, 520), "고리 %d 개 · 작아서 뺀 것 %d 개" % (len(고), sum(f["종"] == "작음" for f in fs)), font=F(24), fill=(60, 60, 60), anchor="mm"); 넣(im, 14)
# 4 깊이 정하기 (A 정답 · B AI)
im, d = 판(4, "고리마다 깊이: 바탕보다 0.02 넘게 깊으면 판다")
for row, (판이름, 키) in enumerate((("A 정답 깊이", "A"), ("B AI 깊이", "B"))):
    d.text((20, 125 + row * 330), 판이름, font=F(24), fill=(30, 110, 230) if 키 == "B" else (200, 120, 20))
    for x, k in zip(xs, (0, 2, 4)):
        a = 선판(k)
        for f in 고:
            if f["쪽"] == k: a[f["m"] > 0] = (90, 200, 120) if f[키] - f["바탕"] > .02 else (215, 215, 215)
        a[L[k] > .5] = (40, 40, 40); im.paste(키움(a, 270), (x + 15, 160 + row * 330))
d.text((W // 2, 800), "초록 = 판다 · 회색 = 바탕 그대로", font=F(22), fill=(60, 60, 60), anchor="mm"); 넣(im, 16)
# 5 CAD 포켓 (정답 깊이 판 · 한 번 팔 때마다)
찍 = [trimesh.Trimesh(v, f_) for v, f_ in D["찍A"]]; 가 = 0.0
for j, m in enumerate([trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i))] + 찍):
    for t in range(4):
        im, d = 판(5, "CAD 포켓: 고리 스케치 → 그 깊이까지 빼기", "파기 %d / %d" % (j, len(찍))); 가 += 2 * np.pi / 40
        g = 그(정(m), 가, 640); im.paste(Image.fromarray(g) if not isinstance(g, Image.Image) else g, (180, 100)); fr.append(im)
# 6 채점
gtm = trimesh.load(RR + D["부품"], force="mesh")
줄 = [("사람 부품", gtm, None, None), ("화소 깎기 (정답 깊이)", trimesh.load(os.path.join(R, "윤곽2", "결과_기울기02g", "%02d_깎음.stl" % i)), json.load(open(os.path.join(R, "윤곽2", "결과_기울기02g", "%02d.json" % i), encoding="utf-8"))["edge_f1"], None),
     ("선 고리 A (정답 깊이)", trimesh.load(os.path.join(H, "결과_A", "%02d_선고리.stl" % i)), D["기록"]["A"]["edge_f1"], None),
     ("선 고리 B (AI 깊이)", trimesh.load(os.path.join(H, "결과_B", "%02d_선고리.stl" % i)), D["기록"]["B"]["edge_f1"], None)]
줄 = [(n, m, e, None if e is None else 부스러기(m)) for n, m, e, _ in 줄]
for t in range(24):
    im, d = 판(6, "채점: 모서리 점수 + 부스러기")
    for j, (n, m, e, b) in enumerate(줄):
        x = 10 + j * 247; g = 그(정(m), 2 * np.pi * t / 24, 240, None if j == 0 else (0.45, 0.68, 0.98)); im.paste(Image.fromarray(g) if not isinstance(g, Image.Image) else g, (x, 160))
        d.text((x + 120, 125), n, font=F(19), fill="black", anchor="mm")
        if e is not None:
            d.text((x + 120, 440), "점수 %.2f" % e, font=F(26), fill=(40, 150, 60) if e >= .42 else (200, 40, 40), anchor="mm")
            d.text((x + 120, 480), "조각 %d · 얇음 %.1f%%" % (b[0], 100 * b[1]), font=F(22), fill=(200, 40, 40) if b[0] else (60, 60, 60), anchor="mm")
    fr.append(im)
out = os.path.join(H, "단계_%02d.gif" % i); fr[0].save(out, save_all=True, append_images=fr[1:], duration=140, loop=0); print("ok", out, len(fr), "장")
print("부스러기:", [(n, b) for n, _, _, b in 줄])
