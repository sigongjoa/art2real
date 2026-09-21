# -*- coding: utf-8 -*-
"""**부품 분할 A** — 관절 부위 × 색, 같은 색은 부위 안에서 합친다 (2026-09-21).

    python 부품분할.py 벤치            -> out/기록/부품분할_벤치_<때>.json
    python 부품분할.py 벤치 <케이스>    한 케이스만 (무거우면 쪼개 돌린다 — `bench-runs-get-killed`)

설계: `claudedocs/research_부품분할_구현_20260921.md` 의 ①③④⑤. ②쉘 · ⑥홈 · ⑦틈 · ⑧핀 은 벤치 뒤에.

    ① 부위    `면자르기.부위` — 거리장 분수령 (관절에서 갈린다)
    ③ 색      원화 앞 · 뒤 판 색을 양자화 -> 기둥 앞 절반은 앞 판 · 뒤 절반은 뒤 판 (`색분할` 규칙)
    ④ 합치기  부품 = (부위, 색) 쌍. 같은 부위 안 같은 색은 떨어져 있어도 한 부품 (Surface2Volume)
              작은 조각(< 최소몫)은 가장 가까운 부품에 붙인다
    ⑤ 빠지나  6 축 방향 · 여러 번 분해 — 지금 빠지는 부품부터 뺀다

## 벤치 (정답 = truth.glb 의 연결 덩어리)

게임 · 마네킹 메시는 부품이 **떨어진 덩어리**로 들어 있다. 표면의 1% 이상인 덩어리를 정답 부품으로 본다.

    회수율 R = Σ_t |t| · max_p IoU(t, p) / Σ_t |t|      (표면 복셀 위에서 · 쉘/속 차이를 안 탄다)

**문턱 (돌리기 전에 적는다):**

    G1  A 의 R 중앙값 > 높이 자르기(같은 부품 수) R 중앙값, 그리고 케이스의 60% 이상에서 A 가 이긴다
    G2  A 의 R 중앙값 >= ①만 의 R 중앙값 - 0.01           (색을 더해 망가지지 않는다)
    G3  A 부품의 빠지는 몫 중앙값 >= 0.9                   (6 축 · 여러 번 분해)
    G4  모든 케이스 부품 수 <= 132

케이스 집합 (돌리기 전에 고정): 벤치 시트 중 **변형 접미사가 없고** 정답 부품이 3~60 개인 것.
"""
import json
import os
import re
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 면자르기 as MJ
W = H.W
OUT = H.OUT
N = MJ.N                         # 192 — 분수령과 같은 격자
색뭉치 = 32                      # 색 양자화 칸
색최소 = 0.01                    # 판 몸 넓이 대비. 이보다 작은 색은 색으로 안 본다 (경계 섞임 · 부스러기)
최소몫 = 0.004                   # 부피 대비. 이보다 작은 부품은 이웃에 붙인다
정답최소 = 0.01                  # 표면 대비. 이보다 작은 정답 덩어리는 부품으로 안 본다
상한 = 132
접미 = re.compile(r"_(선2|배관|생성flash|생성pro|정면만|초정밀|상자|뒤만생성|옆만생성|darkness|v)$")


def 판(case):
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    return raw, H._warp(masks, p), bs, p


def 색지도(case, raw, p, v, 몸):
    """원화 판 -> 창 위 색 번호. 어두운 선 · 드문 색은 가장 가까운 색으로 메운다."""
    import cv2
    im = cv2.imdecode(np.fromfile(os.path.join(H.art_dir(case), H.CASES[case]["src"][v]), np.uint8),
                      cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB).astype(np.float32)
    if im.ndim == 3 and im.shape[2] == 4:
        rgb = np.where(im[:, :, 3:4] > 127, rgb, 255)
    d = H.declutter(raw[v])
    창 = np.dstack([H._warp_one(H.to_win(d, rgb[:, :, k])[1], v, p) for k in range(3)])
    q = np.clip(창, 0, 255).astype(np.int32) // 색뭉치
    코드 = q[:, :, 0] * 10000 + q[:, :, 1] * 100 + q[:, :, 2]
    밝 = 창.mean(2) > 60
    몸 = 몸.astype(bool)
    값, 수 = np.unique(코드[몸 & 밝], return_counts=True)
    쓸 = 값[수 >= 색최소 * 몸.sum()]
    L = np.zeros(몸.shape, np.int32)
    for i, c in enumerate(쓸, 1):
        L[몸 & 밝 & (코드 == c)] = i
    if (L > 0).any():
        idx = ndimage.distance_transform_edt(L == 0, return_distances=False, return_indices=True)
        L = np.where(몸, L[tuple(idx)], 0)
    return L, 쓸


