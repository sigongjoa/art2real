# -*- coding: utf-8 -*-
"""**형태가 얼마나 남았나.** 정면 실루엣을 원화 실측과 겹쳐 IoU 를 잰다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python sil_check.py

커밋된 기준값 (LESSONS 119) — 손으로 지은 것 0.906 · 생성 71,842면 0.677
산출: out/sil_art.npy · sil_gen.npy · sil_retopo.npy · sil_hand.npy · sil_rows.json
"""
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mask2d
from mask2d import topix

OUT = os.path.join(HERE, "out")
RES = mask2d.RES


def sil(path, tag):
    bpy.ops.wm.open_mainfile(filepath=path)
    obs = [x for x in bpy.context.scene.objects if x.type == 'MESH']
    m = np.zeros((RES, RES), bool)
    nf = 0
    for o in obs:
        me = o.data
        nf += len(me.polygons)
        V = np.array([o.matrix_world @ v.co for v in me.vertices], float)
        for p in me.polygons:
            vs = V[list(p.vertices)]
            py, px = topix(vs[:, 0], vs[:, 2])
            for k in range(1, len(py) - 1):
                xa = np.array([px[0], px[k], px[k+1]], float)
                ya = np.array([py[0], py[k], py[k+1]], float)
                x0, x1 = int(xa.min()), int(np.ceil(xa.max())) + 1
                y0, y1 = int(ya.min()), int(np.ceil(ya.max())) + 1
                if x1 <= x0 or y1 <= y0:
                    continue
                gy, gx = np.mgrid[y0:y1, x0:x1]
                qx, qy = gx + .5, gy + .5
                det = (ya[1]-ya[2])*(xa[0]-xa[2]) + (xa[2]-xa[1])*(ya[0]-ya[2])
                if abs(det) < 1e-9:
                    continue
                w0 = ((ya[1]-ya[2])*(qx-xa[2]) + (xa[2]-xa[1])*(qy-ya[2])) / det
                w1 = ((ya[2]-ya[0])*(qx-xa[2]) + (xa[0]-xa[2])*(qy-ya[2])) / det
                h = (w0 >= -.002) & (w1 >= -.002) & (w0 + w1 <= 1.002)
                if h.any():
                    m[gy[h], gx[h]] = True
    print("SIL %-20s 면 %6d  실루엣 %6d px" % (tag, nf, m.sum()))
    return m, nf


ART = mask2d.raster(mask2d.load()["front"])
print("원화 실측 정면 %d px" % ART.sum())
np.save(os.path.join(OUT, "sil_art.npy"), ART)

rows = []
for f, tag, key in (("tri_paint.blend", "생성 71,842면", "gen"),
                    ("panel_q800.blend", "리토폴로지 723 쿼드", "retopo"),
                    ("pauldron.blend", "손으로 지은 286면", "hand")):
    p = os.path.join(OUT, f)
    if not os.path.exists(p):
        print("없음:", f)
        continue
    m, nf = sil(p, tag)
    inter = int((m & ART).sum()); uni = int((m | ART).sum())
    iou = inter / max(uni, 1)
    print("    IoU %.3f   덮음 %.1f%%   삐져나감 %.1f%%"
          % (iou, inter/ART.sum()*100, (m & ~ART).sum()/max(m.sum(), 1)*100))
    np.save(os.path.join(OUT, "sil_%s.npy" % key), m)
    rows.append(dict(key=key, tag=tag, nf=int(nf), iou=float(iou),
                     cover=float(inter/ART.sum()),
                     spill=float((m & ~ART).sum()/max(m.sum(), 1))))
json.dump(rows, open(os.path.join(OUT, "sil_rows.json"), "w", encoding="utf-8"), ensure_ascii=False)
