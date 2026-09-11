# -*- coding: utf-8 -*-
"""**깊이맵의 천장.** 정답 메시에서 진짜 깊이를 뽑아 *같은 깎기 규칙*에 넣는다.

    python 오라클.py 도형          기본도형 11개
    python 오라클.py 벤치 [n]      실물 벤치 앞에서 n 장 (기본 8)
        -> out/기록/오라클_<날짜>.json
    python 오라클.py 그림          도형 11개를 모양으로 — 판본들의 단면
        -> out/오라클단면.png

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

## 오라클을 원화만으로 추정한다 — 타원 (2026-09-11)

오라클은 정답을 보고 푼 점수라 의뢰에는 못 쓴다. `ellipse_depths` 는 **hull 만 보고**
같은 규약의 깊이맵을 만든다 — 높이마다 hull 단면(직사각형들)에 타원을 내접시키고 그 앞·뒤
표면을 잰다. 새 정보는 없고 **「단면은 둥글다」는 가정 하나**를 넣는다. 원기둥·원뿔·구는
이론상 오라클과 같고, 상자는 틀리게 되어 있다. 채점은 둘 — 3D IoU, 그리고 깊이맵 자체가
오라클과 얼마나 닮았나(`map_corr`, 깎기가 실제로 읽는 값에서).
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


def ellipse_depths(plain, axes, back_sign):
    """hull 만 보고 **오라클을 추정한다** — 높이마다 단면에 타원을 내접시킨다.

    이진 hull 의 단면은 높이마다 축정렬 직사각형 몇 개다 (x구간 × y구간). 그 안에 내접
    타원을 넣고, 그 앞·뒤 표면으로 `oracle_depth` 와 **같은 규약**의 깊이를 만든다.
    정답을 안 본다. 대신 **「단면은 둥글다」는 가정 하나**를 넣는다.

    `carve_depth` 는 깊이를 **복셀 중심 화소에서만** 읽으므로 그 화소에만 찍는다. 나머지는
    1 (= 안 깎는다) 이라, 자가검사도 복셀 중심에서 읽어야 헛통과가 안 난다."""
    u, _, z = axes
    n = len(u)
    I, Jg = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    E = np.zeros_like(plain)
    for k in range(plain.shape[2]):
        lab, _ = ndimage.label(plain[:, :, k])
        for idx, s in enumerate(ndimage.find_objects(lab), 1):
            a, b = (s[0].stop - s[0].start) / 2, (s[1].stop - s[1].start) / 2
            ic, jc = s[0].start + a - 0.5, s[1].start + b - 0.5
            E[s[0], s[1], k] |= ((((I[s] - ic) / a) ** 2 + ((Jg[s] - jc) / b) ** 2) <= 1) & (lab[s] == idx)
    j = np.arange(n)[None, :, None]
    jf, jb = np.where(E, j, n).min(1), np.where(E, j, -1).max(1)  # (x, z) 앞면·뒷면 칸
    has = jf < n
    out = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    if not has.any():
        return out
    ys = np.nonzero(E.any((0, 2)))[0]
    lo, hi = u[ys.min()], u[ys.max()]                    # **물건의 y 범위 하나로** — oracle 과 같다
    span = max(hi - lo, 1e-9)
    hf = np.where(has, (hi - u[np.clip(jf, 0, n - 1)]) / span, 1.0)
    hb = np.where(has, (u[np.clip(jb, 0, n - 1)] - lo) / span, 1.0)
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    for v, h in (("front", hf), ("back", hb)):
        py, px = W.topix((back_sign if v == "back" else W.VIEW_AXIS[v][1]) * X2, Z2)
        out[v][py, px] = np.clip(h, 0, 1)
    return out


def build(case, truth, lam, which):
    """`대조.build` 와 같은 순서. `which` 로 깊이맵만 갈아끼운다 -> (이진, 깎은 것, 축, 깊이맵)."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        dep = (H.load_depth(v, d, case=case) if which == "파이프" else
               oracle_depth(truth, v) if which == "오라클" else
               np.ones(d.shape, np.float32))                 # 타원은 정렬 뒤 hull 에서 만든다
        masks[v], deps[v] = H.to_win(d, dep)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    plain, axes = H.carve(masks, back_sign=bs)
    if which == "타원":
        deps = ellipse_depths(plain, axes, bs)
    deep, _ = H.carve_depth(masks, deps, lam=lam, back_sign=bs)
    return plain, deep, axes, deps


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

    # **타원 추정.** 반지름 0.3 원기둥의 hull(정사각 기둥)을 주면 원의 앞면이 나와야 한다.
    # 원의 앞면 y = -0.3·√(1-(x/0.3)²) -> 튀어나옴 (1+√(1-(x/0.3)²))/2. 가운데 1.0 · x=0.26 이면 0.75
    n = H.N
    u = W.U0 + (np.arange(n) + 0.5) / n * (W.U1 - W.U0)
    zz = W.Z0 + (np.arange(n) + 0.5) / n * (W.Z1 - W.Z0)
    X, Y, Z = np.meshgrid(u, u, zz, indexing="ij")
    e = ellipse_depths((np.abs(X) < 0.3) & (np.abs(Y) < 0.3) & (Z > 0.2) & (Z < 0.8), (u, u, zz), BACK)
    # **x 도 z 도 복셀 중심에서 읽는다** — docstring 참조. z=0.5 를 그대로 읽었다가 안 찍힌
    # 화소(기본값 1)를 읽어 가장자리가 1.000 으로 나왔다 (2026-09-11)
    vox = lambda x: u[np.argmin(np.abs(u - x))]
    vz = zz[np.argmin(np.abs(zz - 0.5))]
    want = lambda x: (1 + np.sqrt(1 - (vox(x) / 0.3) ** 2)) / 2
    ec, ee, eb = at(e["front"], vox(0.0), vz), at(e["front"], vox(0.26), vz), at(e["back"], BACK * vox(0.26), vz)
    assert abs(ec - want(0.0)) < 0.03 and abs(ee - want(0.26)) < 0.03 and abs(eb - want(0.26)) < 0.03, \
        "타원: 원기둥의 앞면이 원이 아니다 (가운데 %.3f/%.3f · 옆 %.3f/%.3f · 뒤 %.3f)" \
        % (ec, want(0.0), ee, want(0.26), eb)
    print("  자가검사 통과 — 앞 튀어나온 곳 %.3f · 몸통 %.3f · 뒤(평평) %.3f/%.3f · 타원 %.3f/%.3f (답 %.3f)"
          % (mid, side, bmid, bside, ec, ee, want(0.26)))


