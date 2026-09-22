# -*- coding: utf-8 -*-
"""**도면 벤치 · 껍질** — 색을 기둥이 아니라 겉 껍질 두께만큼만 입힌다 (2026-09-22).

    python 도면벤치_껍질.py           얼린 10 케이스 -> out/기록/도면벤치_껍질_<때>.json · out/도면벤치_껍질.png

외부 평가(README 09-22 외부 평가 절)에서 ChatGPT · Gemini · Grok **셋 다** 같은 원인을 짚고 같은 실험을 냈다:
「앞 판 색을 두께 절반까지 기둥으로 밀어 넣어 얇은 겉판(갑주)과 어긋나고 옆면까지 색이 묻는다 → 색을 껍질에만」.
미리 적은 판정 기준(두 곳 이상 · 인용 · 삼면도만 · 성공 숫자)을 통과해 채택했다.

**바꾸는 것은 하나 — 색이 들어가는 두께.** 나머지(분수령 부위 · 색 라벨 규칙 · 연결 덩어리로 가르기 · 자 · 케이스)는
`도면벤치_색.py` 의 A′ 그대로다.

    껍질 k   겉에서 k 칸 안(부피 안 거리장 ≤ k)만 색 라벨, 그 안쪽은 부위 라벨   k = 1 · 2 · 3 칸 (1 칸 ≈ 0.8 mm)
    기둥     지금 방식 (= A′) — 대조

**따라 바뀌는 것 하나** (두께를 바꾸면 없앨 수 없다): 작은 조각을 이웃에 붙이는 기준을 **부피**가 아니라 **겉 넓이**
(겉 한 칸 층 복셀 수)로 잰다. 부피로 재면 껍질 조각은 얇아서 전부 0.4% 미만이라 지워진다. 문턱 몫(0.004)은 같다.

문턱을 **돌리기 전에** 적는다 (외부 평가 절과 같다):

    성공   어떤 k 에서든 맞은 짝(IoU ≥ 0.5) 합 ≥ 17  그리고  그 k 의 짝 폭 · 높이 e 중앙 ≤ 0.23
    대조   기둥(A′) 짝 10 · e 0.259 · 부위만 짝 11 · e 0.174
    지면   색 두께가 병목이 아니다 — 외부 평가 셋의 공통 진단이 틀렸다고 적는다
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
import 도면벤치 as DB
import 도면벤치_색 as DC
import 부품분할 as BB
import 면자르기 as MJ
import 깊이추정 as GC

OUT = H.OUT
두께들 = (1, 2, 3)


def 껍질판(부위, 색, O, k):
    """겉 k 칸 안은 (부위, 색) · 안쪽은 (부위, 0) -> 연결 덩어리 -> 작은 조각은 **겉 넓이** 기준으로 이웃에."""
    D = ndimage.distance_transform_edt(O)
    겉k = O & (D <= k)
    쌍 = np.where(O, 부위.astype(np.int64) * 1000 + np.where(겉k, 색, 0), 0)
    _, lab = np.unique(쌍, return_inverse=True)
    lab = lab.reshape(O.shape).astype(np.int32)
    out = np.zeros_like(lab)
    n = 0
    for l in np.unique(lab):
        if l == 0:
            continue
        cc, m = ndimage.label(lab == l, np.ones((3, 3, 3), bool))
        out[cc > 0] = cc[cc > 0] + n
        n += m
    겉1 = O & (D <= 1)
    넓이 = np.bincount(out[겉1].ravel(), minlength=out.max() + 1)
    작 = np.where(넓이 < BB.최소몫 * 겉1.sum())[0]
    out[np.isin(out, 작[작 > 0])] = 0
    out = BB.채우기(out, O)
    _, out = np.unique(out, return_inverse=True)
    return out.reshape(O.shape).astype(np.int32)


def main(only=None):
    cases = [only] if only else GC.케이스들
    판들 = ["기둥(A′)"] + ["껍질%d" % k for k in 두께들]
    기록, 앞들 = {}, {}
    for c in cases:
        t0 = time.time()
        raw, masks, bs, p = BB.판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        O = g > 0
        _, 부위, _ = MJ.부위(O)
        부위 = BB.채우기(부위, O)
        색, n색 = BB.색라벨(c, raw, masks, p, bs, O)
        labs = {"기둥(A′)": DC.연결로(BB.합치기(부위, 색, O), O)}
        for k in 두께들:
            labs["껍질%d" % k] = 껍질판(부위, 색, O, k)
        w, t, 정 = DB.정답상자(c)
        r = {k: DC.재기(labs[k], ux, uy, z, w, t, 정) for k in 판들}
        r["정답 부품"] = len(정); r["칸 mm"] = float((ux[1] - ux[0]) * DB.DM.키mm / (z[-1] - z[0]))
        기록[c] = r
        앞들[c] = (DB.정답앞(c),) + tuple(DB.앞그림(c, labs[k]) for k in 판들)
        print("  %-38s 정답 %2d | " % (c, len(정)) + " | ".join(
            "%s %2d R %.3f 짝 %2d" % (k, r[k]["부품"], r[k]["R"], len(r[k]["짝"])) for k in 판들) + "  %.0f초" % (time.time() - t0), flush=True)
    요약 = {"케이스": len(기록)}
    for k in 판들:
        모든 = [x for r in 기록.values() for x in r[k]["짝"]]
        e = float(np.median([x["e폭"] for x in 모든] + [x["e높이"] for x in 모든])) if 모든 else None
        요약[k] = {"R 중앙": float(np.median([r[k]["R"] for r in 기록.values()])), "짝 합": len(모든), "e 폭높이": e,
                  "성공": len(모든) >= 17 and e is not None and e <= 0.23}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "도면벤치_껍질_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    그림(기록, 앞들, 판들, os.path.join(OUT, "도면벤치_껍질.png"))
    print(p)


def 그림(기록, 앞들, 판들, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    rng = np.random.default_rng(3)
    팔 = rng.uniform(0.25, 0.95, (4096, 3)); 팔[0] = 1
    n = len(앞들)
    fig, axs = plt.subplots(1 + len(판들), n, figsize=(2.2 * n, 2.5 * (1 + len(판들))), dpi=100)
    axs = np.asarray(axs).reshape(1 + len(판들), n)
    for k, (c, 앞) in enumerate(앞들.items()):
        r = 기록[c]
        for i, im in enumerate(앞):
            a = axs[i, k]; a.imshow(팔[im % 4096]); a.axis("off")
            a.set_title(("%s\n정답 %d" % (c.split("_")[0] + "_" + c.split("_")[1][:6], r["정답 부품"])) if i == 0 else
                        "%s %d · 짝 %d" % (판들[i - 1], r[판들[i - 1]]["부품"], len(r[판들[i - 1]]["짝"])), fontsize=8)
    fig.suptitle("도면 벤치 · 껍질 — 위부터 정답 · 기둥(A′) · 껍질 1 · 2 · 3 칸 (정면 · 색은 부품마다 임의)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