def 격자로(L2):
    import cv2
    return cv2.resize(L2.astype(np.float32), (N, N), interpolation=cv2.INTER_NEAREST).astype(np.int32).T[:, ::-1]


def 색라벨(case, raw, masks, p, bs, O):
    """3D 색 라벨 — 앞 절반은 앞 판, 뒤 절반은 뒤 판. **같은 색은 같은 번호**(앞뒤 공용 팔레트)."""
    앞2, 앞색 = 색지도(case, raw, p, "front", masks["front"])
    뒤2, 뒤색 = 색지도(case, raw, p, "back", masks["back"])
    팔 = {c: i for i, c in enumerate(sorted(set(앞색.tolist()) | set(뒤색.tolist())), 1)}
    앞L = 격자로(np.where(앞2 > 0, np.array([0] + [팔[c] for c in 앞색])[앞2], 0))
    뒤L = 격자로(np.where(뒤2 > 0, np.array([0] + [팔[c] for c in 뒤색])[뒤2], 0))
    if bs < 0:
        뒤L = 뒤L[::-1, :]
    있 = O.any(1)
    앞 = np.where(있, O.argmax(1), 0)
    뒤 = np.where(있, N - 1 - O[:, ::-1].argmax(1), 0)
    앞쪽 = np.arange(N)[None, :, None] <= ((앞 + 뒤) // 2)[:, None, :]
    lab = np.where(O & 앞쪽, 앞L[:, None, :], np.where(O, 뒤L[:, None, :], 0))
    return 채우기(lab, O), len(팔)


def 채우기(lab, O):
    빈 = O & (lab == 0)
    if 빈.any() and (lab > 0).any():
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab = np.where(빈, lab[tuple(idx)], lab)
    return np.where(O, lab, 0)


def 합치기(부위, 색, O):
    """부품 = (부위, 색) 쌍 — 같은 부위 안 같은 색은 **떨어져 있어도 한 부품**. 작은 부품은 이웃에."""
    쌍 = np.where(O, 부위.astype(np.int64) * 1000 + 색, 0)
    _, lab = np.unique(쌍, return_inverse=True)
    lab = lab.reshape(O.shape).astype(np.int32)                     # 0 은 바깥 (쌍 0 이 제일 작다)
    크 = np.bincount(lab.ravel())
    작 = np.where(크 < 최소몫 * O.sum())[0]
    lab[np.isin(lab, 작[작 > 0])] = 0
    lab = 채우기(lab, O)
    _, lab = np.unique(lab, return_inverse=True)
    return lab.reshape(O.shape).astype(np.int32)


def 높이자르기(O, k):
    """대조군 — 부피가 같은 z 판 k 장."""
    z = np.where(O)[2]
    경계 = np.quantile(z, np.linspace(0, 1, k + 1)[1:-1])
    zz = np.broadcast_to(np.arange(O.shape[2])[None, None, :], O.shape)
    return np.where(O, np.searchsorted(경계, zz, side="right") + 1, 0).astype(np.int32)


def 빠지나(lab):
    """6 축 · 여러 번 분해. -> (빠진 부품 몫, 못 뺀 부품 목록)."""
    남 = [int(v) for v in np.unique(lab) if v > 0]
    빠짐 = 0
    총 = len(남)
    while 남:
        이번 = []
        for v in 남:
            P = lab == v
            다른 = (lab > 0) & ~P & np.isin(lab, 남)
            for ax in range(3):
                for s in (1, -1):
                    D = 다른[(slice(None),) * ax + (slice(None, None, s),)]
                    앞 = np.maximum.accumulate(D, axis=ax)[(slice(None),) * ax + (slice(None, None, s),)]
                    # 앞[i] = i 에서 s 방향 **끝까지** 다른 부품이 있나 (i 포함) — 자기 자리엔 다른 게 없으니 그대로 쓴다
                    if not (P & 앞).any():
                        이번.append(v)
                        break
                else:
                    continue
                break
        if not 이번:
            break
        빠짐 += len(이번)
        남 = [v for v in 남 if v not in 이번]
    return 빠짐 / max(총, 1), 남


def 정답부품(case):
    """truth.glb -> (표면 복셀 세계좌표, 정답 부품 번호). 작은 덩어리는 가장 가까운 큰 덩어리에."""
    import trimesh
    import 정답 as JD
    from scipy.spatial import cKDTree
    t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
    fc = trimesh.graph.connected_component_labels(t.face_adjacency, node_count=len(t.faces))
    vc = np.zeros(len(t.vertices), np.int64)
    vc[t.faces.ravel()] = np.repeat(fc, 3)
    A, o = JD.grid(t)
    겉 = A & ~ndimage.binary_erosion(A)
    ij = np.argwhere(겉)
    w = (ij + o) * JD.PITCH
    _, ni = cKDTree(t.vertices).query(w)
    c = vc[ni]
    값, 수 = np.unique(c, return_counts=True)
    큰 = 값[수 >= 정답최소 * len(c)]
    if len(큰) == 0:
        return w, np.zeros(len(c), np.int64), 0
    작 = ~np.isin(c, 큰)
    if 작.any():
        _, j = cKDTree(w[~작]).query(w[작])
        c[작] = c[~작][j]
    _, c = np.unique(c, return_inverse=True)
    return w, c, len(큰)


def 표본(lab, ax, w):
    """우리 라벨을 정답 표면 점에서 읽는다. 우리 형상 밖이면 가장 가까운 라벨."""
    idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    i = [np.clip(np.rint((w[:, k] - ax[k][0]) / (ax[k][1] - ax[k][0])).astype(int), 0, lab.shape[k] - 1)
         for k in range(3)]
    return lab[tuple(idx[k][tuple(i)] for k in range(3))]


def 회수율(t, p):
    """R = Σ_t |t| · max_p IoU(t, p) / Σ|t|."""
    M = np.zeros((t.max() + 1, p.max() + 1), np.int64)
    np.add.at(M, (t, p), 1)
    tn, pn = M.sum(1, keepdims=True), M.sum(0, keepdims=True)
    iou = M / np.maximum(tn + pn - M, 1)
    return float((tn[:, 0] * iou.max(1)).sum() / tn.sum())


def 한케이스(case):
    w, t, nt = 정답부품(case)
    if not (3 <= nt <= 60):
        return {"case": case, "정답 부품": nt, "제외": "정답 부품 수 범위 밖"}
    raw, masks, bs, p = 판(case)
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    O = g > 0
    _, 부위, _ = MJ.부위(O)
    부위 = 채우기(부위, O)
    색, n색 = 색라벨(case, raw, masks, p, bs, O)
    A = 합치기(부위, 색, O)
    A1 = 합치기(부위, np.zeros_like(색), O)
    k = int(A.max())
    Hz = 높이자르기(O, k)
    r = {"case": case, "정답 부품": nt, "색": n색, "부품 A": k, "부품 ①만": int(A1.max()),
         "R A": 회수율(t, 표본(A, ax, w)), "R ①만": 회수율(t, 표본(A1, ax, w)),
         "R 높이": 회수율(t, 표본(Hz, ax, w)), "R 통짜": 회수율(t, 표본(O.astype(np.int32), ax, w))}
    r["빠지는 몫"], 못 = 빠지나(A)
    r["못 뺀 부품"] = len(못)
    return r


def 벤치(only=None):
    H.register_sheets()
    cases = [c for c in H.CASES if os.path.exists(os.path.join(OUT, "시트", c, "truth.glb"))
             and not 접미.search(c) and (only is None or c == only)]
    기록 = os.path.join(OUT, "기록", "부품분할_벤치.jsonl")
    os.makedirs(os.path.dirname(기록), exist_ok=True)
    됨 = set()
    if os.path.exists(기록) and only is None:
        됨 = {json.loads(l)["case"] for l in open(기록, encoding="utf-8")}
    for c in cases:
        if c in 됨:
            continue
        t0 = time.time()
        try:
            r = 한케이스(c)
        except Exception as e:                                           # 한 케이스가 깨져도 나머지는 잰다
            r = {"case": c, "실패": str(e)[:120]}
        r["초"] = round(time.time() - t0, 1)
        open(기록, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()},
                                ensure_ascii=False), flush=True)
    요약(기록)


