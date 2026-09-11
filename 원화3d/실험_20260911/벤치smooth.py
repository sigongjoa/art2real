# -*- coding: utf-8 -*-
"""실물 벤치 · **스무딩 σ 0 · 2** · 대조군도 같은 σ · 찢김 · 조각 · 실루엣 손실.

    python 벤치smooth.py <out.jsonl> [n] [초 예산]

판본 장 f = 부호거리장 (`hull.sdf_of`). 스무딩 = min(가우시안(f, σ), hull 장) — hull 밖으로 못
부푼다 (`hull.smooth_field`). 메시는 장의 수준 0 에서 바로 뽑는다 (`hull.mesh_from_field`).
대조군 장 = hull 장 − t (판본의 σ0 메시 부피가 되는 t) 에 **같은 σ**.

σ0 은 `오라클_벤치lam4` 와 같은 계산이다 (수준 0 면 = 불 0.5 면, 대조군 = 수준 t 면). 그래서 σ0
숫자가 lam4 를 재현해야 한다 — 그게 이 드라이버의 대조 점검이다.
케이스마다 한 줄씩 바로 적고 이어 돈다. 예산(초)을 넘기면 새 케이스를 안 잡는다."""
import gc
import json
import os
import sys
import time

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np
import psutil
import trimesh
from scipy import ndimage
import 오라클 as O

H = O.H
P = psutil.Process()
PITCH = {"128": O.J.PITCH, "192": (O.W.U1 - O.W.U0) / 192.0}
VERS = [("파이프", 0.20), ("파이프", 0.50), ("타원", 0.50), ("오라클", 0.50)]
SIG = (0, 2)


def mesh(f, axes, process=True):
    V, F = H.mesh_from_field(f, axes)
    m = trimesh.Trimesh(V, F, process=process)
    if m.volume < 0:
        m.invert()
    return m


def tear(v):
    """앞면이 위아래 이웃 줄끼리 3칸 넘게 튄 쌍의 비율 (`깨짐.py` 와 같은 정의)."""
    n = v.shape[1]
    jf = np.where(v, np.arange(n)[None, :, None], n).min(1).astype(float)
    jf[jf >= n] = np.nan
    dz = np.abs(np.diff(jf, axis=1))
    dz = dz[np.isfinite(dz)]
    return float((dz > 3).mean()) if dz.size else 0.0


def pieces(v):
    lab, _ = ndimage.label(v, structure=np.ones((3, 3, 3)))
    s = np.bincount(lab.ravel())[1:]
    return int((s >= 50).sum())


def sil_loss(v, plain):
    """hull 의 정면·측면 실루엣 중 잃은 비율 — 큰 쪽. 흐리면 뿔·손가락이 사라질 수 있다."""
    out = []
    for ax in (1, 0):                                   # 1 = 정면 (x, z) · 0 = 측면 (y, z)
        a = plain.any(ax)
        out.append(float((a & ~v.any(ax)).sum() / max(a.sum(), 1)))
    return max(out)


def main():
    out = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
    O.H.register_sheets()
    O.selfcheck()
    cases = [c["name"] for c in json.load(open("벤치.json", encoding="utf-8"))["cases"]][:n]
    done = {json.loads(l)["case"] for l in open(out, encoding="utf-8")} if os.path.exists(out) else set()
    print("  %d 장 · 이미 %d" % (len(cases), len(done & set(cases))), flush=True)
    T0 = time.time()
    for case in cases:
        if case in done:
            continue
        if time.time() - T0 > budget:
            print("  예산 %.0f초를 넘겼다 — 다시 돌리면 이어서 한다" % budget, flush=True)
            break
        tp = os.path.join(O.OUT, "시트", case, "truth.glb")
        if not os.path.exists(tp):
            print("  %-24s 정답 메시가 없다 — 건너뜀" % case[:24], flush=True)
            continue
        t0 = time.time()
        truth = trimesh.load(tp, force="mesh")
        TG = {g: O.J.grid(truth, p) for g, p in PITCH.items()}
        plain, vox = None, {}
        for which, l in VERS:
            pl, v, axes, _ = O.build(case, truth, l, which)
            plain = pl if plain is None else plain
            vox["%s%.2f" % (which, l)] = v
        keep = H.sdf_of(plain)
        vh = mesh(keep, axes).volume
        r = {"case": case, "128": {}, "192": {}, "부피": {}, "찢김": {}, "조각": {}, "실루엣": {}, "t": {}}

        def put(name, f):
            m = mesh(f, axes)
            for g, p in PITCH.items():
                T, ot = TG[g]
                G, og = O.J.grid(m, p)
                A, B = O.J.common(T, ot, G, og)
                r[g][name] = float((A & B).sum() / max((A | B).sum(), 1))
            v = f > 0
            r["부피"][name] = round(float(m.volume / vh), 4)
            r["찢김"][name] = round(tear(v), 4)
            r["조각"][name] = pieces(v)
            r["실루엣"][name] = round(sil_loss(v, plain), 4)

        for s in SIG:
            put("이진σ%d" % s, H.smooth_field(keep, keep, s))
        # 대조군의 수준 t — hull 장의 부피 곡선 (lam4 와 같은 규칙)
        fv = {k: H.sdf_of(v) for k, v in vox.items()}
        rv = {k: mesh(f, axes, False).volume / vh for k, f in fv.items()}
        ts, vs = [0.0], [1.0]
        while vs[-1] > min(rv.values()) and ts[-1] < 12:
            ts.append(ts[-1] + 0.25)
            vs.append(mesh(keep - ts[-1], axes, False).volume / vh)
        for k, f in fv.items():
            t = float(np.interp(rv[k], vs[::-1], ts[::-1]))
            r["t"][k] = round(t, 3)
            for s in SIG:
                put("%sσ%d" % (k, s), H.smooth_field(f, keep, s))
                put("균일@%sσ%d" % (k, s), H.smooth_field(keep - t, keep, s))
            got = r["부피"]["균일@%sσ0" % k]
            assert abs(got - rv[k]) < 0.02, "%s %s: 대조군 부피 %.4f 가 목표 %.4f 와 안 맞는다" % (case, k, got, rv[k])
        del vox, fv, keep
        gc.collect()
        r["초"] = round(time.time() - t0, 1)
        mi = P.memory_info()
        r["최대GB"] = round(mi.peak_wset / 2 ** 30, 2)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        d = lambda k, s: r["128"]["%sσ%d" % (k, s)] - r["128"]["균일@%sσ%d" % (k, s)]
        print("  %-24s 대조 대비(128) 파이프.20 σ0 %+.4f σ2 %+.4f · 오라클.50 σ0 %+.4f σ2 %+.4f"
              " | 오라클 찢김 %.0f%%->%.0f%% | %.0f초 최대 %.2fGB" % (
              case[:24], d("파이프0.20", 0), d("파이프0.20", 2), d("오라클0.50", 0), d("오라클0.50", 2),
              100 * r["찢김"]["오라클0.50σ0"], 100 * r["찢김"]["오라클0.50σ2"], r["초"], r["최대GB"]), flush=True)


if __name__ == "__main__":
    main()
