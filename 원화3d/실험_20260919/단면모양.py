# -*- coding: utf-8 -*-
"""**단면 모양 — 틈 잇기 · 각짐에 따른 초타원 지수 · 창 잘림** (2026-09-19).

    python 단면모양.py 검사     자가검사만 (각짐 지표 · 지수 사상 · 대조군)
    python 단면모양.py 창       ③ 창 잘림만 잰다 -> out/기록/단면모양_창.json
    python 단면모양.py [n]      아직 안 한 장 n 개 (첫 장은 닫힌 궤짝) -> out/기록/단면모양_진행.jsonl
    python 단면모양.py 판정     -> out/기록/단면모양_판정_<때>.json
    python 단면모양.py 그림     네 장 접촉지 (면 법선 명암) -> out/단면모양_명암.png

판정은 `claudedocs/plan_단면모양_20260919.md` 「3 판정」 그대로다 — 돌리기 전에 적었다.
판본은 **단면에 넣는 모양**만 바꾼다. 깎기(`hull.carve_depth`) · lam 1.00 · 채점(속 채운 정답 ·
격자 128 · 192 · IoU 중앙)은 `실험_20260915/점수판.py` 규약 그대로다.

대조군은 판본마다 따로 둔다 — `hull.depth_control` 로 **그 판본과 같은 칸 수**까지 모든 기둥을
앞뒤로 같은 비율만큼 판 것. 깎는 축도 부피도 같고 모양 정보만 0 이다. 하나(기본)만 두면
대조군이 전부 바닥에 깔려 두 팔 사이를 못 가른다 (09-18 층분해).
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
sys.path.insert(0, os.path.join(HERE, "실험_20260916"))
os.chdir(HERE)
import hull as H
import win as W
import 정답 as J
import 표면 as SF
from 겉면채점 import bench_cases, fill_slices
from 깨짐 import thin_share
from 조각묶기 import masks_of, scorer, section

PROG = os.path.join(HERE, "out", "기록", "단면모양_진행.jsonl")
TAG = ("단면모양 · 실물28 · p2·p2.5·p4·p10 / 묶기k5·k9 + 판본마다 균일 대조 · 타원 lam1.00 · "
       "속채운 정답 · 격자128·192 (2026-09-19)")
PGRID = (2.0, 2.5, 4.0, 10.0)                    # 지수 눈금. 각짐연속 · 각짐문턱 · 오라클p 는 여기서 **고르기만** 한다
VARS = tuple("p%g" % p for p in PGRID) + ("묶기k5", "묶기k9")
DIRTY = ("cloak_Chest_Closed_AngpV0HxD8", "mech_Mech_4UvIHxnoSR")     # 창 밖 정답 ≥ 1% (계획 Q0)
FOUR = ("wizard_Wizard_o87Upt5uHX", "cloak_Chest_Closed_AngpV0HxD8",
        "cloak_Chest_O72u4Drp8k", "mech_Drill_8uBbH7Dvmb")            # 09-15 에 눈으로 짚인 네 장
BACK4 = FOUR + ("cape_Hat_Stylised_lNN3PlrjSa",)                      # 후퇴 네 장 = 궤짝 둘 · 드릴 · 모자
REGRESS = ("cloak_Chest_Closed_AngpV0HxD8", "cloak_Chest_O72u4Drp8k",
           "mech_Drill_8uBbH7Dvmb", "cape_Hat_Stylised_lNN3PlrjSa")


# ------------------------------------------------------------------ ③ 창 잘림

def clip_out(case):
    """**정답 복셀 중 창 밖으로 나간 몫.** `to_win` 이 아니라 시트 렌더 창(u ∈ [−0.6, 0.6])의 한계다.

    `to_win` 쪽은 따로 본다 — 앉힌 폭 w 가 창 폭을 넘으면 그 함수는 가운데가 아니라 **왼쪽 RES 열**을
    잘라 물건을 오른쪽으로 민다. 넘는 장이 하나도 없으면 그 경로는 이 벤치에서 안 탄다."""
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    T, o = J.grid(truth)
    idx = np.argwhere(fill_slices(T)) + o
    x, y = (idx[:, 0] + 0.5) * J.PITCH, (idx[:, 1] + 0.5) * J.PITCH
    src, base = H.CASES[case]["src"], H.art_dir(case)
    wmax = 0
    for v, f in src.items():
        m = H.declutter(W.art_mask(os.path.join(base, f)))
        ys, xs = np.where(m)
        h = int(round(W.RES / (W.Z1 - W.Z0)))
        wmax = max(wmax, int(round((np.ptp(xs) + 1) * h / (np.ptp(ys) + 1))))
    return {"창밖": round(float(((np.abs(x) > W.U1) | (np.abs(y) > W.U1)).mean()), 4),
            "정답 가로·깊이": [round(float(np.ptp(x)), 3), round(float(np.ptp(y)), 3)],
            "앉힌 최대 폭": wmax, "to_win 넘침": bool(wmax > W.RES)}


# ------------------------------------------------------------------ 각짐 (원화만 본다)

def straightness(m):
    """실루엣 외곽의 **긴 직선 변이 차지하는 둘레 몫.** 원 → 0 · 직사각형 → 1.

    둘레²/(4π·면적) 같은 촘촘함 지표는 팔다리 · 망토 같은 돌기에서 폭발해 「복잡함」을 「각짐」으로
    읽는다. 그래서 다각형 근사를 하고 **둘레의 10% 이상인 변**만 센다.

    **근사 오차 ε 은 두 정점이 정한다** (벤치 숫자를 보고 고르지 않았다). ε = 둘레의 1% 면 반지름
    120 화소 원이 0.41 로 읽힌다 — 둘레의 10% 짜리 현이 호에서 5.9 화소 벗어나는데 ε 이 7.5 화소라
    통과하기 때문이다. ε = 0.2% 로 내리면 정사각 1.00 · 원 0.00 이 되고, 그게 `selfcheck` 의 문이다."""
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    per = cv2.arcLength(c, True)
    ap = cv2.approxPolyDP(c, 0.002 * per, True)[:, 0, :].astype(float)
    seg = np.linalg.norm(np.diff(np.vstack([ap, ap[:1]]), axis=0), axis=1)
    return float(seg[seg >= 0.10 * per].sum() / max(per, 1e-9))


def angularity(case):
    """세 시점 각짐의 중앙값. **정답을 안 본다.**"""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    return float(np.median([straightness(H.declutter(W.art_mask(os.path.join(base, src[v]))))
                            for v in W.VIEWS]))


def p_of(theta):
    """각짐 → 지수. **두 정점으로 고정한다** — 원 θ=0 → p=2 (타원) · 정사각 θ=1 → p=10 (상자).
    데이터로 맞춘 상수가 없다. 눈금 `PGRID` 에 로그 최근접으로 붙인다.

    -> (각짐연속 p, 각짐문턱 p)"""
    cont = min(PGRID, key=lambda q: abs(np.log(q) - np.log(2.0 * 5.0 ** theta)))
    return cont, (10.0 if theta >= 0.5 else 2.0)


# ------------------------------------------------------------------ 판본

def build(masks, bs, how, plain=None, axes=None):
    """판본 하나의 복셀. `plain` · `axes` 를 주면 hull 을 다시 안 깎는다."""
    if plain is None:
        plain, axes = H.carve(masks, back_sign=bs)
    if how.startswith("묶기"):
        deps = H.ellipse_depths(plain, axes, bs, E=section(plain, how))
    else:
        deps = H.ellipse_depths(plain, axes, bs, p=float(how[1:]))
    vox, _ = H.carve_depth(masks, deps, lam=H.DEPTH_LAM, back_sign=bs)
    return vox, plain, axes


def metrics(vox, plain):
    return {"조각": SF.pieces(vox), "얇은판": round(thin_share(vox), 5),
            "찢김": round(SF.tear(vox), 4), "실루엣손실": round(SF.sil_loss(vox, plain), 4),
            "칸": int(vox.sum())}


def one(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    score = scorer(truth)
    masks, bs = masks_of(c)
    th = angularity(c)
    row = {"case": c, "판": TAG, "각짐": round(th, 3), "p연속": p_of(th)[0], "p문턱": p_of(th)[1],
           "오염": c in DIRTY}
    plain = axes = None
    for how in VARS:
        vox, plain, axes = build(masks, bs, how, plain, axes)
        s = score(H.trimesh.Trimesh(*H.mesh_from(vox, axes), process=True))
        row[how] = dict(iou=s[""], iou192=s["·192"], **metrics(vox, plain))
        even, q = H.depth_control(plain, int(vox.sum()))
        se = score(H.trimesh.Trimesh(*H.mesh_from(even, axes), process=True))
        row["균일@" + how] = {"iou": se[""], "iou192": se["·192"], "q": round(q, 4),
                             "칸": int(even.sum())}
    row["초"] = round(time.time() - t0, 1)
    return row


# ------------------------------------------------------------------ 판정

# **사후 민감도 — p < 2 (마름모 쪽).** 계획의 눈금은 {2, 2.5, 4, 10} 이라 아래쪽을 안 봤다. 09-12 기록에
# 모자가 p=1.0 을 원했다고 적혀 있어, 오라클 게이트의 0 이 눈금 누락 탓인지 따로 잰다. **판정에 안 넣고
# 「사후」로만 싣는다** — 돌린 뒤에 더한 팔이다.
BOTAM = os.path.join(HERE, "out", "기록", "단면모양_보탬_진행.jsonl")
BTAG = "단면모양 보탬 · p1.5 + 같은 부피 균일 · 사후 민감도 (2026-09-19)"


def one_botam(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    score = scorer(truth)
    masks, bs = masks_of(c)
    vox, plain, axes = build(masks, bs, "p1.5")
    s = score(trimesh.Trimesh(*H.mesh_from(vox, axes), process=True))
    even, q = H.depth_control(plain, int(vox.sum()))
    se = score(trimesh.Trimesh(*H.mesh_from(even, axes), process=True))
    return {"case": c, "판": BTAG, "p1.5": {"iou": s[""], "iou192": s["·192"]},
            "균일@p1.5": {"iou": se[""], "iou192": se["·192"]}, "초": round(time.time() - t0, 1)}


def botam_rows():
    out = {}
    if os.path.exists(BOTAM):
        for line in open(BOTAM, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == BTAG:
                out[r["case"]] = r
    return out


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def pipe(r):
    """배관 — `p2` 가 09-15 점수판의 새 기본(= `hull.carve_default`)을 되찾나."""
    sb = {x["case"]: x for x in map(json.loads, open(os.path.join(HERE, "out", "기록", "점수판_진행.jsonl"), encoding="utf-8"))}
    return abs(r["p2"]["iou"] - sb[r["case"]]["새"][1])


def pick(r, how):
    """`각짐연속` · `각짐문턱` · `오라클p` 는 p 눈금 넷 중에서 **고르기만** 한다."""
    if how == "오라클p":
        return max(("p%g" % p for p in PGRID), key=lambda k: r[k]["iou"])
    return "p%g" % (r["p연속"] if how == "각짐연속" else r["p문턱"])


def col(rs, cs, how, key="iou"):
    return np.array([rs[c][pick(rs[c], how) if how in DERIVED else how][key] for c in cs])


def even_col(rs, cs, how, key="iou"):
    return np.array([rs[c]["균일@" + (pick(rs[c], how) if how in DERIVED else how)][key] for c in cs])


DERIVED = ("각짐연속", "각짐문턱", "오라클p")
SHOW = VARS + DERIVED


def vol_err(rs, cs, how):
    """**대조군이 부피를 정말 맞췄나.** `depth_control` 은 기둥마다 앞뒤 한 칸씩은 반드시 벗기므로
    (q=0 이 상한이 아니다) hull 에 가까운 판본에서는 목표 칸 수에 못 닿는다. 부피가 안 맞으면
    그 판본의 정보몫은 「모양 이득」이 아니라 「부피 차」를 읽는다 — 09-19 검토가 짚었다."""
    k = "칸"
    a = np.array([rs[c]["균일@" + (pick(rs[c], how) if how in DERIVED else how)][k] for c in cs], float)
    b = np.array([rs[c][pick(rs[c], how) if how in DERIVED else how][k] for c in cs], float)
    d = (a - b) / np.maximum(b, 1)
    return {"중앙": round(float(np.median(d)), 4), "최대|오차|": round(float(np.abs(d).max()), 4),
            "1% 넘게 어긋난 장": int((np.abs(d) > 0.01).sum())}


def arm(rs, cs, how):
    """판본 하나의 판정 숫자. 차는 `p2` 대비, 정보몫은 **같은 부피 균일** 대비.

    `정보몫`(열 중앙)과 `짝 정보몫 이득`(짝 중앙)을 둘 다 싣는다. 판본 사이를 견줄 때는
    **짝 쪽**을 봐야 한다 — 두 열의 중앙값을 빼면 서로 다른 장이 중앙에 와서 크기가 부풀고,
    09-19 검토에서 묶기k9 가 실제 +0.0025 인데 +0.0094 로 보였다."""
    out = {}
    for key, tag in (("iou", "128"), ("iou192", "192")):
        v, b = col(rs, cs, how, key), col(rs, cs, "p2", key)
        e, e0 = even_col(rs, cs, how, key), even_col(rs, cs, "p2", key)
        out[tag] = {"중앙": round(float(np.median(v)), 4), "차 중앙": round(float(np.median(v - b)), 4),
                    "차 평균": round(float((v - b).mean()), 4), "차 합": round(float((v - b).sum()), 4),
                    "차 최저": round(float((v - b).min()), 4), "차 최고": round(float((v - b).max()), 4),
                    "오른 장": int((v - b > 5e-4).sum()),
                    "정보몫": round(float(np.median(v - e)), 4),
                    "짝 정보몫 이득": round(float(np.median((v - b) - (e - e0))), 4)}
    out["대조군 부피오차"] = vol_err(rs, cs, how)
    sel = lambda c: pick(rs[c], how) if how in DERIVED else how
    out["찢김 중앙"] = round(float(np.median([rs[c][sel(c)]["찢김"] for c in cs])), 4)
    out["실루엣손실 최대"] = round(float(max(rs[c][sel(c)]["실루엣손실"] for c in cs)), 4)
    out["조각 합"] = int(sum(rs[c][pick(rs[c], how) if how in DERIVED else how]["조각"] for c in cs))
    out["얇은판 궤짝·로봇형 마법사"] = [rs[k][pick(rs[k], how) if how in DERIVED else how]["얇은판"]
                                for k in ("cloak_Chest_Closed_AngpV0HxD8", "wizard_Wizard_o87Upt5uHX")]
    out["후퇴 네 장 차"] = {k: round(float(rs[k][pick(rs[k], how) if how in DERIVED else how]["iou"] - rs[k]["p2"]["iou"]), 4)
                       for k in REGRESS if k in rs}
    return out


def judge_set(rs, cs, name):
    out = {"집합": name, "장": len(cs)}
    A = {how: arm(rs, cs, how) for how in SHOW}
    out["판본"] = A
    thin0 = A["p2"]["얇은판 궤짝·로봇형 마법사"]
    info0 = A["p2"]["128"]["정보몫"]
    # Q1 — 틈 잇기
    out["Q1 틈 잇기"] = {}
    for how in ("묶기k5", "묶기k9"):
        a = A[how]
        c1 = all(a[t]["차 중앙"] >= 0 and a[t]["차 최저"] >= -0.01 for t in ("128", "192"))
        c2 = a["128"]["정보몫"] >= info0
        c3 = all(x <= 0.5 * y for x, y in zip(a["얇은판 궤짝·로봇형 마법사"], thin0))
        c4 = a["조각 합"] <= A["p2"]["조각 합"]
        out["Q1 틈 잇기"][how] = {"① 안 떨어짐": c1, "② 부피가 아님": c2, "③ 판 줄음": c3,
                              "④ 안 깨짐": c4, "통과": bool(c1 and c2 and c3 and c4)}
    # Q2 — 오라클 게이트 먼저
    gate = A["오라클p"]["128"]["차 중앙"]
    up = A["오라클p"]["128"]["오른 장"]
    out["Q2 지수"] = {"오라클 게이트 차 중앙": gate, "문턱": 0.005, "게이트": bool(gate >= 0.005),
                   # **이 게이트는 0 말고는 못 내는 자리일 수 있다** (09-19 검토). 눈금의 왼쪽 끝이 기준선 p2
                   # 자신이라 오라클 ≥ p2 이고, 고칠 수 있는 장이 절반을 못 넘으면 중앙은 크기와 무관하게 0 이다
                   "오른 장": up, "중앙이 0 으로 강제되나": bool(up <= len(cs) / 2),
                   "오라클 차 평균 · 합 · 최고": [A["오라클p"]["128"]["차 평균"], A["오라클p"]["128"]["차 합"],
                                        A["오라클p"]["128"]["차 최고"]]}
    for how in ("각짐연속", "각짐문턱"):
        a = A[how]
        c1 = all(a[t]["차 중앙"] >= 0 and a[t]["차 최저"] >= -0.01 for t in ("128", "192"))
        c2 = a["128"]["정보몫"] >= info0
        c3 = sum(1 for v in a["후퇴 네 장 차"].values() if v > 5e-4) >= 3
        c4 = gate > 0 and a["128"]["차 중앙"] / gate >= 0.5
        out["Q2 지수"][how] = {"① 안 떨어짐": c1, "② 부피가 아님": c2, "③ 후퇴 세 장 회복": c3,
                            "④ 천장몫 ≥ 0.5": c4,
                            "통과": bool(out["Q2 지수"]["게이트"] and c1 and c2 and c3 and c4)}
    return out


def judge():
    rs = rows()
    cs = [c for c in bench_cases() if c != "소체"]
    if any(c not in rs for c in cs):
        return {"판": TAG, "판정": "%d/%d 장 — 판정 안 함" % (len(rs), len(cs))}
    out = {"판": TAG, "배관 최대차": round(max(pipe(rs[c]) for c in cs), 6),
           "각짐": {c: rs[c]["각짐"] for c in cs},
           "고른 p": {c: {h: pick(rs[c], h) for h in DERIVED} for c in cs}}
    if out["배관 최대차"] >= 1e-4:
        out["배관"] = "어긋남 — 숫자를 버린다"
        return out
    out["배관"] = "통과"
    # 조사 권고 2 — 「각짐 지표 ↔ 최선 p」의 상관만 먼저 본다. 추정기를 만들기 전에 길이 살았나 보는 값이다
    from scipy.stats import spearmanr
    th = np.array([rs[c]["각짐"] for c in cs])
    bp = np.array([float(pick(rs[c], "오라클p")[1:]) for c in cs])
    out["각짐 ↔ 오라클p"] = {"스피어만": round(float(spearmanr(th, bp).correlation), 3),
                        "오라클p 분포": {"p%g" % p: int((bp == p).sum()) for p in PGRID}}
    out["Q0 창 잘림"] = {"오염 장": list(DIRTY), "판정": "고치지 않는다 — 배관 버그가 아니라 창 규약의 한계",
                     "근거": "to_win 넘침 0 장 · 잘림은 시트 렌더 창(u ∈ [−0.6, 0.6])"}
    br = botam_rows()
    if all(c in br for c in cs):
        # 눈금에 p1.5 를 넣었으면 오라클 게이트가 달랐을까. **판정이 아니라 사후 민감도다**
        v = np.array([br[c]["p1.5"]["iou"] for c in cs])
        b = np.array([rs[c]["p2"]["iou"] for c in cs])
        e = np.array([br[c]["균일@p1.5"]["iou"] for c in cs])
        o5 = np.array([max(br[c]["p1.5"]["iou"], *(rs[c]["p%g" % p]["iou"] for p in PGRID)) for c in cs])
        out["사후 p1.5 (판정 밖)"] = {
            "p1.5 중앙": round(float(np.median(v)), 4), "차 중앙": round(float(np.median(v - b)), 4),
            "차 최저": round(float((v - b).min()), 4), "오른 장": int((v - b > 5e-4).sum()),
            "정보몫": round(float(np.median(v - e)), 4),
            "눈금에 1.5 를 넣은 오라클 차 중앙": round(float(np.median(o5 - b)), 4),
            "그때도 게이트 짐": bool(float(np.median(o5 - b)) < 0.005)}
    out["28장"] = judge_set(rs, cs, "28장")
    out["26장 (오염 뺀)"] = judge_set(rs, [c for c in cs if c not in DIRTY], "26장")
    q1 = {h: out["28장"]["Q1 틈 잇기"][h]["통과"] for h in ("묶기k5", "묶기k9")}
    q2 = out["28장"]["Q2 지수"]["게이트"]
    same = all(out["28장"]["Q1 틈 잇기"][h]["통과"] == out["26장 (오염 뺀)"]["Q1 틈 잇기"][h]["통과"] for h in q1) \
        and q2 == out["26장 (오염 뺀)"]["Q2 지수"]["게이트"]
    out["28장 · 26장 결론이 같나"] = bool(same)
    nxt = []
    if any(q1.values()):
        nxt.append("틈 잇기(%s)를 기본값 후보로 사람에게 올린다" % " · ".join(h for h in q1 if q1[h]))
    if not q2 and out["28장"]["Q2 지수"]["중앙이 0 으로 강제되나"]:
        # **줄기를 닫지 않는다.** 게이트가 0 말고는 못 내는 자리였다 (09-19 검토) — 눈금의 왼쪽 끝이
        # 기준선 p2 자신이라 오라클 ≥ p2 이고, 고칠 수 있는 장이 8/28 이면 중앙은 크기와 무관하게 0 이다.
        # 사후 p1.5 가 그 의심을 숫자로 확인했다: 눈금에 1.5 를 넣으면 오라클 차 중앙이 문턱을 넘는다
        nxt.append("Q2 는 「짐」이 아니라 **판정 무효**다 — 게이트가 구조적으로 0 만 낼 수 있었다 "
                   "(오라클이 고칠 수 있는 장 %d/%d · 실제 평균 이득 %+.4f · 최고 %+.4f). "
                   "지수 줄기는 p<2 쪽으로 다시 연다" % (out["28장"]["Q2 지수"]["오른 장"], len(cs),
                                              out["28장"]["판본"]["오라클p"]["128"]["차 평균"],
                                              out["28장"]["판본"]["오라클p"]["128"]["차 최고"]))
    elif not q2:
        nxt.append("지수 줄기를 닫는다 — 정답을 보고 고른 p 도 문턱을 못 넘었다")
    elif any(out["28장"]["Q2 지수"][h]["통과"] for h in ("각짐연속", "각짐문턱")):
        nxt.append("각짐 규칙을 올린다")
    else:
        nxt.append("지수에 머리 위는 있으나 원화 규칙이 못 따라간다 — 부품별 지수로")
    if "사후 p1.5 (판정 밖)" in out:
        b = out["사후 p1.5 (판정 밖)"]
        nxt.append("사후 p1.5 (판정 밖): 차 중앙 %+.4f · 오른 장 %d/%d · 정보몫 %+.4f — "
                   "**각짐 가설과 반대 방향**이다 (상자가 아니라 마름모 쪽)"
                   % (b["차 중앙"], b["오른 장"], len(cs), b["정보몫"]))
    if not any(q1.values()) and not q2:
        nxt.append("네 장의 이상함은 단면 모양이 아니다 — 다음은 격자(256→512) · 창")
    if not same:
        nxt.append("28장과 26장 결론이 갈린다 — 창 탓. 어느 쪽도 기본값 후보로 안 올린다")
    out["다음"] = " · ".join(nxt)
    return out


# ------------------------------------------------------------------ 그림 (눈으로 보는 접촉지)

def figure():
    """네 장 × (정답 · p2 · 묶기k9 · 각짐문턱 · 오라클p) — 면 법선 명암. 같은 틀 · 같은 빛.
    얇은 판 몫은 09-15 에 이상함을 못 잡았다 (절대값 0.3% 이하). 그래서 눈으로 본다."""
    import 깊이색 as DC
    import 앨리어싱 as AL
    from 폴리싱 import shaded
    rs = rows()
    cols = ["정답 (GT)", "p2 = 지금 기본", "묶기k9", "p10 (상자 쪽)", "p1.5 (마름모 쪽)", "오라클p"]
    br = botam_rows()
    out = []
    for c in FOUR:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        masks, bs = masks_of(c)
        r = rs.get(c)
        hows = ["p2", "묶기k9", "p10", "p1.5", pick(r, "오라클p") if r else "p4"]
        meshes = [truth]
        plain = axes = None
        for how in hows:
            vox, plain, axes = build(masks, bs, how, plain, axes)
            meshes.append(trimesh.Trimesh(*H.mesh_from(vox, axes), process=True))
        fr = AL.frame_of(meshes[0], 45)
        tiles = [shaded(m, 45, fr, 400) for m in meshes]
        lab = "%s  (각짐 %.2f)" % (c[:22], r["각짐"] if r else float("nan"))
        if r:
            val = lambda h: br[c]["p1.5"]["iou"] if h == "p1.5" else r[h]["iou"]
            lab += "\n%s" % " · ".join("%.3f" % val(h) for h in hows)
        out.append((lab, tiles))
        print("  %s 명암 (%s)" % (c[:28], " · ".join(hows)), flush=True)
    DC.grid(out, cols, "단면 모양 — 09-15 에 눈으로 짚인 네 장 (면 법선 명암 · z 버퍼 · az 45)",
            "같은 빛 · 같은 틀. 숫자는 속 채운 정답 IoU (격자 128). p1.5 는 판정 밖 사후 판본 · 오라클p 는 정답을 보고 케이스마다 고른 값이다",
            os.path.join(HERE, "out", "단면모양_명암.png"))


# ------------------------------------------------------------------ 자가검사

def selfcheck():
    # 1 각짐 — 정사각형은 1 에 가깝고 원은 0 에 가깝다 (지표가 방향을 맞나)
    sq = np.zeros((400, 400), bool); sq[80:320, 80:320] = True
    I, Jg = np.meshgrid(np.arange(400), np.arange(400), indexing="ij")
    ci = ((I - 200.) ** 2 + (Jg - 200.) ** 2) <= 120. ** 2
    a, b = straightness(sq), straightness(ci)
    assert a > 0.95 and b < 0.05, "각짐의 두 정점이 안 맞는다 (정사각 %.2f · 원 %.2f)" % (a, b)
    # 2 지수 사상의 두 정점 — 데이터가 아니라 이 둘이 상수를 정한다
    assert p_of(0.0) == (2.0, 2.0) and p_of(1.0) == (10.0, 10.0), "사상의 정점이 틀렸다 %s" % (p_of(0.0), p_of(1.0))
    assert p_of(0.5)[1] == 10.0 and p_of(0.49)[1] == 2.0, "문턱이 0.5 가 아니다"
    # 3 지수가 단면을 실제로 채우나 — p 가 크면 상자에 가까워 칸이 는다
    v = np.zeros((40, 40, 6), bool); v[8:32, 10:30, 2:4] = True
    n2, n10 = H.superellipse(v, 2.0).sum(), H.superellipse(v, 10.0).sum()
    assert n10 > n2 * 1.15, "지수를 올렸는데 단면이 안 찬다 (%d -> %d)" % (n2, n10)
    # 4 균일 대조군 — 같은 칸 수를 되찾고, 정면 실루엣을 안 갉는다 (정보 0 인데 부피가 다르면 비교가 깨진다)
    # 기둥 깊이가 칸마다 같으면(순수 상자) 부피가 1080 칸씩 뚝뚝 뛰어 어떤 q 도 목표를 못 맞춘다.
    # 실제 hull 은 기둥 깊이가 제각각이라 거의 연속이다 — 그 쪽으로 검사한다
    gx, gy, gz = np.meshgrid(*[np.arange(48) - 23.5] * 3, indexing="ij")
    plain = (gx ** 2 / 20. ** 2 + gy ** 2 / 14. ** 2 + gz ** 2 / 22. ** 2) <= 1.0
    tgt = int(plain.sum() * 0.6)
    even, q = H.depth_control(plain, tgt)
    assert abs(even.sum() - tgt) / tgt < 0.05, "균일 대조군 부피가 %d 대 %d" % (even.sum(), tgt)
    assert even.any(1).sum() == plain.any(1).sum(), "균일 대조군이 정면 실루엣을 갉았다"
    # 5 묶기는 깊이(y) 축으로만 잇는다 (`조각묶기.section` 을 그대로 부른다 — 코드를 다시 안 짰다)
    g = np.zeros((20, 21, 3), bool); g[2:18, 2:10, 1] = g[2:18, 11:19, 1] = True
    from scipy import ndimage as nd
    assert nd.label(section(g, "묶기k5")[:, :, 1])[1] == 1, "묶기가 틈 너머로 안 이었다"
    print("  자가검사 통과 — 각짐 지표 · 지수 사상 정점 · 초타원 채움 · 균일 대조군 부피/실루엣 · 묶기")


def main():
    H.register_sheets()
    selfcheck()
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        return
    if a == "그림":
        return figure()
    if a == "창":
        v = {c: clip_out(c) for c in bench_cases() if c != "소체"}
        p = os.path.join(HERE, "out", "기록", "단면모양_창.json")
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        for c, r in sorted(v.items(), key=lambda kv: -kv[1]["창밖"]):
            print("  %-34s 창밖 %6.2f%% · 가로·깊이 %s · 앉힌 폭 %4d · to_win 넘침 %s"
                  % (c[:34], 100 * r["창밖"], r["정답 가로·깊이"], r["앉힌 최대 폭"], r["to_win 넘침"]))
        print("  -> %s" % p)
        return
    if a == "보탬":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 28
        done = botam_rows()
        for c in [c for c in bench_cases() if c != "소체" and c not in done][:n]:
            r = one_botam(c)
            with open(BOTAM, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-30s p1.5 %.3f (균일 %.3f) · %.0f초" % (c[:30], r["p1.5"]["iou"], r["균일@p1.5"]["iou"], r["초"]), flush=True)
        print("  %d/28 장 (보탬)" % len(botam_rows()))
        return
    if a != "판정":
        done = rows()
        order = [DIRTY[0]] + [c for c in bench_cases() if c not in ("소체", DIRTY[0])]
        for c in [c for c in order if c not in done][:int(a)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-26s θ%.2f 배관차 %.6f · " % (c[:26], r["각짐"], pipe(r))
                  + " · ".join("%s %.3f(균일 %.3f)" % (k, r[k]["iou"], r["균일@" + k]["iou"]) for k in VARS)
                  + " · %.0f초" % r["초"], flush=True)
            if pipe(r) >= 1e-4:
                print("  배관 어긋남 — 멈춘다")
                return
        print("  %d/28 장" % len(rows()))
    if a == "판정" or len(rows()) >= 28:
        v = judge()
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "단면모양_판정_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)


if __name__ == "__main__":
    main()
