# -*- coding: utf-8 -*-
"""**Reach for the Arcs 다리** — 가벼운 모듈로 따로 띄운다.

    python rfta_추출.py <in.npz(U, S)> <out.npz(V, F)>

`gpytoolbox.reach_for_the_arcs(parallel=True)` 는 윈도우에서 **spawn 으로 자식 프로세스를 띄운다.**
그러면 자식이 `__main__` 모듈을 다시 import 하는데, `메시추출.py` 를 그대로 부르면 그 무거운
import 사슬(trimesh · cv2 · hull · 대조 · 대각 …)이 배치마다 다시 돈다 — 09-19 에 이것 때문에
합성 구 195 초짜리가 도형 하나에서 30 분을 넘겼다. 여기는 numpy · gpytoolbox 둘만 import 한다.

**매개변수는 기본값만.** `parallel` 은 계산이 아니라 일정이라 계획의 「기본값만」에 안 걸린다.
"""
import sys

import numpy as np
import gpytoolbox as gpy


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d = np.load(src)
    V, F = gpy.reach_for_the_arcs(d["U"], d["S"], parallel=True)
    np.savez(dst, V=V, F=F)


if __name__ == "__main__":
    main()
