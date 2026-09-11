# -*- coding: utf-8 -*-
"""**겹 사이 선형 보간이 맞나.** 새 대조군(`벤치lam.py`)이 기대는 가정 하나를 잰다.

    python 선형검사.py 케이스 [케이스 ...]

부호거리장 sdf = EDT(안) - EDT(밖) 을 마칭큐브로 **겹 사이 수준**에서 자르면 점박이 없이
매끈하게 「반 겹」 벗긴 면이 나온다. 판본과 같은 부피(메시 부피 비)가 되는 수준을 이분법으로
찾아 그 IoU(연속 대조)를 겹 보간값(보간 대조)과 나란히 놓는다. 둘이 가까우면 가정이 선다.
수준 0 은 `hull.mesh_from`(불 0.5)과 같은 면이다 — 자가검사로 본다."""
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import 오라클 as O


def sdf_mesh(sdf, axes, t):
    p = np.pad(sdf, 1, constant_values=-1.0)
    V, F, _, _ = measure.marching_cubes(p, t)
    ux, uy, uz = axes
    s = [a[1] - a[0] for a in axes]
    V = np.stack([ux[0] + (V[:, 0] - 1) * s[0], uy[0] + (V[:, 1] - 1) * s[1], uz[0] + (V[:, 2] - 1) * s[2]], 1)
    m = trimesh.Trimesh(V, F, process=True)
    if m.volume < 0:
        m.invert()
    return m


def main():
    O.H.register_sheets()
    for case in sys.argv[1:]:
        truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
        T, ot = O.J.grid(truth)

        def iou_m(m):
            G, og = O.J.grid(m)
            A, B = O.J.common(T, ot, G, og)
            return float((A & B).sum() / max((A | B).sum(), 1))

        plain, p20, axes, _ = O.build(case, truth, 0.20, "파이프")
        p50 = O.build(case, truth, 0.50, "파이프")[1]
        sdf = (ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)).astype(np.float32)
        hull_m = O.C.to_mesh(plain, axes)
        vh = hull_m.volume
        m0 = sdf_mesh(sdf, axes, 0.0)
        assert abs(m0.volume / vh - 1) < 0.01, "수준 0 이 hull 메시와 부피가 다르다 (%.4f)" % (m0.volume / vh)
        # 겹 곡선 (벤치lam 과 같은 규칙: 칸 부피로 보간)
        layers = [plain]
        while layers[-1].sum() > 0.5 * plain.sum():
            layers.append(ndimage.binary_erosion(layers[-1]))
        cv = [c.sum() / plain.sum() for c in layers]
        ci = [iou_m(O.C.to_mesh(c, axes)) for c in layers]
        print("  %s  겹 부피 %s · IoU %s" % (case[:28], " ".join("%.3f" % x for x in cv), " ".join("%.4f" % x for x in ci)))
        for name, v in (("파이프0.20", p20), ("파이프0.50", p50)):
            f = v.sum() / plain.sum()
            interp = float(np.interp(f, cv[::-1], ci[::-1]))
            rv = O.C.to_mesh(v, axes).volume / vh            # 메시 부피 비로 맞춘다
            lo, hi = 0.0, 8.0
            for _ in range(14):
                t = (lo + hi) / 2
                if sdf_mesh(sdf, axes, t).volume / vh > rv:
                    lo = t
                else:
                    hi = t
            mc = sdf_mesh(sdf, axes, (lo + hi) / 2)
            cont = iou_m(mc)
            print("    %-10s 칸부피 %.3f 메시부피 %.3f | 판본 %.4f · 보간 대조 %.4f (%+.4f) · 연속 대조 %.4f (%+.4f)"
                  " · 연속-보간 %+.4f" % (name, f, rv, iou_m(O.C.to_mesh(v, axes)), interp,
                  iou_m(O.C.to_mesh(v, axes)) - interp, cont, iou_m(O.C.to_mesh(v, axes)) - cont, cont - interp),
                  flush=True)


if __name__ == "__main__":
    main()
