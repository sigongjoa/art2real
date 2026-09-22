# -*- coding: utf-8 -*-
"""**원화 -> 피규어 도면** — 3D 는 이 수치표에서 계산된다 (2026-09-22).

    python 도면.py [케이스=오메가몬]   -> out/도면/<케이스>.json · out/도면_<케이스>.png
    python 도면.py 검사               검산 규칙 자체검사 (합성 도면 · assert)

사용자(09-22): 「그림은 수치가 없다」 · 「도면을 바탕으로 계산, llm 한테는 아이디어만」 ·
「패널라인 먹선이랑 shape 까지는 오케이 — 여기서 분석을 시작하자」

**칸** = {값, 출처, 상태, 근거}. 출처 = 그림 · 옆판 · 사양 · 사전 · 사람 · llm. 상태 = 확정 · 추정 · 보정.
숫자 칸의 출처에 **llm 은 없다** (09-22 깊이 실험: LLM 0.362 vs 비율 사전 0.330 · 5/10 — README).

    부위      `면자르기.부위` (거리장 분수령) — 관절표 · 도색표와 같은 번호
    폭 · 높이  부위 복셀의 x · z 폭 × (키 mm / 전체 높이)     출처 그림 · 확정  (정면 실루엣이 정한다)
    깊이      부위 복셀의 y 폭                               출처 옆판 · **추정** (오메가몬 앞뒤 거울 IoU 0.637 — 판이 안 맞는다)
              제안 = 비율 사전 (깊이 = 폭 × 1.00)
    관절점    `관절_<케이스>.json` 의 분수령 경계면           출처 그림 · 추정 (벤치 R 0.266 — 관절 찾기가 약하다)
    핀지름    사양표에서 관절에 들어가는 제일 큰 것             출처 사양
    색        `색굽기` 도색표 대표색                          출처 그림 · 확정

검산 규칙 (앱의 검산기와 같은 함수):

    R1 그림 대조   폭 · 높이를 라벨에서 다시 재서 0.5 mm 넘게 어긋나면 **보정**
    R2 좌우 대칭   거울 짝(중심 x 반대 · z 가까움)의 치수가 10% 또는 2 mm 안 · **짝 없는 L/R 부품**을 따로 센다
                   (짝을 못 찾으면 대칭 검사가 공짜로 통과한다 — 09-22 오메가몬 다리가 한쪽 1 조각 · 한쪽 2 조각)
    R3 이어짐     관절점이 두 부품 상자 안 (2 mm 여유)
    R4 핀        핀지름 + 2 × 최소벽 <= 관절 지름
    R7 출처       숫자 칸에 출처 llm 이 없다
"""
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import win as W

OUT = os.path.join(H.OUT, "도면")
키mm = 150.0
사양 = {"최소벽": 1.2, "공차": 0.2, "핀지름": [2.0, 3.0, 4.0, 5.0, 6.0]}
숫자칸 = ("폭", "높이", "깊이", "관절점", "핀지름", "지름")


def 칸(값, 출처, 상태, 근거=""):
    return {"값": 값, "출처": 출처, "상태": 상태, "근거": 근거}


def 라벨(case):
    """면자르기.main 과 같은 배관 -> (lab, 세계 좌표 축 ux · uy · z)."""
    import 면자르기 as MJ
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    g, (ux, uy, z) = H.field_default(masks, back_sign=bs, n=MJ.N)
    _, lab, _ = MJ.부위(g > 0)
    return lab, np.asarray(ux), np.asarray(uy), np.asarray(z)


def 잰치수(lab, ux, uy, z):
    """부위마다 x · y · z 최소 · 최대 (mm). 도면을 뽑을 때와 R1 에서 같이 쓴다."""
    ii = np.argwhere(lab > 0)
    mm = 키mm / (z[ii[:, 2]].max() - z[ii[:, 2]].min() + (z[1] - z[0]))
    L = lab[tuple(ii.T)]
    P = np.stack([ux[ii[:, 0]], uy[ii[:, 1]], z[ii[:, 2]]], 1) * mm
    z0 = P[:, 2].min()
    P[:, 2] -= z0                                              # 바닥 = 0
    셀 = (ux[1] - ux[0]) * mm
    r = {}
    for l in np.unique(L):
        q = P[L == l]
        r[int(l)] = {"lo": q.min(0) - 셀 / 2, "hi": q.max(0) + 셀 / 2, "c": q.mean(0), "n": len(q)}
    return r, mm, z0


