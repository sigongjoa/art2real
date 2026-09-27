# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 3 차 — 눈만 고침(2026-09-28). 「눈동자가 없잖아」.

    python 얼굴3_눈.py           -> 디자인_얼굴3/{눈바탕L,눈바탕R,눈L,눈R,가면투구}_v2.stl · 눈_v2.json(검사)
    python 얼굴3_눈.py --렌더    -> 위 + 멋/얼굴3_눈.jpg ([FRA | 3차 전 | 눈 고침] 정면 · 3/4 · 눈 확대)

겹: 가면(흰) 눈구멍 → 검은 눈바탕(뒤에서 끼움 · 테) → 초록 홍채(바탕의 얕은 자리에 끼움) → 홍채 구멍으로 바탕의 보스(검은 눈동자).
얼굴 나머지는 얼굴3 그대로(가면_v2 = 얼굴3.가면 − 큰 눈구멍).
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
from shapely.geometry import Polygon, Point, box
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3 as F3
from 얼굴3 import OUT, 메, 얇은곳, 틈, 벽, 색, 멋, FRA

# ════════ 손잡이(mm) ════════
키움 = 1.1                 # 눈구멍을 옛 육각에서 사방으로 키운 양
들어감 = 0.6               # 가면 겉 → 눈바탕 앞면
자리 = 1.0                 # 홍채 자리 깊이(= 홍채 두께 · 0.4 는 0.8 살 규칙에 걸려 1.0)
홍채반 = (2.1, 1.8)        # 홍채 반지름(기운 축 · 수직 축) — 둥근 편
홍채밀 = 0.4               # 홍채를 눈구멍 가운데에서 안쪽(코 쪽)으로
동자지름 = 1.6             # 눈동자 보스 지름(홍채 구멍 = + 2 틈)
동자밀 = 0.25              # 눈동자를 홍채 가운데에서 안쪽으로(노려봄)
기울 = np.degrees(np.arctan2(279.3 - 276.8, 9.4 - 4.6))     # 눈 윗날 기울기 27.5°

옛눈 = Polygon(F3.눈반)
구멍 = 옛눈.buffer(키움, join_style=2).intersection(box(2.9, 0, 10.3, 400))      # 뾰족 끝은 자름 — 바깥 끝이 옆벽(x 11)을 뚫지 않게
u = np.array([np.cos(np.radians(기울)), np.sin(np.radians(기울))])
c = np.array(구멍.centroid.coords[0]) - 홍채밀 * u
홍채 = affinity.rotate(affinity.scale(Point(*c).buffer(1.0, 32), *홍채반), 기울)
동자c = c - 동자밀 * u
동자 = Point(*동자c).buffer(동자지름 / 2, 32)

def 기둥(pg, a, b, s):
    """(x, z) 다각형 → 눈 면(y = 눈면y(x)) 에서 a~b 뒤 사이의 기운 기둥. s = ±1(좌우)."""
    from shapely.geometry.polygon import orient
    m = M.CrossSection([list(orient(pg, 1.0).exterior.coords)[:-1]]).extrude(b - a)
    m = m.transform([[s, 0, 0, 0], [5.0 / 11.0, 0, 1, -2.6 + a], [0, 1, 0, 0]])      # 오른쪽에서 짓고 거울은 변환으로
    assert m.volume() > 0, "뒤집힘"; return m

def 눈조각(s):
    창 = 기둥(구멍, -1.0, 벽 + 0.6, s)
    바탕 = 기둥(구멍.buffer(-틈, join_style=2), 들어감, 벽 + 0.5, s) + 기둥(구멍.buffer(0.9, join_style=2), 벽 + 틈, 벽 + 틈 + 0.9, s)
    바탕 = 바탕 - (기둥(홍채.buffer(틈), 들어감 - 0.1, 들어감 + 자리, s) - 기둥(동자, 들어감 - 0.2, 들어감 + 자리 + 0.1, s))   # 자리 파고 보스 남김
    초록 = 기둥(홍채, 들어감, 들어감 + 자리 - 0.05, s) - 기둥(동자.buffer(틈), 들어감 - 0.2, 들어감 + 자리 + 0.1, s)
    return 창, 바탕, 초록
창L, 바탕L, 눈L = 눈조각(-1); 창R, 바탕R, 눈R = 눈조각(1)
가면 = max((F3.가면 - 창L - 창R).decompose(), key=lambda p: p.volume())
가면부풀 = F3.F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]

새 = {"가면투구_v2": (가면, 색["흰"], "얼굴3 가면 − 키운 눈구멍(옛 육각 + %.1f)" % 키움),
      "눈바탕L_v2": (바탕L, 색["검"], "검은 눈바탕 — 뒤에서 끼움 · 홍채 자리 %.1f + 눈동자 보스 Ø%.1f" % (자리, 동자지름)), "눈바탕R_v2": (바탕R, 색["검"], "검은 눈바탕"),
      "눈L_v2": (눈L, 색["초록"], "초록 홍채 — 바탕 자리에 끼움 · 눈동자 구멍 Ø%.2f · 틈 0.12" % (동자지름 + 2 * 틈)), "눈R_v2": (눈R, 색["초록"], "초록 홍채")}

