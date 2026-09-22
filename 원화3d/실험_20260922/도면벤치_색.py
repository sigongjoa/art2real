# -*- coding: utf-8 -*-
"""**도면 벤치 · 색** — 부위(관절)만으로 가르던 도면에 색 경계를 얹는다 (2026-09-22).

    python 도면벤치_색.py            얼린 10 케이스 -> out/기록/도면벤치_색_<때>.json · out/도면벤치_색.png
    python 도면벤치_색.py <케이스>

사용자(09-22): 「일단은 해보자고」 — art2real 남은 일 1번. 앞선 도면 벤치(`도면벤치.py`, 커밋 dc31b2d)에서
**병목은 나누기**였다: R 0.241 · 정답 부품 182 중 11 개만 IoU ≥ 0.5 로 맞았다. 조사(`research_피규어소프트웨어_20260922`)
에서 업계의 첫째 분할 기준이 **색**이었다.

세 판을 같은 자로 잰다 (케이스 · 정답 · 자 전부 `도면벤치.py` 그대로):

    부위     면자르기 분수령만 (= 도면벤치 · 대조군)
    A        부위 × 색 — 같은 부위 안 같은 색은 떨어져 있어도 한 부품 (`부품분할.합치기`, 09-21 그대로)
    A′       A 를 연결 덩어리로 다시 가른다 — 같은 색이라도 떨어져 있으면 따로 (정답이 연결 덩어리라서)

**미리 아는 것**: A 의 R 은 09-21 부품분할 벤치에서 이미 쟀다(이 10 케이스 중앙 ≈ 0.255 · 부위만 0.241 과
같은 배관). 그래서 R 은 새 시험이 아니라 확인이다. **새로 재는 것은 맞은 짝 수와 그 치수다.**

문턱을 **돌리기 전에** 적는다 (집계 = 케이스 중앙값 · 맞은 짝은 합계 · 치수 e 는 모든 짝 중앙):

    Q1  맞은 짝     A 또는 A′ 의 맞은 짝 합계 > 부위 판의 1.5 배 (11 -> 17 이상)
    Q2  R          같은 판의 R 중앙이 부위 판보다 높다 · 10 중 6 케이스 이상에서 이긴다
    Q3  치수        그 판의 맞은 짝 폭 · 높이 e 중앙 <= 0.10 (도면벤치 0.174 — 10% 안이면 도면 칸으로 쓸 만하다)

    Q1 · Q2 둘 다 이긴 판이 없으면 -> 색은 도면 분할 기본값으로 안 넣는다 (메카 한정 옵션으로만)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import 도면 as DM
import 도면벤치 as DB
import 부품분할 as BB
import 면자르기 as MJ
import 깊이추정 as GC

OUT = H.OUT
판들 = ("부위", "A", "A′")


def 연결로(lab, O):
    """라벨마다 연결 덩어리로 다시 번호를 매긴다 · 작은 조각(< 최소몫)은 이웃에 붙인다."""
    out = np.zeros_like(lab)
    n = 0
    for l in np.unique(lab):
        if l == 0:
            continue
        cc, k = ndimage.label(lab == l, np.ones((3, 3, 3), bool))
        out[cc > 0] = cc[cc > 0] + n
        n += k
    크 = np.bincount(out.ravel())
    작 = np.where(크 < BB.최소몫 * O.sum())[0]
    out[np.isin(out, 작[작 > 0])] = 0
    out = BB.채우기(out, O)
    _, out = np.unique(out, return_inverse=True)
    return out.reshape(O.shape).astype(np.int32)


def 라벨들(case):
    raw, masks, bs, p = BB.판(case)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    O = g > 0
    _, 부위, _ = MJ.부위(O)
    부위 = BB.채우기(부위, O)
    색, n색 = BB.색라벨(case, raw, masks, p, bs, O)
    A = BB.합치기(부위, 색, O)
    return {"부위": 부위, "A": A, "A′": 연결로(A, O)}, [np.asarray(a) for a in ax], n색


def 재기(lab, ux, uy, z, w, t, 정):
    잰, _, _ = DM.잰치수(lab, ux, uy, z)
    p = BB.표본(lab, (ux, uy, z), w)
    R = BB.회수율(t, p)
    M = np.zeros((t.max() + 1, p.max() + 1), np.int64)
    np.add.at(M, (t, p), 1)
    iou = M / np.maximum(M.sum(1, keepdims=True) + M.sum(0, keepdims=True) - M, 1)
    짝 = []
    for ti in range(iou.shape[0]):
        pi = int(iou[ti].argmax())
        if iou[ti, pi] < 0.5 or pi not in 잰:
            continue
        a, b = 잰[pi], 정[ti]
        ea, eb = a["hi"] - a["lo"], b["hi"] - b["lo"]
        짝.append({"e폭": DB.e(ea[0], eb[0]), "e높이": DB.e(ea[2], eb[2]), "e깊이옆판": DB.e(ea[1], eb[1])})
    return {"R": R, "부품": len(잰), "짝": 짝}


def main(only=None):
    cases = [only] if only else GC.케이스들
    기록, 앞들 = {}, {}
    for c in cases:
        t0 = time.time()
        labs, (ux, uy, z), n색 = 라벨들(c)
        w, t, 정 = DB.정답상자(c)
        r = {k: 재기(labs[k], ux, uy, z, w, t, 정) for k in 판들}
        r["정답 부품"] = len(정); r["색 수"] = n색
        기록[c] = r
        앞들[c] = (DB.정답앞(c),) + tuple(DB.앞그림(c, labs[k]) for k in 판들)
        print("  %-38s 정답 %2d 색 %2d | " % (c, len(정), n색) + " | ".join(
            "%s 부품 %2d R %.3f 짝 %2d" % (k, r[k]["부품"], r[k]["R"], len(r[k]["짝"])) for k in 판들) + "  %.0f초" % (time.time() - t0), flush=True)
    요약 = {"케이스": len(기록), "정답 부품 합": sum(r["정답 부품"] for r in 기록.values())}
    for k in 판들:
        모든 = [x for r in 기록.values() for x in r[k]["짝"]]
        요약[k] = {"R 중앙": float(np.median([r[k]["R"] for r in 기록.values()])),
                  "짝 합": len(모든),
                  "e 폭높이": float(np.median([x["e폭"] for x in 모든] + [x["e높이"] for x in 모든])) if 모든 else None,
                  "e 깊이옆판": float(np.median([x["e깊이옆판"] for x in 모든])) if 모든 else None,
                  "R 승(대 부위)": int(sum(r[k]["R"] > r["부위"]["R"] for r in 기록.values()))}
    for k in ("A", "A′"):
        s = 요약[k]
        s["Q1"] = s["짝 합"] >= 1.5 * max(요약["부위"]["짝 합"], 1)
        s["Q2"] = s["R 중앙"] > 요약["부위"]["R 중앙"] and s["R 승(대 부위)"] >= 0.6 * len(기록)
        s["Q3"] = s["e 폭높이"] is not None and s["e 폭높이"] <= 0.10
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "도면벤치_색_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    그림(기록, 앞들, os.path.join(OUT, "도면벤치_색.png"))
    print(p)


def 그림(기록, 앞들, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    rng = np.random.default_rng(3)
    팔 = rng.uniform(0.25, 0.95, (4096, 3)); 팔[0] = 1
    n = len(앞들)
    fig, axs = plt.subplots(4, n, figsize=(2.2 * n, 10), dpi=100)
    axs = np.atleast_2d(axs).reshape(4, n)
    줄이름 = ["정답"] + list(판들)
    for k, (c, 앞) in enumerate(앞들.items()):
        r = 기록[c]
        for i, im in enumerate(앞):
            axs[i, k].imshow(팔[im % 4096]); axs[i, k].axis("off")
            if i == 0:
                axs[i, k].set_title("%s\n정답 %d" % (c.split("_")[0] + "_" + c.split("_")[1][:6], r["정답 부품"]), fontsize=8)
            else:
                q = r[판들[i - 1]]
                axs[i, k].set_title("%s %d · R %.2f · 짝 %d" % (판들[i - 1], q["부품"], q["R"], len(q["짝"])), fontsize=8)
    fig.suptitle("도면 벤치 · 색 — 위부터 정답 · 부위만 · A(색으로 합침) · A′(떨어진 조각은 따로)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
