# 열린 면 네 조건 그림 — 줄 = 부품 · 칸 = 사람 / ① 깊이 보임 / ② 테두리 두께 / ③ 둘러쌈 / ④ 반대쪽 바닥 / 판정 · 정답 깊이(A) · 10-10
import os, sys, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "깊이학습"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
import 선고리 as G
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 220; 단 = 110 / 128   # 화소 → 긴 변 100 단위
줄 = [(4, "맞게"), (21, "맞게"), (1, "맞게"), (24, "맞게"), (12, "잘못"), (15, "잘못"), (19, "잘못"), (29, "잘못")]
T = np.load(os.path.join(R, "깊이학습", "시험.npz")); X = T["X"].astype(np.float32); 부 = T["부품"]
쪽이름 = {0: "앞", 1: "뒤", 2: "옆(왼)", 3: "옆(오른)", 4: "위", 5: "아래"}
기준 = {"②": 3.0, "③": 0.10, "④": 3.0}
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 칸(a): return Image.fromarray(a).resize((C, C), Image.NEAREST)
열 = ["사람 부품", "① 깊이 들여다보임", "② 테두리 두께 ≤ 3", "③ 테두리가 둘러쌈", "④ 반대쪽 바닥 ≤ 3", "판정"]
im = Image.new("RGB", (190 + 6 * (C + 12), 130 + len(줄) * (C + 56)), "white"); d = ImageDraw.Draw(im)
d.text((20, 18), "열린 면 = ① 깊이 들여다보이고 ② 테두리가 얇고 ③ 테두리가 둘러싸고 ④ 반대쪽 바닥이 얇다 — 넷 다 맞아야 껍질", font=F(26), fill="black")
d.text((20, 58), "지금 코드는 ① 만 봄 · 위 넷 = 맞게 걸린 껍질 · 아래 넷 = 잘못 걸린 컵 · 홈 · 비탈 (정답 깊이로 계산)", font=F(20), fill=(90, 90, 90))
for j, t in enumerate(열): d.text((190 + j * (C + 12) + C // 2, 108), t, font=F(21), fill=(31, 95, 173), anchor="mm")
for r_, (i, 종) in enumerate(줄):
    y = 130 + r_ * (C + 56); S, L, Dh, D = X[i]; 열림 = G.열린면(S, Dh, D)
    d.text((20, y + C // 2 - 18), "#%d" % i, font=F(30), fill="black"); d.text((20, y + C // 2 + 20), "셸 " + 종 + " 걸림", font=F(19), fill=(40, 150, 60) if 종 == "맞게" else (200, 40, 40))
    m_ = 정(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"))
    im.paste(render(np.asarray(m_.vertices), np.asarray(m_.faces), [1, .6, .8], img_size=C), (190, y))
    if 열림 is None: d.text((190 + (C + 12) + C // 2, y + C // 2), "없음", font=F(26), fill=(200, 40, 40), anchor="mm"); continue
    k, m, tpx, frac = 열림; s8 = S[k] > .5; ok = []
    # ① 깊이 보임
    a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235); a[m] = (240, 120, 60); im.paste(칸(a), (190 + (C + 12), y))
    d.text((190 + (C + 12) + C // 2, y + C + 14), "%s 쪽 · 넓이 %d%%" % (쪽이름[k], 100 * frac), font=F(18), fill=(60, 60, 60), anchor="mm"); ok.append(True)
    # ② 테두리 두께: 열린 영역 테두리에서 실루엣 바깥까지 거리
    dist = cv2.distanceTransform(s8.astype(np.uint8), cv2.DIST_L2, 3); 테 = m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    t2 = float(np.median(dist[테])) * 단 if 테.any() else 0; a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235); 띠 = s8 & ~m & (dist <= np.median(dist[테]) + .5)
    a[띠] = (40, 160, 70) if t2 <= 기준["②"] else (200, 40, 40); im.paste(칸(a), (190 + 2 * (C + 12), y)); ok.append(t2 <= 기준["②"])
    d.text((190 + 2 * (C + 12) + C // 2, y + C + 14), "벽 %.1f" % t2, font=F(20), fill=(40, 150, 60) if ok[-1] else (200, 40, 40), anchor="mm")
    # ③ 둘러쌈: 열린 영역 테두리 중 실루엣 바깥선에 닿은 몫
    바깥 = s8 & ~cv2.erode(s8.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool); 닿음 = 테 & 바깥; c3 = 닿음.sum() / max(테.sum(), 1)
    a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235); a[테] = (40, 160, 70); a[cv2.dilate(닿음.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0] = (220, 30, 30)
    im.paste(칸(a), (190 + 3 * (C + 12), y)); ok.append(c3 <= 기준["③"])
    d.text((190 + 3 * (C + 12) + C // 2, y + C + 14), "바깥에 닿음 %d%%" % (100 * c3), font=F(20), fill=(40, 150, 60) if ok[-1] else (200, 40, 40), anchor="mm")
    # ④ 반대쪽 바닥: 열린 쪽 깊이 + 반대쪽 깊이 사이 남은 두께 (진짜 깊이 기준)
    바닥 = np.clip(1 - D[k] - D[k ^ 1], 0, 1) * 110; t4 = float(np.median(바닥[m])); a = np.full((128, 128, 3), 255, np.uint8); a[s8] = (220, 225, 235)
    v = np.clip(바닥 / 15, 0, 1); a[m] = np.stack([255 * v, 255 * (1 - v) * .8, 60 + 0 * v], -1)[m].astype(np.uint8); im.paste(칸(a), (190 + 4 * (C + 12), y)); ok.append(t4 <= 기준["④"])
    d.text((190 + 4 * (C + 12) + C // 2, y + C + 14), "바닥 %.1f" % t4, font=F(20), fill=(40, 150, 60) if ok[-1] else (200, 40, 40), anchor="mm")
    # 판정
    x = 190 + 5 * (C + 12); 전부 = all(ok)
    for q, (n_, o) in enumerate(zip(("①", "②", "③", "④"), ok)): d.text((x + 20, y + 20 + q * 34), n_ + (" 맞음" if o else " 아님"), font=F(22), fill=(40, 150, 60) if o else (200, 40, 40))
    d.text((x + 20, y + 170), "→ 껍질" if 전부 else "→ 셸 아님", font=F(28), fill=(40, 150, 60) if 전부 else (200, 40, 40))
d.text((20, im.height - 30), "② · ④ 의 3 은 긴 변 100 기준 · ③ 의 10 % 는 테두리 중 실루엣 바깥선에 닿은 몫 — 이 문턱들은 그림을 보고 고칠 수 있는 제안값", font=F(18), fill=(120, 120, 120))
im.save(os.path.join(H, "열린면조건.png")); print("ok")
