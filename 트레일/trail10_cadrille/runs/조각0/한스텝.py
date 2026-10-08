# -*- coding: utf-8 -*-
"""학습 한 스텝을 그림으로 — 입력 그림 → 얼린 인코더 토큰 → 칸 디코더(학습 전) → SDF → 6 방향 그림 → 정답과 차이 → loss → 한 번 고침
python runs/조각0/한스텝.py  →  runs/조각0/한스텝.png"""
import os, sys, json, numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 조각 import 이름, 정답칸, 격자
from 학습 import 디코더, 그림, 손실, K, N3
torch.manual_seed(0); dev = "cuda"; F = lambda n, b=True: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf" if b else "C:/Windows/Fonts/malgun.ttf", n)
X = torch.from_numpy(np.load(os.path.join(H, "특징.npy"))); ids = [0, 2, 4]; g = 격자(N3, dev)[None]
Q = [json.load(open(os.path.join(H, "정답", "%04d.json" % i), encoding="utf-8")) for i in ids]
P, C, S = map(lambda t: torch.stack(t).to(dev), zip(*[정답칸(q, K) for q in Q])); Y = [t.detach() for t in 그림(P, C, S, 0.005, g)]
m = 디코더().to(dev); opt = torch.optim.AdamW(m.parameters(), 3e-4); x = X[ids].to(dev).float()
lg, c, s = m(x); prob = lg.softmax(-1); A = 그림(prob, c, s, 0.05, g)
parts = [float(w * (a - b).abs().mean()) for w, a, b in zip((1, 1, 2), A, Y)]; loss = 손실(A, Y)
opt.zero_grad(); loss.backward(); gn = float(sum(p.grad.norm() ** 2 for p in m.parameters() if p.grad is not None) ** .5); opt.step()
with torch.no_grad(): lg2, c2, s2 = m(x); loss2 = float(손실(그림(lg2.softmax(-1), c2, s2, 0.05, g), Y))
npar = sum(p.numel() for p in m.parameters())

V = (0, 2, 4); Z = 120; W0 = 262
def 판(t, inv=False, cm=None):   # (n,n) → 회색 이미지
    a = t.detach().float().cpu().numpy(); a = a / max(a.max(), 1e-6) if cm == "열" else a
    a = (np.clip(1 - a if inv else a, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(a).resize((Z, Z), Image.NEAREST).convert("RGB")
    if cm == "열": r = np.asarray(im)[..., 0]; im = Image.fromarray(np.stack([np.full_like(r, 255), 255 - r, 255 - r], -1))   # 흰 = 맞음 · 빨강 = 틀림
    return im
cols = [("① 입력 그림", W0), ("② 정답 깊이 (옆 · 앞 · 위)", 3 * Z + 20), ("③ 학습 전 예측 (같은 3 방향)", 3 * Z + 20), ("④ 차이 (빨강 = 틀린 곳 = loss)", 3 * Z + 20)]
Wt = 2050; Hrow = W0 + 30; top = 230
im = Image.new("RGB", (Wt, top + Hrow * 3 + 330), "white"); d = ImageDraw.Draw(im)
d.text((40, 20), "학습 한 스텝 — 컨투어 loss 로 칸 디코더를 한 번 고친다 (조각0)", font=F(40), fill="black")
d.text((40, 80), "① 그림 → cadrille 비전 인코더(얼림) → 토큰 100 개 × 1536 → 칸 디코더(매개변수 %s) → 칸 12 개 각각 [종류 10 칸 확률 · 중심 3 · 크기 3]" % format(npar, ","), font=F(24, False), fill=(60, 60, 60))
d.text((40, 115), "→ 칸마다 SDF → 점유(시그모이드 τ = 0.05, 스무딩 손잡이) → 6 방향에서 본 실루엣 · 깊이 · 깊이 모서리 → 정답과 차이 = loss  (정답 조각 목록은 안 씀 · 정답 그림만)", font=F(24, False), fill=(60, 60, 60))
x0 = 40
for t, w in cols: d.text((x0, top - 45), t, font=F(26), fill="black"); x0 += w + 30
for r, i in enumerate(ids):
    y = top + r * Hrow; im.paste(Image.open(os.path.join(H, "합성", "%04d.png" % i)), (40, y)); x0 = 40 + W0 + 30
    for blk in (lambda v: 판(Y[1][r, v]), lambda v: 판(A[1][r, v]), lambda v: 판((A[1][r, v] - Y[1][r, v]).abs() + (A[2][r, v] - Y[2][r, v]).abs(), cm="열")):
        for k, v in enumerate(V): im.paste(blk(v), (x0 + k * (Z + 10), y + 70))
        x0 += 3 * Z + 50
y = top + 3 * Hrow + 10
d.text((40, y), "loss = 실루엣 %.3f + 깊이 %.3f + 깊이 모서리×2 %.3f = %.3f" % (*parts, float(loss)), font=F(30), fill="black")
d.text((40, y + 50), "→ 거꾸로 흘려(기울기 크기 %.2f) 디코더만 한 번 고침 → 같은 세 부품 loss %.3f → %.3f   (인코더는 얼림 · 안 바뀜)" % (gn, float(loss), loss2), font=F(30), fill=(40, 140, 60))
prob0 = prob[0].detach().cpu(); top6 = prob0[:, 1:].max(-1).values.argsort(descending=True)[:6]
d.text((40, y + 110), "첫 부품의 칸 (학습 전 · 아직 아무 뜻 없음):", font=F(26), fill="black")
for k, j in enumerate(top6.tolist()):
    t = int(prob0[j].argmax()); d.text((40 + (k % 3) * 640, y + 155 + (k // 3) * 40), "칸 %d: %s %.2f · 중심 (%.2f, %.2f, %.2f)" % (j, 이름[t], prob0[j, t], *c[0, j].tolist()), font=F(24, False), fill=(60, 60, 60))
d.text((40, y + 250), "정답 조각: " + " · ".join("%s" % q[0] for q in Q[0]), font=F(26), fill=(60, 60, 60))
im.save(os.path.join(H, "한스텝.png")); print("ok", parts, float(loss), loss2, gn, npar)