def versions(case, truth, lams=LAMS):
    """판본 전부의 복셀과 깊이맵. `run` 과 `figure` 가 **같은 것**을 본다."""
    plain, pipe, axes, dp = build(case, truth, H.LAM, "파이프")
    # 대조군 — **파이프 판본과 같은 부피**까지 hull 을 매끈하게 안으로 민 면 (`hull.even_control`).
    # 칸 판이 아니라 메시다 — 한 겹씩 벗기던 예전 규약은 부피가 안 맞았다 (2026-09-11).
    # 단면 그림은 metadata 의 수준 t 로 칸 판을 다시 만든다 (`figure`)
    even, t = H.even_control(plain, axes, C.to_mesh(pipe, axes).volume)
    even.metadata["t"] = t
    V, D = {"이진": plain, "파이프": pipe, "균일": even}, {"파이프": dp}
    for which in ("오라클", "타원"):
        for l in lams:
            _, V["%s%.2f" % (which, l)], _, D[which] = build(case, truth, l, which)
    return V, axes, D


def map_corr(D, plain, axes, back_sign, v="front"):
    """깊이맵이 오라클과 얼마나 닮았나 — **깎기가 실제로 읽는 값**에서 잰다.

    `carve_depth` 처럼 복셀 중심에서 읽고 높이마다 max=1 로 나눈 뒤 상관을 본다.
    오라클이 평평하면(상자) 상관이 정의되지 않아 nan 이다."""
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix((back_sign if v == "back" else W.VIEW_AXIS[v][1]) * X2, Z2)
    on = plain.any(1)

    def norm(h):
        return (h / np.maximum(np.where(on, h, 0.0).max(0, keepdims=True), 1e-6))[on]
    ref = norm(D["오라클"][v][py, px])
    out = {}
    for k in ("파이프", "타원"):
        a = norm(D[k][v][py, px])
        ok = a.std() > 1e-9 and ref.std() > 1e-9
        out["상관_" + k] = float(np.corrcoef(a, ref)[0, 1]) if ok else float("nan")
    return out


def _iou_fn(truth, pitch=None):
    """정답 격자를 한 번 굽고 판본마다 IoU. `pitch` 를 주면 그 격자로 — 결론은 격자 둘로 낸다 (22% 흔들린다)."""
    p = pitch or J.PITCH
    T, ot = J.grid(truth, p)

    def iou(vox, axes):
        # 대조군은 메시로 온다 (`versions`) — 칸 판이면 메시로 바꾼다
        G, og = J.grid(vox if isinstance(vox, trimesh.Trimesh) else C.to_mesh(vox, axes), p)
        A, B = J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))
    return iou


