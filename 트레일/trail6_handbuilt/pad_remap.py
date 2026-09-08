# -*- coding: utf-8 -*-
"""**형태는 지어서 낸 것에, 색은 오늘의 3판 매핑으로.**

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python pad_remap.py

손으로 지은 견갑은 전개도를 언랩기에 안 맡기고 **지을 때 같이 냈다** (build.py layout, 72).
섬 5개 · 이음선이 곧다 · 뿔이 sh_horn0..3 이라는 이름 있는 부품이다 —
뿔을 "맞추는" 게 아니라 지어 넣은 것이라 실루엣이 딴 물건으로 안 읽힌다.

그 물건의 약점은 형태가 아니라 색이었다 (직접 31.8% · 전파 60.1%, README 130).
정면 판 하나만 읽었기 때문이다. 오늘 만든 front 15 + side 12 + back 16 을 얹는다.

뿔은 이름이 뿔이므로 부품 단위로 표를 모은다 (계급 투표가 필요 없다, 129).
산출: out/pad43_col.png · pad43_prov.png · pad43.blend
"""
import bpy, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import remap_all as RA          # 판별 라벨맵·마스크·창·DEF 를 그대로 쓴다
import tri_uv
from mask2d import topix

OUT = os.path.join(HERE, "out")
ATLAS = tri_uv.ATLAS


def assign(me, obj):
    """면마다 판 라벨. remap_all 과 같은 규칙 — 가장 정면인 판에서 알베도 라벨을 읽는다."""
    nf = len(me.polygons)
    N = np.empty(nf*3); me.polygons.foreach_get("normal", N); N = N.reshape(-1, 3)
    C = np.empty(nf*3); me.polygons.foreach_get("center", C); C = C.reshape(-1, 3)
    C = np.array([obj.matrix_world @ __import__("mathutils").Vector(c) for c in C])
    sc = np.stack([f(N) for _, f, _, _ in RA.DEF], 1)
    lab = np.full(nf, -1, np.int32); src = np.full(nf, -1, np.int32)
    for i in range(nf):
        for k in np.argsort(-sc[i]):
            if sc[i, k] <= 0.15:
                break
            name, _, (ax, sgn), off = RA.DEF[k]
            x0, x1, y0, y1 = RA.Win[name]
            py, px = topix(sgn*C[i, ax], C[i, 2])
            cy, cx = py - y0, px - x0
            if not (0 <= cy < y1-y0 and 0 <= cx < x1-x0):
                continue
            if not RA.Mk[name][cy, cx]:
                continue
            v = int(RA.Lm[name][cy, cx])
            if v <= 1:
                continue
            lab[i] = off + v; src[i] = k
            break
    return lab, src


def colour(L):
    name = "front" if L < 100 else ("side" if L < 200 else "back")
    off = 0 if L < 100 else (100 if L < 200 else 200)
    x0, x1, y0, y1 = RA.Win[name]
    m = (RA.Lm[name] == L - off) & RA.Mk[name]
    sub = RA.Art[name][y0:y1, x0:x1]
    px = sub[..., :3][m & (sub[..., 3] >= 128)]
    return np.median(px, 0) if len(px) else np.array([128., 128., 128.])


ARG = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
BLEND, PRE = (ARG + ["pauldron.blend", "pad43"])[:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, BLEND))
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
img = np.zeros((ATLAS, ATLAS, 3), np.float32)
hit = np.zeros((ATLAS, ATLAS), bool)
pimg = np.zeros((ATLAS, ATLAS, 3), np.float32)
tot = dir_n = 0
GOLD = np.array([158., 138., 76.])
# 금 라벨은 **전 판에서** 고른다. 부품 안 후보만 보면 뿔이 라벤더로 굳는다
ALL = []
for _nm in ("front", "side", "back"):
    _off = {"front": 0, "side": 100, "back": 200}[_nm]
    for _v in np.unique(RA.Lm[_nm]):
        if _v > 1 and (RA.Mk[_nm] & (RA.Lm[_nm] == _v)).sum() >= RA.MINPX:
            ALL.append(_off + int(_v))
GOLD_L = min(ALL, key=lambda v: np.linalg.norm(colour(v) - GOLD))
print("금 라벨 %d  RGB(%3.0f,%3.0f,%3.0f)" % (GOLD_L, *colour(GOLD_L)))

for o in objs:
    me = o.data
    lab, src = assign(me, o)
    n = len(me.polygons)
    if o.name.startswith("sh_horn"):
        # 이름이 뿔이다 — 부품 안에서 표를 모으고, 표가 없으면 금으로 (129)
        got = [int(v) for v in lab if v >= 0]
        win = max(set(got), key=got.count) if got else None
        dgold = 1e9 if win is None else float(np.linalg.norm(colour(win) - GOLD))
        print("   %s 표 %s  RGB(%s)  금까지 %.0f" % (o.name, win,
              "" if win is None else "%3.0f,%3.0f,%3.0f" % tuple(colour(win)), dgold))
        if win is None or dgold > 70:
            win = GOLD_L
        lab[:] = win
    cmap = {int(L): colour(int(L)) for L in np.unique(lab) if L >= 0}
    col = np.array([cmap[int(L)] if L >= 0 else [110., 110., 118.] for L in lab])
    prov = np.where(src >= 0, 0, 1)
    if o.name.startswith("sh_horn"):
        prov = np.where(src >= 0, 0, 2)                 # 파랑 = 뿔 계급
    np.save(os.path.join(OUT, "dbg_%s_lab.npy" % o.name), lab)
    np.save(os.path.join(OUT, "dbg_%s_col.npy" % o.name), col)
    ar = np.empty(len(me.polygons)); me.polygons.foreach_get("area", ar)
    dk = col.max(1) < 80
    if dk.any():
        print("   어두운 면 %d개 면적 %.1f%%  라벨 %s" % (dk.sum(), ar[dk].sum()/ar.sum()*100,
              sorted(set(int(v) for v in lab[dk]))))
    a, h = tri_uv.rasterize(me, col, ATLAS)
    b, _ = tri_uv.rasterize(me, tri_uv.PROVCOL[prov], ATLAS)
    img[h] = a[h]; pimg[h] = b[h]; hit |= h
    tot += n; dir_n += int((src >= 0).sum())
    print("%-16s 면 %3d  직접 %3d  라벨 %s" % (o.name, n, (src >= 0).sum(),
          sorted(set(int(v) for v in np.unique(lab)))[:6]))

tri_uv.save(img, hit, "%s_col.png" % PRE)
tri_uv.save(pimg, hit, "%s_prov.png" % PRE)
print("합 %d면  직접 %d (%.1f%%)  채운 텍셀 %.1f%%" % (tot, dir_n, dir_n/tot*100, hit.mean()*100))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "%s.blend" % PRE))
