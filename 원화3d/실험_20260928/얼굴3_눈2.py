# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 3 차 — 눈 둘째 고침(2026-09-28). 「놀란 부엉이 눈」 → 노려보는 눈.

    python 얼굴3_눈2.py           -> 디자인_얼굴3/{가면투구,눈바탕L/R,눈L/R}_v3.stl · 눈_v3.json(검사)
    python 얼굴3_눈2.py --렌더    -> 위 + 멋/얼굴3_눈2.jpg ([FRA | 눈 고침 1 | 눈 고침 2] 정면 · 눈 확대 · 3/4 확대)

눈구멍 = 기운 아몬드 육각(안쪽 끝 낮고 뾰족 · 윗변 사선). 홍채 = 큰 원을 눈구멍(테 안쪽)으로 자름 — 윗변이 눈꺼풀.
눈동자 = 윗변에 붙어 일부 잘림(보스가 테와 한 몸). 구조 · 기둥 · 렌더 틀은 얼굴3_눈 그대로.
"""
import os, sys, json, subprocess
import numpy as np
from shapely.geometry import Polygon, Point, box
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_눈 as E
from 얼굴3_눈 import F3, 기둥, 들어감, 자리
from 얼굴3 import OUT, 메, 얇은곳, 틈, 벽, 색, 멋, FRA

# ════════ 손잡이(mm) ════════
# 눈구멍 (x, z) 오른쪽: 안쪽 끝 → 윗변(사선) → 바깥 위 → 바깥 세로 → 아랫변
구멍점 = [(2.9, 275.5), (9.6, 279.9), (10.3, 279.3), (10.3, 276.8), (8.4, 274.6), (5.4, 274.5)]
테 = 0.5                   # 검은 윤곽선 폭
홍채지름 = 4.8
잘림 = 0.27                # 홍채 원 지름 가운데 윗변(눈꺼풀)에 잘리는 몫
홍채x = 6.7                # 홍채 원 중심이 놓이는 윗변 위의 x
동자지름 = 1.8
동자깊이 = 0.55            # 눈동자 중심이 윗변(테 안쪽 선)에서 내려온 거리 — 반지름보다 작으면 윗변에 잘림
동자밀 = 0.35              # 눈동자를 홍채 중심에서 안쪽(코 쪽)으로
for i, a in enumerate(sys.argv):      # 바퀴 돌 때 손잡이: --잘림 0.3 --동자깊이 0.5 …
    if a.startswith("--") and a[2:] in ("테", "홍채지름", "잘림", "홍채x", "동자지름", "동자깊이", "동자밀"): globals()[a[2:]] = float(sys.argv[i + 1])

구멍 = Polygon(구멍점); 안 = 구멍.buffer(-테, join_style=2)
A, B = np.array(구멍점[0]), np.array(구멍점[1])
u = (B - A) / np.linalg.norm(B - A); n = np.array([u[1], -u[0]])          # 윗변 방향 · 아래쪽 법선
기울 = float(np.degrees(np.arctan2(u[1], u[0])))
윗 = A + u * (홍채x - A[0]) / u[0] + n * 테                                 # 테 안쪽 윗변 위의 점
c = 윗 + n * (0.5 - 잘림) * 홍채지름
원 = Point(*c).buffer(홍채지름 / 2, 48)
홍채 = 원.intersection(안).buffer(-0.2).buffer(0.2)                          # 뾰족 귀는 둥글림(얇은 살 방지)
동자c = 윗 - u * 동자밀 + n * 동자깊이
동자 = Point(*동자c).buffer(동자지름 / 2, 32)
초록꼴 = 홍채.difference(동자.buffer(틈)).buffer(-0.2).buffer(0.2)
초록꼴 = max(getattr(초록꼴, "geoms", [초록꼴]), key=lambda g: g.area)

def 눈조각(s):
    창 = 기둥(구멍, -1.0, 벽 + 0.6, s)
    바탕 = 기둥(구멍.buffer(-틈, join_style=2), 들어감, 벽 + 0.5, s) + 기둥(구멍.buffer(0.9).intersection(box(2.0, 0, 11.2, 400)), 벽 + 틈, 벽 + 틈 + 0.9, s)     # 턱(뒤 걸림) — 둥근 모 · 뾰족 끝 가시 자름
    바탕 = 바탕 - 기둥(초록꼴.buffer(틈), 들어감 - 0.1, 들어감 + 자리, s)       # 초록 자리만 팜 — 눈동자 보스 · 테는 남음
    초록 = 기둥(초록꼴, 들어감, 들어감 + 자리 - 0.05, s)
    return 창, 바탕, 초록
창L, 바탕L, 눈L = 눈조각(-1); 창R, 바탕R, 눈R = 눈조각(1)
메움 = 기둥(E.옛눈, 0.0, 벽, -1) + 기둥(E.옛눈, 0.0, 벽, 1)          # F3.가면 에는 옛 육각 구멍이 이미 뚫려 있다 — 막고 새로 뚫는다(안 막으면 새 구멍 밖으로 옛 구멍이 삐져나옴)
가면 = max((F3.가면 + 메움 - 창L - 창R).decompose(), key=lambda p: p.volume())
가면부풀 = F3.F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]

새 = {"가면투구_v3": (가면, 색["흰"], "얼굴3 가면 − 아몬드 육각 눈구멍"),
      "눈바탕L_v3": (바탕L, 색["검"], "검은 눈바탕 — 뒤에서 끼움 · 홍채 자리 %.1f + 눈동자 보스 Ø%.1f(윗변 테와 한 몸)" % (자리, 동자지름)), "눈바탕R_v3": (바탕R, 색["검"], "검은 눈바탕"),
      "눈L_v3": (눈L, 색["초록"], "초록 홍채 — Ø%.1f 원을 눈구멍으로 자름 · 틈 0.12" % 홍채지름), "눈R_v3": (눈R, 색["초록"], "초록 홍채")}

def 치수():
    def 폭(pg, d): q = np.array(pg.exterior.coords) @ d; return round(float(q.max() - q.min()), 2)
    ex, ez = np.array([1, 0]), np.array([0, 1])
    xs = np.linspace(3.0, 10.2, 145)
    from shapely.geometry import LineString
    세로 = max(구멍.intersection(LineString([(x, 0), (x, 400)])).length for x in xs)
    위살 = 동자.buffer(틈).intersection(안).area / 동자.buffer(틈).area
    return dict(눈구멍=dict(가로x=폭(구멍, ex), 세로z_전체=폭(구멍, ez), 가장높은곳_세로=round(세로, 2), 윗변수직높이=폭(구멍, n), 윗변기울기deg=round(기울, 1),
                          안쪽끝각deg=round(기울 + np.degrees(np.arctan2(구멍점[0][1] - 구멍점[-1][1], 구멍점[-1][0] - 구멍점[0][0])), 1), 넓이=round(구멍.area, 2)),
                홍채=dict(원지름=홍채지름, 윗잘림몫=잘림, 보이는_가로=폭(초록꼴, ex), 보이는_세로=폭(초록꼴, ez), 두께=자리 - 0.05,
                        원에서_남은몫=round(홍채.area / 원.area, 2), 아래도_잘림=bool(원.difference(안.buffer(0.01)).difference(Polygon([tuple(윗 - 9 * u), tuple(윗 + 9 * u), tuple(윗 + 9 * u - 9 * n), tuple(윗 - 9 * u - 9 * n)])).area > 0.05)),
                눈동자=dict(보스지름=동자지름, 보이는몫=round(위살, 2), 홍채살_아래=round(float(홍채지름 / 2 - (동자c - c) @ n - 동자지름 / 2 - 틈), 2)),
                넓이비=dict(초록_대_눈구멍=round(초록꼴.area / 구멍.area, 2), 초록_대_테안쪽=round(초록꼴.area / 안.area, 2), 검정_대_눈구멍=round(1 - 초록꼴.area / 구멍.area, 2)),
                테=테, 들어감=들어감)

def 내보내기():
    검, 겹 = {}, {}
    for k, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, k + " 안 닫힘/조각"
        t.export(os.path.join(OUT, k + ".stl"))
        검[k] = dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(t.extents, 2).tolist())
        if k != "가면투구_v3": 검[k]["얇은곳mm3"] = 얇은곳(m)
    ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:]: 겹["%s∩%s" % (a, b)] = round((새[a][0] ^ 새[b][0]).volume(), 4)
    assert max(겹.values()) < 0.005, 겹
    d = dict(설명="얼굴 3 차 눈 둘째 고침(09-28) — 아몬드 육각 눈구멍 · 눈꺼풀에 잘린 홍채 · 윗변에 붙은 눈동자", 치수mm=치수(), 눈구멍점=구멍점, 겹침=겹,
             부품={k: dict(파일=k + ".stl", 색=c_, 비고=b, **검[k]) for k, (m, c_, b) in 새.items()})
    json.dump(d, open(os.path.join(OUT, "눈_v3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(치수=d["치수mm"], 검사=검, 겹침최대=max(겹.values())), ensure_ascii=False, default=float))

def 렌더():
    from PIL import Image, ImageDraw, ImageFont
    D = os.path.join(OUT, "_바퀴", "눈"); v3 = {k[:-3]: k for k in 새}
    d = os.path.join(D, "후2"); os.makedirs(d, exist_ok=True)
    parts = [(os.path.join(OUT, v3.get(k, k) + ".stl"), c_) for k, (m, c_, _) in F3.새.items()]
    jf = os.path.join(d, "빠른.json"); pf = os.path.join(d, "빠른.py")
    json.dump(dict(부품=parts, out=d.replace("\\", "/"), 컷=E.컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F3.F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 그(이름, c_): return Image.open(os.path.join(D, 이름, c_ + ".png")).convert("RGB")       # 「후」 = 눈 고침 1(이미 렌더됨)
    def 띠(im): w, h = im.size; return im.crop((0, int(h * 0.27), w, int(h * 0.73)))
    m12 = Image.open(os.path.join(FRA, "mh_12.jpg")); m13 = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
    px = 26.0 / 0.155 / 2; py = 222 + (293.3 - 277.0) / 0.155
    fra눈 = m12.crop((int(229 - px), int(py - px * 0.46), int(229 + px), int(py + px * 0.46)))
    w3, h3 = m13.size; fra눈3 = m13.crop((int(w3 * 0.42), int(h3 * 0.58), int(w3 * 0.86), int(h3 * 0.58 + w3 * 0.44 * 0.46)))
    줄 = [[("FRA 정면(mh_12)", m12), ("눈 고침 1", 그("후", "정면")), ("눈 고침 2", 그("후2", "정면"))],
          [("FRA 눈", fra눈), ("눈 고침 1 눈", 띠(그("후", "눈정면"))), ("눈 고침 2 눈", 띠(그("후2", "눈정면")))],
          [("FRA 3/4 눈(mh_13 뒤집음)", fra눈3), ("눈 고침 1 3/4 확대", 띠(그("후", "눈반옆"))), ("눈 고침 2 3/4 확대", 띠(그("후2", "눈반옆")))]]
    W, 높이 = 1990, [560, 300, 300]
    S = Image.new("RGB", (W, sum(높이) + 45 * 3 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, 높이):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); dr.text((x + 4, y - 38), t, font=f, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴3_눈2.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--렌더" in sys.argv: 렌더()