def 뽑기(case):
    lab, ux, uy, z = 라벨(case)
    잰, mm, z0 = 잰치수(lab, ux, uy, z)
    관 = json.load(open(os.path.join(H.OUT, "관절_%s.json" % case), encoding="utf-8"))["joints"]
    try:
        도색 = {d["부위"]: d["대표색"] for d in
              json.load(open(os.path.join(H.OUT, "색굽기", case, "도색표.json"), encoding="utf-8"))["도색표"]}
    except FileNotFoundError:
        도색 = {}
    부품 = []
    for l, s in sorted(잰.items(), key=lambda kv: -kv[1]["n"]):
        e = s["hi"] - s["lo"]
        쪽 = "L" if s["c"][0] > 3 else "R" if s["c"][0] < -3 else "C"     # 캐릭터 기준 왼쪽 = 화면 오른쪽(+x)
        부품.append({
            "id": "P%02d" % l, "부위": l, "쪽": 쪽,
            "이름": 칸(None, "llm", "추정", "비움 — 이름은 LLM 제안 칸"),
            "폭": 칸(round(float(e[0]), 1), "그림", "확정", "정면 실루엣 x 폭"),
            "높이": 칸(round(float(e[2]), 1), "그림", "확정", "정면 실루엣 z 폭"),
            "깊이": 칸(round(float(e[1]), 1), "옆판", "추정", "옆 판 y 폭 · 판 불일치(거울 IoU 0.637)"),
            "깊이제안": {"사전": round(float(e[0]) * 1.00, 1)},
            "중심": [round(float(v), 1) for v in s["c"]],
            "상자": [[round(float(v), 1) for v in s["lo"]], [round(float(v), 1) for v in s["hi"]]],
            "색": 칸(도색.get(l), "그림", "확정" if l in 도색 else "추정", "색굽기 대표색"),
        })
    관절 = []
    for j in 관:
        p = np.array(j["cut"]["point"]) * mm - [0, 0, z0]
        d = 2 * j["r"] * mm
        맞는 = [x for x in 사양["핀지름"] if x + 2 * 사양["최소벽"] <= d]
        관절.append({"id": j["id"], "부품": ["P%02d" % a for a in j["parts"]],
                   "종류": 칸(None, "llm", "추정", "볼 · 힌지 · 핀 · 고정 — LLM 제안 칸"),
                   "관절점": 칸([round(float(v), 1) for v in p], "그림", "추정", "분수령 경계면 (벤치 R 0.266)"),
                   "지름": 칸(round(float(d), 1), "그림", "추정", "경계면 원 반지름 × 2"),
                   "핀지름": 칸(max(맞는) if 맞는 else None, "사양", "확정" if 맞는 else "추정",
                              "사양표 중 들어가는 제일 큰 것" if 맞는 else "들어가는 핀이 없다"),
                   "기운각": j["tilt_deg"]})
    return {"메타": {"케이스": case, "키_mm": 키mm, "단위": "mm", "좌표": "x 오른쪽(화면) · y 뒤 · z 위 · 바닥 0"},
            "사양": 사양, "부품": 부품, "관절": 관절}, 잰


# ---------------------------------------------------------------- 검산기
def R1(도, 잰, 허용=0.5):
    """도면의 폭 · 높이를 라벨에서 다시 잰 값과 댄다. 어긋나면 그림 값으로 **보정** 하고 적는다."""
    out = []
    for p in 도["부품"]:
        s = 잰[p["부위"]]
        e = s["hi"] - s["lo"]
        for k, v in (("폭", e[0]), ("높이", e[2])):
            if abs(p[k]["값"] - v) > 허용:
                out.append("%s %s %.1f -> %.1f" % (p["id"], k, p[k]["값"], v))
                p[k] = 칸(round(float(v), 1), "그림", "보정", "R1: %s 였음 (%s)" % (p[k]["값"], p[k]["출처"]))
    return out


