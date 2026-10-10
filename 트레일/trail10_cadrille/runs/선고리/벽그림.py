# 5 판 흐름도 — 셸 = ① 깊이 들여다보임 + ② 벽 ≤ 6 (실루엣 바깥에 붙은 테두리는 빼고 잼) · 줄 = 부품 · 정답 깊이(A) · 10-10
import os, sys, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "깊이학습"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
import 선고리 as G
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 200; 단 = 110 / 128; 상한 = 6
줄 = [(4, "맞게"), (21, "맞게"), (1, "맞게"), (24, "맞게"), (12, "잘못"), (15, "잘못"), (19, "잘못"), (29, "잘못")]
T = np.load(os.path.join(R, "깊이학습", "시험.npz")); X = T["X"].astype(np.float32); 부 = T["부품"]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 칸(a): return Image.fromarray(a).resize((C, C), Image.NEAREST)
열 = ["사람 부품", "① 깊이 들여다보임", "옛 벽: 테두리 전부", "새 벽: 바깥 붙은 곳 뺌", "새 판정"]
im = Image.new("RGB", (170 + 5 * (C + 14) + 10, 150 + len(줄) * (C + 50) + 150), "white"); d = ImageDraw.Draw(im)
d.text((20, 16), "셸 5 판: 「안이 깊게 보이고 + 벽이 얇다(≤ %d)」여야 속을 비운다" % 상한, font=F(28), fill="black")
d.text((20, 58), "빨강 = 실루엣 바깥에 붙은 테두리(벽이 없음 → 잴 때 뺌) · 초록/주황 = 벽 · 위 넷 = 진짜 껍질 · 아래 넷 = 지난 판에 잘못 걸린 컵 · 홈", font=F(18), fill=(90, 90, 90))
for j, t in enumerate(열): d.text((170 + j * (C + 14) + C // 2, 118), t, font=F(20), fill=(31, 95, 173), anchor="mm")
for r_, (i, 종) in enumerate(줄):
    y = 140 + r_ * (C + 50); S, L, Dh, D = X[i]; k, m, tpx, frac = G.열린면(S, Dh, D); s8 = S[k] > .5
    d.text((20, y + C // 2 - 18), "#%d" % i, font=F(30), fill="black"); d.text((20, y + C // 2 + 20), "진짜 껍질" if 종 == "맞게" else "컵 · 홈", font=F(19), fill=(40, 150, 60) if 종 == "맞게" else (200, 40, 40))
    m_ = 정(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh")); im.paste(render(np.asarray(m_.vertices), np.asarray(m_.faces), [1, .6, .8], img_size=C), (170, y))
    a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235); a[m] = (240, 120, 60); im.paste(칸(a), (170 + (C + 14), y))
    dist = cv2.distanceTransform(s8.astype(np.uint8), cv2.DIST_L2, 3); 테 = m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    붙 = 테 & (dist <= 1.01); 남 = 테 & ~붙; 옛 = tpx * 단; 새 = float(np.median(dist[남])) * 단 if 남.any() else 0
    for j, (값, 빼기) in enumerate(((옛, False), (새, True))):
        a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235); 띠 = s8 & ~m & (dist <= 값 / 단 + .5)
        a[띠] = (40, 160, 70) if 값 <= 상한 else (230, 140, 30)
        if 빼기: a[cv2.dilate(붙.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0] = (220, 30, 30)
        x = 170 + (2 + j) * (C + 14); im.paste(칸(a), (x, y)); d.text((x + C // 2, y + C + 14), "벽 %.1f" % 값, font=F(22), fill=(40, 150, 60) if 값 <= 상한 else (200, 40, 40), anchor="mm")
    x = 170 + 4 * (C + 14); 셸 = 새 <= 상한; 맞음 = 셸 == (종 == "맞게")
    d.text((x + 10, y + 60), "→ 속 비움" if 셸 else "→ 그대로", font=F(28), fill=(40, 150, 60) if 셸 else (90, 90, 90))
    d.text((x + 10, y + 110), "맞음" if 맞음 else "틀림", font=F(26), fill=(40, 150, 60) if 맞음 else (200, 40, 40))
y = im.height - 140; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
d.text((30, y + 15), "가져가는 것: 선 고리 가 판(메시 모서리 선 · 문턱 4 · 조각 검사) · 속 비우는 방법(빈 속 빼기)과 벽 두께 값은 그대로", font=F(19), fill="black")
d.text((30, y + 48), "바꾸는 것: 셸에 걸리는 조건 하나(벽 ≤ %d) — 걸림이 안 바뀐 부품은 지난 결과를 그대로 씀 · B(AI 깊이)는 #23 이 새로 걸려 한 번 지음" % 상한, font=F(19), fill="black")
d.text((30, y + 81), "판정(지난 판과 같음): A 통과 ≥ 32 · 조각 ≤ 8 · 잘못 걸림 ≤ 3 · 눈으로 껍질 확인 — 문턱 6 은 이 여덟을 보고 정함(확인이지 증명 아님)", font=F(19), fill=(200, 40, 40))
im.save(os.path.join(H, "셸5판흐름.png")); print("ok")