RUN_TAG = "알파판·제부피대조·격자2·깨짐 (2026-09-11)"   # 진행 파일의 줄이 이 규약으로 잰 것인지


def run(cases, lams=LAMS, prog=None):
    """판본마다 IoU (격자 128 · 192) · **제 부피 대조군** · 깨짐 셋. `prog` 를 주면 케이스마다 적고 이어 돈다.

    대조군을 판본마다 그 판본 부피로 맞춘다 (`균일@<판본>`). 파이프 부피 하나에 맞춘 대조군(`균일`)과
    lam 0.50 판본을 대면 **많이 깎은 것만으로** 유리하다 — hull 은 뚱뚱해서 아무렇게나 깎아도 IoU 가
    오른다 (2026-09-11). 부피 곡선은 케이스당 한 번만 그린다 (`hull.even_control` 의 cache)."""
    import 표면 as SF
    rows = []
    if prog and os.path.exists(prog):
        rows = [r for r in map(json.loads, open(prog, encoding="utf-8")) if r.get("판") == RUN_TAG]
        if rows:
            print("  이어서 한다 — 이미 %d 장 (%s)" % (len(rows), os.path.relpath(prog, HERE)))
    done = {r["case"] for r in rows}
    P192 = (W.U1 - W.U0) / 192.0
    print("  %-22s %7s %7s %7s | %s | %s | 상관 파이프·타원" % ("케이스", "이진", "파이프", "균일",
          " ".join("오라클%.2f" % l for l in lams), " ".join("타원%.2f" % l for l in lams)))
    for case in cases:
        if case in done:
            continue
        tp = os.path.join(OUT, "시트", case, "truth.glb")
        if not os.path.exists(tp):
            print("  %-22s 정답 메시가 없다 — 건너뜀" % case[:22]); continue
        t0 = time.time()
        truth = trimesh.load(tp, force="mesh")
        iou, iou2 = _iou_fn(truth), _iou_fn(truth, P192)
        V, axes, D = versions(case, truth, lams)
        plain = V["이진"]
        M = {k: v if isinstance(v, trimesh.Trimesh) else C.to_mesh(v, axes) for k, v in V.items()}
        r = {"case": case, **{k: iou(m, axes) for k, m in M.items()}}     # 128 은 예전 칸 이름 그대로
        r.update({k + "·192": iou2(m, axes) for k, m in M.items()})
        cache = {}
        for k, m in M.items():
            if k in ("이진", "균일"):
                continue
            em, _ = H.even_control(plain, axes, m.volume, cache=cache)
            r["균일@" + k], r["균일@%s·192" % k] = iou(em, axes), iou2(em, axes)
            r["찢김_" + k], r["조각_" + k] = SF.tear(V[k]), SF.pieces(V[k])
            r["실루엣_" + k] = SF.sil_loss(V[k], plain)
        r.update(map_corr(D, plain, axes, H.CASES[case]["back_sign"]))
        r["초"], r["판"] = round(time.time() - t0, 1), RUN_TAG
        rows.append(r)
        if prog:
            with open(prog, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-22s %7.4f %7.4f %7.4f | %s | %s | %6.3f %6.3f" % (
              case[:22], r["이진"], r["파이프"], r["균일"],
              " ".join("%9.4f" % r["오라클%.2f" % l] for l in lams),
              " ".join("%8.4f" % r["타원%.2f" % l] for l in lams),
              r["상관_파이프"], r["상관_타원"]), flush=True)
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
    print("\n  오라클을 원화만으로 추정 — 타원 단면 (정답을 안 본다)")
    for l in lams:
        k = "타원%.2f" % l
        print("    %-12s %+.4f  (%d/%d 승)  · 같은 lam 오라클과 %+.4f · 파이프와 %+.4f" % (
              "타원 lam%.2f" % l, (g(k) - g("균일")).mean(), (g(k) > g("균일")).sum(), n,
              (g(k) - g("오라클%.2f" % l)).mean(), (g(k) - g("파이프")).mean()))
    print("    깊이맵 상관 (오라클과 · 앞면 · 중앙)  파이프 %.3f · 타원 %.3f  (nan 빼고 %d 장)" % (
          np.nanmedian(g("상관_파이프")), np.nanmedian(g("상관_타원")),
          int(np.isfinite(g("상관_타원")).sum())))
    # **판정 — 판본마다 제 부피 대조군 · 격자 둘 다** 평균 > 0 이고 과반 승이어야 「통과」 (돌리기 전 기준)
    print("\n  판정 · 판본마다 제 부피 대조군 (격자128 · 격자192) · 깨짐 셋 (중앙 / 최악)")
    verdicts = {}
    for c in [k for k in rows[0] if k.startswith("균일@") and not k.endswith("·192")]:
        k = c[3:]
        a = [g(k) - g(c), g(k + "·192") - g(c + "·192")]
        ok = [v.mean() > 0 and (v > 0).sum() > n / 2 for v in a]
        verdicts[k] = "통과" if all(ok) else ("격자가 갈림" if any(ok) else "짐")
        print("    %-10s %+.4f (%2d/%d) · %+.4f (%2d/%d)  %-6s 찢김 %4.1f%%/%4.1f%% · 조각 %.0f/%d · 실루엣 손실 %.2f%%/%.2f%%"
              % (k, a[0].mean(), (a[0] > 0).sum(), n, a[1].mean(), (a[1] > 0).sum(), n, verdicts[k],
                 100 * np.median(g("찢김_" + k)), 100 * g("찢김_" + k).max(), np.median(g("조각_" + k)),
                 g("조각_" + k).max(), 100 * np.median(g("실루엣_" + k)), 100 * g("실루엣_" + k).max()))
    p = os.path.join(OUT, "기록", "오라클_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "LAM": H.LAM, "lams": list(lams), "판": RUN_TAG,
               "판정": verdicts, "rows": rows}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases, lams=(0.20, 0.50)):
    """**오라클을 모양으로 본다.** 숫자로만 있던 「진짜 깊이를 주면 이긴다」를 단면으로.

    물건 높이 50% 에서 자른 단면. 검정 선 = 정답, 칠 = 그 판본, 아래가 앞(-y).
    타원(원화만)과 오라클(정답)을 **같은 lam 끼리 나란히** 둔다 — 둘은 깊이맵만 다르다."""
    from PIL import Image, ImageDraw
    from 계획 import _font
    cols = [("이진", (205, 205, 205)), ("균일", (244, 196, 130)), ("파이프", (150, 185, 235))]
    for l in lams:
        cols += [("타원%.2f" % l, (196, 168, 232)), ("오라클%.2f" % l, (140, 210, 160))]
    S, G, LW, TOP, RH = 180, 14, 150, 120, 222
    im = Image.new("RGB", (LW + len(cols) * (S + G) + G, TOP + len(cases) * RH + 50), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((24, 18), "오라클 단면 — 진짜 깊이 vs 원화만으로 추정한 깊이(타원)", fill=(20, 20, 20), font=f1)
    d.text((24, 56), "물건 높이 50% 단면 · 검정 선 = 정답 · 칠 = 그 판본 · 아래가 앞(-y) · "
                     "칸 아래 = 3D IoU (괄호는 균일 대비)", fill=(90, 90, 90), font=f3)
    d.text((24, 76), "타원 = hull 단면에 타원을 내접시킨 깊이맵 (정답 안 봄) · 오라클 = 정답에서 잰 깊이맵. "
                     "같은 lam 끼리 나란히 — 둘은 깊이맵만 다르다", fill=(90, 90, 90), font=f3)
    for j, (name, _) in enumerate(cols):
        d.text((LW + G + j * (S + G), TOP - 24), name, fill=(40, 40, 40), font=f2)
    scores = []
    for r, case in enumerate(cases):
        truth = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
        iou = _iou_fn(truth)
        V, axes, _ = versions(case, truth, lams)
        u, _, z = axes
        du = u[1] - u[0]
        z0, z1 = truth.bounds[:, 2]
        k = int(np.argmin(np.abs(z - (z0 + 0.5 * (z1 - z0)))))
        sec = truth.section(plane_origin=[0, 0, z[k]], plane_normal=[0, 0, 1])
        ii, jj = np.nonzero(V["이진"][:, :, k])
        xs, ys = [u[ii.min()], u[ii.max()]], [u[jj.min()], u[jj.max()]]
        if sec is not None:
            (tx0, ty0, _), (tx1, ty1, _) = sec.bounds
            # **좌표가 맞나.** hull 은 정답을 덮으니 정답 단면은 이진 단면의 상자 안에 있어야
            # 한다. y 가 뒤집히면 L자·두기둥대각 같은 비대칭 도형에서 여기 걸린다
            assert (tx0 > xs[0] - 3 * du and tx1 < xs[1] + 3 * du
                    and ty0 > ys[0] - 3 * du and ty1 < ys[1] + 3 * du), \
                "%s: 정답 단면이 hull 밖이다 — 좌표가 어긋났다" % case
        cx, cy = sum(xs) / 2, sum(ys) / 2
        span = max(xs[1] - xs[0], ys[1] - ys[0]) * 1.15 + 4 * du
        p = (np.arange(S) + 0.5) / S - 0.5
        ix = np.round((cx + p * span - u[0]) / du).astype(int)
        iy = np.round((cy - p * span - u[0]) / du).astype(int)   # 행이 내려갈수록 y 가 작다 = 앞
        ok = ((ix >= 0) & (ix < len(u)))[None, :] & ((iy >= 0) & (iy < len(u)))[:, None]
        ix, iy = np.clip(ix, 0, len(u) - 1), np.clip(iy, 0, len(u) - 1)
        row = {n: iou(v, axes) for n, v in V.items()}
        scores.append(row)
        # 대조군은 메시다 — 단면은 같은 수준 t 로 hull 장에서 칸 판을 다시 만든다
        vv = {n: (H.sdf_of(V["이진"]) > v.metadata["t"]) if isinstance(v, trimesh.Trimesh) else v
              for n, v in V.items()}
        y0 = TOP + r * RH
        d.text((24, y0 + 70), case.replace("도형_", ""), fill=(20, 20, 20), font=f2)
        for j, (name, col) in enumerate(cols):
            tile = np.full((S, S, 3), 250, np.uint8)
            tile[vv[name][:, :, k][ix[None, :], iy[:, None]] & ok] = col
            x0 = LW + G + j * (S + G)
            im.paste(Image.fromarray(tile), (x0, y0))
            d.rectangle([x0, y0, x0 + S - 1, y0 + S - 1], outline=(215, 215, 215))
            for L in (sec.discrete if sec is not None else []):
                d.line([(x0 + ((x - cx) / span + 0.5) * S, y0 + (0.5 - (y - cy) / span) * S)
                        for x, y, _ in L], fill=(15, 15, 15), width=2)
            dv = row[name] - row["균일"]
            txt = "%.4f" % row[name] + ("" if name == "균일" else "  (%+.4f)" % dv)
            d.text((x0, y0 + S + 4), txt, font=f3,
                   fill=(40, 40, 40) if name == "균일" else (30, 130, 70) if dv > 0 else (190, 60, 40))
        print("  %-14s 단면 z=%.3f" % (case, z[k]), flush=True)
    g = lambda n: np.array([s[n] for s in scores])
    d.text((24, TOP + len(cases) * RH + 10), "균일 대비 평균 · " + "   ".join(
        "%s %+.4f (%d/%d 승)" % (n, (g(n) - g("균일")).mean(), (g(n) > g("균일")).sum(), len(scores))
        for n, _ in cols if n not in ("이진", "균일")), fill=(20, 20, 20), font=f2)
    im.save(os.path.join(OUT, "오라클단면.png"))
    print("  -> out/오라클단면.png")


def main():
    H.register_sheets()
    selfcheck()
    what = sys.argv[1] if len(sys.argv) > 1 else "도형"
    if what in ("도형", "그림"):
        import 도형 as SH
        cases = ["도형_" + n for n, *_ in SH.FORMS]
    else:
        b = json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]
        cases = [c["name"] for c in b][:int(sys.argv[2]) if len(sys.argv) > 2 else 8]
    if what == "그림":
        figure(cases)
        return
    print("  %s %d 장 · lam %s\n" % (what, len(cases), LAMS))
    # 케이스마다 적고 이어 돈다 — 이 PC 에선 긴 실행이 메모리 부족으로 자주 정리된다 (2026-09-11)
    prog = os.path.join(OUT, "기록", "오라클_%s_진행.jsonl" % what)
    os.makedirs(os.path.dirname(prog), exist_ok=True)
    rows = run(cases, prog=prog)
    report(rows)
    todo = [c for c in cases if os.path.exists(os.path.join(OUT, "시트", c, "truth.glb"))]
    if {r["case"] for r in rows} >= set(todo) and os.path.exists(prog):
        os.remove(prog)                      # 다 끝났으면 치운다 — 결과는 위 기록 json 에 남았다


if __name__ == "__main__":
    main()