def R2(도, 비=0.10, 절대=2.0):
    out, 짝 = [], []
    ps = [p for p in 도["부품"] if p["쪽"] == "L"]
    for a in ps:
        후보 = [b for b in 도["부품"] if b["쪽"] == "R"]
        if not 후보:
            continue
        b = min(후보, key=lambda b: abs(a["중심"][0] + b["중심"][0]) + abs(a["중심"][2] - b["중심"][2]))
        if abs(a["중심"][0] + b["중심"][0]) > 8 or abs(a["중심"][2] - b["중심"][2]) > 8:
            continue
        짝.append((a["id"], b["id"]))
        for k in ("폭", "높이", "깊이"):
            x, y = a[k]["값"], b[k]["값"]
            if abs(x - y) > max(절대, 비 * max(x, y)):
                out.append("%s/%s %s %.1f vs %.1f" % (a["id"], b["id"], k, x, y))
    return out, 짝


def R3(도, 잰, 여유=2.0):
    out = []
    ids = {p["id"]: p["부위"] for p in 도["부품"]}
    for j in 도["관절"]:
        q = np.array(j["관절점"]["값"])
        for pid in j["부품"]:
            s = 잰[ids[pid]]
            if np.any(q < s["lo"] - 여유) or np.any(q > s["hi"] + 여유):
                out.append("%s 가 %s 밖" % (j["id"], pid))
    return out


def R4(도):
    m = 도["사양"]["최소벽"]
    return ["%s 지름 %.1f 에 핀 %s 안 들어감" % (j["id"], j["지름"]["값"], j["핀지름"]["값"])
            for j in 도["관절"] if j["핀지름"]["값"] is None or j["핀지름"]["값"] + 2 * m > j["지름"]["값"]]


def R7(도):
    out = []
    for p in 도["부품"] + 도["관절"]:
        for k in 숫자칸:
            if k in p and isinstance(p[k], dict) and p[k].get("출처") == "llm":
                out.append("%s %s" % (p["id"], k))
    return out


def 검산(도, 잰):
    r1 = R1(도, 잰)                                            # 보정이 먼저 — 대칭은 고친 값으로 본다
    r2, 짝 = R2(도)
    짝된 = {i for ab in 짝 for i in ab}
    외톨 = [p["id"] for p in 도["부품"] if p["쪽"] != "C" and p["id"] not in 짝된]
    return {"R1 보정": r1, "R2 대칭": r2, "R2 짝": 짝, "R2 짝없음": 외톨, "R3 이어짐": R3(도, 잰), "R4 핀": R4(도), "R7 출처": R7(도)}


def 검사():
    """합성 도면 — 규칙마다 걸려야 할 것이 걸리고, 멀쩡한 것은 안 걸린다."""
    잰 = {1: {"lo": np.array([-30., -10, 0]), "hi": np.array([30., 10, 60]), "c": np.array([0., 0, 30]), "n": 9},
         2: {"lo": np.array([30., -5, 40]), "hi": np.array([50., 5, 55]), "c": np.array([40., 0, 47]), "n": 3},
         3: {"lo": np.array([-50., -5, 40]), "hi": np.array([-30., 5, 55]), "c": np.array([-40., 0, 47]), "n": 3}}
    def p(l, 쪽, 폭, 높, 깊):
        s = 잰[l]
        return {"id": "P%02d" % l, "부위": l, "쪽": 쪽, "중심": list(s["c"]),
                "폭": 칸(폭, "그림", "확정"), "높이": 칸(높, "그림", "확정"), "깊이": 칸(깊, "옆판", "추정")}
    도 = {"사양": 사양, "부품": [p(1, "C", 60, 60, 20), p(2, "L", 20, 15, 10), p(3, "R", 26, 15, 10)],
         "관절": [{"id": "j0", "부품": ["P01", "P02"], "관절점": 칸([30, 0, 47], "그림", "추정"),
                  "지름": 칸(7.0, "그림", "추정"), "핀지름": 칸(5.0, "사양", "확정")},
                 {"id": "j1", "부품": ["P01", "P03"], "관절점": 칸([-80, 0, 47], "llm", "추정"),
                  "지름": 칸(12.0, "그림", "추정"), "핀지름": 칸(4.0, "사양", "확정")}]}
    r = 검산(도, 잰)
    assert r["R1 보정"] == ["P03 폭 26.0 -> 20.0"] and 도["부품"][2]["폭"]["상태"] == "보정", r["R1 보정"]
    assert r["R2 대칭"] == [] and r["R2 짝"] == [("P02", "P03")] and r["R2 짝없음"] == [], r        # R1 이 먼저 고쳐서 대칭이 맞는다
    assert r["R3 이어짐"] == ["j1 가 P01 밖", "j1 가 P03 밖"], r["R3 이어짐"]
    assert r["R4 핀"] == ["j0 지름 7.0 에 핀 5.0 안 들어감"], r["R4 핀"]
    assert r["R7 출처"] == ["j1 관절점"], r["R7 출처"]
    print("검사 통과 — R1 R2 R3 R4 R7")


