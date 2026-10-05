# -*- coding: utf-8 -*-
"""분할 모델 A — 학습 되는지 확인 (2026-10-05 · 판정 기준은 돌리기 전에 고정)
질문: 사람이 자른 출력용 모델로 배우면, 처음 보는 모델에서 사람이 자를 자리(부품 경계)를 맞히나
- 데이터: _학습/*.npz (조립 위치 모델 · 바깥 점 · 경계 = 다른 부품 1.5 mm 안)
- 나누기: 모델 단위 · 시험 4 개 얼림(씨앗 고정) · 학습 개수 6 → 10 → 전부(곡선)
- 모델: 작은 DGCNN(EdgeConv 3 층 · k 16) · 입력 = 4096 점 조각(중심 주변 최근접) · 좌표/30 mm · 법선
- 대조: 규칙(이웃 2 mm 안 법선 흩어짐이 문턱 넘으면 경계 · 문턱은 학습 모델에서 고름) · 무작위(경계 비율만큼)
- 판정: 시험 4 개 경계 F1(2 mm 허용) — 학습이 규칙보다 +0.1 이상이면 「배웠다」 · 문턱(0.5 아님)도 학습 모델에서 고름
- 과정 시각화(필수): 매 에폭 시험 모델 4 개 예측 경계를 색칠한 프레임 → 학습과정.mp4
python 분할학습.py <학습 개수 | all> <에폭>"""
import os, sys, glob, json, time, subprocess, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
D = "G:/art2real/원화3d/out/레퍼런스/사람분할/_학습/"; NTR = sys.argv[1]; EP = int(sys.argv[2]) if len(sys.argv) > 2 else 30
O = D + f"run_{NTR}/"; os.makedirs(O + "프레임", exist_ok=True)
fs = sorted(glob.glob(D + "*.npz")); rng = np.random.default_rng(7); perm = rng.permutation(len(fs))
te = [fs[i] for i in perm[:4]]; trall = [fs[i] for i in perm[4:]]; tr = trall if NTR == "all" else trall[:int(NTR)]
L = lambda f: dict(np.load(f)); TR = [L(f) for f in tr]; TE = [L(f) for f in te]
print("학습", [os.path.basename(f) for f in tr]); print("시험", [os.path.basename(f) for f in te])
K, NP, SC = 16, 4096, 30.0
def 조각(d, c=None):
    t = d.get("_t") or cKDTree(d["xyz"]); d["_t"] = t
    if c is None: c = d["xyz"][np.random.randint(len(d["xyz"]))]
    _, idx = t.query(c, k=min(NP, len(d["xyz"])))
    x = (d["xyz"][idx] - c) / SC; return np.hstack([x, d["n"][idx]]).astype(np.float32), d["경계"][idx].astype(np.float32), idx
def knn(x, k):
    d = -2 * x @ x.transpose(2, 1) + (x ** 2).sum(-1, keepdim=True) + (x ** 2).sum(-1).unsqueeze(1); return d.topk(k, largest=False)[1]
def edge(x, idx):
    B, N, C = x.shape; nb = torch.gather(x.unsqueeze(1).expand(B, N, N, C) if False else x, 1, idx.reshape(B, -1, 1).expand(-1, -1, C)).reshape(B, N, -1, C)
    return torch.cat([nb - x.unsqueeze(2), x.unsqueeze(2).expand(-1, -1, idx.shape[2], -1)], -1)
class Net(nn.Module):
    def __init__(s):
        super().__init__(); s.e1 = nn.Sequential(nn.Linear(12, 64), nn.GELU(), nn.Linear(64, 64)); s.e2 = nn.Sequential(nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 64))
        s.e3 = nn.Sequential(nn.Linear(128, 128), nn.GELU()); s.h = nn.Sequential(nn.Linear(64 + 64 + 128 + 128, 128), nn.GELU(), nn.Linear(128, 1))
    def forward(s, x):
        idx = knn(x[..., :3], K); a = s.e1(edge(x, idx)).max(2)[0]
        idx2 = knn(a, K); b = s.e2(edge(a, idx2)).max(2)[0]; c = s.e3(edge(b, knn(b, K))).max(2)[0]
        g = c.max(1, keepdim=True)[0].expand_as(c); return s.h(torch.cat([a, b, c, g], -1)).squeeze(-1)
