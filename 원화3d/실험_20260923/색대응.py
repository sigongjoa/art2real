# -*- coding: utf-8 -*-
"""**색 대응** — 앞 판과 옆 판의 색을 맞춰 유령을 깎는다 (2026-09-23).

    python 색대응.py            얼린 10 케이스 -> out/기록/색대응_<때>.json

09-23 최소 표면 · 폭 사전이 잇따라 진 뒤의 배움: **정칙화로는 안 되고 입력을 세게 해야 한다.**
옆 실루엣의 유령은 「옆 판의 y 구간이 어느 x 에 속하나」를 몰라서 생긴다 — **색이 그 대응을 준다.**
    앞 (x,z) 색 ≠ 옆 (y,z) 색 이면 그 복셀은 깎는다 (colored visual hull)
    겉에서 k 칸까지만 걸고 속은 놔둔다 (얇은 겉판이 색을 갖는다 · 09-22 껍질 실험과 같은 손잡이)
대조군: **옆 판 색을 뒤섞기** — 뒤섞어도 좋아지면 색이 일한 게 아니다.
판정(README · 돌리기 전): IoU ≥ 0.70 · 정밀 ≥ 0.75 · 재현 ≥ 0.85 · 뒤섞기보다 IoU +0.02 이상.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC


def 판색(case, raw, masks, p, bs):
    """세 판의 색 번호를 **한 팔레트**로 맞춰 격자에 올린다. front · back -> (x,z) · side -> (y,z)."""
    지도, 색들 = {}, {}
    for v in ("front", "side", "back"):
        지도[v], 색들[v] = BB.색지도(case, raw, p, v, masks[v])
    팔 = {c: i for i, c in enumerate(sorted(set().union(*[set(x.tolist()) for x in 색들.values()])), 1)}
    격 = {}
    for v in ("front", "side", "back"):
        옮 = np.array([0] + [팔[c] for c in 색들[v]])
        격[v] = BB.격자로(np.where(지도[v] > 0, 옮[지도[v]], 0))
    if bs < 0:
        격["back"] = 격["back"][::-1, :]
    return 격, len(팔)


def 깎기(O, 격, k, 뒤섞기=None):
    """앞(x,z) · 뒤(x,z) 색과 옆(y,z) 색이 겉 k 칸 안에서 어긋나면 깎는다."""
    S = 격["side"]
    if 뒤섞기 is not None:                                   # 대조군: 옆 판 색만 다른 번호로 바꾼다
        S = 뒤섞기[S]
    F, B = 격["front"][:, None, :], 격["back"][:, None, :]
    Sy = S[None, :, :]
    맞 = ((F == Sy) | (B == Sy) | (F == 0) | (Sy == 0))
    if np.isfinite(k):
        깊 = ndimage.distance_transform_edt(O)
        맞 |= 깊 > k                                          # 속은 색 규칙을 안 건다
    X = O & 맞
    for a in (0, 1):                                        # 실루엣이 비면 그 광선은 원래대로 되돌린다
        빈 = O.any(axis=a) & ~X.any(axis=a)
        if 빈.any():
            X |= O & np.expand_dims(빈, a)
    return X


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    격, n색 = 판색(c, raw, masks, p, bs)
    r = {"지금": PB.재기(O, T), "색 수": n색}
    rng = np.random.default_rng(11)
    뒤 = np.concatenate([[0], rng.permutation(np.arange(1, n색 + 1))])
    for k in (1, 3, 6, np.inf):
        이름 = "겉%s" % ("전부" if not np.isfinite(k) else k)
        r["색 " + 이름] = PB.재기(깎기(O, 격, k), T)
        r["뒤섞 " + 이름] = PB.재기(깎기(O, 격, k, 뒤), T)
    return r


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-30s 색%d | " % (c[:30], r["색 수"]) + " | ".join("%s %.2f" % (k.replace("겉", ""), v["IoU"]) for k, v in r.items() if isinstance(v, dict)) + "  %.0f초" % (time.time() - t0), flush=True)
    판들 = [k for k, v in 기록[GC.케이스들[0]].items() if isinstance(v, dict)]
    중앙 = lambda 판, m, 집합: float(np.median([기록[c][판][m] for c in 집합]))
    홀, 짝 = GC.케이스들[0::2], GC.케이스들[1::2]
    요약 = {"전체": {p: {m: round(중앙(p, m, GC.케이스들), 3) for m in ("IoU", "정밀도", "재현율", "부피 비")} for p in 판들}}
    고른 = max([p for p in 판들 if p.startswith("색 ")], key=lambda p: 중앙(p, "IoU", 홀))
    짝대조 = 고른.replace("색 ", "뒤섞 ")
    h = {m: 중앙(고른, m, 짝) for m in ("IoU", "정밀도", "재현율")}
    요약["고름(홀수 5 장)"] = 고른
    요약["홀드아웃(짝수 5 장)"] = {k: round(v, 3) for k, v in h.items()}
    요약["대조군(뒤섞기) 홀드아웃 IoU"] = round(중앙(짝대조, "IoU", 짝), 3)
    요약["판정"] = {"IoU ≥ 0.70": h["IoU"] >= 0.70, "정밀도 ≥ 0.75": h["정밀도"] >= 0.75,
                  "재현율 ≥ 0.85": h["재현율"] >= 0.85,
                  "뒤섞기보다 +0.02": h["IoU"] - 중앙(짝대조, "IoU", 짝) >= 0.02}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "색대응_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
