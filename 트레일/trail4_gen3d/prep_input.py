# -*- coding: utf-8 -*-
"""턴 시트 판을 TripoSG 입력 형식으로 만든다.

    D:\imggen\venv\Scripts\python.exe prep_input.py

TripoSG 는 물체가 가운데 오는 정사각 이미지를 전제한다. 판을 흰 배경 정사각
캔버스에 넣고 1024 로 맞춘다. **이 파일이 없으면 생성이 재현되지 않는다** —
run_triposg.py 는 있는데 그 입력을 만드는 절차가 인라인이라 한 번 빠졌었다.
"""
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "trail2_manga_anim", "ref")
OUT = os.path.join(HERE, "in")
RES = 1024

os.makedirs(OUT, exist_ok=True)
for name in ("turn_front", "turn_side", "omnimon_front"):
    im = Image.open(os.path.join(SRC, name + ".png")).convert("RGB")
    a = np.asarray(im)
    h, w = a.shape[:2]
    s = max(h, w)
    pad = np.full((s, s, 3), 255, np.uint8)
    pad[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = a
    out = cv2.resize(pad, (RES, RES), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, name + ".png"), cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    print(f"{name:15s} {im.size} -> {RES}x{RES}")
print("in/*.png")
