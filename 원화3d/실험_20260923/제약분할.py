# -*- coding: utf-8 -*-
"""**제약 분할** — 빠짐 방향(탈형)을 분할의 «제약»으로 넣는다 (2026-09-23).

    python 제약분할.py            얼린 10 케이스 -> out/기록/제약분할_<때>.json

외부 평가 5 회에서 채택. 셋 다 「우리 부품은 공간을 균등하게 자른 조각 · 실제 키트 부품은 조립 단위로 설계된 것」.
Gemini: 「탈형 불가 10/25 는 금형 · 프린팅 분할 규칙(드래프트 · 언더컷)이 규칙에 안 들어가서다 — 시각 영역으로만 잘랐다.」
지금: 부위(거리장 분수령) × 색 을 곱해 나눈 **뒤에** 탈형을 검사만 한다.
고침: **부위에서 시작해, 한 축으로도 안 빠지는 부품은 빠질 때까지 쪼갠다.** 색은 안 쓴다.
    빠짐 = 그 축 기둥마다 채워진 칸이 한 토막(`조립.빠짐방향`) — 언더컷이 없다는 뜻
    쪼개기 = 축마다 「기둥의 첫 토막」과 「나머지」로 가르고 이어진 덩어리로 다시 나눈다 (부품 수가 가장 적게 느는 축을 고른다)

판정(돌리기 전 · 10 장 합계 · 외부 평가 5 회에서 받은 숫자 · IoU 는 고쳐 적는다):
    ① 탈형 불가 부품 0 개           (지금 10/25 · 케이스마다)
    ② 부품 수 케이스당 15~18        (인물 BJD 13~24 수준)
    ③ ⚠ 부피 IoU 는 **안 변한다** — 분할은 부피를 안 바꾼다. 0.61 ± 0.005 로 유지되는지 **불변 검사**로만 본다
      (외부 평가는 IoU ≥ 0.65 를 성공 숫자로 냈지만, 그건 분할로는 원리상 못 올린다. 그대로 적어 두고 판정에서 뺀다.)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 조립 as A
import 깊이추정 as GC

최소몫 = 0.004          # 이보다 작은 조각은 이웃에 돌려준다
깊이한도 = 4


def 빠지나(P):
    return any(A.빠짐방향(P))


def 첫토막(P, axis):
    """축 방향 기둥마다 «첫 토막»과 «나머지»로 가른다."""
    n = P.shape[axis]
    idx = np.arange(n).reshape([-1 if a == axis else 1 for a in range(3)])
    있 = P.any(axis=axis, keepdims=True)
    시작 = np.expand_dims(np.argmax(P, axis=axis), axis)
    끝없 = np.where(P, idx, -1).max(axis=axis, keepdims=True)
    # 첫 토막 = 시작부터 처음 빈 칸 전까지
    앞 = (idx >= 시작) & P
    빈 = (~P) & (idx > 시작) & (idx <= 끝없)
    첫빈 = np.where(빈.any(axis=axis, keepdims=True), np.expand_dims(np.argmax(빈, axis=axis), axis), n)
    첫 = 앞 & (idx < 첫빈) & 있
    return 첫, P & ~첫


def 쪼개기(P, 깊이=0):
    """빠질 때까지 쪼갠다. 축마다 시험해 **부품 수가 가장 적게 느는** 쪽을 고른다."""
    if 빠지나(P) or 깊이 >= 깊이한도 or P.sum() < 60:
        return [P]
    후보 = []
    for axis in range(3):
        첫, 남 = 첫토막(P, axis)
        if not 첫.any() or not 남.any():
            continue
        조각 = []
        for M in (첫, 남):
            l, k = ndimage.label(M, np.ones((3, 3, 3), bool))
            조각 += [l == i for i in range(1, k + 1)]
        조각 = [c for c in 조각 if c.sum() >= 30]
        if 조각:
            후보.append((len(조각), axis, 조각))
    if not 후보:
        return [P]
    _, axis, 조각 = min(후보, key=lambda t: t[0])
    out = []
    for c in 조각:
        out += 쪼개기(c, 깊이 + 1)
    return out


def 부스러기붙이기(부품, O):
    크기 = np.bincount(부품.ravel()); 크기[0] = 0
    작 = np.where((크기 > 0) & (크기 < 최소몫 * O.sum()))[0]
    if len(작):
        idx = ndimage.distance_transform_edt(np.isin(부품, 작) | ~O, return_distances=False, return_indices=True)
        부품 = np.where(np.isin(부품, 작), 부품[tuple(idx)], 부품)
    return 부품


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A2, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A2.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    색, _ = BB.색라벨(c, raw, masks, p, bs, O)

    def 세기(lab):
        라 = [l for l in np.unique(lab) if l]
        못 = [l for l in 라 if not 빠지나(lab == l)]
        return len(라), len(못)

    # 지금 판: 부위 × 색
    쌍 = (부위.astype(np.int64) * 1000 + 색.astype(np.int64)) * O
    지금 = np.zeros(O.shape, np.int32); 다음 = 0
    for v in np.unique(쌍):
        if v == 0: continue
        l, k = ndimage.label(쌍 == v, np.ones((3, 3, 3), bool))
        지금 = np.where(l > 0, l + 다음, 지금); 다음 += k
    지금 = 부스러기붙이기(지금, O)

    # 새 판: 부위에서 시작해 빠질 때까지 쪼갠다
    새 = np.zeros(O.shape, np.int32); n = 0
    for l in [l for l in np.unique(부위) if l]:
        for c2 in 쪼개기(부위 == l):
            n += 1; 새 = np.where(c2, n, 새)
    새 = 부스러기붙이기(새, O)

    r = {"부위": int(부위.max())}
    for 이름, lab in (("지금(부위×색)", 지금), ("제약분할", 새)):
        수, 못 = 세기(lab)
        r[이름] = {"부품": 수, "탈형 불가": 못, "IoU": PB.재기(lab > 0, T)["IoU"]}
    return r


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-28s 부위 %2d | 지금 부품 %3d 탈형불가 %2d | 제약 부품 %3d 탈형불가 %2d | IoU %.3f/%.3f  %.0f초"
              % (c[:28], r["부위"], r["지금(부위×색)"]["부품"], r["지금(부위×색)"]["탈형 불가"],
                 r["제약분할"]["부품"], r["제약분할"]["탈형 불가"], r["지금(부위×색)"]["IoU"], r["제약분할"]["IoU"], time.time() - t0), flush=True)
    m = lambda 판, k: float(np.median([기록[c][판][k] for c in GC.케이스들]))
    요약 = {판: {k: m(판, k) for k in ("부품", "탈형 불가", "IoU")} for 판 in ("지금(부위×색)", "제약분할")}
    요약["판정"] = {"① 탈형 불가 0": m("제약분할", "탈형 불가") == 0,
                  "② 부품 15~18": 15 <= m("제약분할", "부품") <= 18,
                  "③ IoU 불변(±0.005)": abs(m("제약분할", "IoU") - m("지금(부위×색)", "IoU")) <= 0.005}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "제약분할_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
