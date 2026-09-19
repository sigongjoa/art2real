# -*- coding: utf-8 -*-
"""**하드서피스에서 깊이 깎기는 정보를 넣는가** — 가설이 나오지 않은 9장에서 (2026-09-19).

    python 하드서피스.py 검사     자가검사 + 배관 3 (벤치 한 장 되찾기)
    python 하드서피스.py [n]      아직 안 한 장 n 개 -> out/기록/하드서피스_진행.jsonl
    python 하드서피스.py 판정     -> out/기록/하드서피스_판정_<때>.json
    python 하드서피스.py 그림     정보몫 최악 · 최선 장 × 네 열 -> out/하드서피스_명암.png

판정은 `claudedocs/plan_하드서피스_20260919.md` 그대로다 — 돌리기 전에 적었다. **문턱을 안 바꾼다.**
배관은 전부 기존 것을 부른다: `대조.build`(= `hull.carve_default`) · `hull.even_control` ·
`오라클.build` · `조각묶기.scorer`(속 채운 정답 · 격자 128 · 192) · `단면모양.angularity`(θ).
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260919"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
from 겉면채점 import bench_cases
from 조각묶기 import scorer
from 단면모양 import angularity

PROG = os.path.join(HERE, "out", "기록", "하드서피스_진행.jsonl")
TAG = ("하드서피스 · 얼린 9장(벤치 밖) · 이진/기본/균일@기본/오라클 · 타원 lam1.00 · "
       "속채운 정답 · 격자128·192 (2026-09-19)")

# 계획 「얼린 집합」 그대로. 같은 물건의 변형은 안 넣는다.
NINE = ("mech_Mech_D5wW2jDO42", "mech_Mech_o3Ps8z8ByP", "mech_Mech_tLs9mFVCSU",
        "robot_Animated_Robot_QCm7qe9uNJ", "robot_Robot_Enemy_1gNo5ezvmr",
        "robot_Robot_Enemy_Flying_lF3jeRJwiH", "statue_Fox_Statue_abxyXID5EA",
        "statue_Stag_Statue_cKloIsNcT8", "statue_Town_Center_76GTkSh4KM")

# 계획 「Q」 · 「분류」 절의 문턱. **숫자를 본 뒤 바꾸지 않는다.**
H1_MED, H1_NEG, H2_GAP, H3_MED, THETA = 0.005, 5, 0.02, 0.02, 0.05
HUMAN18 = 0.0335                                  # 계획에 얼린 사람형 18장 정보몫 중앙
VOL_TOL = 0.01                                    # 배관 2 — 균일@기본 부피가 기본과 1% 이내
PIPE_CASE = "base_female"                         # 배관 3 — 벤치에서 제일 싼 장


def build_all(c, truth):
    """판본 넷의 메시. **새로 안 짠다** — 제품 경로(`대조.build`)와 벤치 경로(`오라클.build`)를 그대로 부른다."""
    plain, deep, axes, _ = C.build(c)                        # = hull.carve_default
    mb, md = O.C.to_mesh(plain, axes), O.C.to_mesh(deep, axes)
    em, t = H.even_control(plain, axes, md.volume)           # 정보 0 대조군 — 기본과 같은 부피
    _, odeep, oaxes, _ = O.build(c, truth, H.DEPTH_LAM, "오라클")
    return {"이진": mb, "기본": md, "균일@기본": em, "오라클": O.C.to_mesh(odeep, oaxes)}, t


def one(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    score = scorer(truth)
    ms, t = build_all(c, truth)
    row = {"case": c, "판": TAG, "각짐": round(angularity(c), 3), "수준 t": round(float(t), 3)}
    for k, m in ms.items():
        s = score(m)
        row[k] = {"iou": s[""], "iou192": s["·192"], "부피": round(float(abs(m.volume)), 6)}
    row["부피오차"] = round(abs(ms["균일@기본"].volume) / max(abs(ms["기본"].volume), 1e-12) - 1, 5)
    row["초"] = round(time.time() - t0, 1)
    return row


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


# ------------------------------------------------------------------ 배관 3

def pipe3():
    """벤치 28장 중 한 장을 **같은 코드로** 다시 재서 기존 기록을 되찾나.

    계획은 `논문/기본파이프라인/장별.csv` 를 가리키는데 그 파일은 소수 셋째 자리까지라
    1e-4 를 물을 수 없다. 그래서 **그 csv 를 만든 원본**(`겉면채점_벤치_진행.jsonl`, 다섯째 자리)과
    대고, csv 값도 같이 적는다 (문턱은 계획대로 1e-4)."""
    b = {x["case"]: x for x in map(json.loads,
         open(os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl"), encoding="utf-8"))}[PIPE_CASE]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", PIPE_CASE, "truth.glb"), force="mesh")
    score = scorer(truth)
    ms, _ = build_all(PIPE_CASE, truth)
    got = {"기본": score(ms["기본"])[""], "균일@기본": score(ms["균일@기본"])[""],
           "이진": score(ms["이진"])[""], "오라클": score(ms["오라클"])[""]}
    ref = {"기본": b["타원1.00"][1], "균일@기본": b["균일@타원1.00"][1],
           "이진": b["이진"][1], "오라클": b["오라클1.00"][1]}
    csv = {}
    for line in open(os.path.join(HERE, "논문", "기본파이프라인", "장별.csv"), encoding="utf-8"):
        f = line.strip().split(",")
        if f[0] == PIPE_CASE:
            csv = {"기본": float(f[4]), "균일@기본": float(f[5]), "이진": float(f[6]), "오라클": float(f[7])}
    d = {k: round(abs(got[k] - ref[k]), 6) for k in got}
    return {"장": PIPE_CASE, "잰 값": got, "기록(jsonl 5자리)": ref, "차": d,
            "최대차": max(d.values()), "통과": bool(max(d.values()) < 1e-4),
            "장별.csv(3자리)": csv,
            "csv 최대차": round(max(abs(got[k] - csv[k]) for k in csv), 4) if csv else None}


# ------------------------------------------------------------------ 판정

def stats(v):
    v = np.asarray(v, float)
    return {"중앙": round(float(np.median(v)), 4), "평균": round(float(v.mean()), 4),
            "최악": round(float(v.min()), 4), "최선": round(float(v.max()), 4),
            "≤0 장": int((v <= 0).sum()), "장": len(v)}


def judge():
    rs = rows()
    done = [c for c in NINE if c in rs]
    miss = [c for c in NINE if c not in rs]
    out = {"판": TAG, "완주": len(done), "완주 못 한 장": miss}
    if not done:
        out["판정"] = "장이 없다"
        return out
    # 배관 2 — 균일@기본이 기본과 같은 부피인가. 안 맞는 장은 판정에서 뺀다
    ve = {c: rs[c]["부피오차"] for c in done}
    bad = [c for c in done if abs(ve[c]) > VOL_TOL]
    out["배관2 부피오차"] = {"장별": ve, "최대|오차|": round(max(abs(x) for x in ve.values()), 5),
                       "1% 넘게 어긋난 장": bad, "통과": not bad}
    cs = [c for c in done if c not in bad]
    out["판정에 쓴 장"] = cs
    if len(cs) < 5:
        out["판정"] = "배관 2 가 %d/%d 장에서 깨졌다 — 정보몫을 쓸 수 없다 (계획 분기 4)" % (len(bad), len(done))
        return out
    # 정보몫 = IoU(기본) − IoU(균일@기본). 부피가 같으므로 남는 차는 모양 정보다
    I = {}
    for key, tag in (("iou", "128"), ("iou192", "192")):
        v = [rs[c]["기본"][key] - rs[c]["균일@기본"][key] for c in cs]
        I[tag] = dict(stats(v), 장별={c: round(float(x), 4) for c, x in zip(cs, v)})
    out["정보몫"] = I
    out["서술 (판정 아님)"] = {
        t: {n: round(float(np.median([rs[c][n][k] for c in cs])), 4)
            for n in ("이진", "기본", "균일@기본", "오라클")}
        for k, t in (("iou", "128"), ("iou192", "192"))}
    out["서술 (판정 아님)"]["천장 (오라클 − 기본) 128"] = stats([rs[c]["오라클"]["iou"] - rs[c]["기본"]["iou"] for c in cs])
    # H1 · H2 · H3 — 문턱은 계획에서 얼렸다
    h1 = all(I[t]["중앙"] <= H1_MED and I[t]["≤0 장"] >= H1_NEG for t in ("128", "192"))
    gap = round(I["128"]["중앙"] - HUMAN18, 4)
    h2 = abs(gap) >= H2_GAP
    h3 = I["128"]["중앙"] >= H3_MED
    out["H1 하드서피스에서 깎기가 정보를 못 넣나"] = {
        "문턱": "중앙 ≤ %+.3f 이고 ≤0 장 ≥ %d/9 · 격자 둘 다" % (H1_MED, H1_NEG),
        "128": [I["128"]["중앙"], I["128"]["≤0 장"]], "192": [I["192"]["중앙"], I["192"]["≤0 장"]],
        "통과": bool(h1)}
    out["H2 사람형과 다른가"] = {"문턱": "|9장 중앙 − 사람형18 중앙(%+.4f)| ≥ %.2f" % (HUMAN18, H2_GAP),
                          "9장 중앙": I["128"]["중앙"], "차": gap, "통과": bool(h2)}
    out["H3 (반증) 내 주장이 틀렸나"] = {"문턱": "중앙 ≥ %+.2f 이면 주장 기각" % H3_MED,
                              "9장 중앙": I["128"]["중앙"], "발동": bool(h3)}
    # Q-분류 — θ 가 이름 키워드 없이 하드서피스를 찍나
    th = {c: rs[c]["각짐"] for c in done}
    q = sum(1 for c in NINE if c in th and th[c] > THETA)
    out["Q-분류 (각짐 θ)"] = {"문턱": "θ > %.2f 인 장 ≥ 7/9" % THETA, "장별": th,
                         "넘은 장": q, "통과": bool(q >= 7)}
    if h3:
        nxt = "**주장 기각** — 가설이 나오지 않은 집합에서 하드서피스도 깎기가 정보를 넣는다. 28장에서 본 것은 그 10장의 성질이거나 사후 분류의 산물이다"
    elif h1:
        nxt = "재현됐다 — 다음 바퀴에 「θ 로 갈라 하드서피스는 깎기를 끄기」를 사전 등록해 28+9 장에서 판정 (채택 규칙에 최악 사례 하한을 넣는다)"
    else:
        nxt = "못 가름 (+%.3f ~ +%.2f 구간) — n=%d 로는 안 갈린다. 새 물건으로 장을 늘리든가 다른 자를 찾는다" % (H1_MED, H3_MED, len(cs))
    if not out["Q-분류 (각짐 θ)"]["통과"]:
        nxt += " · θ 는 이 9장에서 이름 키워드를 대신하지 못했다 (문턱 0.05 는 28장을 보고 정한 사후값이다)"
    out["다음"] = nxt
    return out


# ------------------------------------------------------------------ 그림

def figure():
    """정보몫이 제일 음수인 장 · 제일 양수인 장 × (정답 · 이진 hull · 기본 · 균일@기본) 명암 접촉지.
    `실험_20260919/단면모양.py` 의 명암 렌더를 그대로 부른다."""
    import 깊이색 as DC
    import 앨리어싱 as AL
    from 폴리싱 import shaded
    rs = rows()
    cs = [c for c in NINE if c in rs and abs(rs[c]["부피오차"]) <= VOL_TOL]
    I = sorted(cs, key=lambda c: rs[c]["기본"]["iou"] - rs[c]["균일@기본"]["iou"])
    pick = [(I[0], "정보몫 최악"), (I[-1], "정보몫 최선")]
    cols = ["정답 (GT)", "이진 hull", "기본 (타원 lam1.00)", "균일@기본 (정보 0)"]
    out = []
    for c, why in pick:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        ms, _ = build_all(c, truth)
        meshes = [truth, ms["이진"], ms["기본"], ms["균일@기본"]]
        fr = AL.frame_of(truth, 45)
        tiles = [shaded(m, 45, fr, 400) for m in meshes]
        r = rs[c]
        lab = "%s\n%s\n%s\n정보몫 %+.4f\nθ %.2f\n%.3f · %.3f\n· %.3f" % (
            c.split("_")[0], c.split("_", 1)[1][:13], why,
            r["기본"]["iou"] - r["균일@기본"]["iou"], r["각짐"],
            r["이진"]["iou"], r["기본"]["iou"], r["균일@기본"]["iou"])
        out.append((lab, tiles))
        print("  %s 명암" % c[:34], flush=True)
    DC.grid(out, cols, "하드서피스 9장 — 정보몫 최악 · 최선 (면 법선 명암 · z 버퍼 · az 45)",
            "같은 빛 · 같은 틀. 숫자는 속 채운 정답 IoU (격자 128) — 이진 hull · 기본 · 균일@기본. "
            "균일@기본은 기본과 같은 부피까지 매끈하게 민 hull 이라 모양 정보가 0 이다",
            os.path.join(HERE, "out", "하드서피스_명암.png"))


# ------------------------------------------------------------------ 자가검사

def selfcheck():
    # 1 얼린 9장이 벤치 28장과 안 겹친다 (가설이 나온 집합에서 재면 확증이 아니다)
    b = set(bench_cases())
    assert not (set(NINE) & b), "얼린 집합이 벤치와 겹친다: %s" % (set(NINE) & b)
    # 2 even_control 이 목표 부피를 1% 안에 맞추나 — 배관 2 의 자가 문
    g = np.meshgrid(*[np.arange(64) - 31.5] * 3, indexing="ij")
    plain = (g[0] ** 2 / 26. ** 2 + g[1] ** 2 / 18. ** 2 + g[2] ** 2 / 29. ** 2) <= 1.0
    ax = tuple(np.arange(64) / 64. for _ in range(3))
    V, F = H.mesh_from(plain, ax)
    tgt = abs(trimesh.Trimesh(V, F, process=False).volume) * 0.7
    m, t = H.even_control(plain, ax, tgt)
    assert abs(abs(m.volume) / tgt - 1) < VOL_TOL, "대조군 부피가 %.2f%% 어긋난다" % (100 * (m.volume / tgt - 1))
    assert t > 0, "부피를 줄이라 했는데 수준이 안 움직였다"
    # 3 판정 문턱이 양쪽을 다 낼 수 있나 (09-19 「문턱은 질 수 있어야 한다」)
    assert stats([-0.03, -0.02, -0.01, 0.0, 0.01])["중앙"] <= H1_MED
    assert stats([0.03, 0.04, 0.05, 0.02, 0.06])["중앙"] >= H3_MED
    assert not (stats([0.01] * 5)["중앙"] <= H1_MED or stats([0.01] * 5)["중앙"] >= H3_MED), "못 가름 구간이 비었다"
    print("  자가검사 통과 — 얼린 집합이 벤치 밖 · even_control 부피 1% · H1/H3 둘 다 날 수 있고 못 가름 구간이 있다")


def main():
    H.register_sheets()
    selfcheck()
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        p = pipe3()
        print(json.dumps(p, ensure_ascii=False, indent=1))
        assert p["통과"], "배관 3 어긋남 — 숫자를 버린다"
        return
    if a == "그림":
        return figure()
    if a != "판정":
        done = rows()
        for c in [c for c in NINE if c not in done][:int(a)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-36s θ%.2f · 이진 %.3f · 기본 %.3f · 균일 %.3f · 오라클 %.3f · 정보몫 %+.4f · 부피오차 %+.3f%% · %.0f초"
                  % (c[:36], r["각짐"], r["이진"]["iou"], r["기본"]["iou"], r["균일@기본"]["iou"],
                     r["오라클"]["iou"], r["기본"]["iou"] - r["균일@기본"]["iou"], 100 * r["부피오차"], r["초"]), flush=True)
        print("  %d/9 장" % len(rows()))
    if a == "판정" or len(rows()) >= len(NINE):
        v = judge()
        v["배관3"] = pipe3()
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "하드서피스_판정_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)


if __name__ == "__main__":
    main()
