# -*- coding: utf-8 -*-
"""실물 벤치 · lam 0.20 vs 0.50 · **대조군을 판본마다 제 부피로, 매끈하게.**

    python 벤치lam.py <out.jsonl> [n]

균일 침식은 「같은 부피만큼 정보 없이 깎으면」이다. 대조군을 세 번 고쳤다 (2026-09-11):

    옛 (저장소)   한 겹씩 벗겨 목표 이하 첫 겹 (`대조.py:270` · `오라클.py:201`).
                 한 겹에 부피가 20% 넘게 빠져 **부피가 안 맞는다** (avatarsample_d 1겹 0.768)
    칸 단위       같은 거리 칸을 무작위로 — 점박이 표면이 측정에 안 잡혀 칸 0.863 이 측정 0.974.
                 **너무 약하다**
    겹 보간       통째로 벗긴 겹 사이를 부피로 선형 보간 — IoU 곡선이 위로 볼록이라
                 **최대 0.026 과소평가** (`선형검사.py`)
    지금          부호거리장 sdf = EDT(안) - EDT(밖) 을 마칭큐브로 **수준 t 에서** 자른다.
                 매끈하고, 부피를 연속으로 맞출 수 있다. t 는 부피 곡선(0.25 간격)에서 찾는다

옛 대조군(`균일층@`)도 같이 적는다 — 저장소의 결론이 얼마나 움직이나 보려고.
케이스마다 한 줄씩 바로 적고, 이미 적힌 케이스는 건너뛴다 (메모리 정리 대비)."""
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
from skimage import measure
import 오라클 as O

P = psutil.Process()
PITCH = {"128": O.J.PITCH, "192": (O.W.U1 - O.W.U0) / 192.0}
VERS = [("파이프", 0.20), ("파이프", 0.50), ("타원", 0.20), ("타원", 0.50), ("오라클", 0.20), ("오라클", 0.50)]
DT = 0.25                                            # 부피 곡선의 수준 간격 (칸)


def sdf_mesh(sdf, axes, t, process=True):
    """수준 t 의 면. t=0 은 `hull.mesh_from`(불 0.5)과 같은 면이다."""
    p = np.pad(sdf, 1, constant_values=-1.0)
    V, F, _, _ = measure.marching_cubes(p, t)
    ux, uy, uz = axes
    s = [a[1] - a[0] for a in axes]
    V = np.stack([ux[0] + (V[:, 0] - 1) * s[0], uy[0] + (V[:, 1] - 1) * s[1], uz[0] + (V[:, 2] - 1) * s[2]], 1)
    m = trimesh.Trimesh(V, F, process=process)
    if m.volume < 0:
        m.invert()
    return m


