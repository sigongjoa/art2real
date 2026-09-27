# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 3 차 — 눈 넷째 고침(2026-09-28). 「눈이 좌우로 긴데 못 따라간다 · 2 번 비율에 더 둥글게 · 타원으로」.

    python 얼굴3_눈4.py                       -> 디자인_얼굴3/{가면투구,눈바탕L/R,눈L/R}_v5.stl · 눈_v5.json(검사)
    python 얼굴3_눈4.py --렌더                -> 위 + 멋/얼굴3_눈4.jpg
    python 얼굴3_눈4.py --축각 33.3 --표 b --렌더 -> 윗변과 나란한 타원 시험(_v5b · 후4b · 얼굴3_눈4b.jpg)

눈구멍 = (홍채 타원 + 테) ∪ 안쪽 눈꼬리 점의 볼록 껍질 ∩ 눈꺼풀 반평면, 바깥 모서리는 열림(buffer −r +r)으로 둥글림.
홍채 · 눈동자 = 가로로 긴 타원(같은 방향 · 같은 비). 홍채는 윗변만 잘리고 눈동자는 온전하다. 구조는 고침 3 그대로.
"""
import os, sys, json, subprocess
import numpy as np
from shapely.geometry import Polygon, Point, MultiPoint, LineString
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_눈 as E
from 얼굴3_눈 import F3, 기둥, 들어감, 자리
from 얼굴3 import OUT, 메, 얇은곳, 틈, 벽, 색, 멋, FRA, 볼록, V홈, 송곳니

# ════════ 손잡이(mm) ════════
A, B = np.array((2.9, 275.5)), np.array((9.6, 279.9))     # 윗변 사선(고침 2 그대로) · A = 안쪽 눈꼬리(뾰족)
테 = 0.5
홍채긴, 홍채짧 = 5.0, 3.7   # 타원 축(비 1.35)
축각 = 20.0               # 타원 긴 축 기울기(도) — 윗변(33.3)보다 덜 기욺. 나란한 쪽은 --축각 33.3 --표 b 로 시험(FRA 에는 20 이 가까움)
잘림 = 0.25                # 홍채가 윗변 수직 방향으로 눈꺼풀에 가려지는 몫
바깥x = 10.3               # 눈구멍 바깥 끝 x(고침 2 와 같음) — 발x 는 여기서 거꾸로 푼다
모 = 0.8                   # 바깥 위 모서리(윗변 ∩ 타원) 둥글림 반지름
동자긴, 동자짧 = 2.1, 1.6
동자띄움 = 0.45            # 눈동자 윗끝이 홍채 윗변(테 안쪽 사선)에서 떨어진 거리
동자밀 = 0.25              # 홍채 중심에서 안쪽(코 쪽)으로
표 = ""
for i, a in enumerate(sys.argv):
    if a.startswith("--") and a[2:] in ("홍채긴", "홍채짧", "축각", "잘림", "바깥x", "모", "동자긴", "동자짧", "동자띄움", "동자밀", "테"): globals()[a[2:]] = float(sys.argv[i + 1])
    if a == "--표": 표 = sys.argv[i + 1]
V = "_v5" + 표

u = (B - A) / np.linalg.norm(B - A); n = np.array([u[1], -u[0]])           # 윗변 방향 · 아래쪽 법선
기울 = float(np.degrees(np.arctan2(u[1], u[0])))
if 축각 is None: 축각 = 기울
def 아래(p): return Polygon([tuple(p - 20 * u), tuple(p + 20 * u), tuple(p + 20 * u + 20 * n), tuple(p - 20 * u + 20 * n)])   # p 를 지나는 사선의 아래 반평면
def 타원(c, 긴, 짧): return affinity.translate(affinity.rotate(affinity.scale(Point(0, 0).buffer(1, 32), 긴 / 2, 짧 / 2), 축각, origin=(0, 0)), *c)   # 둘레 128
def 뻗음(긴, 짧, d):                                                         # 타원이 방향 d 로 뻗는 반폭
    t = np.radians(축각); e = np.array([np.cos(t), np.sin(t)]); f = np.array([-e[1], e[0]])
    return float(np.hypot(긴 / 2 * (e @ d), 짧 / 2 * (f @ d)))
hn = 뻗음(홍채긴, 홍채짧, n)
def 짓기(발x):
    발 = A + u * (발x - A[0]) / u[0]
    c = 발 + n * (테 + (1 - 2 * 잘림) * hn)
    큰 = 타원(c, 홍채긴 + 2 * 테, 홍채짧 + 2 * 테)
    g = MultiPoint(list(큰.exterior.coords) + [tuple(A)]).convex_hull.intersection(아래(발))
    g = MultiPoint(list(g.buffer(-모).buffer(모, 16).exterior.coords) + [tuple(A)]).convex_hull      # 모서리 둥글림 · 안쪽 눈꼬리만 뾰족
    return 발, c, g
발x = 6.5
for _ in range(20): 발x += 바깥x - 짓기(발x)[2].bounds[2]                   # 바깥 끝을 바깥x 에 맞춤
발, c, 구멍 = 짓기(발x)
온타원 = 타원(c, 홍채긴, 홍채짧)
홍채 = 온타원.intersection(아래(발 + n * 테)).buffer(-0.2).buffer(0.2, 16)    # 윗변 양 끝 귀만 둥글림
동자c = 발 + n * (테 + 동자띄움 + 뻗음(동자긴, 동자짧, n)) - u * 동자밀
동자 = 타원(동자c, 동자긴, 동자짧)
초록꼴 = 홍채.difference(동자.buffer(틈, 16))
윗선 = LineString([tuple(A - u), tuple(B + 3 * u)]).buffer(0.02)
아랫테 = float(구멍.exterior.difference(윗선).distance(홍채))
assert 구멍.contains(홍채) and 아랫테 >= 0.4, "홍채 아래 · 옆 테 %.2f < 0.4" % 아랫테
assert 온타원.contains(동자.buffer(틈 + 0.5)) and 홍채.contains(동자.buffer(0.3)), "눈동자 둘레 초록 살 < 0.5 또는 윗변 띄움 < 0.3"
assert 구멍.bounds[0] >= 2.9 - 1e-6 and 구멍.bounds[2] <= 10.3 + 1e-3, 구멍.bounds

def 눈조각(s):
    창 = 기둥(구멍, -1.0, 벽 + 0.6, s)
    바탕 = 기둥(구멍.buffer(-틈, join_style=2), 들어감, 벽 + 0.5, s) + 기둥(구멍.buffer(0.9), 벽 + 틈, 벽 + 틈 + 0.9, s)
    # 기둥() 은 바깥 윤곽만 읽는다(구멍 무시) — 눈동자는 기둥끼리 뺀다
    바탕 = 바탕 - (기둥(홍채.buffer(틈), 들어감 - 0.1, 들어감 + 자리, s) - 기둥(동자, 들어감 - 0.2, 들어감 + 자리 + 0.1, s))   # 자리 파고 보스 남김
    초록 = 기둥(홍채, 들어감, 들어감 + 자리 - 0.05, s) - 기둥(동자.buffer(틈, 16), 들어감 - 0.2, 들어감 + 자리 + 0.1, s)
    return 창, 바탕, 초록
창L, 바탕L, 눈L = 눈조각(-1); 창R, 바탕R, 눈R = 눈조각(1)
# 가면: 얼굴3 의 식에서 옛 눈구멍(창)만 빼고 그대로(고침 3 과 같음)
가면 = V홈(F3.껍질 - F3.F2.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
for s in (1, -1):
    가면 = 가면 - 볼록([(s * x, y, z) for x in (송곳니["x"] - 0.45, 송곳니["x"] + 0.45) for y in (-6, -2.0)
                     for z in (송곳니["위"], 송곳니["아래"] + 1.5)] + [(s * 송곳니["x"], y, 송곳니["아래"]) for y in (-6, -2.2)])
가면 = max((가면 - 창L - 창R).decompose(), key=lambda p: p.volume())
가면부풀 = F3.F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]

새 = {"가면투구" + V: (가면, 색["흰"], "얼굴3 가면(옛 구멍 없음) − 둥근 아몬드 눈구멍"),
      "눈바탕L" + V: (바탕L, 색["검"], "검은 눈바탕 — 뒤에서 끼움 · 홍채 자리 %.1f + 눈동자 타원 보스 %.1f × %.1f" % (자리, 동자긴, 동자짧)), "눈바탕R" + V: (바탕R, 색["검"], "검은 눈바탕"),
      "눈L" + V: (눈L, 색["초록"], "초록 홍채 — %.1f × %.1f 타원 · 윗변만 잘림 · 틈 0.12" % (홍채긴, 홍채짧)), "눈R" + V: (눈R, 색["초록"], "초록 홍채")}

def 치수():
    def 폭(pg, d): q = np.array(pg.exterior.coords) @ d; return round(float(q.max() - q.min()), 2)
    ex, ez = np.array([1, 0]), np.array([0, 1])
    세로 = max(구멍.intersection(LineString([(x, 0), (x, 400)])).length for x in np.linspace(3.0, 10.2, 145))
    return dict(눈구멍=dict(가로x=폭(구멍, ex), 세로z_전체=폭(구멍, ez), 가장높은곳_세로=round(세로, 2), 윗변방향길이=폭(구멍, u), 윗변수직높이=폭(구멍, n), 윗변기울기deg=round(기울, 1),
                          모서리둥글림=모, 범위=np.round(구멍.bounds, 2).tolist(), 넓이=round(구멍.area, 2), 중심x=round(구멍.centroid.x, 2)),
                홍채=dict(긴축=홍채긴, 짧은축=홍채짧, 축각deg=round(축각, 1), 중심=np.round(c, 2).tolist(), 윗잘림몫=잘림, 타원에서_남은넓이몫=round(홍채.area / 온타원.area, 2),
                        아래옆_테=round(아랫테, 2), 보이는_가로=폭(홍채, ex), 보이는_세로=폭(홍채, ez), 두께=자리 - 0.05),
                눈동자=dict(긴축=동자긴, 짧은축=동자짧, 중심=np.round(동자c, 2).tolist(), 윗변에서_띄움=동자띄움, 초록살_윗변쪽=round(동자띄움 - 틈, 2),
                          둘레_초록살_호쪽=round(온타원.exterior.distance(동자.buffer(틈, 16)), 2), 온전함=bool(홍채.contains(동자))),
                넓이비=dict(초록_대_눈구멍=round(초록꼴.area / 구멍.area, 2), 검정_대_눈구멍=round(1 - 초록꼴.area / 구멍.area, 2)),
                테=테, 들어감=들어감)

def 내보내기():
    검, 겹 = {}, {}
    for k, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, k + " 안 닫힘/조각"
        t.export(os.path.join(OUT, k + ".stl"))
        검[k] = dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(t.extents, 2).tolist())
        if not k.startswith("가면투구"): 검[k]["얇은곳mm3"] = 얇은곳(m)
    ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:]: 겹["%s∩%s" % (a, b)] = round((새[a][0] ^ 새[b][0]).volume(), 4)
    assert max(겹.values()) < 0.005, 겹
    d = dict(설명="얼굴 3 차 눈 넷째 고침(09-28) — 둥근 아몬드 눈구멍 · 가로 타원 홍채 · 온전한 타원 눈동자", 치수mm=치수(), 겹침=겹,
             부품={k: dict(파일=k + ".stl", 색=c_, 비고=b, **검[k]) for k, (m, c_, b) in 새.items()})
    json.dump(d, open(os.path.join(OUT, "눈" + V + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(치수=d["치수mm"], 검사=검, 겹침최대=max(겹.values())), ensure_ascii=False, default=float))

def 렌더():
    from PIL import Image, ImageDraw, ImageFont
    D = os.path.join(OUT, "_바퀴", "눈"); v5 = {k[:-len(V)]: k for k in 새}
    d = os.path.join(D, "후4" + 표); os.makedirs(d, exist_ok=True)
    parts = [(os.path.join(OUT, v5.get(k, k) + ".stl"), c_) for k, (m, c_, _) in F3.새.items()]
    jf = os.path.join(d, "빠른.json"); pf = os.path.join(d, "빠른.py")
    json.dump(dict(부품=parts, out=d.replace("\\", "/"), 컷=E.컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F3.F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    def 그(이름, c_): return Image.open(os.path.join(D, 이름, c_ + ".png")).convert("RGB")       # 「후2」「후3」 = 눈 고침 2 · 3(이미 렌더됨)
    def 띠(im): w, h = im.size; return im.crop((0, int(h * 0.27), w, int(h * 0.73)))
    m12 = Image.open(os.path.join(FRA, "mh_12.jpg")); m13 = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
    px = 26.0 / 0.155 / 2; py = 222 + (293.3 - 277.0) / 0.155
    fra눈 = m12.crop((int(229 - px), int(py - px * 0.46), int(229 + px), int(py + px * 0.46)))
    w3, h3 = m13.size; fra눈3 = m13.crop((int(w3 * 0.42), int(h3 * 0.58), int(w3 * 0.86), int(h3 * 0.58 + w3 * 0.44 * 0.46)))
    후 = "후4" + 표
    줄 = [[("FRA 눈", fra눈)] + [("눈 고침 %s 눈" % k, 띠(그(v, "눈정면"))) for k, v in (("2", "후2"), ("3", "후3"), ("4", 후))],
          [("FRA 3/4 눈(mh_13 뒤집음)", fra눈3)] + [("눈 고침 %s 3/4" % k, 띠(그(v, "눈반옆"))) for k, v in (("2", "후2"), ("3", "후3"), ("4", 후))],
          [("FRA 정면(mh_12)", m12), ("눈 고침 4", 그(후, "정면"))]]
    W, 높이 = 1990, [224, 224, 640]
    S = Image.new("RGB", (W, sum(높이) + 45 * 3 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, 높이):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); dr.text((x + 4, y - 36), t, font=f, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴3_눈4%s.jpg" % 표); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--렌더" in sys.argv: 렌더()
