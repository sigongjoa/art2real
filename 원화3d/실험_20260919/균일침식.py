# -*- coding: utf-8 -*-
"""**고정 비율 균일 침식** — 지금 기본을 부피 r 배까지 안으로 민다 (2026-09-19).

    python 실험_20260919/균일침식.py 검사      자가검사 · 배관 (한 장 · even_control 대조까지)
    python 실험_20260919/균일침식.py [n]       아직 안 한 장 n 개 -> out/기록/균일침식_진행.jsonl
    python 실험_20260919/균일침식.py 보강 [n]  앞뒤이진@r (검토가 짚은 빠진 대조군) 만 이어 붙인다
    python 실험_20260919/균일침식.py 판정      -> out/기록/균일침식_<때>.json
    python 실험_20260919/균일침식.py 그림      -> out/균일침식.png

판정은 `claudedocs/plan_균일침식_20260919.md` 그대로다 — 돌리기 전에 적었다.

**함정**: 균일 침식은 이 저장소의 정보 0 대조군이다. 후보로 올리면 「후보 = 대조군」이라 IoU 로는 못 가른다.
그래서 판본 넷을 나란히 둔다 — 같은 부피에서 실루엣을 지키는 `앞뒤@r`(방향) · 깊이 깎기를 뺀 `균일이진@r`(정보 0).
그리고 IoU 말고 **못덮음**(원화 실루엣 약속)을 같이 잰다.
"""
import json
import os
import sys
import time

import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C
import 정답 as J
import 표면 as SF
import 생성깎기 as GC
from 겉면채점 import bench_cases, fill_slices
from 점수판 import adopt

RS = (0.95, 0.90, 0.85)                       # 계획에서 미리 정한 셋. 돌린 뒤에 고르지 않는다
PROG = os.path.join(HERE, "out", "기록", "균일침식_진행.jsonl")
TAG = ("균일침식 · 실물28 · 기본/균일@r/앞뒤@r/균일이진@r · r %s · 속채운 정답 · 격자128·192 (2026-09-19)"
       % "·".join("%.2f" % r for r in RS))
TAG2 = "균일침식 보강 · 앞뒤이진@r (앞뒤의 정보 0 대조군) · 실물28 (2026-09-19)"
P192 = (W.U1 - W.U0) / 192.0
PITCH = {"": J.PITCH, "·192": P192}
FAMS = ("균일", "앞뒤", "균일이진", "앞뒤이진")


def cases():
    return [c for c in bench_cases() if c != "소체"]           # `소체` 는 base_female 과 같은 메시


def names():
    return ["기본"] + ["%s@%.2f" % (f, r) for r in RS for f in FAMS]


# ── 판본 ─────────────────────────────────────────────────────────────────────

def field(vox):
    """침식에 쓰는 **매끈한 거리장** — EDT 를 σ1 칸으로 흐린 것.

    `hull.even_control` 은 EDT 의 수준 t 를 부피 곡선(마칭큐브 보간)에서 찾는다. 그런데 순수 EDT 는
    값이 양자화되어 있어 **한 겹이 부피의 5~10%** 다 — 고정 비율(5% · 10% · 15%)은 겹 **안**에 떨어지고,
    겹 안에서 칸을 임의로 고르면 표면이 점박이가 된다. 마칭큐브로 보간하면 메시가 되는데, 메시를 다시
    복셀로 구우면 칸이 15% 부푼다 (`GC.voxelize` 왕복 실측 127,704 -> 147,175). 부피가 판정의 축인
    이 바퀴에서는 그 왕복을 쓸 수 없다.

    그래서 **복셀 공간에서 끝낸다** — 흐린 거리장의 수준집합은 연속값이라 목표 칸 수를 정확히 맞추고,
    r 이 작아질수록 자동으로 포개진다(`{f≥t}` 는 t 에 대해 단조). `even_control` 과 같은 것을 보는지는
    배관에서 확인한다 (`pipe_even`)."""
    d = ndimage.distance_transform_edt(vox).astype(np.float32)
    return ndimage.gaussian_filter(d, 1.0)


