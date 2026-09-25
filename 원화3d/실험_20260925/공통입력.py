# -*- coding: utf-8 -*-
"""분할 후보들이 같이 쓰는 입력 한 벌 — out/분할후보/입력.npz · 몸.ply (2026-09-25).

  O        09-24 키트의 몸 (field_default · 192³ · [x=ux, y=깊이 uy, z=높이])
  ux uy z  축 (창 단위)
  축i      좌우 거울 축의 x 색인 (반 칸 단위 · 몸통·다리 행에서 O 를 뒤집어 가장 잘 겹치는 곳)
  선앞 선뒤  대칭 패널라인을 창 판(1024)으로 · 앞 판 선은 **작은 y** 쪽 겉(발끝 · 채점기 앞 겉과 같은 쪽 — 09-25 확인)
  원앞 원뒤  원화 먹선 그대로 (대조용)
  색앞 색뒤  원화 색을 창 판으로 (RGB)
  bs       뒤 판 좌우 부호 · p 창 정렬 값은 hull 모듈이 다시 만든다
몸.ply 는 같은 몸을 창 좌표 메시로 (Z.메시로)."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path[:0] = [r"G:\art2real\원화3d"] + [r"G:\art2real\원화3d\실험_202609%02d" % d for d in (21, 22, 23, 24, 25)]
import hull as H, 부품분할 as BB, 먹선분할 as MS, 지표 as Z
from 대칭분할 import 대칭먹선

c = "오메가몬"; os.environ.setdefault("INK_W", "1")
raw, masks, bs, p = BB.판(c)
g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
ux, uy, z = [np.asarray(a) for a in ax]; O = g > 0
# 거울 축: 높이 아래 70% (팔 끝 위 칼·대포를 덜 타게) 에서 O 를 x 로 뒤집어 IoU 최대
zs = np.nonzero(O.any((0, 1)))[0]; 아래 = O[:, :, zs[0]:zs[0] + int(0.7 * len(zs))]
xs = np.nonzero(O.any((1, 2)))[0]; 최 = None
for a2 in range(2 * xs[0], 2 * xs[-1] + 1):
    j = a2 - np.arange(O.shape[0]); ok = (j >= 0) & (j < O.shape[0])
    f = np.zeros_like(아래); f[ok] = 아래[j[ok]]
    s = (f & 아래).sum() / (f | 아래).sum()
    if 최 is None or s > 최[0]: 최 = (s, a2)
print("거울 축 x 색인 %.1f · 아래 70%% 몸 IoU %.3f" % (최[1] / 2, 최[0]))
대 = 대칭먹선(c, raw, p, bs, 넓힘=0); 원 = MS.창먹선(c, raw, p, bs, 넓힘=0)
src, base = H.CASES[c]["src"], H.art_dir(c); 색 = {}
for v in ("front", "back"):
    im = np.array(Image.open(os.path.join(base, src[v])).convert("RGB")).astype(np.float32) / 255
    ch = []
    for k in range(3):
        _, w2 = H.to_win(H.declutter(raw[v]), im[..., k]); ch.append(H._warp_one(w2, v, p))
    색[v] = np.stack(ch, -1).astype(np.float16)
np.savez_compressed(os.path.join(H.OUT, "분할후보", "입력.npz"), O=O, g=g.astype(np.float32), ux=ux, uy=uy, z=z, 축i=최[1] / 2, bs=bs,
                    선앞=대["front"], 선뒤=대["back"], 원앞=원["front"], 원뒤=원["back"], 색앞=색["front"], 색뒤=색["back"])
m = Z.메시로(g, (ux, uy, z)); m.export(os.path.join(H.OUT, "분할후보", "몸.ply"))
print("몸 메시 정점 %d 면 %d 닫힘 %s · extents %s" % (len(m.vertices), len(m.faces), m.is_watertight, m.extents.round(3)))
