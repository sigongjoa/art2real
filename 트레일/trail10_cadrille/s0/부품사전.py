# -*- coding: utf-8 -*-
"""부품 사전 v0 — 「낱말은 외우고 · 숫자는 재고 · 조합만 배운다」 (설계 claudedocs/design_외우는구조_20261008.md · 10-08)
구조 문장 = 한 줄에 낱말 하나:  낱말 이름=값 … [@x,y,z] [회=rx,ry,rz] [빼기]
  · 좌표 단위는 cadrille 과 같은 상자(약 −100~100) · 회전은 도 · 「빼기」면 지금까지 모양에서 깎음(구멍 · 홈 류는 기본이 빼기)
  · 줄 순서대로 더하거나 깎는다. 「거울」 「배열」은 앞까지 / 바로 앞 낱말에 작용
낱말(v0 · 21 개):
  상자 w d h            원통 r h               공 r                   원뿔 r1 r2 h        링 r1 r2 h
  사다리꼴 w1 d1 w2 d2 h (아래 → 위 가늘어지는 상자)     윤곽판 p=x,y;x,y;… t   (점 3~10 개 · 판 모양 · z 로 t 만큼)
  공관절 r 목r 목h      (공 + 목 원통 · 목은 −z 로)      C소켓 r 두께 h 열림 (열림 = 도 · +x 쪽이 열림)
  핀 r h                축구멍 r h                        구멍 r h      사각구멍 w d h      슬롯 길이 폭 h      홈 길이 폭 깊이
  리브 길이 폭 h        모따기 c   (지금까지 모양의 세로 모서리)    둥글게 r (지금까지 모양의 세로 모서리)
  거울 축=x|y|z         배열 n 간격=dx,dy,dz (바로 앞 낱말을 n 번)
python s0/부품사전.py test    자기 검사"""
import math, re
import cadquery as cq

def _solid(w, a):   # 낱말 → (solid, 기본 빼기?)
    g = lambda k, d=None: float(a.get(k, d)) if a.get(k, d) is not None else None
    if w == "상자": return cq.Workplane("XY").box(g("w"), g("d"), g("h")), False
    if w == "원통": return cq.Workplane("XY").cylinder(g("h"), g("r")), False
    if w == "핀": return cq.Workplane("XY").cylinder(g("h"), g("r")), False
    if w == "공": return cq.Workplane("XY").sphere(g("r")), False
    if w == "원뿔": return cq.Workplane("XY").add(cq.Solid.makeCone(g("r1"), g("r2"), g("h"), pnt=cq.Vector(0, 0, -g("h") / 2))), False
    if w == "링": return cq.Workplane("XY").circle(g("r1")).circle(g("r2")).extrude(g("h")).translate((0, 0, -g("h") / 2)), False
    if w == "사다리꼴":
        h = g("h"); s = cq.Workplane("XY").workplane(offset=-h / 2).rect(g("w1"), g("d1")).workplane(offset=h).rect(g("w2"), g("d2")).loft(); return s, False
    if w == "윤곽판":
        pts = [tuple(map(float, q.split(","))) for q in a["p"].split(";") if q]; t = g("t")
        return cq.Workplane("XY").polyline(pts).close().extrude(t).translate((0, 0, -t / 2)), False
    if w == "공관절":
        r, nr, nh = g("r"), g("목r", g("r") * 0.45), g("목h", g("r") * 1.2)
        return cq.Workplane("XY").sphere(r).union(cq.Workplane("XY").cylinder(nh, nr).translate((0, 0, -r - nh / 2 + r * 0.3))), False
    if w == "C소켓":
        r, t, h, op = g("r"), g("두께", g("r") * 0.35), g("h", g("r") * 1.6), g("열림", 70)
        ring = cq.Workplane("XY").circle(r + t).circle(r).extrude(h).translate((0, 0, -h / 2))
        cut = cq.Workplane("XY").polyline([(0, 0), ((r + t) * 2 * math.cos(math.radians(op / 2)), (r + t) * 2 * math.sin(math.radians(op / 2))),
                                           ((r + t) * 2 * math.cos(math.radians(op / 2)), -(r + t) * 2 * math.sin(math.radians(op / 2)))]).close().extrude(h * 2).translate((0, 0, -h))
        return ring.cut(cut), False
    if w == "축구멍": return cq.Workplane("XY").cylinder(g("h"), g("r")), True
    if w == "구멍": return cq.Workplane("XY").cylinder(g("h"), g("r")), True
    if w == "사각구멍": return cq.Workplane("XY").box(g("w"), g("d"), g("h")), True
    if w == "슬롯": return cq.Workplane("XY").slot2D(max(g("길이"), g("폭") * 1.01), g("폭")).extrude(g("h")).translate((0, 0, -g("h") / 2)), True
    if w == "홈": return cq.Workplane("XY").box(g("길이"), g("폭"), g("깊이") * 2), True
    if w == "리브": return cq.Workplane("XY").box(g("길이"), g("폭"), g("h")), False
    raise ValueError("모르는 낱말: " + w)