def erode_to(vox, n, f=None):
    """`vox` 를 매끈한 거리장 수준면으로 깎아 칸 수를 정확히 n 으로. -> (복셀, 수준 t)"""
    f = field(vox) if f is None else f
    v = f[vox]
    t = float(np.partition(v, len(v) - n)[len(v) - n])
    out = vox & (f > t)
    need = n - int(out.sum())                                # 수준 t 에 정확히 걸친 동점 (대칭 물건에서 난다)
    if need > 0:
        tie = np.flatnonzero(vox.ravel() & (f.ravel() == t))
        out.reshape(-1)[tie[:need]] = True
    return out, t


def variants(case):
    """케이스 하나. **문맥을 먼저** 주고 판본을 하나씩 흘린다 — 부르는 쪽이 재고 바로 버리게 (RAM 6GB)."""
    masks, bs, plain, base, axes = GC.build(case)
    N = int(base.sum())
    yield "_ctx", None, {"masks": masks, "bs": bs, "plain": plain, "axes": axes, "base_n": N}
    yield "기본", base, {}
    fb, fp = field(base), field(plain)                       # 장은 판본마다가 아니라 원본마다 한 번
    for r in RS:
        n = int(round(r * N))
        ve, t = erode_to(base, n, fb)
        yield "균일@%.2f" % r, ve, {"t": round(t, 3), "목표칸": n}
        del ve
        vd, q = H.depth_control(base, n)
        yield "앞뒤@%.2f" % r, vd, {"q": round(float(q), 4), "목표칸": n}
        del vd
        vb, tb = erode_to(plain, n, fp)
        yield "균일이진@%.2f" % r, vb, {"t": round(tb, 3), "목표칸": n}
        del vb


# ── 채점 ─────────────────────────────────────────────────────────────────────

def truth_grids(case):
    """속 채운 정답 격자 둘 (`실험_20260915/점수판.score` 와 같은 정의)."""
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    out = {}
    for tag, p in PITCH.items():
        T, ot = J.grid(truth, p)
        out[tag] = (fill_slices(T), ot)
    return out


def measure(vox, grids, ctx):
    r = {"칸": int(vox.sum())}
    mesh = C.to_mesh(vox, ctx["axes"])
    for tag, (F, ot) in grids.items():
        G, og = J.grid(mesh, PITCH[tag])
        A, B = J.common(F, ot, G, og)
        r["IoU" + tag] = round(float((A & B).sum() / max((A | B).sum(), 1)), 5)
    del mesh
    s = GC.sil_fit(vox, ctx["masks"], ctx["bs"], ctx["axes"])
    r["못덮음"] = round(max(s["못덮음_front"], s["못덮음_side"]), 4)
    r["넘침"] = round(max(s["넘침_front"], s["넘침_side"]), 4)
    r["실루엣손실"] = round(SF.sil_loss(vox, ctx["plain"]), 4)
    r["조각"] = SF.pieces(vox)
    r["찢김"] = round(SF.tear(vox), 4)
    return r


def one(case):
    t0 = time.time()
    grids = truth_grids(case)
    ctx, out = None, {"case": case, "판": TAG, "기본값": "%s lam%.2f" % (H.DEPTH, H.DEPTH_LAM)}
    for name, vox, extra in variants(case):
        if name == "_ctx":
            ctx = extra
            out["칸_기본"] = ctx["base_n"]
            continue
        cap = ctx["plain"].sum() if name.startswith("균일이진") else ctx["base_n"]
        assert int(vox.sum()) <= cap + 1, "%s 가 원본보다 크다 (%d > %d)" % (name, vox.sum(), cap)
        m = measure(vox, grids, ctx)
        m.update(extra)
        out[name] = m
        print("    %-14s 칸 %8d  IoU %.4f/%.4f  못덮음 %.4f  넘침 %.4f  실손 %.4f  조각 %d"
              % (name, m["칸"], m["IoU"], m["IoU·192"], m["못덮음"], m["넘침"], m["실루엣손실"], m["조각"]), flush=True)
        del vox
    out["초"] = round(time.time() - t0, 1)
    return out


# ── 배관 ─────────────────────────────────────────────────────────────────────