dev = "cuda"; net = Net().to(dev); opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4)
pos = np.mean(np.concatenate([d["경계"] for d in TR])); pw = torch.tensor((1 - pos) / max(pos, 1e-3), device=dev)
print("경계 비율", round(float(pos), 3))
def 예측(d):
    t = d.get("_t") or cKDTree(d["xyz"]); d["_t"] = t; n = len(d["xyz"]); s = np.zeros(n); c = np.zeros(n)
    cs = d["xyz"][np.random.default_rng(0).choice(n, max(1, n // 1200), replace=False)]
    net.eval()
    with torch.no_grad():
        for cc in cs:
            x, _, idx = 조각(d, cc); p = torch.sigmoid(net(torch.tensor(x[None], device=dev)))[0].cpu().numpy(); s[idx] += p; c[idx] += 1
    net.train(); s[c == 0] = 0; return s / np.maximum(c, 1)
def F1(d, pred, tol=2.0):
    gt = d["경계"].astype(bool); P_, G_ = d["xyz"][pred], d["xyz"][gt]
    if len(P_) == 0 or len(G_) == 0: return 0.0
    pr = np.mean(cKDTree(G_).query(P_)[0] < tol); rc = np.mean(cKDTree(P_).query(G_)[0] < tol); return 0 if pr + rc == 0 else 2 * pr * rc / (pr + rc)
def 규칙점수(d, r=2.0):
    t = cKDTree(d["xyz"]); nb = t.query_ball_point(d["xyz"], r); n = d["n"]
    return np.array([1 - np.abs(n[i] @ n[j].T).mean() if len(j) > 1 else 0 for i, j in enumerate(nb)])
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
def 그림(d, pred, w=360):
    x = d["xyz"]; lo, hi = x.min(0), x.max(0); s = (w - 20) / max(hi[0] - lo[0], hi[2] - lo[2]); im = Image.new("RGB", (w, w), "white"); dr = ImageDraw.Draw(im)
    o = np.argsort(x[:, 1])[::-1]; gt = d["경계"].astype(bool)
    for i in o:
        px, py = 10 + (x[i, 0] - lo[0]) * s, w - 10 - (x[i, 2] - lo[2]) * s
        col = (210, 40, 40) if pred[i] and gt[i] else (240, 150, 40) if pred[i] else (40, 150, 60) if gt[i] else (190, 190, 195)
        dr.point((px, py), fill=col)
    return im
# 규칙 대조: 문턱을 학습 모델에서 고름
rs_tr = [규칙점수(d) for d in TR]; ths = np.quantile(np.concatenate(rs_tr), np.linspace(0.5, 0.99, 25))
best_th = max(ths, key=lambda th: np.mean([F1(d, r > th) for d, r in zip(TR, rs_tr)]))
규칙F1 = [F1(d, 규칙점수(d) > best_th) for d in TE]; 무작위F1 = [F1(d, np.random.default_rng(1).random(len(d["xyz"])) < pos) for d in TE]
print("대조 규칙", np.round(규칙F1, 3), "무작위", np.round(무작위F1, 3))
기록 = {"학습": [os.path.basename(f) for f in tr], "시험": [os.path.basename(f) for f in te], "규칙F1": 규칙F1, "무작위F1": 무작위F1, "에폭": []}
STEPS = 120
for ep in range(EP + 1):
    if ep > 0:
        tl = 0
        for _ in range(STEPS):
            xs, ys = zip(*[조각(TR[np.random.randint(len(TR))])[:2] for _ in range(4)])
            x = torch.tensor(np.stack(xs), device=dev); y = torch.tensor(np.stack(ys), device=dev)
            loss = Fn.binary_cross_entropy_with_logits(net(x), y, pos_weight=pw); opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss)
    # 문턱은 학습 모델에서
    ptr = [예측(d) for d in TR[:6]]; th = max(np.linspace(0.2, 0.9, 15), key=lambda t: np.mean([F1(d, p > t) for d, p in zip(TR[:6], ptr)]))
    pte = [예측(d) for d in TE]; f1 = [F1(d, p > th) for d, p in zip(TE, pte)]
    기록["에폭"].append({"에폭": ep, "손실": tl / STEPS if ep else None, "문턱": float(th), "시험F1": f1, "평균": float(np.mean(f1))})
    print("에폭", ep, "손실", round(tl / STEPS, 3) if ep else "-", "시험F1", np.round(f1, 3), "평균", round(float(np.mean(f1)), 3), "규칙", round(float(np.mean(규칙F1)), 3), flush=True)
    c = Image.new("RGB", (4 * 370 + 10, 470), "white"); dr = ImageDraw.Draw(c)
    dr.text((10, 8), f"분할 학습 {NTR} 개 · 에폭 {ep}/{EP} · 시험 F1 평균 {np.mean(f1):.2f} (규칙 {np.mean(규칙F1):.2f})", font=F(26), fill=(20, 40, 90))
    for i, (d, p) in enumerate(zip(TE, pte)):
        c.paste(그림(d, p > th), (10 + i * 370, 50)); dr.text((14 + i * 370, 414), f"{기록['시험'][i][:18]}  F1 {f1[i]:.2f}", font=F(18), fill=(40, 40, 40))
    dr.text((10, 440), "빨강 = 맞힌 경계 · 주황 = 틀리게 찍음 · 초록 = 놓친 경계(사람이 자른 곳)", font=F(18), fill=(90, 90, 100))
    c.save(O + "프레임/%03d.png" % ep)
json.dump(기록, open(O + "기록.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "3", "-i", O + "프레임/%03d.png", "-pix_fmt", "yuv420p", "-vf", "scale=1490:470", O + "학습과정.mp4"])
