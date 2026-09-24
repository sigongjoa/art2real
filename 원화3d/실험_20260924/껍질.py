# -*- coding: utf-8 -*-
"""**껍질** — 덩어리 부품의 속을 비운다 (2026-09-24).

    python 껍질.py [케이스] [벽mm]      기본 mech_Mech_4UvIHxnoSR · 1.2mm

비즈니스 패널 권고 ①의 가장 싼 판. 형태는 그대로 두고 **속만** 비워서
부피 · 출력 시간 · 게이트 ②(껍질인가)가 어디까지 가는지 본다.
⚠ 이것은 형태를 고치지 않는다. 울퉁불퉁한 덩어리를 비우면 울퉁불퉁한 껍질이 나온다.
"""
import os, sys
import numpy as np, trimesh
from scipy import ndimage
from skimage import measure

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260924"]
import hull as H
import 제조가능성 as MG

케이스 = sys.argv[1] if len(sys.argv) > 1 else "mech_Mech_4UvIHxnoSR"
벽 = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
피치 = 0.4
들 = os.path.join(H.OUT, "출력", 케이스)
낼 = os.path.join(H.OUT, "출력", 케이스 + "_껍질%.1f" % 벽); os.makedirs(낼, exist_ok=True)


def 비우기(m, 벽, 피치=피치):
    v = m.voxelized(피치).fill()
    P = np.pad(np.asarray(v.matrix, bool), 2)
    k = max(1, int(round(벽 / 피치)))
    속 = ndimage.binary_erosion(P, iterations=k)
    S = P & ~속
    if S.sum() < 100 or 속.sum() == 0:
        return None, 0.0
    vt, ft, _, _ = measure.marching_cubes(S.astype(np.float32), 0.5)
    g = trimesh.Trimesh(vt[:, [0, 1, 2]] * 피치, ft, process=False)
    g.apply_translation(np.asarray(v.bounds[0]) - 2 * 피치)
    # fix_normals() 를 쓰면 **안쪽 면까지 바깥으로 돌려** 공동이 부피에 더해진다(09-24 에 부피가 2 배로 늘었다).
    # 마칭 큐브가 준 방향이 이미 맞다 — 바깥면은 밖으로, 안쪽면은 공동 쪽으로. 전체 부호만 본다.
    g.merge_vertices()
    if g.volume < 0: g.invert()
    return g, float(S.sum()) * 피치 ** 3


fs = sorted(f for f in os.listdir(들) if f.lower().endswith(".stl"))
원부피 = 껍부피 = 0.0
for f in fs:
    m = trimesh.load(os.path.join(들, f), force="mesh")
    g, 복셀부피 = 비우기(m, 벽)
    if g is None:
        print("  건너뜀", f); continue
    g.export(os.path.join(낼, f))
    원부피 += abs(m.volume); 껍부피 += abs(g.volume)
    assert abs(abs(g.volume) - 복셀부피) < 0.25 * 복셀부피, "껍질 부피가 복셀 셈과 안 맞는다 (면 방향 확인)"
    r = MG.부품재기(g)
    print("  %-12s %7.1f -> %6.1f cm³  얇기 %.3f  얇은몫 %.3f  %s" % (
        f[:-4], abs(m.volume) / 1000, abs(g.volume) / 1000, r["얇기"], r["얇은몫"],
        "통과" if r["통과"] else "떨어짐(" + " ".join(k for k in ("①벽", "②껍질", "③서포트", "④판") if not r[k]) + ")"))
print("합계 %.1f -> %.1f cm³  (%.0f%%)" % (원부피 / 1000, 껍부피 / 1000, 100 * 껍부피 / max(원부피, 1)))
print(낼)