def pipe_score(row):
    """배관 ①: `기본` 이 09-15 점수판의 「새」와 같은가. -> 격자 둘의 최대 차 (기록이 없으면 None)."""
    p = os.path.join(HERE, "out", "기록", "점수판_진행.jsonl")
    if not os.path.exists(p):
        return None
    for line in open(p, encoding="utf-8"):
        s = json.loads(line)
        if s.get("case") == row["case"] and "새" in s:
            return round(max(abs(row["기본"]["IoU"] - s["새"][1]), abs(row["기본"]["IoU·192"] - s["새·192"][1])), 6)
    return None


def verr(row, k):
    return abs(row[k]["칸"] - row[k]["목표칸"]) / max(row[k]["목표칸"], 1)


def pipe_ok(row):
    """`균일` · `균일이진` 은 칸 수가 정확해야 한다. `앞뒤` 는 아래 사각지대 때문에 여기서 안 막고 Q3 이 본다."""
    d = pipe_score(row)
    if d is not None and d >= 1e-4:
        return False, "점수판 차 %.6f" % d
    for r in RS:
        for f in ("균일", "균일이진"):
            k = "%s@%.2f" % (f, r)
            if verr(row, k) >= 0.02:
                return False, "%s 칸 %d 목표 %d" % (k, row[k]["칸"], row[k]["목표칸"])
    return True, "통과 (점수판 차 %s)" % ("—" if d is None else "%.6f" % d)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def _ball(n, c, rx, ry, rz):
    i = np.arange(n)
    X, Y, Z = np.meshgrid(i - c, i - c, i - c, indexing="ij")
    return ((X / rx) ** 2 + (Y / ry) ** 2 + (Z / rz) ** 2) <= 1.0


def _iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))


def selfcheck():
    """**답을 아는 합성 물건 둘.** 이 둘이 갈려야 Q3(균일 대 앞뒤)이 판별력을 가진다."""
    n = 64
    # ① 등방으로 뚱뚱 — 균일 침식이 맞다
    t1, h1 = _ball(n, 32, 12, 12, 12), _ball(n, 32, 15, 15, 15)
    e1, _ = erode_to(h1, int(t1.sum()))
    d1, _ = H.depth_control(h1, int(e1.sum()))
    ie, idp = _iou(e1, t1), _iou(d1, t1)
    assert ie > idp + 0.01, "등방 과추정인데 균일이 앞뒤를 못 이긴다 (%.3f 대 %.3f)" % (ie, idp)

    # ② 앞뒤(y)로만 뚱뚱 — 앞뒤균일이 맞고, 균일은 정면 실루엣을 잃는다
    t2, h2 = _ball(n, 32, 14, 6, 14), _ball(n, 32, 14, 13, 14)
    e2, _ = erode_to(h2, int(t2.sum()))
    d2, _ = H.depth_control(h2, int(e2.sum()))
    ie2, id2 = _iou(e2, t2), _iou(d2, t2)
    assert id2 > ie2 + 0.01, "y 로만 뚱뚱한데 앞뒤가 균일을 못 이긴다 (%.3f 대 %.3f)" % (id2, ie2)
    se, sd = SF.sil_loss(e2, h2), SF.sil_loss(d2, h2)
    assert se > 0.02 and sd < se, "균일이 실루엣을 안 잃었다 (균일 %.3f · 앞뒤 %.3f)" % (se, sd)

    # ③ 칸 수가 목표와 정확히 같고 · r 이 작아질수록 포개진다
    for tag, e, t in (("①", e1, t1), ("②", e2, t2)):
        assert abs(int(e.sum()) - int(t.sum())) <= 5, "%s 균일 칸 수가 목표와 어긋난다" % tag
    a9, _ = erode_to(h1, int(0.9 * h1.sum()))
    a8, _ = erode_to(h1, int(0.8 * h1.sum()))
    assert (a8 & ~a9).sum() == 0, "더 깊은 침식이 얕은 것의 부분집합이 아니다"
    # 합성 구는 대칭이라 `depth_control` 의 기둥이 한꺼번에 잘린다 (실물은 기둥 2만 개라 훨씬 곱다 — 배관에서 2% 로 잡는다)
    assert abs(int(d1.sum()) - int(e1.sum())) / max(int(e1.sum()), 1) < 0.08, "앞뒤가 균일과 부피를 못 맞췄다"

    # ④ 채택 규칙 (빌려 쓰므로 그대로 다시 돈다)
    assert adopt([0.1, 0.2, -0.05, 0.3, 0.15])["통과"]
    assert not adopt([0.5, -0.1, -0.1, -0.1, 0.5])["통과"]
    assert not adopt([0.01, 0.01, -0.3, -0.3, 0.01, -0.3])["통과"]
    print("  자가검사 통과 — ① 등방 균일 %.3f > 앞뒤 %.3f · ② y뚱뚱 앞뒤 %.3f > 균일 %.3f "
          "(실루엣손실 균일 %.3f 대 앞뒤 %.3f) · ③ 부피 맞춤 · 포개짐 · ④ 채택 규칙" % (ie, idp, id2, ie2, se, sd))


