# -*- coding: utf-8 -*-
"""템플릿 투영 — 도안의 판(3D 다각형)을 캡처마다 풀린 자세로 찍어 「예측 분할」을 만든다 (2026-09-29 「어떻게 할건데?」 1 → 2 단계).
    python 투영.py -> out/오메가몬2/지표/투영_<캡처>.png (판 윤곽 색 · 접점 흰 점) · 투영.json(캡처별 판 2D 다각형 · 접점 px)
판 = 이름 붙은 3D 다각형(머리 높이 100 단위 · x 오른쪽 + · y 아래 + · z 앞 +). 반쪽만 적고 거울(L = x 음수). 꼭짓점 중 맞춤.py 로 맞춘 랜드마크는 그 값.
접점 = 두 판 이상이 공유하는 꼭짓점(같은 좌표) — Type I 랜드마크. 판 구조에서 자동으로 나온다.
보임 = 판 법선이 카메라를 향할 때(뒷면 제거). 그 외 가려짐은 아직 안 다룬다.
다음 단계(끌어당김)는 이 그림을 사용자가 보고 난 뒤.
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 자세 import 캡처 as 캡처2D
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
F = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8")); LM = {**F["반쪽"], **F["가운데"]}
def P(k): return tuple(LM[k])                                   # 맞춘 랜드마크 좌표
# ── 판 (반쪽 · x ≥ 0) ──  꼭짓점: 랜드마크 이름 또는 (x, y, z)
반쪽판 = {
    "뿔":     ["뿔아래꼭짓점", "뿔밑동", (9, 0, 12), (7, -40, 8), (3, -80, 4), (0, -98, 2)],
    "코":     ["뿔아래꼭짓점", "눈안쪽위", "눈안쪽아래", (7, 70, 38), "코끝"],
    "눈구멍": ["눈안쪽위", "눈바깥위", "눈바깥아래", "눈안쪽아래"],
    "차양":   [(4.7, 44, 22), (12, 36, 12), (24, 30, -6), (30, 34, -14), "눈바깥위", "눈안쪽위"],
    "윗판":   ["코끝", (7, 70, 38), (18, 66, 8), (24, 75, 0), "윗판끝", (0, 78, 32)],
    "턱":     [(0, 78, 32), "윗판끝", (14, 88, 20), (7.5, 100, 18), "턱끝"],
    "볼":     [(30, 34, -14), "투구최대폭", "볼날개끝", (20, 84, 0), (24, 75, 0), "눈바깥아래"],
    "투구앞": ["뿔밑동", (20, 24, 8), (34, 22, -16), "투구최대폭", (30, 34, -14), (24, 30, -6), (12, 36, 12)],
    "정수리": [(0, 2, 5), (16, 3, 0), (26, 10, -8), (34, 22, -16), (20, 24, 8), "뿔밑동", (0, 27, 26)],
    "안테나": [(23, 20, -19), (25, 18, -20), (62, -30, -40), (60, -32, -39)],
}
대칭판 = {"뿔", "코", "윗판", "턱", "정수리"}                     # 가운데를 지나는 판: 반쪽 + 거울을 한 다각형으로
색 = {"뿔": (200, 200, 220), "코": (255, 220, 0), "눈구멍": (230, 40, 40), "차양": (255, 120, 40), "윗판": (0, 190, 90), "턱": (0, 150, 170), "볼": (200, 90, 230), "투구앞": (120, 160, 255), "정수리": (80, 110, 220), "안테나": (255, 190, 0)}
def 좌표(v): return np.array(P(v) if isinstance(v, str) else v, float)
def 판들():
    out = {}
    for 이름, vs in 반쪽판.items():
        R = [좌표(v) for v in vs]
        if 이름 in 대칭판:
            L = [q * (-1, 1, 1) for q in reversed(R) if q[0] != 0]; out[이름] = R + L
        else:
            out[이름 + "R"] = R; out[이름 + "L"] = [q * (-1, 1, 1) for q in reversed(R)]
    return out
def 접점(판):
    """같은 좌표를 두 판 이상이 쓰면 접점. 이름 = 만나는 판 이름 합."""
    표 = {}
    for n, vs in 판.items():
        for q in vs: 표.setdefault(tuple(np.round(q, 1)), set()).add(n.rstrip("LR"))
    return {"–".join(sorted(s)) + ("" if q[0] == 0 else ("R" if q[0] > 0 else "L")): np.array(q) for q, s in 표.items() if len(s) >= 2}
def 찍기(q, 자):
    R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); c = R @ (np.asarray(q, float) * (1, 1, -1)); return 자["s"] * c[:2] + np.asarray(자["t"]), c[2]
머리중심 = np.array([0.0, 50.0, 0.0])
def 보임(vs, 자):
    n = np.zeros(3)
    for a, b in zip(vs, vs[1:] + vs[:1]): n += np.cross(a, b)         # Newell 법선(모델 좌표)
    if np.dot(n, np.mean(vs, 0) - 머리중심) < 0: n = -n               # 감기 방향과 무관하게 바깥을 향하게
    R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); nc = R @ (n * (1, 1, -1))
    return nc[2] < 0                                                 # 카메라 쪽(−z)을 향하면 보임
if __name__ == "__main__":
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 15); 판 = 판들(); 점 = 접점(판); 결과 = {}
    print("판", len(판), "· 접점", len(점), ":", ", ".join(sorted(점)))
    for 이름, (f, _) in 캡처2D.items():
        자 = F["자세"][이름]; im = Image.fromarray(읽기(J(장면, f))[:, :, ::-1]).convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); r = {}
        순서 = sorted(판, key=lambda n: -np.mean([찍기(q, 자)[1] for q in 판[n]]))        # 먼 판부터 그림
        for n in 순서:
            if not 보임(판[n], 자): continue
            uv = [tuple(찍기(q, 자)[0]) for q in 판[n]]; c = 색[n.rstrip("LR")]; d.polygon(uv, fill=c + (70,), outline=c + (255,)); d.line(uv + uv[:1], fill=c + (255,), width=3); r[n] = [list(map(float, p)) for p in uv]
        vis = Image.alpha_composite(im, ov); d = ImageDraw.Draw(vis); pts = {}
        for k, q in 점.items():
            u, z = 찍기(q, 자);
            if any(k.rstrip("LR").split("–")[0] in n and n in r for n in r) is False: continue
            pts[k] = list(map(float, u)); d.ellipse((u[0] - 4, u[1] - 4, u[0] + 4, u[1] + 4), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        for n in r:
            cx, cy = np.mean(r[n], 0); d.text((cx - 12, cy - 8), n, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
        p = J(OUT, "투영_%s.png" % 이름.replace("/", "-").replace(" ", "_")); vis.convert("RGB").save(p); 결과[이름] = dict(판=r, 접점=pts); print(p, "보이는 판", len(r))
    json.dump(결과, open(J(OUT, "투영.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
