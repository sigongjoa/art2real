# -*- coding: utf-8 -*-
"""**출력 준비** — 제약분할 부품을 실물 1:1 크기 STL 로 낸다 (2026-09-23).

    python 출력준비.py [케이스] [전고mm]      기본 mech_Mech_4UvIHxnoSR · 125mm (1/144 건담 전고)

실물 건담 키트와 나란히 놓고 보기 위한 것이다. 배치 · 서포트 · 다보는 아직 없다 —
지금 확인하려는 것은 «우리가 낸 부품이 손에 쥐면 무엇인가» 뿐이다.
"""
import os, sys
import numpy as np, trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921",
                r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H, 부품분할 as BB, 면자르기 as MJ, 지표 as Z
import 제약분할 as CS

c = sys.argv[1] if len(sys.argv) > 1 else "mech_Mech_4UvIHxnoSR"
전고 = float(sys.argv[2]) if len(sys.argv) > 2 else 125.0
out = os.path.join(H.OUT, "출력", c); os.makedirs(out, exist_ok=True)

raw, masks, bs, p = BB.판(c)
g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
ux, uy, z = [np.asarray(a) for a in ax]
O = g > 0
_, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)

새 = np.zeros(O.shape, np.int32); n = 0
for l in [l for l in np.unique(부위) if l]:
    for c2 in CS.쪼개기(부위 == l):
        n += 1; 새 = np.where(c2, n, 새)
새 = CS.부스러기붙이기(새, O)

전체 = Z.메시로(g, (ux, uy, z))          # 장 그대로 — 0/1 로 바꾸면 격자 계단이 남는다
배율 = 전고 / float(전체.extents[2])
쓴, 총부피 = [], 0.0
for l in [l for l in np.unique(새) if l]:
    # 부품마다 «장» 과 «그 부품 영역까지의 부호거리» 의 최솟값으로 자른다.
    # 겉면은 장 그대로라 매끈하고, 자른 면도 계단이 아니라 매끈하다.
    안 = ndimage.distance_transform_edt(새 == l)
    밖 = ndimage.distance_transform_edt(새 != l)
    d = np.where(새 == l, 안 - 0.5, -(밖 - 0.5)).astype(np.float32)
    d = ndimage.gaussian_filter(d, 1.0)          # 라벨 격자는 0/1 이라 자른 면에 계단이 남는다 — 한 칸만 고른다
    m = Z.메시로(np.minimum(g, d), (ux, uy, z))
    m.apply_scale(배율)
    if m.volume < 50:                      # 50 mm^3 미만은 출력해도 의미가 없다
        continue
    m.apply_translation(-m.bounds[0])      # 바닥에 앉힌다
    f = os.path.join(out, "부품%02d.stl" % len(쓴))
    m.export(f)
    쓴.append((f, m.extents, m.volume, CS.빠지나(새 == l)))
    총부피 += m.volume

print("케이스 %s · 전고 %.0fmm · 배율 %.4f" % (c, 전고, 배율))
print("부품 %d 개 · 합계 부피 %.1f cm^3 (PLA 밀도 1.24 로 약 %.0f g)" % (len(쓴), 총부피 / 1000, 총부피 / 1000 * 1.24))
for f, e, v, ok in 쓴:
    print("  %-14s %5.1f x %5.1f x %5.1f mm  %7.1f mm^3  %s" % (
        os.path.basename(f), e[0], e[1], e[2], v, "탈형 OK" if ok else "탈형 불가"))
print(out)
