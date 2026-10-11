# 기능0 학습 흐름도 — 선 그림 → 정리된 깊이(학생) → 통과된 짓기 방식 · 10-11
import os, sys, numpy as np, cv2, torch
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path.insert(0, os.path.join(R, "깊이학습"))
from 학습 import 망
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
X = np.load(os.path.join(R, "깊이학습", "시험.npz"))["X"]; T = np.load(os.path.join(R, "깊이학습", "정답T_시험.npy"))
m = 망().cuda(); m.load_state_dict(torch.load(os.path.join(R, "깊이학습", "모델.pt"))); m.eval()
def 깊(d, s):
    v = np.where(s, d, np.nan); lo, hi = np.nanmin(v), np.nanmax(v); a = np.where(s, 40 + 200 * (1 - (d - lo) / max(hi - lo, 1e-6)), 255).astype(np.uint8)
    return cv2.resize(np.stack([a] * 3, -1), (230, 230), interpolation=cv2.INTER_NEAREST)
im = Image.new("RGB", (2300, 1260), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "학습: 선 그림만 보고 「정리된 깊이」를 맞히는 학생 → 통과된 짓기 방식(교차 + 큰 홈 + 선 고리 디테일)에 그대로 넣는다", font=F(28), fill="black")
열 = ["선 그림(입력)", "교차 깊이(입력)", "실물 깊이(옛 목표)", "정리된 깊이(새 목표)", "옛 학생(실물 깊이 학습)"]
for j, t in enumerate(열): d.text((180 + j * 245 + 115, 80), t, font=F(19), fill=(200, 40, 40) if j == 3 else (31, 95, 173), anchor="mm")
for r_, (i, k) in enumerate(((7, 4), (33, 2), (13, 0))):
    x = X[i].astype(np.float32); s = x[0, k] > .5; y = 100 + r_ * 250; d.text((20, y + 100), "#%d" % i, font=F(30), fill="black")
    with torch.no_grad(): p = m(torch.from_numpy(x[:3, k:k + 1]).permute(1, 0, 2, 3).cuda())[0, 0].cpu().numpy()
    L = np.where(x[1, k] > .5, 0, np.where(s, 225, 255)).astype(np.uint8)
    for j, a in enumerate([cv2.resize(np.stack([L] * 3, -1), (230, 230), interpolation=cv2.INTER_NEAREST), 깊(x[2, k], s), 깊(x[3, k], s), 깊(T[i, k].astype(np.float32), s), 깊(p, s)]):
        im.paste(Image.fromarray(a), (180 + j * 245, y))
y = 860
for q, t in enumerate(["1) 정리된 깊이 = 교차 깊이에서 시작 · 큰 홈은 평평한 바닥 하나 · 선 고리는 깊이 하나 — 통과된 35 부품을 지은 바로 그 방식을 깊이 그림에서 (2,883 부품)",
                       "2) 학생 = 지금 깊이 망(작은 U-Net)을 이어 학습 · 목표만 실물 깊이 → 정리된 깊이 · 입력은 선 · 실루엣 · 교차 깊이(그림에서 계산)",
                       "3) 시험 35: 학생 깊이로 같은 짓기(교차 + 큰 홈 + 선 고리) → 옛 학생 깊이로 지은 것 · 통과된 한 벌(정답 깊이)과 썸네일로 나란히"]):
    d.text((20, y + q * 45), t, font=F(20), fill="black")
y = im.height - 170; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["판정: 사용자 썸네일 1 순위 · Claude 눈 — 새 학생이 옛 학생보다 통과된 한 벌에 같거나 가까움 35 중 20 이상 · 부스러기 늘지 않음",
                       "안 함: IoU · 선 점수로 통과 선언 · 손으로 지은 18 부품의 기능 순서(원기둥 · 구)는 이번 학습 대상 아님"]):
    d.text((30, y + 15 + q * 50), t, font=F(21), fill=(200, 40, 40) if q == 0 else "black")
im.save(os.path.join(H, "흐름9.png")); print("ok")