def 치수():
    def 폭(pg, d): q = np.array(pg.exterior.coords) @ d; return round(float(q.max() - q.min()), 2)
    v = np.array([-u[1], u[0]])
    보임 = 구멍.difference(홍채)
    return dict(눈구멍=dict(길이=폭(구멍, u), 높이=폭(구멍, v), 가로x=폭(구멍, np.array([1, 0])), 세로z=폭(구멍, np.array([0, 1])), 옛_길이=폭(옛눈, u), 옛_높이=폭(옛눈, v)),
                홍채=dict(길이=2 * 홍채반[0], 높이=2 * 홍채반[1], 두께=자리 - 0.05),
                눈동자=dict(보스지름=동자지름, 홍채구멍지름=동자지름 + 2 * 틈, 홍채대비=round(동자지름 / (2 * 홍채반[1]), 2), 홍채살_최소=round(홍채.exterior.distance(동자.buffer(틈)), 2)),
                검은테=dict(최소=round(구멍.exterior.distance(홍채), 2), 위아래=round((폭(구멍, v) - 2 * 홍채반[1]) / 2, 2),
                          안쪽=round(폭(구멍, u) / 2 - 홍채반[0] - 홍채밀, 2), 바깥=round(폭(구멍, u) / 2 - 홍채반[0] + 홍채밀, 2), 넓이비_검정_대_구멍=round(보임.area / 구멍.area, 2)),
                들어감=들어감)

def 내보내기():
    검, 겹 = {}, {}
    for n, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각"
        t.export(os.path.join(OUT, n + ".stl"))
        검[n] = dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(t.extents, 2).tolist())
        if n != "가면투구_v2": 검[n]["얇은곳mm3"] = 얇은곳(m)          # 가면 전체 검사는 메모리 폭주 — 눈 부품만
    검["대조_옛부품_얇은곳mm3"] = {n: 얇은곳(F3.새[n][0]) for n in ("눈바탕R", "눈R")}
    ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:]: 겹["%s∩%s" % (a, b)] = round((새[a][0] ^ 새[b][0]).volume(), 4)
    assert max(겹.values()) < 0.005, 겹
    d = dict(설명="얼굴 3 차 눈 고침(09-28) — 검은 테 + 초록 홍채 + 검은 눈동자(바탕의 보스)", 치수mm=치수(), 겹침=겹,
             도색_스티커=["흰 반사점 — 눈동자 위 바깥쪽 Ø0.5 쯤 · 출력 불가 → 도색/스티커"],
             대조_옛부품_얇은곳mm3=검.pop("대조_옛부품_얇은곳mm3"), 부품={n: dict(파일=n + ".stl", 색=c_, 비고=b, **검[n]) for n, (m, c_, b) in 새.items()})
    json.dump(d, open(os.path.join(OUT, "눈_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(치수=d["치수mm"], 검사=검, 겹침=겹), ensure_ascii=False, default=float))

# ════════ 렌더: 얼굴3 의 빠른 렌더 틀 재사용 ════════
컷 = [("정면", 0, 0, 70.0, 292.9), ("반옆", 62, 8, 70.0, 288.0), ("눈정면", 0, 0, 26.0, 277.0), ("눈반옆", 38, 5, 26.0, 277.0)]
def 렌더():
    from PIL import Image, ImageDraw, ImageFont
    D = os.path.join(OUT, "_바퀴", "눈"); v2 = {n[:-3]: n for n in 새}
    for 이름, 고침 in (("전", False), ("후", True)):
        d = os.path.join(D, 이름); os.makedirs(d, exist_ok=True)
        parts = [(os.path.join(OUT, (v2.get(n, n) if 고침 else n) + ".stl"), c_) for n, (m, c_, _) in F3.새.items()]
        jf = os.path.join(d, "빠른.json"); pf = os.path.join(d, "빠른.py")
        json.dump(dict(부품=parts, out=d.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
        open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
        r = subprocess.run([F3.F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 그(이름, c_): return Image.open(os.path.join(D, 이름, c_ + ".png")).convert("RGB")
    def 띠(im): w, h = im.size; return im.crop((0, int(h * 0.27), w, int(h * 0.73)))       # 눈 확대 칸은 가운데 띠만
    m12 = Image.open(os.path.join(FRA, "mh_12.jpg")); m13 = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
    px = 26.0 / 0.155 / 2; py = 222 + (293.3 - 277.0) / 0.155
    fra눈 = m12.crop((int(229 - px), int(py - px * 0.46), int(229 + px), int(py + px * 0.46)))
    줄 = [[("FRA 정면(mh_12)", m12), ("3차 전", 그("전", "정면")), ("3차 눈 고침", 그("후", "정면"))],
          [("FRA 3/4(mh_13 뒤집음)", m13), ("3차 전", 그("전", "반옆")), ("3차 눈 고침", 그("후", "반옆"))],
          [("FRA 눈", fra눈), ("3차 전 눈", 띠(그("전", "눈정면"))), ("눈 고침 눈", 띠(그("후", "눈정면")))],
          [("눈 고침 3/4 확대", 띠(그("후", "눈반옆"))), ("3차 전 3/4 확대", 띠(그("전", "눈반옆")))]]
    W, 높이 = 1980, [560, 560, 300, 300]
    S = Image.new("RGB", (W, sum(높이) + 45 * 4 + 10), (245, 245, 243)); d = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, 높이):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); d.text((x + 4, y - 38), t, font=f, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴3_눈.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--렌더" in sys.argv: 렌더()
