# -*- coding: utf-8 -*-
"""단면 로프트 머리 값 (10-05 · 외부 LLM 세 곳 공통 「바탕을 단면 로프트로 · 얼굴 면을 단면 안에」)
높이 z 마다: 폭 = 정면 몸 윤곽 x 범위 · 깊이 = 옆 몸 윤곽 y 범위 → 단면 = 둥근 사각(초타원 지수 3) ∩ 앞 V(y ≥ y앞 + r·|x − 가운데|)
r = 얼굴 V 기울기(정수리 0.5 둥글게 · 눈썹 · 눈 1.0 · 부리 1.5 뾰족) · 24 점(중심에서 같은 각도) — 로프트 꼭짓점 수 같게
출력: 스크래치/cad/loft_sec.json"""
import json, numpy as np
from shapely.geometry import Polygon, LineString
SC = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
V = json.load(open(SC + "v3.json", encoding="utf-8"))["v4"]
F = Polygon(V["정면 몸"]).buffer(0); S = Polygon(V["옆 몸"]).buffer(0)
def 범위(P, z):
    q = P.intersection(LineString([(-500, z), (500, z)]))
    if q.is_empty: return None
    xs = [c[0] for g in getattr(q, "geoms", [q]) for c in g.coords]; return min(xs), max(xs)
LV = [(-121, 0.5), (-135, 0.6), (-155, 0.8), (-177, 1.0), (-195, 1.0), (-207, 1.0), (-220, 1.1), (-232, 1.3), (-250, 1.5), (-270, 1.6), (-290, 1.7)]
out = []; yb207 = 999
for z, r in LV:
    fx, sy = 범위(F, z), 범위(S, z)
    if not fx or not sy: print("빈", z); continue
    cx = 0.0; hw = min(70.0, max(abs(fx[0]), abs(fx[1])))   # 70 = 처마 반폭 · 눈 높이 정면 윤곽엔 볼 가시 끝까지 섞임(가시는 따로 붙는 부품) · 좌우 대칭(축 A 기준) — 원화 정면이 살짝 돌아 반폭이 다름 → 큰 쪽
    yf, yb = sy
    if z < -207: yb = min(yb, yb207)   # L2: 눈 아래는 옆 윤곽에 목 · 뒤 아래가 섞여 기둥이 됨 → 뒤 끝을 눈 높이 값까지
    if z == -207: yb207 = yb
    yc = (yf + yb) / 2; hd = (yb - yf) / 2
    pts = []
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        d = np.array([np.cos(a), np.sin(a)])
        lo, hi = 0.0, 400.0
        for _ in range(40):   # 이분법: 둥근 사각 ∩ 앞 V 안쪽 경계
            m = (lo + hi) / 2; x = cx + d[0] * m; y = yc + d[1] * m
            ins = (abs((x - cx) / hw) ** 3 + abs((y - yc) / hd) ** 3 <= 1) and (y >= yf + r * abs(x - cx))
            lo, hi = (m, hi) if ins else (lo, m)
        pts.append([round(cx + d[0] * lo, 2), round(yc + d[1] * lo, 2)])
    out.append({"z": z, "pts": pts}); print(z, "폭", round(2 * hw), "깊이", round(2 * hd), "앞", round(yf), "r", r)
top = out[0]; c = np.mean(top["pts"], axis=0)   # L2: 맨 위가 넓은 채 끝나 모자챙 → 줄어드는 단면 둘로 돔을 닫음
for dz, f in ((4, 0.65), (7, 0.3)):
    out.insert(0, {"z": top["z"] + dz, "pts": [[round(c[0] + (x - c[0]) * f, 2), round(c[1] + (y - c[1]) * f, 2)] for x, y in top["pts"]]})
json.dump(out, open(SC + "loft_sec.json", "w"))
