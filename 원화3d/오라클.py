# -*- coding: utf-8 -*-
"""**깊이맵의 천장.** 정답 메시에서 진짜 깊이를 뽑아 *같은 깎기 규칙*에 넣는다.

    python 오라클.py 도형          기본도형 11개
    python 오라클.py 벤치 [n]      실물 벤치 앞에서 n 장 (기본 8)
        -> out/기록/오라클_<날짜>.json

## 무엇을 가르나

`대조.py` 가 낸 결론은 「깊이 깎기가 균일 침식만도 못하다」(29장에서 -0.0134, 3승)이다.
용의자가 둘 남았고 **이 한 실험이 둘을 가른다:**

    오라클이 균일을 크게 이긴다  -> 깎기 규칙은 멀쩡하다. **깊이맵이 약한 것**이다
                                  (크리스 인플레이션은 실루엣의 함수라 새 정보가 없다)
    오라클도 균일한테 진다       -> **규칙이 범인**이다. 앞뒤(y)만 움직이는 게 한계고,
                                  단면을 직사각형에서 벗어나게 하는 쪽으로 가야 한다

## 오라클 깊이맵을 어떻게 뽑나

`시트.py` 의 그리기 규약을 흉내내지 않는다 — **깎기가 쓰는 프레임에서 바로 뽑는다.**
`carve_depth` 는 앞면을 `lo`(기둥의 최소 y)에, 뒷면을 `hi`(최대 y)에 댄다. 그러니 오라클은
「(x, z) 마다 정답의 최소/최대 y」다. `truth.glb` 는 이미 `W.normalize` 를 거친 창 좌표라
배율을 다시 안 잡는다.

`hull.load_depth` 규약에 맞춘다 — 0~1, **1 이 제일 튀어나온 곳**. 앞뒤는 **물건의 y 범위
하나로** 정규화한다 (시점마다 따로 하면 평평한 뒷면이 0 이 되어 전부 깎으라는 뜻이 된다).

## 이게 오라클이지 정답이 아닌 이유

깊이맵이 완벽해도 **깎기 규칙의 상한**은 그대로다 — `jf = lo + (1-hf)·lam·D` 는 앞뒤로
`lam` 배까지만 판다. 그래서 여기 나오는 값은 「진짜 깊이를 줬을 때 이 규칙이 낼 수 있는
최대」다. `--lam` 으로 규칙의 상한도 같이 본다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hull as H
import win as W
import 정답 as J
import 대조 as C

OUT = os.path.join(HERE, "out")
LAMS = (0.20, 0.35, 0.50)
BACK = -1                                        # 시트 케이스의 후면 좌우 규약 (register_sheets)


def oracle_depth(truth, view):
    """정답 메시 -> 그 시점의 **진짜 깊이 이미지** (W.RES², 1 이 제일 튀어나온 곳).

    `시트.py` 의 그리기 규약을 흉내내지 않는다 — **깎기가 쓰는 프레임에서 바로 뽑는다.**
    `carve_depth` 는 앞면 깊이를 `lo`(= 그 기둥의 **최소 y**)에 대고, 뒷면을 `hi`(최대 y)에
    댄다. 그러니 오라클은 「(x, z) 마다 정답의 최소/최대 y」면 된다.

    부호는 실측으로 정했다 — base_male 에서 정답의 y 를 뒤집으면 IoU 0.6972 -> 0.4396 이다.
    즉 정답 메시와 hull 은 같은 y 를 쓰고, **앞면은 최소 y** 다.

    화가 알고리즘으로 (x, z) 평면에 y 를 찍는다. front 는 먼 것(큰 y)부터 찍어 작은 y 가
    남고, back 은 반대다. `carve_depth` 가 back 을 `topix(back_sign·x, z)` 로 읽으므로
    그 화소 좌표에 맞춰 찍는다."""
    Vw = np.asarray(truth.vertices, np.float64)
    F = np.asarray(truth.faces, np.int64)
    y = Vw[:, 1]
    if view == "side":
        return np.ones((W.RES, W.RES), np.float32)           # side 는 이진 그대로 둔다
    sx = +1.0 if view == "front" else float(BACK)
    py, px = W.topix(sx * Vw[:, 0], Vw[:, 2])
    P = np.stack([px, py], 1).astype(np.int32)[F]
    yf = y[F].mean(1)
    img = np.full((W.RES, W.RES), np.nan, np.float32)
    order = np.argsort(y[F].max(1))[::-1] if view == "front" else np.argsort(y[F].min(1))
    for i in order:                                          # 먼 것부터 -> 가까운 것이 남는다
        cv2.fillConvexPoly(img, P[i], float(yf[i]))
    m = ~np.isnan(img)
    if not m.any():
        return np.ones((W.RES, W.RES), np.float32)
    # **앞뒤를 물건의 y 범위 하나로** 정규화한다. 시점마다 따로 하면 평평한 뒷면이
    # lo==hi 라 0 (= 전부 깎아라)이 된다 — 자가검사가 이걸 잡았다
    lo, hi = float(y.min()), float(y.max())
    prot = (hi - img) if view == "front" else (img - lo)     # 튀어나온 쪽이 크다
    h = np.where(m, prot / max(hi - lo, 1e-9), 1.0)          # 모르는 곳은 1 = 안 깎는다
    return np.clip(h, 0, 1).astype(np.float32)


def build(case, truth, lam, which):
    """`대조.build` 와 같은 순서. `which` 로 깊이맵만 갈아끼운다."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        dep = H.load_depth(v, d, case=case) if which == "파이프" else oracle_depth(truth, v)
        masks[v], deps[v] = H.to_win(d, dep)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    plain, axes = H.carve(masks, back_sign=bs)
    deep, _ = H.carve_depth(masks, deps, lam=lam, back_sign=bs)
    return plain, deep, axes