LINE = re.compile(r"^\s*(\S+)((?:\s+[^\s@=]+=[^\s@]+)*)\s*(?:@(\S+))?\s*(?:회=(\S+))?\s*(빼기|더하기)?\s*$")

def 읽기(문장):
    out = []
    for i, l in enumerate(문장.strip().splitlines()):
        l = l.split("#")[0].strip()
        if not l: continue
        m = LINE.match(l)
        if not m: raise ValueError(f"{i + 1} 줄을 못 읽음: {l}")
        w, kv, at, rot, op = m.groups(); a = dict(x.split("=", 1) for x in kv.split())
        out.append((w, a, tuple(map(float, at.split(","))) if at else (0, 0, 0), tuple(map(float, rot.split(","))) if rot else (0, 0, 0), op))
    return out

def 짓기(문장):
    """구조 문장 → cq.Workplane"""
    r, last = None, None
    for w, a, at, rot, op in 읽기(문장):
        if w == "거울":
            if r is None: continue
            ax = a.get("축", "x"); r = r.union(r.mirror({"x": "YZ", "y": "XZ", "z": "XY"}[ax])); continue
        if w == "배열":
            if last is None: continue
            n = int(float(a.get("n", 2))); d = tuple(map(float, a.get("간격", "10,0,0").split(","))); s, sub = last
            for k in range(1, n):
                p = s.translate((d[0] * k, d[1] * k, d[2] * k)); r = r.cut(p) if sub else r.union(p)
            continue
        if w in ("모따기", "둥글게"):
            try: r = r.edges("|Z").chamfer(float(a["c"])) if w == "모따기" else r.edges("|Z").fillet(float(a["r"]))
            except Exception: pass   # 모서리가 작아 실패하면 그대로(사전 v0 · 알려진 한계)
            continue
        s, sub = _solid(w, a)
        for k, ang in zip(((1, 0, 0), (0, 1, 0), (0, 0, 1)), rot):
            if ang: s = s.rotate((0, 0, 0), k, ang)
        s = s.translate(at); sub = (op == "빼기") or (sub and op != "더하기")
        if r is None: r = s if not sub else None
        else: r = r.cut(s) if sub else r.union(s)
        last = (s, sub)
    if r is None: raise ValueError("더하는 낱말이 하나도 없음")
    return r

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["test"]:
        q = """상자 w=60 d=30 h=8
공관절 r=9 목r=4 목h=10 @-30,0,20
C소켓 r=8 두께=3 h=10 열림=70 @30,0,8
구멍 r=3 h=20 @0,0,0
배열 n=2 간격=12,0,0
거울 축=y
모따기 c=1.5"""
        s = 짓기(q); bb = s.val().BoundingBox(); v = s.val().Volume()
        assert 50 < bb.xlen < 100 and v > 0, (bb.xlen, v)
        assert len(읽기(q)) == 7
        try: 짓기("날개 w=3"); raise AssertionError("모르는 낱말이 통과")
        except ValueError: pass
        print("ok 부피 %.0f · 상자 %.0f×%.0f×%.0f" % (v, bb.xlen, bb.ylen, bb.zlen))
