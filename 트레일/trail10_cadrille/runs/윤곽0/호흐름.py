# 호 판 흐름도 — #4 위 실루엣: 꺾은선 대 직선 + 원호 · 바탕 렌더 둘 · 10-11
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
import 윤곽 as W
from 실물보기 import 실물보기
from s0 import unit
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 330; i = 4
부 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
m0 = unit(trimesh.load(W.RR + 부[i], force="mesh")); S, _ = 실물보기(m0, W.N); sil = S[2]
k = C / 1.1 * 0.95; px = lambda p: (int((p[1] + .05) * k), int((p[0] + .05) * k))
def 바탕():
    a = np.full((C, C, 3), 255, np.uint8); s_ = int(C * .95); a[:s_, :s_][cv2.resize((sil > .5).astype(np.uint8), (s_, s_), interpolation=cv2.INTER_NEAREST) > 0] = (225, 228, 236); return a
def 꺾그림():
    a = 바탕()
    for o, _ in W.다각형들(sil):
        q = [px(p) for p in o]
        for j in range(len(q)): cv2.line(a, q[j], q[(j + 1) % len(q)], (200, 40, 40), 2); cv2.circle(a, q[j], 4, (200, 40, 40), -1)
    return a
def 호그림():
    a = 바탕()
    for o, _ in W.다각형들_호(sil):
        for t, *q in o:
            if t == "L": cv2.line(a, px(q[0]), px(q[1]), (40, 110, 230), 2)
            else:
                c = W._원(*[np.array(x) for x in q]); 각 = [np.arctan2(*(np.array(x) - c[0])[::-1]) for x in (q[0], q[1], q[2])]
                a0, a1, a2 = 각; 
                if not (min(a0, a2) <= a1 <= max(a0, a2)): a2 = a2 + 2 * np.pi if a2 < a0 else a2 - 2 * np.pi
                ts = np.linspace(a0, a2, 40); pts = [px(c[0] + c[1] * np.array([np.cos(t), np.sin(t)])) for t in ts]
                for j in range(39): cv2.line(a, pts[j], pts[j + 1], (40, 160, 70), 4)
            cv2.circle(a, px(q[0]), 4, (60, 60, 60), -1)
    return a
def 렌더(f, v):
    m = trimesh.load(f); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(.9 / max(m.extents)); m.apply_translation([.5] * 3)
    return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C)))
j0, j1 = [json.load(open(os.path.join(H, d, "%02d.json" % i), encoding="utf-8")) for d in ("결과", "결과_호")]
im = Image.new("RGB", (60 + 4 * (C + 10), 140 + 2 * (C + 60) + 170), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "호 판: 바탕 실루엣 테두리를 「꺾은선」 대신 「직선 + 원호」로", font=F(30), fill="black")
d.text((20, 62), "부품 #4 (휜 등판) · 위에서 본 실루엣 → 세 방향 밀어 겹친 바탕 · 바탕이 각지면 그 뒤 파기 · 셸 결과도 끝까지 각짐", font=F(19), fill=(90, 90, 90))
for r_, (이름, 선, f, j) in enumerate((("지금: 꺾은선", 꺾그림(), "결과", j0), ("호 판: 직선(파랑) + 원호(초록)", 호그림(), "결과_호", j1))):
    y = 120 + r_ * (C + 60); d.text((20, y), 이름, font=F(24), fill=(200, 40, 40) if r_ == 0 else (40, 150, 60))
    im.paste(Image.fromarray(선), (20, y + 35))
    for q, v in enumerate(([1, .6, .8], [-1, -.6, -.8], [0, 0, 1])): im.paste(렌더(os.path.join(H, f, "%02d_교차.stl" % i), v), (30 + (q + 1) * (C + 10), y + 35))
    d.text((30 + 2 * (C + 10) + C // 2 + C // 2, y + 10), "바탕 점수 %.2f · 부피 IoU %.2f" % (j["B"], j["B_iou"]), font=F(22), fill="black", anchor="mm")
y = im.height - 160; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["1) 35 부품 바탕을 호 판으로 다시 지음 (윤곽0/결과_호) · 원호는 최소제곱 원, 오차 1.2 화소 안 · 원호가 직선보다 4 화소 넘게 길게 맞을 때만",
                       "2) 안전장치: 원호 판 부피가 꺾은선 판과 3 % 넘게 다르거나 교차 부피가 10 % 넘게 다르면 그 부품은 꺾은선 바탕 · 렌더 틈 구멍(작고 테두리에 붙음)은 버림",
                       "3) 그 바탕 위에 선 고리 5 판 그대로(메시 선 · 문턱 4 · 조각 검사 · 셸 벽 ≤ 6) → 결과_A/B_호",
                       "판정: A 통과 ≥ 32 (지금 32) · 조각 ≤ 8 · 바탕 중앙 점수 안 떨어짐 · 눈으로 #4 둥글게"]):
    d.text((30, y + 15 + q * 34), t, font=F(19), fill=(200, 40, 40) if q == 3 else "black")
im.save(os.path.join(H, "호흐름.png")); print("ok")
