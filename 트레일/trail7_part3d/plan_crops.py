# -*- coding: utf-8 -*-
"""부위마다 **크롭을 얼마나 키워야 하는지** 뽑기 전에 계산한다.

    venv/Scripts/python.exe plan_crops.py in/omega_front_clean.png

근거 (오늘 실측):
    생성 격자는 대략 256칸이다. 원화 세로가 923화소면 **한 칸 = 3.61 원본화소.**
    먹선이 한 칸보다 얇으면 격자에 안 걸리고 통째로 사라진다.

        얼굴 먹선 1.9화소 / 3.61 = 0.5칸  -> 전신 1회에서 얼굴이 안 나왔다
        가슴 먹선 7.4화소 / 3.61 = 2.0칸  -> 가슴 문양은 나왔다
        얼굴 크롭 후 한 칸 0.31화소       -> 1.9/0.31 = 6칸, 눈·입이 새겨졌다

    그래서 필요한 크롭 배율 = (원하는 칸수 x 한 칸) / 먹선 굵기.
    NEED_CELLS 는 관측값이다 — 2칸이면 살아남고(가슴), 6칸이면 뚜렷하다(얼굴 크롭).

한계도 같이 적는다: **원화에 없는 것은 배율로 안 나온다.** 뒤통수·손 안쪽·겨드랑이는
정면 한 장에 정보가 없으므로 크롭을 아무리 키워도 지어낸 값이다. 거긴 손으로 지어야 한다.
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

GRID = 256          # 생성 격자 (PartCrafter/TripoSG 계열 실효 해상도, 노브)
NEED_CELLS = 3.0    # 선이 살아남는 데 필요한 칸수. 2 에서 살아남고 6 에서 뚜렷했다

# (이름, x0, x1, y0, y1) — 몸통 bbox 대비 비율
REGIONS = [
    ("face",  0.44, 0.62, 0.075, 0.17),
    ("head",  0.34, 0.66, 0.00, 0.17),
    ("torso", 0.28, 0.72, 0.11, 0.45),
    ("armL",  0.00, 0.36, 0.08, 0.95),
    ("armR",  0.64, 1.00, 0.08, 0.64),
    ("legs",  0.22, 0.80, 0.42, 1.00),
]


def ink_width(L, m, y0, y1, x0, x1):
    """먹선 굵기 = 거리변환 중앙값 x 2. 선이 없으면 None."""
    ink = ((L[y0:y1, x0:x1] < 90) & m[y0:y1, x0:x1]).astype(np.uint8)
    if ink.sum() < 50:
        return None
    dt = cv2.distanceTransform(ink, cv2.DIST_L2, 3)
    return 2 * float(np.median(dt[dt > 0]))


def main(path):
    a = np.array(Image.open(path))
    m = a[..., 3] > 0
    L = a[..., :3].max(2)
    ys, xs = np.where(m)
    Y0, Y1, X0, X1 = ys.min(), ys.max(), xs.min(), xs.max()
    H, W = Y1 - Y0 + 1, X1 - X0 + 1
    cell_full = H / GRID
    print("원화 몸통 %dx%d · 격자 %d칸 -> 전신 1회일 때 한 칸 = %.2f 원본화소\n" % (W, H, GRID, cell_full))
    print("%-6s %8s %8s %9s %9s  %s" % ("부위", "선굵기", "크롭세로", "지금칸수", "필요배율", "판정"))

    for name, fx0, fx1, fy0, fy1 in REGIONS:
        x0, x1 = int(X0 + fx0*W), int(X0 + fx1*W)
        y0, y1 = int(Y0 + fy0*H), int(Y0 + fy1*H)
        w = ink_width(L, m, y0, y1, x0, x1)
        if w is None:
            print("%-6s %8s  (먹선 부족)" % (name, "-"))
            continue
        side = max(x1-x0, y1-y0)            # 정사각 크롭 기준
        cell_now = side / GRID              # 그 부위만 크롭했을 때 한 칸
        cells_full = w / cell_full          # 전신 1회에서 이 선이 차지하는 칸수
        cells_crop = w / cell_now           # 부위 크롭에서 차지하는 칸수
        need = NEED_CELLS / cells_crop      # 추가로 몇 배 더 좁혀야 하나
        verdict = "그대로 OK" if cells_crop >= NEED_CELLS else "%.1f배 더 좁혀라" % need
        print("%-6s %8.1f %8d %9.1f %9.1f  %s"
              % (name, w, side, cells_full, cells_crop, verdict))

    print("\n크롭으로 못 고치는 것: 뒤통수·손 안쪽·겨드랑이 — 정면 한 장에 정보가 없다.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "in/omega_front_clean.png")