def pipe_even(case="base_male"):
    """배관 ④ — 내 침식이 `hull.even_control` 과 **같은 것을 보는가** (한 장 · r 0.90).

    둘은 구현이 다르다 (복셀 수준집합 대 마칭큐브 부피 곡선). 그래서 t 를 직접 못 댄다 —
    대신 **같은 메시 부피**에서 판정의 자(속 채운 정답 IoU)가 같은 값을 주는지 본다."""
    masks, bs, plain, base, axes = GC.build(case)
    v, t = erode_to(base, int(round(0.90 * base.sum())))
    mine = C.to_mesh(v, axes)
    ref, t2 = H.even_control(base, axes, abs(mine.volume), cache={})
    g = truth_grids(case)
    F, ot = g[""]
    iou = lambda m: float((lambda A, B: (A & B).sum() / max((A | B).sum(), 1))(*J.common(F, ot, *J.grid(m, J.PITCH))))
    a, b = iou(mine), iou(ref)
    print("  배관 even_control 대조 (%s · r0.90): 내 IoU %.4f · even_control IoU %.4f · 차 %.4f (t %.2f 칸)"
          % (case, a, b, abs(a - b), t2))
    assert abs(a - b) < 0.005, "even_control 과 IoU 가 %.4f 어긋난다" % abs(a - b)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def rows():
    """본 판 + 보강 판(`앞뒤이진@r`)을 케이스마다 합친다. 보강이 없으면 그 판본만 없다."""
    out, add = {}, {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
            elif r.get("판") in (TAG2, TAG3):
                add.setdefault(r["case"], {}).update(r)
    for c, r in add.items():
        if c in out:
            out[c].update({k: v for k, v in r.items() if k.startswith("앞뒤이진")})
            if r.get("균일옛@제안부피"):
                out[c]["균일옛@제안부피"] = r["균일옛@제안부피"]
            elif "사유" in r:
                out[c]["옛사유"] = r["사유"]
    return out


TAG3 = "균일침식 옛대조 · 균일옛@제안부피 (옛 기본을 새 기본 부피까지 민 것) · 실물28 (2026-09-19)"


def old_control(n):
    """**논문 감사가 짚은 빠진 대조군** (`논문/기본파이프라인` 4.3).

    4.3 의 동일 부피 대조군은 *무처리 hull* 을 제안 부피까지 민 것이라 이진 바닥에 깔려 있다
    (09-18 층분해가 걸린 그 함정). 물음이 「타원 lam1.00 대 파이프 lam0.20」이므로 제대로 된 짝은
    **옛 기본(B)을 제안(A)의 부피까지 민 것**이다. 여기서 그것만 잰다."""
    import 오라클 as O
    have = rows()
    todo = [c for c in cases() if c in have and "균일옛@제안부피" not in have[c] and "옛사유" not in have[c]][:n]
    for c in todo:
        t0 = time.time()
        grids = truth_grids(c)
        masks, bs, plain, base, axes = GC.build(c)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        _, old, oaxes, _ = O.build(c, truth, H.LAM, "파이프")
        ctx = {"masks": masks, "bs": bs, "plain": plain, "axes": oaxes}
        nA, nB = int(base.sum()), int(old.sum())
        if nB <= nA:
            # 옛 기본이 제안보다 작은 장이 있다 — 밀어서 부피를 맞출 수 없다. 이 비교에서만 뺀다
            row = {"case": c, "판": TAG3, "균일옛@제안부피": None, "옛칸": nB, "목표칸": nA,
                   "사유": "옛 기본이 제안보다 작다 (밀 수 없다)", "초": round(time.time() - t0, 1)}
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print("  %-30s 구성 불가 — 옛 %d <= 제안 %d" % (c[:30], nB, nA), flush=True)
            continue
        v, t = erode_to(old, nA)
        m = measure(v, grids, ctx)
        m.update({"t": round(t, 3), "목표칸": nA, "옛칸": int(old.sum())})
        row = {"case": c, "판": TAG3, "균일옛@제안부피": m, "초": round(time.time() - t0, 1)}
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("  %-30s 옛 %d -> %d  IoU %.4f/%.4f (제안 %.4f/%.4f) · %.0f초"
              % (c[:30], old.sum(), m["칸"], m["IoU"], m["IoU·192"],
                 have[c]["기본"]["IoU"], have[c]["기본"]["IoU·192"], row["초"]), flush=True)
        del v, old, base
    print("  옛대조 남은 것 %d 장" % len([c for c in cases() if c in rows() and "균일옛@제안부피" not in rows()[c]]))


def boost(n):
    """**검토가 짚은 빠진 대조군.** `앞뒤@r` 의 정보 0 짝 — 이진 hull 을 같은 칸 수까지 앞뒤로만 깎은 것.
    본 판을 다시 안 돌리고 이 판본만 이어 붙인다 (같은 `케이스` · 같은 격자 · 같은 채점)."""
    have = rows()
    todo = [c for c in cases() if c in have and "앞뒤이진@%.2f" % RS[0] not in have[c]][:n]
    for c in todo:
        t0 = time.time()
        grids = truth_grids(c)
        masks, bs, plain, base, axes = GC.build(c)
        ctx = {"masks": masks, "bs": bs, "plain": plain, "axes": axes}
        out = {"case": c, "판": TAG2}
        print("  %s" % c, flush=True)
        for r in RS:
            n_r = have[c]["앞뒤@%.2f" % r]["칸"]              # 짝이 맞아야 하므로 `앞뒤@r` 의 **실제** 칸 수에 맞춘다
            v, q = H.depth_control(plain, n_r)
            m = measure(v, grids, ctx)
            m.update({"q": round(float(q), 6), "목표칸": n_r})
            out["앞뒤이진@%.2f" % r] = m
            print("    %-14s 칸 %8d (목표 %d)  IoU %.4f/%.4f  못덮음 %.4f  조각 %d"
                  % ("앞뒤이진@%.2f" % r, m["칸"], n_r, m["IoU"], m["IoU·192"], m["못덮음"], m["조각"]), flush=True)
            del v
        out["초"] = round(time.time() - t0, 1)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("  보강 남은 것 %d 장" % len([c for c in cases() if c in rows()
                                     and "앞뒤이진@%.2f" % RS[0] not in rows()[c]]))


def q_iou(rs, cs, a, b):
    o = {"뺄셈": "%s − %s" % (a, b)}
    for tag, name in (("", "128"), ("·192", "·192")):
        o[name] = adopt([rs[c][a]["IoU" + tag] - rs[c][b]["IoU" + tag] for c in cs])
    o["통과"] = bool(o["128"]["통과"] and o["·192"]["통과"])
    return o


def judge():
    rs = rows()
    cs = [c for c in cases() if c in rs]
    out = {"판": TAG, "장": len(cs), "케이스": cs, "r": list(RS)}
    if len(cs) < len(cases()):
        out["판정"] = "%d/%d 장 — 규칙상 판정 아님 (관찰)" % (len(cs), len(cases()))
    bad = {c: pipe_ok(rs[c])[1] for c in cs if not pipe_ok(rs[c])[0]}
    out["배관"] = "통과" if not bad else {"어긋남": bad}
    if bad:
        out["판정"] = "배관 어긋남 — 숫자를 버린다"
        return out

    ns = [k for k in names() if all(k in rs[c] for c in cs)]
    out["중앙"] = {k: {g: round(float(np.median([rs[c][k][g] for c in cs])), 5)
                      for g in ("IoU", "IoU·192", "못덮음", "넘침", "실루엣손실", "찢김", "조각")} for k in ns}
    out["중앙"] = {k: dict(v, 조각최대=max(rs[c][k]["조각"] for c in cs)) for k, v in out["중앙"].items()}
    out["부피비"] = {k: round(float(np.median([rs[c][k]["칸"] / rs[c]["칸_기본"] for c in cs])), 4) for k in ns}
    # 검토 지적: 채택 규칙의 중앙값은 큰 후퇴를 안 센다. 평균과 최악 두 장을 같이 낸다
    out["평균·최악"] = {}
    for k in ns:
        if k == "기본":
            continue
        d = sorted(((rs[c][k]["IoU"] - rs[c]["기본"]["IoU"], c) for c in cs))
        out["평균·최악"][k + " − 기본"] = {"평균": round(float(np.mean([x for x, _ in d])), 5),
                                        "최악 두 장": [[c, round(x, 4)] for x, c in d[:2]]}
    # 검토 지적: `depth_control` 의 q 가 0 에 붙으면 그 판본은 r 로 매개된 것이 아니다 (float32 반올림 산물)
    out["앞뒤 q"] = {"앞뒤@%.2f" % r: {"중앙": round(float(np.median([rs[c]["앞뒤@%.2f" % r]["q"] for c in cs])), 6),
                                     "q<1e-3 장": int(sum(rs[c]["앞뒤@%.2f" % r]["q"] < 1e-3 for c in cs)),
                                     "부피오차 2% 넘는 장": int(sum(verr(rs[c], "앞뒤@%.2f" % r) >= 0.02 for c in cs))}
                    for r in RS}

    Q, nxt = {}, []
    for r in RS:
        u, d, b = ("%s@%.2f" % (f, r) for f in ("균일", "앞뒤", "균일이진"))
        q = {"Q1 형상": q_iou(rs, cs, u, "기본")}
        mu = np.array([rs[c][u]["못덮음"] - rs[c]["기본"]["못덮음"] for c in cs])
        pc = float(np.median([rs[c][u]["조각"] for c in cs]))
        q["Q2 약속"] = {"뺄셈": "%s − 기본 · 못덮음" % u, "중앙": round(float(np.median(mu)), 5),
                       "오른 장": int((mu > 0).sum()), "n": len(cs), "조각 중앙": pc,
                       "문턱": "중앙 ≤ +0.005 그리고 조각 중앙 ≤ 1",
                       "통과": bool(np.median(mu) <= 0.005 and pc <= 1.0)}
        # Q3 은 **같은 부피에서만** 뜻이 있다. `depth_control` 은 q>0 이 되는 순간 기둥마다 앞뒤 한 칸씩을
        # 한꺼번에 떼어 내 **첫 10% 가 사각지대**다 (avatarsample_d 실측: 133,372 -> 119,878 으로 건너뛴다).
        # 그 안에 떨어지는 r 에서는 짝을 못 지으므로 판정하지 않는다 (측정 뒤에 안 곳 · 기록에 남긴다).
        ve = float(np.median([verr(rs[c], d) for c in cs]))
        q["Q3 방향"] = (q_iou(rs, cs, u, d) if ve < 0.02 else
                      {"뺄셈": "%s − %s" % (u, d), "판정": "부피 불일치 — 판정 불가", "통과": None})
        q["Q3 부피오차 중앙"] = round(ve, 4)
        q["Q4 정보0"] = q_iou(rs, cs, u, b)
        q["참고 앞뒤−기본"] = q_iou(rs, cs, d, "기본")
        # **Q5 (검토가 짚은 빠진 대조군).** `앞뒤@r` 도 제 정보 0 짝을 이겨야 한다 — `hull.depth_control` 은
        # 저장소가 스스로 「정보를 0 만큼 쓴다」고 적어 둔 함수다. 이걸 안 두면 추천 판본만 대조군 없이 통과한다.
        db = "앞뒤이진@%.2f" % r
        q["Q5 앞뒤의 정보0"] = (q_iou(rs, cs, d, db) if all(db in rs[c] for c in cs)
                            else {"판정": "안 쟀다 (보강 미완)", "통과": None})
        md = np.array([rs[c][d]["못덮음"] - rs[c]["기본"]["못덮음"] for c in cs])
        q["참고 앞뒤 약속"] = {"중앙": round(float(np.median(md)), 5), "오른 장": int((md > 0).sum())}
        Q["r=%.2f" % r] = q

        if not q["Q1 형상"]["통과"]:
            nxt.append("r=%.2f Q1 짐 — 부피를 그만큼 조여도 점수판이 안 오른다" % r)
        elif not q["Q4 정보0"]["통과"]:
            nxt.append("r=%.2f Q1 통과 · Q4 짐 — 그 부피에서 깊이 깎기가 부피 손잡이다. 그 이하는 안 본다" % r)
        elif not q["Q2 약속"]["통과"]:
            alt = ("앞뒤@%.2f 가 Q1 통과 — 그쪽을 낸다" % r if q["참고 앞뒤−기본"]["통과"]
                   else "앞뒤@%.2f 도 Q1 짐 — 채택 안 함" % r)
            nxt.append("r=%.2f Q1 통과 · Q2 짐 (못덮음 %+.5f) — %s" % (r, q["Q2 약속"]["중앙"], alt))
        else:
            nxt.append("r=%.2f Q1·Q2·Q4 통과 — %s 를 기본값 후보로"
                       % (r, u if q["Q3 방향"]["통과"] is not False else d))
    out["Q"], out["다음"] = Q, nxt
    return out


# ── 그림 ─────────────────────────────────────────────────────────────────────

def figure():
    rs = rows()
    cs = [c for c in cases() if c in rs]
    if not cs:
        print("  잰 장이 없다")
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fp = r"C:\Windows\Fonts\malgun.ttf"
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    med = lambda k, g: float(np.median([rs[c][k][g] for c in cs]))

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    styles = (("균일", "#c0392b", "균일@r  (후보 · 사방으로 민다)"),
              ("앞뒤", "#2471a3", "앞뒤@r  (같은 부피 · 실루엣 지킴)"),
              ("균일이진", "#7f8c8d", "균일이진@r  (정보 0 · 깎기 없음)"))
    for j, (g, ylab, ttl) in enumerate((("IoU", "속 채운 정답 IoU 중앙 (격자 128)", "형상"),
                                        ("못덮음", "원화 못덮음 중앙 (작아야 약속을 지킨다)", "약속 — 원화 실루엣"),
                                        ("실루엣손실", "hull 실루엣 손실 중앙", "약속 — hull 대비"))):
        for fam, col, lab in styles:
            x = list(RS) if fam == "균일이진" else [1.0] + list(RS)
            y = ([] if fam == "균일이진" else [med("기본", g)]) + [med("%s@%.2f" % (fam, r), g) for r in RS]
            ax[j].plot(x, y, "o-", color=col, label=lab if j == 0 else None)
        ax[j].axhline(med("기본", g), ls="--", c="k", lw=0.8)
        ax[j].set_xlabel("부피 비율 r  (1.00 = 지금 기본)")
        ax[j].set_ylabel(ylab)
        ax[j].set_title(ttl)
        ax[j].invert_xaxis()
        ax[j].grid(alpha=0.3)
    ax[0].legend(fontsize=8, loc="best")
    fig.suptitle("고정 비율 균일 침식 · 실물 %d장 · 점선 = 지금 기본 (타원 lam1.00)" % len(cs))
    fig.tight_layout()
    p = os.path.join(HERE, "out", "균일침식.png")
    fig.savefig(p, dpi=110)
    print("  -> %s" % p)


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
        pipe_even()
        return
    if a == "그림":
        figure()
        return
    if a == "보강":
        boost(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
        return
    if a == "옛대조":
        old_control(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
        return
    if a != "판정":
        selfcheck()
        done = rows()
        for c in [c for c in cases() if c not in done][:int(a)]:
            print("  %s" % c, flush=True)
            r = one(c)
            ok, why = pipe_ok(r)
            print("    배관 %s · %.0f초" % (why, r["초"]), flush=True)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            if not ok:
                print("  배관 어긋남 — 멈춘다")
                return
        print("  남은 것 %d 장" % (len(cases()) - len(rows())))
    if a == "판정" or len(rows()) >= len(cases()):
        v = judge()
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "균일침식_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)


if __name__ == "__main__":
    main()