def 요약(기록):
    rs = [json.loads(l) for l in open(기록, encoding="utf-8")]
    rs = [r for r in rs if "R A" in r]
    if not rs:
        return
    m = lambda k: float(np.median([r[k] for r in rs]))
    승 = np.mean([r["R A"] > r["R 높이"] for r in rs])
    g = {"케이스": len(rs), "R A": m("R A"), "R ①만": m("R ①만"), "R 높이": m("R 높이"), "R 통짜": m("R 통짜"),
         "A 가 높이를 이긴 몫": float(승), "빠지는 몫 중앙": m("빠지는 몫"), "부품 최대": max(r["부품 A"] for r in rs)}
    g["G1"] = bool(g["R A"] > g["R 높이"] and 승 >= 0.6)
    g["G2"] = bool(g["R A"] >= g["R ①만"] - 0.01)
    g["G3"] = bool(g["빠지는 몫 중앙"] >= 0.9)
    g["G4"] = bool(g["부품 최대"] <= 상한)
    print("\n  요약 " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()},
                                 ensure_ascii=False), flush=True)
    json.dump({"요약": g, "케이스": rs}, open(os.path.join(OUT, "기록", "부품분할_벤치_%s.json"
                                                     % time.strftime("%Y%m%d_%H%M")), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def demo():
    """자기검사 — 회수율과 빠지나가 답을 아는 경우에 맞게 나오나."""
    t = np.array([0, 0, 1, 1])
    assert abs(회수율(t, t) - 1) < 1e-9
    assert abs(회수율(t, np.zeros(4, int)) - 0.5) < 1e-9                  # 통짜: 두 부품 모두 IoU 0.5
    lab = np.zeros((6, 6, 6), np.int32)
    lab[1:3, 1:5, 1:5] = 1
    lab[3:5, 1:5, 1:5] = 2
    assert 빠지나(lab) == (1.0, [])                                    # 나란한 두 상자는 빠진다
    lab = np.zeros((7, 7, 7), np.int32)
    lab[1:6, 1:6, 1:6] = 1
    lab[3, 3, 3] = 2                                                  # 1 에 완전히 갇힌 2
    frac, 못 = 빠지나(lab)
    assert frac == 0.0, (frac, 못)                                   # 갇힌 부품은 조립이 불가능하다 — 둘 다 못 뺀다
    lab = np.zeros((8, 8, 8), np.int32)
    lab[1:7, 1:7, 1:4] = 1
    lab[3:5, 3:5, 2:6] = 2                                            # 1 에 꽂힌 기둥 2 (위로 빠진다)
    lab[2:6, 2:6, 6] = 3                                              # 2 위의 뚜껑 3
    assert 빠지나(lab) == (1.0, []), 빠지나(lab)                       # 3 -> 2 -> 1 순서로 여러 번 분해
    print("  demo 통과")



def 그림(cases=("마네킹_다리벌림", "mech_Mech_D5wW2jDO42", "robot_Robot_ejDr8lRglP", "sakurada_fumiriya")):
    """정답 · A · 관절만 · 높이 — 표면 점을 앞에서 본다 (부품마다 색). -> out/부품분할_벤치.png"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    H.register_sheets()
    열 = ["정답 (연결 덩어리)", "A 관절×색", "관절만", "높이 자르기 (대조군)"]
    fig, axs = plt.subplots(len(cases), 4, figsize=(16, 4.4 * len(cases)))
    rng = np.random.default_rng(0)
    for i, c in enumerate(cases):
        w, t, nt = 정답부품(c)
        raw, masks, bs, p = 판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=N)
        O = g > 0
        _, 부위, _ = MJ.부위(O)
        부위 = 채우기(부위, O)
        색, _ = 색라벨(c, raw, masks, p, bs, O)
        A = 합치기(부위, 색, O)
        A1 = 합치기(부위, np.zeros_like(색), O)
        labs = [t, 표본(A, ax, w), 표본(A1, ax, w), 표본(높이자르기(O, int(A.max())), ax, w)]
        앞 = np.argsort(w[:, 1])[::-1]                                  # 뒤 -> 앞 순서로 찍어 앞이 위에 온다
        for j, L in enumerate(labs):
            팔 = rng.permutation(max(int(L.max()) + 1, 1))
            a = axs[i, j]
            a.scatter(w[앞, 0], w[앞, 2], c=팔[L[앞]], cmap="tab20", s=1.2, lw=0)
            a.set_aspect("equal"); a.axis("off")
            R = "" if j == 0 else " · R %.2f" % 회수율(t, L)
            a.set_title("%s\n%s · 부품 %d%s" % (c[:28], 열[j], len(np.unique(L)), R), fontsize=10)
    fig.tight_layout()
    o = os.path.join(OUT, "부품분할_벤치.png")
    fig.savefig(o, dpi=80)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "demo":
        demo()
    elif a and a[0] == "그림":
        그림()
    elif a and a[0] == "벤치":
        벤치(a[1] if len(a) > 1 else None)
