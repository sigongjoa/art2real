# -*- coding: utf-8 -*-
"""대조군 「교차만」 — 세 그림자 겹치기만(짓기B 의 첫 단계) · 판정 시트에서 우리와 나란히 · 10-12
SET=시험|검증 python runs/기능0/짓기교차.py 번호…  →  B_교차[_검증]/NN.stl"""
import os, sys
from 도구 import *
from 윤곽 import 메시로
O = os.path.join(H, "B_교차" + ("" if 세트 == "시험" else "_" + 세트)); os.makedirs(O, exist_ok=True)
for i in [int(a) for a in sys.argv[1:]]:
    s = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2)); 메시로(s).export(os.path.join(O, "%02d.stl" % i)); print(i, flush=True)