def main():
    out = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    O.H.register_sheets()
    O.selfcheck()
    cases = [c["name"] for c in json.load(open("벤치.json", encoding="utf-8"))["cases"]][:n]
    done = {json.loads(l)["case"] for l in open(out, encoding="utf-8")} if os.path.exists(out) else set()
    print("  %d 장 · 이미 %d" % (len(cases), len(done & set(cases))), flush=True)
    for case in cases:
        if case in done:
            continue
        tp = os.path.join(O.OUT, "시트", case, "truth.glb")
        if not os.path.exists(tp):
            print("  %-24s 정답 메시가 없다 — 건너뜀" % case[:24], flush=True)
            continue
        t0 = time.time()
        truth = trimesh.load(tp, force="mesh")
        TG = {g: O.J.grid(truth, p) for g, p in PITCH.items()}

        def iou_m(m):
            res = {}
            for g, p in PITCH.items():
                T, ot = TG[g]
                G, og = O.J.grid(m, p)
                A, B = O.J.common(T, ot, G, og)
                res[g] = float((A & B).sum() / max((A | B).sum(), 1))
            return res

        plain, vox = None, {}
        for which, l in VERS:
            pl, v, axes, _ = O.build(case, truth, l, which)
            plain = pl if plain is None else plain
            vox["%s%.2f" % (which, l)] = v
        r = {"case": case, "128": {}, "192": {}, "부피": {}, "t": {}, "ZSMOOTH": O.H.ZSMOOTH}
        import 벤치smooth as BS                        # 깨짐 셋 — 찢김 · 조각 · 실루엣 손실 (정의는 거기)
        r["찢김"] = {k: round(BS.tear(v), 4) for k, v in vox.items()}
        r["조각"] = {k: BS.pieces(v) for k, v in vox.items()}
        r["실루엣"] = {k: round(BS.sil_loss(v, plain), 4) for k, v in vox.items()}
        hm = O.C.to_mesh(plain, axes)
        vh = hm.volume
        for g, x in iou_m(hm).items():
            r[g]["이진"] = x
        rv = {}
        for k, v in vox.items():
            m = O.C.to_mesh(v, axes)
            rv[k] = m.volume / vh                        # 메시 부피 비로 맞춘다
            for g, x in iou_m(m).items():
                r[g][k] = x
        # 새 대조군 — 부호거리장의 수준 t. 부피 곡선을 DT 간격으로 그려 t 를 찾는다
        sdf = (ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)).astype(np.float32)
        ts, vs = [0.0], [sdf_mesh(sdf, axes, 0.0, False).volume / vh]
        assert abs(vs[0] - 1) < 0.01, "%s: 수준 0 이 hull 과 부피가 다르다 (%.4f)" % (case, vs[0])
        while vs[-1] > min(rv.values()) and ts[-1] < 12:
            ts.append(ts[-1] + DT)
            vs.append(sdf_mesh(sdf, axes, ts[-1], False).volume / vh)
        assert all(b < a for a, b in zip(vs, vs[1:])), "%s: 수준을 올릴수록 부피가 줄어야 한다" % case
        for k in vox:
            t = float(np.interp(rv[k], vs[::-1], ts[::-1]))
            m = sdf_mesh(sdf, axes, t)
            got = m.volume / vh
            assert abs(got - rv[k]) < 0.02, "%s %s: 대조군 부피 %.4f 가 목표 %.4f 와 안 맞는다" % (case, k, got, rv[k])
            for g, x in iou_m(m).items():
                r[g]["균일@" + k] = x
            r["부피"][k] = round(float(rv[k]), 4)
            r["t"][k] = round(t, 3)
        # 옛 대조군 — 한 겹씩, 칸 부피 목표 이하 첫 겹
        V = float(plain.sum())
        need = {k: float(v.sum() / V) for k, v in vox.items()}
        layers, e = [plain], plain
        while e.sum() / V > min(need.values()) and len(layers) < 40:
            e = ndimage.binary_erosion(e)
            layers.append(e)
        cv = [float(c.sum() / V) for c in layers]
        li = [iou_m(O.C.to_mesh(c, axes)) if i else {g: r[g]["이진"] for g in PITCH} for i, c in enumerate(layers)]
        for k in vox:
            first = next(i for i, c in enumerate(cv) if c <= need[k])
            for g in PITCH:
                r[g]["균일층@" + k] = li[first][g]
        r["층부피"] = cv
        del vox, layers, e, sdf
        gc.collect()
        r["초"] = round(time.time() - t0, 1)
        mi = P.memory_info()
        r["GB"], r["최대GB"] = round(mi.rss / 2 ** 30, 2), round(mi.peak_wset / 2 ** 30, 2)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        d = lambda k, c="균일@": r["128"][k] - r["128"][c + k]
        print("  %-24s 새 대조(128) 파이프 .20 %+.4f .50 %+.4f · 오라클 .20 %+.4f .50 %+.4f"
              " | 옛 파이프.20 %+.4f | %.0f초 최대 %.2fGB" % (
              case[:24], d("파이프0.20"), d("파이프0.50"), d("오라클0.20"), d("오라클0.50"),
              d("파이프0.20", "균일층@"), r["초"], r["최대GB"]), flush=True)


if __name__ == "__main__":
    main()
