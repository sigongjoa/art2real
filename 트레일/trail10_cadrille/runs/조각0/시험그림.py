# -*- coding: utf-8 -*-
"""조각0 시험 그림 — 입력 · 정답 깊이 · 학습 때 보던 섞인 예측(부드러움) · 시험 때 한 종류씩 고른 예측(딱딱함) — 왜 숫자가 무너졌나"""
import os, sys, json, glob, numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 조각 import 이름, 정답칸, 격자, 보기
from 조각 import 점유
from 학습 import 디코더, K, N3
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
X = torch.from_numpy(np.load(os.path.join(H, "특징.npy"))); ids = list(range(3600, 3606)); g = 격자(N3, "cuda")[None]
m = 디코더().cuda(); m.load_state_dict(torch.load(os.path.join(H, "디코더.pt"))); m.eval()
E_ = json.load(open(os.path.join(H, "평가.json"), encoding="utf-8"))
with torch.no_grad():
    lg, c, s = m(X[ids].cuda().float()); soft = 보기(점유(g, lg.softmax(-1), c, s, .01), N3)[1]
    hard = 보기(점유(g, torch.nn.functional.one_hot(lg.argmax(-1), len(이름)).float(), c, s, .01), N3)[1]
    Q = [json.load(open(os.path.join(H, "정답", "%04d.json" % i), encoding="utf-8")) for i in ids]
    P, C, S = map(lambda t: torch.stack(t).cuda(), zip(*[정답칸(q, K) for q in Q])); gt = 보기(점유(g, P, C, S, .005), N3)[1]
Z = 110; cols = ["입력", "정답 (위 · 앞)", "학습 때 보던 것: 종류를 섞은 안개", "시험: 칸마다 한 종류만 고르면"]
W = 262 + 3 * (2 * Z + 40) + 80; im = Image.new("RGB", (W, 120 + len(ids) * 280 + 60), "white"); d = ImageDraw.Draw(im)
d.text((30, 20), "조각0 결과 — 안개로는 맞히는데 조각으로 고르면 무너진다 (시험 400: 맞힘 1.5 % · 대조 21 %)", font=F(30), fill="black")
x0 = 30
for t, w in zip(cols, [262, 2 * Z + 40, 2 * Z + 40, 2 * Z + 40]): d.text((x0, 75), t, font=F(22), fill="black"); x0 += w + 30
tile = lambda a: Image.fromarray((a.cpu().numpy().clip(0, 1) * 255).astype(np.uint8)).resize((Z, Z), Image.NEAREST).convert("RGB")
for r, i in enumerate(ids):
    y = 120 + r * 280; im.paste(Image.open(os.path.join(H, "합성", "%04d.png" % i)), (30, y)); x0 = 30 + 262 + 30
    for D_ in (gt, soft, hard):
        for k, v in enumerate((4, 2)): im.paste(tile(D_[r, v]), (x0 + k * (Z + 10), y + 70))
        x0 += 2 * Z + 70
    e = E_["디코더"][i - 3600]; d.text((x0 - 2 * Z - 70, y + 190), "모서리 %.2f · IoU %.2f" % (e["edge_f1"], e["iou"]), font=F(20), fill=(200, 40, 40))
d.text((30, im.height - 50), "예측 4800 칸의 종류: 구멍z 2478 · 원통x 2042 · 공 280 — 상자와 빈칸은 한 번도 안 나옴 (정답에는 상자 321)", font=F(22), fill=(60, 60, 60))
im.save(os.path.join(H, "시험그림.png")); print("ok")
