# -*- coding: utf-8 -*-
"""**판정기.** 어떤 생성 모델이든 같은 자로 잰다. 결과 보고 기준을 만들지 않으려고 먼저 짠다.

    python judge_part3d.py out/pc_front.glb [out/다른것.glb ...]

기준 둘 (research_part3d_20260829 에서 미리 못 박은 것)
    1) 뿔 4개가 **별개 파트**로 나오나
    2) 정면 실루엣 IoU 가 TripoSG 의 0.642 를 넘나

정렬은 trail6 tri_shot.py 와 같은 규약 — 정면 bbox 를 견갑 실측 상자에 한 배율로 맞춘다.
뿔 판별도 trail6 129번 규칙 그대로: 원뿔은 e2/e3 ~ 1.0~1.25, 앞판은 2.1.
"""
import os, sys, json
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
T6 = os.path.join(HERE, "..", "trail6_handbuilt")
sys.path.insert(0, T6)
import mask2d
from mask2d import topix

U0, U1, Z0, Z1 = 0.112, 0.245, 0.788, 0.990        # 견갑 실측 상자 (tri_shot.py 와 같아야 한다)
ART = mask2d.raster(mask2d.load()["front"])


def fit(V):
    """정면 bbox 를 실측 상자에 한 배율로. 종횡비를 안 깬다 (tri_shot 규약)."""
    lo, hi = V.min(0), V.max(0)
    s = min((U1-U0)/max(hi[0]-lo[0], 1e-9), (Z1-Z0)/max(hi[2]-lo[2], 1e-9))
    V = V*s
    lo, hi = V.min(0), V.max(0)
    return V + np.array([(U0+U1)/2-(lo[0]+hi[0])/2, 0.027-(lo[1]+hi[1])/2, (Z0+Z1)/2-(lo[2]+hi[2])/2])


def silhouette(V, F):
    m = np.zeros((mask2d.RES, mask2d.RES), bool)
    for f in F:
        vs = V[f]
        py, px = topix(vs[:, 0], vs[:, 2])
        x0, x1 = int(px.min()), int(px.max())+1
        y0, y1 = int(py.min()), int(py.max())+1
        if x1 <= x0 or y1 <= y0:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1]
        qx, qy = gx+.5, gy+.5
        xa, ya = px.astype(float), py.astype(float)
        det = (ya[1]-ya[2])*(xa[0]-xa[2]) + (xa[2]-xa[1])*(ya[0]-ya[2])
        if abs(det) < 1e-9:
            continue
        w0 = ((ya[1]-ya[2])*(qx-xa[2]) + (xa[2]-xa[1])*(qy-ya[2]))/det
        w1 = ((ya[2]-ya[0])*(qx-xa[2]) + (xa[0]-xa[2])*(qy-ya[2]))/det
        h = (w0 >= -.002) & (w1 >= -.002) & (w0+w1 <= 1.002)
        if h.any():
            m[gy[h], gx[h]] = True
    return m


def cone_ratio(V):
    """주성분 e1>=e2>=e3. 원뿔은 e2/e3 ~ 1.0~1.25, 판은 2 이상 (trail6 129)."""
    X = V - V.mean(0)
    e = np.sqrt(np.maximum(np.linalg.eigvalsh(X.T @ X / max(len(X), 1)), 0))[::-1]
    return float(e[0]/max(e[2], 1e-12)), float(e[1]/max(e[2], 1e-12))


def judge(path):
    sc = trimesh.load(path)
    parts = list(sc.geometry.values()) if isinstance(sc, trimesh.Scene) else [sc]
    allV = np.vstack([np.asarray(p.vertices) for p in parts])
    lo, hi = allV.min(0), allV.max(0)
    s = min((U1-U0)/max(hi[0]-lo[0], 1e-9), (Z1-Z0)/max(hi[2]-lo[2], 1e-9))
    off = np.array([(U0+U1)/2-(lo[0]+hi[0])/2*s, 0.027-(lo[1]+hi[1])/2*s, (Z0+Z1)/2-(lo[2]+hi[2])/2*s])

    m = np.zeros((mask2d.RES, mask2d.RES), bool)
    rows = []
    for i, p in enumerate(parts):
        V = np.asarray(p.vertices)*s + off
        F = np.asarray(p.faces)
        m |= silhouette(V, F)
        el, e2 = cone_ratio(V)
        rows.append((i, len(F), el, e2, "뿔?" if (e2 <= 1.35 and el >= 1.3) else ""))

    inter = int((m & ART).sum()); uni = int((m | ART).sum())
    print("\n== %s ==" % os.path.basename(path))
    print("파트 %d개 · 면 합 %d" % (len(parts), sum(r[1] for r in rows)))
    print("  %-4s %8s %8s %8s  %s" % ("파트", "면", "e1/e3", "e2/e3", "판정"))
    for i, nf, el, e2, tag in rows:
        print("  %-4d %8d %8.2f %8.2f  %s" % (i, nf, el, e2, tag))
    horn = sum(1 for r in rows if r[4])
    print("  뿔 후보 %d개  (원화 실측 4개)" % horn)
    print("  실루엣 IoU %.3f   덮음 %.1f%%   삐져나감 %.1f%%   [TripoSG 0.642 · 손으로 지은 것 0.713]"
          % (inter/max(uni, 1), inter/ART.sum()*100, (m & ~ART).sum()/max(m.sum(), 1)*100))
    return dict(path=os.path.basename(path), parts=len(parts), faces=sum(r[1] for r in rows),
                horns=horn, iou=inter/max(uni, 1),
                cover=inter/ART.sum(), spill=float((m & ~ART).sum()/max(m.sum(), 1)))


if __name__ == "__main__":
    res = [judge(p) for p in sys.argv[1:]]
    json.dump(res, open(os.path.join(HERE, "out", "judge.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