def 그림(도, r, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(16, 9), dpi=110)
    ax = fig.add_axes([0.02, 0.05, 0.36, 0.88])
    for p in 도["부품"]:
        (x0, _, z0), (x1, _, z1) = p["상자"]
        c = p["색"]["값"] or "#cccccc"
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=c, ec="#333", alpha=.55, lw=1))
        ax.text((x0 + x1) / 2, (z0 + z1) / 2, p["id"], ha="center", va="center", fontsize=9, weight="bold")
    for j in 도["관절"]:
        q = j["관절점"]["값"]
        ax.plot(q[0], q[2], "o", ms=7, mfc="white", mec="#007aff", mew=2)
        ax.text(q[0] + 2, q[2] + 2, j["id"], color="#007aff", fontsize=8)
    ax.set_aspect("equal"); ax.autoscale(); ax.set_title("정면 — 부품 상자(색 = 도색 대표색) · 관절점", fontsize=11)
    ax.set_xlabel("x mm"); ax.set_ylabel("z mm")
    t = fig.add_axes([0.40, 0.05, 0.58, 0.88]); t.axis("off")
    색 = {"확정": "#f2f2f7", "추정": "#fff3b0", "보정": "#d6f0fb"}
    행 = [[p["id"], p["쪽"], p["폭"]["값"], p["높이"]["값"], p["깊이"]["값"], p["깊이제안"]["사전"], p["색"]["값"] or "-"]
         for p in 도["부품"]]
    tb = t.table(cellText=행, colLabels=["부품", "쪽", "폭", "높이", "깊이(옆판)", "깊이(사전)", "색"],
                 loc="upper left", cellLoc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(9); tb.scale(1, 1.25)
    for i, p in enumerate(도["부품"], 1):
        for j, k in ((2, "폭"), (3, "높이"), (4, "깊이")):
            tb[i, j].set_facecolor(색[p[k]["상태"]])
    줄 = ["검산", "R1 보정 %d · R2 대칭 어긋남 %d (짝 %d · 짝없음 %d) · R3 이어짐 %d · R4 핀 %d · R7 출처 %d"
          % (len(r["R1 보정"]), len(r["R2 대칭"]), len(r["R2 짝"]), len(r["R2 짝없음"]), len(r["R3 이어짐"]), len(r["R4 핀"]), len(r["R7 출처"]))]
    줄 += ["  짝없음: " + " ".join(r["R2 짝없음"])] if r["R2 짝없음"] else []
    줄 += ["  " + s for s in (r["R2 대칭"] + r["R3 이어짐"] + r["R4 핀"])[:8]]
    t.text(0, 0.02, "\n".join(줄), fontsize=9, va="bottom", family="Malgun Gothic")
    t.set_title("도면 — 노랑 = 추정 · 하늘 = 보정 · 회색 = 확정", fontsize=11, loc="left")
    fig.savefig(path)


def main(case="오메가몬"):
    도, 잰 = 뽑기(case)
    r = 검산(도, 잰)
    도["검산"] = {k: v for k, v in r.items()}
    os.makedirs(OUT, exist_ok=True)
    json.dump(도, open(os.path.join(OUT, case + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    그림(도, r, os.path.join(H.OUT, "도면_%s.png" % case))
    추 = sum(p[k]["상태"] == "추정" for p in 도["부품"] for k in ("폭", "높이", "깊이"))
    print("부품 %d · 관절 %d · 추정 칸 %d" % (len(도["부품"]), len(도["관절"]), 추))
    for k, v in r.items():
        print("  %-8s %s" % (k, v if v else "—"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "검사":
        검사()
    else:
        main(a[0] if a else "오메가몬")
