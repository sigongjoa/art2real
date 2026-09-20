# -*- coding: utf-8 -*-
"""**숫자를 내도 되는가** — 도안 게이트 0 단계 (2026-09-20).

    python 게이트.py 검사     자가검사 (부품 복원 · 접촉 자 · 조각 수)
    python 게이트.py 판정     -> out/기록/게이트_<때>.json   (다시 최적화하지 않는다 — 저장된 θ 를 읽는다)
    python 게이트.py 그림     -> out/게이트_궤짝.png · out/게이트_드릴.png

기획 `claudedocs/기획_20260920.md` 주 1 · 스키마 `원화3d/도안/스키마.md` · 실물 `궤짝.json`.
**문턱은 돌리기 전에 여기 적었고 숫자를 보고 안 바꾼다.**

    G1 조각 수      조립 메시의 연결 성분 수 == 도안의 `조각수.기대`            치명
    G2 접촉 그래프  부품 접촉(표면 거리 <= ε)으로 만든 그래프가 한 덩어리      치명
    G3 부착 선언    도안 `assembly` 의 각 변이 실제로 접촉한다                 치명  (도안.json 있는 장만)
    G4 범위 끝      맞춘 θ 가 범위 끝에서 1% 안쪽에 붙지 않았다                주의
    G5 이름 일치    θ 파일의 키 == 도안 θ.항목 == 프로그램 매개변수 이름       치명  (도안.json 있는 장만)
    G6 부품 넘침    부품마다 정답 밖 부피 몫. **문턱 없음 — 서술이다**
    민감도          맞춘 θ 를 범위의 ±1% · ±5% 흔들어 J 의 최대 변화.
                    max|ΔJ| < 0.001 이면 **「그림이 안 정한 축」을 기계가 찾은 것**이다.

ε = 0.0078 (궤짝.json `공차.평가스케일` · 창 단위 · 현행 128 격자 한 칸).
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 도안천장 as DA
CG, ME = DA.CG, DA.ME
H, W, J, DG, DC = DA.H, DA.W, DA.J, DA.DG, DA.DC
HERE = DA.HERE
도안폴더 = r"G:\art2real\원화3d\도안"
OUT = os.path.join(HERE, "out", "기록")
TAG = "게이트 v1 · 저장된 θ · 조각수 · 접촉그래프 · 부착선언 · 범위끝 · 이름일치 · 부품넘침 · 민감도 (2026-09-20)"

EPS = 0.0078
민감_h = (0.01, 0.05)
민감_문턱 = 0.001
끝_여유 = 0.01
판본 = ("도안만", "도안+맞춤", "도안+전맞춤")
도안파일 = {"cloak_Chest_Closed_AngpV0HxD8": "궤짝.json"}        # 드릴은 아직 .json 이 없다 — 있는 것만 검사한다


# ── 자 ───────────────────────────────────────────────────────────────────────

def 부품들(case, t):
    return [(n, CG.tm(p)) for n, p in DA.도안[case][1]([float(x) for x in t])]


def 표면거리(a, b, n=600):
    """a 표면에서 b 표면까지의 최소 거리. 맞닿거나 파고들면 0 이다.
    a 를 n 점 **표본**으로 재니 위로 치우친 값이다 — 「닿는다」는 확실하고 「안 닿는다」는 표본 탓일 수 있다.
    (rtree 가 없어 naive. 정점도 같이 넣어 모서리 접촉을 놓치지 않는다.)"""
    pts = np.vstack([trimesh.sample.sample_surface(a, n)[0], np.asarray(a.vertices)])
    return float(trimesh.proximity.closest_point_naive(b, pts)[1].min())


def 조각(m):
    return int(len(trimesh.graph.connected_components(m.face_adjacency, nodes=np.arange(len(m.faces)))))


def 덩어리(names, 붙음):
    """접촉 그래프의 연결 성분."""
    남, out = set(range(len(names))), []
    while 남:
        s = [남.pop()]
        c = set(s)
        while s:
            i = s.pop()
            for k in range(len(names)):
                if k in 남 and 붙음[i][k]:
                    남.discard(k)
                    c.add(k)
                    s.append(k)
        out.append(sorted(names[i] for i in c))
    return out


def 넘침(m, tv):
    A, B = J.common(*CG.vox(m), *tv)
    return round(float((A & ~B).sum() / max(A.sum(), 1)), 4)


# ── 한 판본 ──────────────────────────────────────────────────────────────────

def 한판(case, t, tv, masks, bs, 스펙):
    ps = 부품들(case, t)
    names = [n for n, _ in ps]
    붙음 = [[False] * len(ps) for _ in ps]
    거리 = {}
    for i in range(len(ps)):
        for k in range(i + 1, len(ps)):
            d = min(표면거리(ps[i][1], ps[k][1]), 표면거리(ps[k][1], ps[i][1]))
            거리["%s—%s" % (names[i], names[k])] = round(d, 5)
            붙음[i][k] = 붙음[k][i] = bool(d <= EPS)
    ds = 덩어리(names, 붙음)
    whole = DA.합(DA.도안[case][1]([float(x) for x in t]))
    m = CG.tm(whole)
    r = {"조각": 조각(m), "기대조각": 스펙["조각수"], "부품수": len(ps),
         "덩어리": ds, "덩어리수": len(ds), "표면거리": 거리,
         "부품넘침": {n: 넘침(mm, tv) for n, mm in ps},
         "부품부피": {n: round(float(mm.volume), 5) for n, mm in ps},
         "J": round(CG.Jsil(m, masks, bs), 5)}
    r["G1 조각수"] = "통과" if r["조각"] == 스펙["조각수"] else "실패"
    r["G2 접촉그래프"] = "통과" if len(ds) == 1 else "실패"
    if 스펙["assembly"]:
        bad = []
        ix = {n: i for i, n in enumerate(names)}
        for a in 스펙["assembly"]:
            c, p = a["child"], a["parent"]
            for cc in ([c] if c in ix else [x for x in names if x.startswith(c)]):
                if p in ix and cc in ix and not 붙음[ix[cc]][ix[p]]:
                    i, k = sorted((ix[cc], ix[p]))
                    bad.append("%s—%s(%.4f)" % (cc, p, 거리["%s—%s" % (names[i], names[k])]))
        r["G3 부착선언"] = "통과" if not bad else "실패"
        r["부착거짓"] = bad
    else:
        r["G3 부착선언"] = "안함(도안.json 없음)"
    return r, ps, m


# ── 민감도 ───────────────────────────────────────────────────────────────────

def 민감도(case, t, masks, bs):
    sp = DA.도안[case][0]
    mk = DA.만들기(case)
    J0 = CG.Jsil(CG.build(mk, t), masks, bs)
    out = {}
    for i, (n, _, (lo, hi), fr) in enumerate(sp):
        row = {"못읽음선언": bool(fr), "θ": round(float(t[i]), 5), "범위": [lo, hi]}
        for h in 민감_h:
            ds = []
            for s in (+1, -1):
                t2 = list(t)
                t2[i] = float(np.clip(t[i] + s * h * (hi - lo), lo, hi))
                if abs(t2[i] - t[i]) < 1e-12:
                    continue                                  # 이미 끝에 붙어 그쪽으로 못 움직인다
                m2 = CG.build(mk, t2)
                ds.append(abs((CG.Jsil(m2, masks, bs) if m2 is not None else 0.0) - J0))
            row["dJ%d%%" % int(h * 100)] = round(max(ds), 6) if ds else None
        row["최대dJ"] = round(max([v for k, v in row.items() if k.startswith("dJ") and v is not None] or [0.0]), 6)
        row["기계판정"] = "안정해짐" if row["최대dJ"] < 민감_문턱 else "정해짐"
        out[n] = row
    return {"J0": round(J0, 5), "문턱": "max|dJ| < %g 이면 안 정해진 축" % 민감_문턱, "축": out}


# ── 판정 ─────────────────────────────────────────────────────────────────────

def 스펙읽기(case):
    f = 도안파일.get(case)
    if not f:
        return {"조각수": 1, "assembly": None, "θ이름": None,
                "note": "도안.json 이 없다 — 조각 수 기대값 1 은 이 장에 대한 **가정**이고 도안이 적은 값이 아니다"}
    d = json.load(open(os.path.join(도안폴더, f), encoding="utf-8"))
    return {"조각수": d["조각수"]["기대"], "assembly": d["assembly"],
            "θ이름": [e["이름"] for e in d["θ"]["항목"]],
            "θ파일": list(json.load(open(os.path.join(도안폴더, d["θ"]["file"]), encoding="utf-8")).keys())}


def verdict():
    H.register_sheets()
    rs = DA.rows()
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "ε": EPS,
         "문턱": {"G1": "조각 == 도안의 조각수.기대", "G2": "접촉 덩어리 == 1", "G3": "assembly 의 각 변이 접촉",
                 "G4": "맞춘 θ 가 범위 끝 %g 안쪽에 없다" % 끝_여유, "G5": "θ 이름 세 곳 일치",
                 "민감도": "max|dJ| < %g 이면 안 정해진 축" % 민감_문턱},
         "장": {}}
    for case in DA.사례:
        if case not in rs:
            continue
        t0 = time.time()
        이름 = DA.한글[case]
        스펙 = 스펙읽기(case)
        masks, bs = CG.G3.art_masks(case), H.CASES[case]["back_sign"]
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        tv = CG.vox(truth)
        sp = DA.도안[case][0]
        g = {"스펙": {k: 스펙[k] for k in ("조각수",) if k in 스펙}, "판본": {}}
        if 스펙.get("θ이름") is not None:
            프 = [n for n, _, _, _ in sp]
            g["G5 이름일치"] = {"프로그램": 프, "도안θ항목": 스펙["θ이름"], "θ파일": 스펙["θ파일"],
                             "통과": bool(프 == 스펙["θ이름"] == 스펙["θ파일"])}
        else:
            g["G5 이름일치"] = "안함(도안.json 없음)"
        for p in 판본:
            t = [x[1] for x in sp] if p == "도안만" else rs[case][p]["θ최선"]
            r, ps, m = 한판(case, t, tv, masks, bs, 스펙)
            r["θ"] = [round(float(x), 5) for x in t]
            if p != "도안만":
                idx = [i for i, (_, _, _, fr) in enumerate(sp) if fr or p == "도안+전맞춤"]
                끝 = {sp[i][0]: round(float(t[i]), 5) for i in idx
                     if min(t[i] - sp[i][2][0], sp[i][2][1] - t[i]) <= 끝_여유 * (sp[i][2][1] - sp[i][2][0])}
                r["G4 범위끝"] = "통과" if not 끝 else "실패"
                r["범위끝붙은축"] = 끝
            r["기록된3D"] = rs[case][p]["iou3d"] if p == "도안만" else \
                rs[case][p]["재시작"][rs[case][p]["최선1"]]["iou3d"]
            r["치명실패"] = [k for k in ("G1 조각수", "G2 접촉그래프", "G3 부착선언") if r.get(k) == "실패"]
            r["숫자를낸다"] = not r["치명실패"]
            g["판본"][p] = r
            print("  %-4s %-9s 조각 %d/%d · 덩어리 %d · J %.4f · 3D %.4f · %s"
                  % (이름, p, r["조각"], 스펙["조각수"], r["덩어리수"], r["J"], r["기록된3D"],
                     "통과" if r["숫자를낸다"] else "실패 " + ",".join(r["치명실패"])), flush=True)
        # **게이트를 통과한 점에서도 잰다** — 도안+맞춤 은 조각이 갈린 점이라 거기서만 재면 핑계가 된다
        g["민감도"] = {p: 민감도(case, [x[1] for x in sp] if p == "도안만" else rs[case][p]["θ최선"], masks, bs)
                     for p in ("도안만", "도안+맞춤")}
        선 = [n for n, _, _, fr in sp if fr]
        g["민감도요약"] = {"손으로선언한못읽음": 선}
        for p, s in g["민감도"].items():
            안 = [n for n, x in s["축"].items() if x["기계판정"] == "안정해짐"]
            g["민감도요약"][p] = {"기계가찾은안정해진축": 안, "수": len(안),
                                "선언했는데반응있음": [n for n in 선 if n not in 안],
                                "선언안했는데반응없음": [n for n in 안 if n not in 선]}
            print("    민감도(%s) 안정해짐 %d/%d %s" % (p, len(안), len(sp), 안), flush=True)
        print("    선언한 못읽음 %d %s (%.0f초)" % (len(선), 선, time.time() - t0), flush=True)
        v["장"][이름] = g
    p = os.path.join(OUT, "게이트_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림():
    from PIL import Image, ImageDraw
    from 계획 import _font
    H.register_sheets()
    rs = DA.rows()
    ps_ = sorted([f for f in os.listdir(OUT) if f.startswith("게이트_")])
    v = json.load(open(os.path.join(OUT, ps_[-1]), encoding="utf-8"))
    for case in DA.사례:
        if case not in rs:
            continue
        이름 = DA.한글[case]
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        frame = ME.AL.frame_of(truth, 45)
        sp = DA.도안[case][0]
        R, cols = [], None
        for p in ("도안만", "도안+맞춤"):
            t = [x[1] for x in sp] if p == "도안만" else rs[case][p]["θ최선"]
            parts = 부품들(case, t)
            g = v["장"][이름]["판본"][p]
            ts, cs = [], []
            for n, mm in parts:
                im = Image.fromarray(ME.타일(mm, frame))
                ImageDraw.Draw(im).text((6, im.size[1] - 22), "넘침 %.3f" % g["부품넘침"][n],
                                        fill=(200, 30, 30), font=_font(15))
                ts.append(np.asarray(im))
                cs.append(n)
            im = Image.fromarray(ME.타일(CG.tm(DA.합(DA.도안[case][1]([float(x) for x in t]))), frame))
            ImageDraw.Draw(im).text((6, im.size[1] - 22), "조각 %d · 덩어리 %d · 3D %.3f"
                                    % (g["조각"], g["덩어리수"], g["기록된3D"]),
                                    fill=(200, 30, 30), font=_font(15))
            ts.append(np.asarray(im))
            cs.append("전체")
            cols = cs
            R.append(("%s · %s%s" % (이름, p, "" if g["숫자를낸다"] else "  ✕"), ts))
        dst = os.path.join(HERE, "out", "게이트_%s.png" % 이름)
        DC.grid(R, cols, "게이트 — 부품 하나씩 (45° 명암 · 같은 틀) · %s" % 이름,
                "빨간 글 = 정답 밖 부피 몫(넘침) · 전체 칸은 조각 수 · 접촉 덩어리 수 · 기록된 3D IoU · ✕ = 치명 게이트 실패라 숫자를 안 낸다",
                dst, S=300)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    H.register_sheets()
    c = DA.사례[0]
    sp = DA.도안[c][0]
    t = [x[1] for x in sp]
    ps = 부품들(c, t)
    assert len(ps) == 6, len(ps)
    # 맞닿는 짝은 0 에 가깝고, 떼어 놓으면 거리가 그만큼 나온다
    d = 표면거리(ps[0][1], ps[1][1])
    assert d <= EPS, "아래몸통—위몸통 %.5f" % d
    보 = ps[3][1].copy()
    보.apply_translation([0, 0, 0.5])
    assert 표면거리(보, ps[2][1]) > EPS
    # 덩어리 자
    assert 덩어리(["a", "b", "c"], [[0, 1, 0], [1, 0, 0], [0, 0, 0]]) .__len__() == 2
    m = CG.tm(DA.합(DA.도안[c][1](t)))
    assert 조각(m) == 1
    print("  자가검사 통과 — 부품 %d · 접촉 %.5f · 조각 %d" % (len(ps), d, 조각(m)))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "판정"
    {"검사": selfcheck, "판정": verdict, "그림": 그림}[a]()
