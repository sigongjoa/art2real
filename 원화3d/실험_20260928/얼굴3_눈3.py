# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 3 차 — 눈 셋째 고침(2026-09-28). 「눈동자는 원형인데 네가 만든 건 각지다」.

    python 얼굴3_눈3.py           -> 디자인_얼굴3/{가면투구,눈바탕L/R,눈L/R}_v4.stl · 눈_v4.json(검사)
    python 얼굴3_눈3.py --렌더    -> 위 + 멋/얼굴3_눈3.jpg ([FRA | 눈 고침 2 | 눈 고침 3] 정면 · 눈 확대 · 3/4 확대)

눈구멍 = (홍채 + 테) 원 ∩ 눈꺼풀 반평면 + 눈꼬리 삼각(원의 접선). 윗변 사선은 고침 2 그대로.
홍채 = 원에서 윗변 위쪽만 잘림. 눈동자 = 온전한 원. 가면은 옛 구멍 없이 다시 지어 새 구멍만 뚫는다(메움 자국 없음).
"""
import os, sys, json, subprocess
import numpy as np
from shapely.geometry import Polygon, Point, MultiPoint
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_눈 as E
from 얼굴3_눈 import F3, 기둥, 들어감, 자리
from 얼굴3 import OUT, 메, 얇은곳, 틈, 벽, 색, 멋, FRA, 볼록, V홈, 송곳니

# ════════ 손잡이(mm) ════════
A, B = np.array((2.9, 275.5)), np.array((9.6, 279.9))     # 윗변 사선(고침 2 그대로)
테 = 0.5
홍채지름 = 4.2
잘림 = 0.20                # 홍채 지름 가운데 윗변에 잘리는 몫
발x = 6.70                 # 홍채 중심에서 윗변에 내린 발의 x
꼬리 = (3.3, 3.0)          # 눈꼬리: 발에서 윗변을 따라 (안쪽, 바깥쪽) 거리
동자지름 = 1.6
동자깊이 = 1.50            # 눈동자 중심이 테 안쪽 윗변에서 내려온 거리(반지름 + 0.3 이상)
동자밀 = 0.25              # 홍채 중심에서 안쪽(코 쪽)으로
for i, a in enumerate(sys.argv):
    if a.startswith("--") and a[2:] in ("홍채지름", "잘림", "발x", "동자지름", "동자깊이", "동자밀"): globals()[a[2:]] = float(sys.argv[i + 1])

u = (B - A) / np.linalg.norm(B - A); n = np.array([u[1], -u[0]])           # 윗변 방향 · 아래쪽 법선
기울 = float(np.degrees(np.arctan2(u[1], u[0])))
발 = A + u * (발x - A[0]) / u[0]
def 아래(p): return Polygon([tuple(p - 20 * u), tuple(p + 20 * u), tuple(p + 20 * u + 20 * n), tuple(p - 20 * u + 20 * n)])   # p 를 지나는 사선의 아래 반평면
c = 발 + n * (테 + (0.5 - 잘림) * 홍채지름)
원 = Point(*c).buffer(홍채지름 / 2, 24)                                     # 사분원 24 = 둘레 96
큰원 = Point(*c).buffer(홍채지름 / 2 + 테, 24)
구멍 = MultiPoint(list(큰원.exterior.coords) + [tuple(발 - u * 꼬리[0]), tuple(발 + u * 꼬리[1])]).convex_hull.intersection(아래(발))
홍채 = 원.intersection(아래(발 + n * 테)).buffer(-0.2).buffer(0.2)            # 윗변 양 끝 귀만 둥글림
동자c = 발 + n * (테 + 동자깊이) - u * 동자밀
동자 = Point(*동자c).buffer(동자지름 / 2, 16)                               # 둘레 64
초록꼴 = 홍채.difference(동자.buffer(틈, 16))
assert 원.contains(동자.buffer(틈 + 0.79)) and 홍채.contains(동자.buffer(0.3)), "눈동자 둘레 초록 살 < 0.8 또는 윗변 띄움 < 0.3"
assert 구멍.bounds[0] >= 2.9 and 구멍.bounds[2] <= 10.3, 구멍.bounds

def 눈조각(s):
    창 = 기둥(구멍, -1.0, 벽 + 0.6, s)
    바탕 = 기둥(구멍.buffer(-틈, join_style=2), 들어감, 벽 + 0.5, s) + 기둥(구멍.buffer(0.9), 벽 + 틈, 벽 + 틈 + 0.9, s)
    # 기둥() 은 바깥 윤곽만 읽는다(구멍 무시) — 눈동자는 기둥끼리 뺀다
    바탕 = 바탕 - (기둥(홍채.buffer(틈), 들어감 - 0.1, 들어감 + 자리, s) - 기둥(동자, 들어감 - 0.2, 들어감 + 자리 + 0.1, s))   # 자리 파고 보스 남김
    초록 = 기둥(홍채, 들어감, 들어감 + 자리 - 0.05, s) - 기둥(동자.buffer(틈, 16), 들어감 - 0.2, 들어감 + 자리 + 0.1, s)
    return 창, 바탕, 초록
창L, 바탕L, 눈L = 눈조각(-1); 창R, 바탕R, 눈R = 눈조각(1)
# 가면: 얼굴3 의 식에서 옛 눈구멍(창)만 빼고 그대로 — 옛 구멍이 애초에 없다
가면 = V홈(F3.껍질 - F3.F2.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
for s in (1, -1):
    가면 = 가면 - 볼록([(s * x, y, z) for x in (송곳니["x"] - 0.45, 송곳니["x"] + 0.45) for y in (-6, -2.0)
                     for z in (송곳니["위"], 송곳니["아래"] + 1.5)] + [(s * 송곳니["x"], y, 송곳니["아래"]) for y in (-6, -2.2)])
가면 = max((가면 - 창L - 창R).decompose(), key=lambda p: p.volume())
가면부풀 = F3.F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]

새 = {"가면투구_v4": (가면, 색["흰"], "얼굴3 가면(옛 구멍 없음) − 원 ∩ 눈꺼풀 눈구멍"),
      "눈바탕L_v4": (바탕L, 색["검"], "검은 눈바탕 — 뒤에서 끼움 · 홍채 자리 %.1f + 눈동자 보스 Ø%.1f(온전한 원)" % (자리, 동자지름)), "눈바탕R_v4": (바탕R, 색["검"], "검은 눈바탕"),
      "눈L_v4": (눈L, 색["초록"], "초록 홍채 — Ø%.1f 원 · 윗변만 잘림 · 틈 0.12" % 홍채지름), "눈R_v4": (눈R, 색["초록"], "초록 홍채")}

def 치수():
    def 폭(pg, d): q = np.array(pg.exterior.coords) @ d; return round(float(q.max() - q.min()), 2)
    ex, ez = np.array([1, 0]), np.array([0, 1])
    return dict(눈구멍=dict(가로x=폭(구멍, ex), 세로z=폭(구멍, ez), 윗변길이=round(sum(꼬리), 2), 윗변수직높이=폭(구멍, n), 윗변기울기deg=round(기울, 1),
                          원지름=홍채지름 + 2 * 테, 범위=np.round(구멍.bounds, 2).tolist(), 넓이=round(구멍.area, 2)),
                홍채=dict(원지름=홍채지름, 중심=np.round(c, 2).tolist(), 윗잘림몫_지름=잘림, 원에서_남은넓이몫=round(홍채.area / 원.area, 2), 보이는_가로=폭(홍채, ex), 보이는_세로=폭(홍채, ez), 두께=자리 - 0.05),
                눈동자=dict(보스지름=동자지름, 중심=np.round(동자c, 2).tolist(), 윗변에서_띄움=round(동자깊이 - 동자지름 / 2, 2),
                          둘레_초록살_호쪽=round(원.exterior.distance(동자.buffer(틈, 16)), 2), 초록살_윗변쪽=round(동자깊이 - 동자지름 / 2 - 틈, 2), 온전한원=bool(홍채.contains(동자))),
                넓이비=dict(초록_대_눈구멍=round(초록꼴.area / 구멍.area, 2), 검정_대_눈구멍=round(1 - 초록꼴.area / 구멍.area, 2)),
                테=테, 들어감=들어감)

def 내보내기():
    검, 겹 = {}, {}
    for k, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, k + " 안 닫힘/조각"
        t.export(os.path.join(OUT, k + ".stl"))
        검[k] = dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(t.extents, 2).tolist())
        if k != "가면투구_v4": 검[k]["얇은곳mm3"] = 얇은곳(m)
    ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:]: 겹["%s∩%s" % (a, b)] = round((새[a][0] ^ 새[b][0]).volume(), 4)
    assert max(겹.values()) < 0.005, 겹
    d = dict(설명="얼굴 3 차 눈 셋째 고침(09-28) — 원 ∩ 눈꺼풀 눈구멍 · 원호 홍채 · 온전한 원 눈동자", 치수mm=치수(), 겹침=겹,
             부품={k: dict(파일=k + ".stl", 색=c_, 비고=b, **검[k]) for k, (m, c_, b) in 새.items()})
    json.dump(d, open(os.path.join(OUT, "눈_v4.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(치수=d["치수mm"], 검사=검, 겹침최대=max(겹.values())), ensure_ascii=False, default=float))

def 렌더():
    from PIL import Image, ImageDraw, ImageFont
    D = os.path.join(OUT, "_바퀴", "눈"); v4 = {k[:-3]: k for k in 새}
    d = os.path.join(D, "후3"); os.makedirs(d, exist_ok=True)
    parts = [(os.path.join(OUT, v4.get(k, k) + ".stl"), c_) for k, (m, c_, _) in F3.새.items()]
    jf = os.path.join(d, "빠른.json"); pf = os.path.join(d, "빠른.py")
    json.dump(dict(부품=parts, out=d.replace("\\", "/"), 컷=E.컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F3.F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 그(이름, c_): return Image.open(os.path.join(D, 이름, c_ + ".png")).convert("RGB")       # 「후2」 = 눈 고침 2(이미 렌더됨)
    def 띠(im): w, h = im.size; return im.crop((0, int(h * 0.27), w, int(h * 0.73)))
    m12 = Image.open(os.path.join(FRA, "mh_12.jpg")); m13 = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
    px = 26.0 / 0.155 / 2; py = 222 + (293.3 - 277.0) / 0.155
    fra눈 = m12.crop((int(229 - px), int(py - px * 0.46), int(229 + px), int(py + px * 0.46)))
    w3, h3 = m13.size; fra눈3 = m13.crop((int(w3 * 0.42), int(h3 * 0.58), int(w3 * 0.86), int(h3 * 0.58 + w3 * 0.44 * 0.46)))
    줄 = [[("FRA 정면(mh_12)", m12), ("눈 고침 2", 그("후2", "정면")), ("눈 고침 3", 그("후3", "정면"))],
          [("FRA 눈", fra눈), ("눈 고침 2 눈", 띠(그("후2", "눈정면"))), ("눈 고침 3 눈", 띠(그("후3", "눈정면")))],
          [("FRA 3/4 눈(mh_13 뒤집음)", fra눈3), ("눈 고침 2 3/4 확대", 띠(그("후2", "눈반옆"))), ("눈 고침 3 3/4 확대", 띠(그("후3", "눈반옆")))]]
    W, 높이 = 1990, [560, 300, 300]
    S = Image.new("RGB", (W, sum(높이) + 45 * 3 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, 높이):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); dr.text((x + 4, y - 38), t, font=f, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴3_눈3.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--렌더" in sys.argv: 렌더()
