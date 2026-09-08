# -*- coding: utf-8 -*-
"""**측면·후면도 알베도로 나눈다.** 정면만 판이 있고 나머지는 라벨 하나였다.

    python segment_views.py     ->  out/_L_alb_side.npy · _L_alb_back.npy · parts/views.json

라벨 18(side/lav) 하나가 아틀라스 면적의 55.8% 를 뭉뚱그리고 있었다 (uv_map_table).
정면 판을 만든 segment.segment() 를 그대로 다른 판에 돌린다.

창(월드 u,z)
    front   u  0.118..0.252   z 0.775..0.985   (커밋된 원본, panels.json 18개)
    side    u -0.075..0.125   z 0.775..0.955   sh_pauldron.json 측면 윤곽 + 여유
    back    u -0.252..-0.118  z 0.775..0.985   정면의 거울 (뒤에서 보면 u = -x)
"""
import os, json
import numpy as np
import segment as SG

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VIEWS = {
    "side": dict(u0=-0.075, u1=0.125, z0=0.775, z1=0.955),
    "back": dict(u0=-0.252, u1=-0.118, z0=0.775, z1=0.985),
}

meta = {}
for v, win in VIEWS.items():
    L, C, S, box, raw, sil = SG.segment(v, win)
    ids = [int(x) for x in np.unique(L) if x > 1 and (L == x).sum() >= SG.MINPX]
    kinds = {}
    for i in ids:
        k = SG.hue(np.median(C[L == i], 0))
        kinds[k] = kinds.get(k, 0) + 1
    np.save(os.path.join(OUT, "_L_alb_%s.npy" % v), L.astype(np.int32))
    meta[v] = dict(win=list(box), world=win, panels=len(ids), hues=kinds,
                   ids=ids, cover=float(np.isin(L, ids).sum() / max(S.sum(), 1)))
    print("%-5s 판 %2d개  %-34s 실루엣 덮임 %.1f%%  크롭 %s"
          % (v, len(ids), kinds, meta[v]["cover"]*100, L.shape))

json.dump(meta, open(os.path.join(HERE, "parts", "views.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("-> parts/views.json")
