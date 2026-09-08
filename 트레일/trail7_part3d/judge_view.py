# -*- coding: utf-8 -*-
"""판정기가 **실제로 잰 것**을 그림으로 뽑는다. 블렌더 카메라가 아니라 judge_part3d 의 투영 그대로.

    venv/Scripts/python.exe judge_view.py out/op_front.glb out/pc_front.glb

빨강=원화 마스크만, 초록=모델만, 회색=겹침. 덮음/삐져나감 숫자가 눈에 보이게 된다.
"""
import os, sys
import numpy as np
from PIL import Image
import trimesh
import judge_part3d as J

for path in sys.argv[1:]:
    s = trimesh.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), path))
    g = list(s.geometry.values()) if hasattr(s, "geometry") else [s]
    V = J.fit(np.vstack([m.vertices for m in g]))
    F, o = [], 0
    for m in g:
        F.append(np.asarray(m.faces) + o); o += len(m.vertices)
    M = J.silhouette(V, np.vstack(F))
    A = J.ART
    rgb = np.zeros(A.shape + (3,), np.uint8) + 255
    rgb[A & ~M] = (220, 60, 60)      # 원화만
    rgb[M & ~A] = (60, 170, 60)      # 모델만
    rgb[A & M] = (120, 120, 120)     # 겹침
    out = path.replace(".glb", "_judge.png")
    Image.fromarray(rgb).save(out)
    print("%s  덮음 %.1f%%  삐져나감 %.1f%%  -> %s"
          % (os.path.basename(path), 100*(A & M).sum()/A.sum(), 100*(M & ~A).sum()/max(M.sum(), 1), out))
