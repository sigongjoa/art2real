# 구멍 학습 — 그림 만들기 · CadQuery 로 짓기 · 윗면 래스터 · IoU (판정기준26) · 10-13
import numpy as np
from PIL import Image, ImageDraw
N = 128; 반 = 12.0   # 그림 칸: 세계 −12 ~ 12 mm → 0 ~ 128 화소
px = lambda v: (v + 반) / (2 * 반) * N

def 그림(r, x, y):   # 선 그림(네모 + 원 윤곽) · 정답 영역(네모 − 원)
    a = Image.new("L", (N, N), 0); d = ImageDraw.Draw(a); d.rectangle((px(-10), px(-10), px(10), px(10)), outline=255, width=2); d.ellipse((px(x - r), px(-y - r), px(x + r), px(-y + r)), outline=255, width=2)
    m = Image.new("L", (N, N), 0); e = ImageDraw.Draw(m); e.rectangle((px(-10), px(-10), px(10), px(10)), fill=255); e.ellipse((px(x - r), px(-y - r), px(x + r), px(-y + r)), fill=0)
    return np.asarray(a, np.float32) / 255, np.asarray(m) > 127

def 코드(r, x, y): return "cq.Workplane('XY').box(20, 20, 20).faces('>Z').workplane().center(%.2f, %.2f).hole(%.2f)" % (x, y, 2 * r)

def 짓기(r, x, y):
    import cadquery as cq
    return cq.Workplane("XY").box(20, 20, 20).faces(">Z").workplane().center(x, y).hole(2 * r)

def 윗면(s):   # 지은 CAD 의 윗면(+Z)을 삼각형으로 쪼개 위에서 래스터 → 마스크
    a = Image.new("L", (N, N), 0); d = ImageDraw.Draw(a)
    for f in s.faces(">Z").vals():
        vs, ts = f.tessellate(0.05, 0.2)
        for t in ts: d.polygon([(px(vs[i].x), px(-vs[i].y)) for i in t], fill=255)
    return np.asarray(a) > 127

def 점수(job):   # (r, x, y, 정답 마스크) → IoU · 지어지지 않으면 0
    r, x, y, m = job
    try: c = 윗면(짓기(max(r, .3), x, y))
    except Exception: return 0.0
    return float((c & m).sum() / max((c | m).sum(), 1))

if __name__ == "__main__":   # 자기 검사: 정답 숫자로 지으면 IoU ≈ 1 · 다른 숫자면 낮다 · 속도
    import time
    a, m = 그림(5, 1, -2); t = time.time(); s1 = 점수((5, 1, -2, m)); s2 = 점수((3, 0, 0, m)); dt = (time.time() - t) / 2
    print("정답 %.3f · 틀림 %.3f · 한 번 %.0f ms" % (s1, s2, dt * 1000)); assert s1 > .97 and s2 < .9
