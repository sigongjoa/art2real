# 로드맵 1 단계(판정기준27) — 여러 부품 프로그램: 바탕(상자 · 원기둥) + 특징 칸 3(없음 · 구멍 · 가로 홈 · 세로 홈) · 그림 · CadQuery · 윗면 래스터 · 10-13
import numpy as np
from PIL import Image, ImageDraw
N = 128; 반 = 14.0; 높 = 10.0; 홈깊이 = 4.0
px = lambda v: (v + 반) / (2 * 반) * N
종류 = ["없음", "구멍", "가로홈", "세로홈"]

# 프로그램 = {"바탕": 0 상자 | 1 원기둥, "b": [가로, 세로, 반지름], "칸": [(종류, x, y, a, b) × 3]}  · 구멍: a = 반지름 · 홈: a = 길이, b = 폭
def 무작위(g):
    원 = g.random() < .35; b = [g.uniform(14, 22), g.uniform(10, 20), g.uniform(6, 10)]
    n = g.integers(0, 4); 칸 = []
    for _ in range(3):
        if len(칸) < n:
            t = int(g.integers(1, 4))
            if 원: lim = b[2] * .55; x, y = g.uniform(-lim, lim, 2)
            else: x, y = g.uniform(-b[0] / 2 * .6, b[0] / 2 * .6), g.uniform(-b[1] / 2 * .6, b[1] / 2 * .6)
            칸.append((t, x, y, g.uniform(1, 3.5) if t == 1 else g.uniform(4, 12), g.uniform(2, 4)))
        else: 칸.append((0, 0, 0, 0, 0))
    return {"바탕": int(원), "b": b, "칸": 칸}

def 코드(p):
    s = "cq.Workplane('XY')" + (".box(%.1f, %.1f, 10)" % (p["b"][0], p["b"][1]) if p["바탕"] == 0 else ".circle(%.1f).extrude(10)" % p["b"][2])
    for t, x, y, a, b in p["칸"]:
        if t == 1: s += "\n  .faces('>Z').workplane().center(%.1f, %.1f).hole(%.1f)" % (x, y, 2 * a)
        elif t in (2, 3): s += "\n  .faces('>Z').workplane().center(%.1f, %.1f).rect(%.1f, %.1f).cutBlind(-4)" % ((x, y, a, b) if t == 2 else (x, y, b, a))
    return s

def 짓기(p):
    import cadquery as cq
    if p["바탕"] == 0: s = cq.Workplane("XY").box(max(p["b"][0], 2), max(p["b"][1], 2), 높).translate((0, 0, 높 / 2))
    else: s = cq.Workplane("XY").circle(max(p["b"][2], 1)).extrude(높)
    for t, x, y, a, b in p["칸"]:
        try:
            if t == 1: s = s.cut(cq.Workplane("XY").center(x, y).circle(max(a, .3)).extrude(높 + 2).translate((0, 0, -1)))
            elif t in (2, 3):
                w, h = (max(a, .5), max(b, .5)) if t == 2 else (max(b, .5), max(a, .5))
                s = s.cut(cq.Workplane("XY").center(x, y).rect(w, h).extrude(홈깊이 + 1).translate((0, 0, 높 - 홈깊이)))
        except Exception: pass
    return s

def 윗면(s):
    a = Image.new("L", (N, N), 0); d = ImageDraw.Draw(a); top = max(f.Center().z for f in s.faces().vals())
    for f in s.faces().vals():
        if abs(f.Center().z - top) > 1e-3 or f.normalAt().z < .99: continue
        vs, ts = f.tessellate(0.05, 0.2)
        for t in ts: d.polygon([(px(vs[i].x), px(-vs[i].y)) for i in t], fill=255)
    return np.asarray(a) > 127

def 그림(p):   # 선 그림: 바탕 윤곽 + 특징 윤곽(위에서 본)
    a = Image.new("L", (N, N), 0); d = ImageDraw.Draw(a)
    if p["바탕"] == 0: w, h = p["b"][0] / 2, p["b"][1] / 2; d.rectangle((px(-w), px(-h), px(w), px(h)), outline=255, width=2)
    else: r = p["b"][2]; d.ellipse((px(-r), px(-r), px(r), px(r)), outline=255, width=2)
    for t, x, y, a_, b in p["칸"]:
        if t == 1: d.ellipse((px(x - a_), px(-y - a_), px(x + a_), px(-y + a_)), outline=255, width=2)
        elif t in (2, 3):
            w, h = (a_ / 2, b / 2) if t == 2 else (b / 2, a_ / 2); d.rectangle((px(x - w), px(-y - h), px(x + w), px(-y + h)), outline=255, width=2)
    return np.asarray(a, np.float32) / 255

def 점수(job):   # (프로그램, 정답 마스크) → IoU
    p, m = job
    try: c = 윗면(짓기(p))
    except Exception: return 0.0
    return float((c & m).sum() / max((c | m).sum(), 1))
def 정답(p):
    try: return 윗면(짓기(p))
    except Exception: return None

if __name__ == "__main__":   # 자기 검사
    import time
    g = np.random.default_rng(1); ok = 0; t = time.time()
    for i in range(20):
        p = 무작위(g); m = 정답(p); s = 점수((p, m)); ok += s > .99
    q = dict(p); q["칸"] = [(0, 0, 0, 0, 0)] * 3
    print("자기 IoU>0.99: %d/20 · 특징 지운 판 %.3f · 한 번 %.0f ms" % (ok, 점수((q, m)), (time.time() - t) / 41 * 1000)); print(코드(p))
    assert ok == 20
