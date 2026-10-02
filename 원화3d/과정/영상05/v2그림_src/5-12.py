# -*- coding: utf-8 -*-
"""5-12: 「바다 괴물」 — 떨어진 검은 혹 셋(꼬리 · 등 · 목). 가리는 물체도 T 접합도 없다. python 5-12.py"""
import numpy as np
from cetz_util import tube, poly, build
tail = tube([(-10.0, -1.6), (-8.4, -1.9), (-7.0, -2.8), (-6.4, -3.7)], lambda t: 0.05 + 0.7 * t ** 1.3)
hump = tube([(-3.6, -2.4), (-3.1, 0.2), (-1.4, 1.3), (0.6, 0.6), (1.3, -0.2)], lambda t: 1.0 - 0.35 * t ** 2)
neck = tube([(4.0, 0.9), (5.0, 2.4), (6.0, 4.0), (7.6, 5.1)], lambda t: 0.75 * (1 - t) ** 1.1 + 0.05)
build("5-12", poly(tail, fill="rgb(\"#1e1e1e\")") + poly(hump, fill="rgb(\"#1e1e1e\")") + poly(neck, fill="rgb(\"#1e1e1e\")"), length="1.35cm")
