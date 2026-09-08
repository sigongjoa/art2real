# -*- coding: utf-8 -*-
"""부위별 생성물을 **원화 상자 비율 그대로** 제자리에 앉혀 한 벌로 만든다.

    venv/Scripts/python.exe assemble_omega.py

손으로 맞춘 값이 없다. regions.py 가 쓴 상자(몸통 bbox 대비 비율)가 곧 배치다 —
원화에서 그 부위가 차지하던 자리에 그대로 놓는다. trail6 tri_shot 의 fit 규약과 같은
생각이다: **정면 bbox 를 실측 상자에 한 배율로 맞추고 종횡비를 안 깬다.**

깊이(z)는 상자가 못 준다. 정면 원화 한 장이 입력이라 앞뒤 위치는 정보가 없다 —
가운데로 놓는다. 노브다.
"""
import os
import numpy as np
import trimesh
from PIL import Image

from regions import REGIONS, body_box

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_H = 2.0             # 조립본 세로 (모델 단위). 나머지는 원화 종횡비가 정한다


def load_region(name, frac=0.25):
    """부위 생성물을 읽고 **허공 잔해를 버린다.**

    PartCrafter 는 파트를 서로 떨어뜨려 놓는 일이 있다(견갑 때 실측). 그 잔해가 bbox 를
    부풀리면 배치에서 본체가 쪼그라든다 — 첫 조립이 그래서 깨졌다.
    가장 큰 조각의 대각선 대비 frac 미만인 조각은 버린다.
    """
    p = os.path.join(HERE, "out", "rg_%s.glb" % name)
    if not os.path.exists(p):
        return None
    s = trimesh.load(p)
    g = list(s.geometry.values()) if hasattr(s, "geometry") else [s]
    cs = []
    for m in g:
        cs += list(m.split(only_watertight=False)) or [m]
    d = np.array([np.linalg.norm(c.vertices.max(0) - c.vertices.min(0)) for c in cs])
    keep = [c for c, dd in zip(cs, d) if dd >= frac * d.max()]
    print("  %-6s 조각 %d -> %d" % (name, len(cs), len(keep)))
    return trimesh.util.concatenate(keep)


def main():
    a = np.array(Image.open(os.path.join(HERE, "in", "omega_front_clean.png")))
    X0, X1, Y0, Y1 = body_box(a[..., 3] > 0)
    W, H = X1 - X0 + 1, Y1 - Y0 + 1
    ppu = MODEL_H / H                      # 화소 -> 모델 단위

    sc = trimesh.Scene()
    for name, fx0, fx1, fy0, fy1 in REGIONS:
        m = load_region(name)
        if m is None:
            print("  %-6s 없음 — 건너뜀" % name); continue

        # 원화 상자를 모델 좌표로. y 는 위가 +.
        # **정사각 패딩을 그대로 되돌린다** — regions.py 가 크롭을 정사각으로 채워 넣으므로
        # 생성물의 화면 틀은 직사각이 아니라 그 정사각이다. 첫 조립이 여기서 깨졌다.
        ax0, ax1 = X0 + fx0*W, X0 + fx1*W
        ay0, ay1 = Y0 + fy0*H, Y0 + fy1*H
        side = max(ax1-ax0, ay1-ay0)
        cx, cy = (ax0+ax1)/2, (ay0+ay1)/2
        ax0, ax1, ay0, ay1 = cx-side/2, cx+side/2, cy-side/2, cy+side/2
        tx0, tx1 = (ax0 - (X0+X1)/2) * ppu, (ax1 - (X0+X1)/2) * ppu
        ty1, ty0 = ((Y0+Y1)/2 - ay0) * ppu, ((Y0+Y1)/2 - ay1) * ppu

        lo, hi = m.vertices.min(0), m.vertices.max(0)
        # 종횡비를 안 깬다 — 가로/세로 중 빠듯한 쪽에 맞춘다
        s = min((tx1-tx0)/max(hi[0]-lo[0], 1e-9), (ty1-ty0)/max(hi[1]-lo[1], 1e-9))
        m.vertices = m.vertices * s
        lo, hi = m.vertices.min(0), m.vertices.max(0)
        m.vertices += np.array([(tx0+tx1)/2 - (lo[0]+hi[0])/2,
                                (ty0+ty1)/2 - (lo[1]+hi[1])/2,
                                -(lo[2]+hi[2])/2])          # 깊이는 가운데 (노브)
        sc.add_geometry(m, node_name=name)
        print("  %-6s 배율 %.3f  면 %7d  자리 x %.2f..%.2f  y %.2f..%.2f"
              % (name, s, len(m.faces), tx0, tx1, ty0, ty1))

    out = os.path.join(HERE, "out", "omega_asm.glb")
    sc.export(out)
    print("저장 %s" % out)


if __name__ == "__main__":
    main()
