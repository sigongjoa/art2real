# 모 판 흐름도 — 실루엣 테두리: 꺾은선 · 호 판 · 모서리 끊고 호 · 부품 #4 #17 #29 · 10-11
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
import 윤곽 as W
from 실물보기 import 실물보기
from s0 import unit
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 330
부 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
k_ = C / 1.1 * 0.95; px = lambda p: (int((p[1] + .05) * k_), int((p[0] + .05) * k_))
def 바탕(sil):
    a = np.full((C, C, 3), 255, np.uint8); s_ = int(C * .95); a[:s_, :s_][cv2.resize((sil > .5).astype(np.uint8), (s_, s_), interpolation=cv2.INTER_NEAREST) > 0] = (225, 228, 236); return a
def 꺾그림(sil):
    a = 바탕(sil)
    for o, _ in W.다각형들(sil):
        q = [px(p) for p in o]
        for j in range(len(q)): cv2.line(a, q[j], q[(j + 1) % len(q)], (200, 40, 40), 2); cv2.circle(a, q[j], 4, (200, 40, 40), -1)
    return a
def 토막그림(sil, 모):
    W.모 = 모; a = 바탕(sil); n = 0
    for o, _ in W.다각형들_호(sil):
        for t, *q in o:
            if t == "L": cv2.line(a, px(q[0]), px(q[1]), (40, 110, 230), 2)
            else:
                n += 1; c = W._원(*[np.array(x) for x in q]); a0, a1, a2 = [np.arctan2(*(np.array(x) - c[0])[::-1]) for x in q]
                if not (min(a0, a2) <= a1 <= max(a0, a2)): a2 = a2 + 2 * np.pi if a2 < a0 else a2 - 2 * np.pi
                pts = [px(c[0] + c[1] * np.array([np.cos(t), np.sin(t)])) for t in np.linspace(a0, a2, 40)]
                for j in range(39): cv2.line(a, pts[j], pts[j + 1], (40, 160, 70), 4)
            cv2.circle(a, px(q[0]), 4, (60, 60, 60), -1)
    return a, n
쪽 = (4, 17, 29)
im = Image.new("RGB", (60 + 4 * (C + 10), 170 + len(쪽) * (C + 50) + 200), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "모 판: 테두리를 모서리(꺾임 ≥ 35°)에서 먼저 끊고, 구간 안에서만 직선/원호", font=F(30), fill="black")
d.text((20, 62), "호 판은 원호가 날카로운 모서리를 둥글게 삼켰다(#17 #29) · 모서리를 경계로 막으면 모서리는 남고 휜 구간만 원호", font=F(19), fill=(90, 90, 90))
for q, t in enumerate(("부품 · 위에서 본 실루엣", "지금: 꺾은선", "호 판(기각)", "모 판: 모서리 끊기")):
    d.text((30 + q * (C + 10) + C // 2, 120), t, font=F(22), fill=(200, 40, 40) if q == 3 else "black", anchor="mm")
for r_, i in enumerate(쪽):
    m0 = unit(trimesh.load(W.RR + 부[i], force="mesh")); S, _ = 실물보기(m0, W.N)
    v = max((0, 2, 4), key=lambda s: sum(t == "A" for o, _ in W.다각형들_호(S[s]) for t, *_ in o) if not setattr(W, "모", False) else 0)   # 원호가 제일 많은 방향
    y = 150 + r_ * (C + 50); sil = S[v]
    im.paste(Image.fromarray(바탕(sil)), (20, y)); d.text((30, y + 5), "#%d" % i, font=F(30), fill="black")
    im.paste(Image.fromarray(꺾그림(sil)), (30 + (C + 10), y))
    for q, 모 in ((2, False), (3, True)):
        a, n = 토막그림(sil, 모); im.paste(Image.fromarray(a), (30 + q * (C + 10), y)); d.text((30 + q * (C + 10) + C // 2, y + C + 18), "원호 %d 개" % n, font=F(18), fill=(40, 150, 60), anchor="mm")
y = im.height - 190; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["1) 35 부품 바탕을 모 판으로 다시 지음 (윤곽0/결과_모) · 원호 맞추기 · 안전장치는 호 판 그대로(부피 3 % · 10 %)",
                       "2) 그 바탕 위에 선 고리 5 판 그대로(메시 선 · 문턱 4 · 조각 검사 · 셸 벽 ≤ 6) → 결과_A/B_모",
                       "대조: 꺾은선 바탕(셸6 · A 32) · 호 판(A 33 · 바탕 중앙 0.534)",
                       "판정: A 통과 ≥ 33 · 조각 ≤ 8 · 바탕 B 중앙 ≥ 0.558(꺾은선) · 눈으로 #17 #29 모서리 남음",
                       "안 하는 것: #4 앞 · 옆 각진 면(직선 실루엣이라 이 판으로는 안 바뀜 → 다음 「휜 판」 과제)"]):
    d.text((30, y + 12 + q * 34), t, font=F(19), fill=(200, 40, 40) if q == 3 else "black")
im.save(os.path.join(H, "모흐름.png")); print("ok")
