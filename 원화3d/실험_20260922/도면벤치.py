# -*- coding: utf-8 -*-
"""**도면 벤치** — 도면을 정답 메시와 댄다 (2026-09-22).

    python 도면벤치.py            얼린 10 케이스 -> out/기록/도면벤치_<때>.json · out/도면벤치.png
    python 도면벤치.py <케이스>    한 케이스만

사용자(09-22): 「벤치마크를 넣어서 결과를 보고 싶어」

케이스 = `깊이추정.케이스들` (메카·로봇·기사·괴물 10 · 얼린 집합 그대로). 도면 = `도면.py` 와 같은 배관.
정답 = `truth.glb` 연결 덩어리(`부품분할.정답부품`). 두 쪽 다 키 150 mm 로 맞춘다.

도면이 틀리는 곳은 둘이다 — **나누기**(어느 조각이 부품인가)와 **재기**(그 조각의 치수). 따로 잰다:

    나누기   R = 정답 부품마다 최대 IoU 를 넓이로 가중 (`부품분할.회수율` · 표면 점 위)
    재기     정답 부품과 IoU >= 0.5 로 맞은 도면 부품만 — 폭 · 높이 · 깊이 e = |ln(도면/정답)|
    깊이     같은 짝에서 옆판 깊이 대 비율 사전(깊이 = 폭)
    짝없음   R2 짝없음 몫 — 도면 대 정답 부품으로 만든 도면 (정답의 비대칭이 바닥선)

문턱을 **돌리기 전에** 적는다 (집계 = 케이스 중앙값 · 재기는 모든 짝을 모은 중앙값):

    Q1  재기    맞은 짝의 폭 · 높이 e 중앙값 <= 0.10          — 부품만 맞으면 그림이 치수를 준다
    Q2  깊이    맞은 짝에서 옆판 e 중앙값 < 사전 e 중앙값      — 벤치 3 판은 완벽하게 맞으니 **옆판이 이겨야 한다**
                                                              (지면 깊이 뽑기가 고장이다 · 진짜 원화는 판이 안 맞아 더 나쁘다)
    Q3  짝없음  도면 짝없음 몫 > 정답 짝없음 몫 인 케이스 >= 7/10 — R2 가 분할의 좌우 어긋남을 잡는 자인가
    (관찰)      R — 09-21 부품분할 벤치의 ①만(관절 분수령) 과 같은 배관이라 비슷해야 한다
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import 도면 as DM
import 부품분할 as BB
import 깊이추정 as GC
import 시트 as S

OUT = H.OUT


def e(a, b):
    return abs(np.log(max(a, 0.1) / max(b, 0.1)))


def 정답상자(case):
    """정답 부품마다 x · y · z 상자 (mm · 키 150 · 바닥 0) — `부품분할.정답부품` 과 같은 덩어리 · 같은 번호."""
    t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh", process=False)
    V, F = np.asarray(t.vertices), np.asarray(t.faces)
    w, lab, nt = BB.정답부품(case)
    mm = DM.키mm / (V[:, 2].max() - V[:, 2].min())
    r = {}
    for l in np.unique(lab):
        q = w[lab == l]
        lo, hi = q.min(0), q.max(0)
        lo, hi = lo * mm, hi * mm
        lo[2] -= V[:, 2].min() * mm; hi[2] -= V[:, 2].min() * mm
        r[int(l)] = {"lo": lo, "hi": hi, "c": q.mean(0) * mm - [0, 0, V[:, 2].min() * mm], "n": int((lab == l).sum())}
    return w, lab, r


def 상자도면(잰):
    """잰치수 모양({라벨: lo · hi · c}) -> R2 가 먹는 최소 도면."""
    ps = []
    for l, s in 잰.items():
        e3 = s["hi"] - s["lo"]
        쪽 = "L" if s["c"][0] > 3 else "R" if s["c"][0] < -3 else "C"
        ps.append({"id": "P%02d" % l, "부위": l, "쪽": 쪽, "중심": [float(v) for v in s["c"]],
                   "폭": DM.칸(float(e3[0]), "그림", "확정"), "높이": DM.칸(float(e3[2]), "그림", "확정"),
                   "깊이": DM.칸(float(e3[1]), "옆판", "추정")})
    return {"부품": ps}


def 짝없음몫(잰):
    도 = 상자도면(잰)
    _, 짝 = DM.R2(도)
    된 = {i for ab in 짝 for i in ab}
    옆 = [p["id"] for p in 도["부품"] if p["쪽"] != "C"]
    return (sum(i not in 된 for i in 옆) / len(옆)) if 옆 else 0.0


def 한케이스(case):
    lab, ux, uy, z = DM.라벨(case)
    잰, mm, z0 = DM.잰치수(lab, ux, uy, z)
    w, t, 정 = 정답상자(case)
    p = BB.표본(lab, (ux, uy, z), w)
    R = BB.회수율(t, p)
    M = np.zeros((t.max() + 1, p.max() + 1), np.int64)
    np.add.at(M, (t, p), 1)
    iou = M / np.maximum(M.sum(1, keepdims=True) + M.sum(0, keepdims=True) - M, 1)
    짝들 = []
    for ti in range(iou.shape[0]):
        pi = int(iou[ti].argmax())
        if iou[ti, pi] < 0.5 or pi not in 잰:
            continue
        a, b = 잰[pi], 정[ti]
        ea, eb = a["hi"] - a["lo"], b["hi"] - b["lo"]
        짝들.append({"정답": ti, "도면": pi, "IoU": round(float(iou[ti, pi]), 3),
                    "e폭": e(ea[0], eb[0]), "e높이": e(ea[2], eb[2]),
                    "e깊이옆판": e(ea[1], eb[1]), "e깊이사전": e(ea[0], eb[1])})
    return {"case": case, "정답 부품": len(정), "도면 부품": len(잰), "R": R, "맞은 짝": 짝들,
            "짝없음 도면": 짝없음몫(잰), "짝없음 정답": 짝없음몫(정)}, (lab, t, p)


def 앞그림(case, lab):
    """도면 부위를 앞에서 본 첫 닿는 라벨 (y 가 앞 -> 뒤)."""
    첫 = np.zeros((lab.shape[0], lab.shape[2]), np.int32)
    for j in range(lab.shape[1]):
        v = lab[:, j, :]
        새 = (첫 == 0) & (v > 0)
        첫[새] = v[새]
    return 첫.T[::-1]


def 정답앞(case):
    t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh", process=False)
    V, F = np.asarray(t.vertices, np.float64), np.asarray(t.faces, np.int64)
    fc = trimesh.graph.connected_component_labels(trimesh.Trimesh(V, F).face_adjacency, node_count=len(F))
    _, ident = S.draw(V, F, np.full((len(F), 3), 200, np.uint8), np.zeros(len(F), np.int32), "front", line=False)
    return np.where(ident >= 0, fc[np.clip(ident, 0, None)] + 1, 0)


def 그림(기록, 앞들, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    rng = np.random.default_rng(3)
    팔 = rng.uniform(0.25, 0.95, (4096, 3)); 팔[0] = 1
    n = len(앞들)
    fig, axs = plt.subplots(2, n, figsize=(2.2 * n, 5.4), dpi=110)
    axs = np.atleast_2d(axs).reshape(2, n)
    for k, (c, (정, 도)) in enumerate(앞들.items()):
        r = 기록[c]
        axs[0, k].imshow(팔[정 % 4096]); axs[1, k].imshow(팔[도 % 4096])
        axs[0, k].set_title("%s\n정답 %d" % (c.split("_")[0] + "_" + c.split("_")[1][:6], r["정답 부품"]), fontsize=8)
        axs[1, k].set_title("도면 %d · R %.2f\n짝없음 %.0f%% (정답 %.0f%%)" % (
            r["도면 부품"], r["R"], 100 * r["짝없음 도면"], 100 * r["짝없음 정답"]), fontsize=8)
        for a in axs[:, k]:
            a.axis("off")
    fig.suptitle("도면 벤치 — 위 정답 부품 · 아래 도면 부품 (정면 · 색은 부품마다 임의)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)


def main(only=None):
    cases = [only] if only else GC.케이스들
    기록, 앞들 = {}, {}
    for c in cases:
        t0 = time.time()
        r, (lab, _, _) = 한케이스(c)
        기록[c] = r
        앞들[c] = (정답앞(c), 앞그림(c, lab))
        m = r["맞은 짝"]
        print("  %-38s 정답 %2d 도면 %2d R %.3f 맞은짝 %2d  e폭 %.3f e높이 %.3f 깊이 옆판 %.3f 사전 %.3f  짝없음 %.2f/%.2f  %.0f초"
              % (c, r["정답 부품"], r["도면 부품"], r["R"], len(m),
                 np.median([x["e폭"] for x in m]) if m else np.nan, np.median([x["e높이"] for x in m]) if m else np.nan,
                 np.median([x["e깊이옆판"] for x in m]) if m else np.nan, np.median([x["e깊이사전"] for x in m]) if m else np.nan,
                 r["짝없음 도면"], r["짝없음 정답"], time.time() - t0), flush=True)
    모든 = [x for r in 기록.values() for x in r["맞은 짝"]]
    e폭높 = float(np.median([x["e폭"] for x in 모든] + [x["e높이"] for x in 모든])) if 모든 else float("nan")
    e옆, e사 = (float(np.median([x[k] for x in 모든])) if 모든 else float("nan") for k in ("e깊이옆판", "e깊이사전"))
    더 = sum(r["짝없음 도면"] > r["짝없음 정답"] for r in 기록.values())
    요약 = {"케이스": len(기록), "맞은 짝": len(모든), "정답 부품 합": sum(r["정답 부품"] for r in 기록.values()),
          "R 중앙": float(np.median([r["R"] for r in 기록.values()])),
          "e 폭높이": e폭높, "e 깊이 옆판": e옆, "e 깊이 사전": e사, "짝없음 도면>정답": 더,
          "Q1": e폭높 <= 0.10, "Q2": e옆 < e사, "Q3": 더 >= 0.7 * len(기록)}
    print("\n" + json.dumps(요약, ensure_ascii=False))
    p = os.path.join(OUT, "기록", "도면벤치_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    그림(기록, 앞들, os.path.join(OUT, "도면벤치.png"))
    print(p)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