def selfcheck():
    """**오라클이 진짜 깊이인지 먼저 본다.** 안 맞으면 아래 숫자가 전부 헛것이다."""
    big = trimesh.creation.box((0.6, 0.4, 1.0))
    bump = trimesh.creation.box((0.2, 0.2, 0.3))
    bump.apply_translation([0, -0.30, 0])                    # **앞(-y)** 으로 튀어나옴
    m = trimesh.util.concatenate([big, bump])
    m.vertices = W.normalize(np.asarray(m.vertices, np.float64))
    hf, hb = oracle_depth(m, "front"), oracle_depth(m, "back")
    at = lambda h, u, z: float(h[tuple(int(v[0]) for v in W.topix(np.array([u]), np.array([z])))])
    # y 범위는 [-0.3, 0.3] (혹 -0.3 · 몸통 앞 -0.1 · 뒤 +0.3) -> **답을 손으로 안다**
    mid, side = at(hf, 0.0, 0.5), at(hf, 0.25, 0.5)
    assert abs(mid - 1.0) < 0.02, "앞: 튀어나온 자리가 1 이 아니다 (%.3f)" % mid
    assert abs(side - 2 / 3) < 0.03, "앞: 몸통이 2/3 이 아니다 (%.3f)" % side
    bmid, bside = at(hb, 0.0, 0.5), at(hb, 0.25 * BACK, 0.5)
    assert abs(bmid - 1.0) < 0.02 and abs(bside - 1.0) < 0.02,         "뒤: 평평한 뒷면인데 1 이 아니다 (%.3f · %.3f)" % (bmid, bside)
    print("  자가검사 통과 — 앞 튀어나온 곳 %.3f · 몸통 %.3f · 뒤(평평) %.3f/%.3f"
          % (mid, side, bmid, bside))


def run(cases, lams=LAMS):
    rows = []
    print("  %-22s %7s %7s %7s | %s" % ("케이스", "이진", "파이프", "균일",
                                        " ".join("오라클%.2f" % l for l in lams)))
    for case in cases:
        tp = os.path.join(OUT, "시트", case, "truth.glb")
        if not os.path.exists(tp):
            print("  %-22s 정답 메시가 없다 — 건너뜀" % case[:22]); continue
        t0 = time.time()
        truth = trimesh.load(tp, force="mesh")
        T, ot = J.grid(truth)

        def iou(vox, axes):
            G, og = J.grid(C.to_mesh(vox, axes))
            A, B = J.common(T, ot, G, og)
            return float((A & B).sum() / max((A | B).sum(), 1))

        plain, pipe, axes = build(case, truth, H.LAM, "파이프")
        r = {"case": case, "이진": iou(plain, axes), "파이프": iou(pipe, axes)}
        # 대조군 — **파이프 판본과 같은 부피**까지 균일 침식. 정보를 0 만큼 쓴다
        even, k = plain.copy(), 0
        while even.sum() > pipe.sum() and k < 40:
            even = ndimage.binary_erosion(even); k += 1
        r["균일"] = iou(even, axes)
        for l in lams:
            _, orc, _ = build(case, truth, l, "오라클")
            r["오라클%.2f" % l] = iou(orc, axes)
        r["초"] = round(time.time() - t0, 1)
        rows.append(r)
        print("  %-22s %7.4f %7.4f %7.4f | %s" % (case[:22], r["이진"], r["파이프"], r["균일"],
              " ".join("%9.4f" % r["오라클%.2f" % l] for l in lams)), flush=True)
    return rows


def report(rows, lams=LAMS):
    if not rows:
        return
    g = lambda k: np.array([r[k] for r in rows])
    n = len(rows)
    print("\n  %d 장 · 균일 침식 대비 (대조군을 이겨야 「좋아졌다」)" % n)
    print("    %-12s %+.4f  (%d/%d 승)" % ("파이프 깊이", (g("파이프") - g("균일")).mean(),
                                           (g("파이프") > g("균일")).sum(), n))
    best = None
    for l in lams:
        k = "오라클%.2f" % l
        d = (g(k) - g("균일")).mean()
        print("    %-12s %+.4f  (%d/%d 승)" % ("오라클 lam%.2f" % l, d, (g(k) > g("균일")).sum(), n))
        if best is None or d > best[1]:
            best = (k, d)
    print("\n  깊이맵이 약한가, 규칙이 약한가")
    print("    파이프 깊이 -> 오라클 (%s) 로 갈아끼우면  %+.4f" % (best[0], (g(best[0]) - g("파이프")).mean()))
    if best[1] > 0.005:
        print("    -> **깊이맵이 약한 것이다.** 규칙은 진짜 깊이를 주면 대조군을 이긴다")
    else:
        print("    -> **규칙이 약한 것이다.** 진짜 깊이를 줘도 균일 침식을 못 이긴다 —")
        print("       앞뒤(y)만 움직이는 게 한계다. 단면을 직사각형에서 벗어나게 해야 한다")
    p = os.path.join(OUT, "기록", "오라클_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "LAM": H.LAM, "lams": list(lams),
               "rows": rows}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def main():
    H.register_sheets()
    selfcheck()
    what = sys.argv[1] if len(sys.argv) > 1 else "도형"
    if what == "도형":
        import 도형 as SH
        cases = ["도형_" + n for n, *_ in SH.FORMS]
    else:
        b = json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]
        cases = [c["name"] for c in b][:int(sys.argv[2]) if len(sys.argv) > 2 else 8]
    print("  %s %d 장 · lam %s\n" % (what, len(cases), LAMS))
    report(run(cases))


if __name__ == "__main__":
    main()
