# -*- coding: utf-8 -*-
"""**FlexiCubes 다리** — 이 저장소 파이썬에는 torch 가 없다. `D:\\imggen\\venv` 로 건너간다.

    <venv python> fc_추출.py <in.npz(f)> <out.npz(V,F)>

`f` 는 우리 규약의 장이다 — 칸 중심 표본 · **안 + · 밖 −**. FlexiCubes 는 반대라 부호를 뒤집는다.
격자는 `construct_voxel_grid(res)` 의 res = N−1 로 잡는다. 그러면 격자 **정점**이 우리 칸 중심과
하나씩 맞는다 (마칭큐브가 배열을 읽는 방식과 같다) — **반 칸 오프셋이 여기서 맞춰진다.**
`verts_unique` 는 `torch.unique(dim=0)` 이 사전순으로 낸 것이라 (x, y, z) C 순서다 = `f.ravel()`.

**가중치를 안 준다** (beta · alpha · gamma 기본) — README 의 「extract a mesh from a known SDF
without optimization」 모드. 매개변수 탐색은 안 한다.
"""
import sys
import os

import numpy as np
import torch

FC = r"G:\art2real\트레일\trail8_meshext\FlexiCubes"
sys.path.insert(0, FC)
from flexicubes import FlexiCubes


def extract(f, device="cuda"):
    n = f.shape[0]
    assert f.shape == (n, n, n), "정육면체 격자만"
    fc = FlexiCubes(device=device)
    res = n - 1
    x, cubes = fc.construct_voxel_grid(res)
    s = torch.tensor(-np.ascontiguousarray(f, np.float32).ravel(), device=device)  # FC: 안 −
    assert len(s) == len(x), "정점 수가 안 맞는다 %d vs %d" % (len(s), len(x))
    V, F, _ = fc(x, s, cubes, res)
    return V.detach().cpu().numpy(), F.detach().cpu().numpy()


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d = np.load(src)
    V, F = extract(d["f"])
    # [-0.5, 0.5] 격자 -> 세계 좌표. 정점 i 는 i/res − 0.5 에 있고 우리 칸 중심은 u0 + i·cell 이다
    u0, cell = float(d["u0"]), float(d["cell"])
    z0 = float(d["z0"])
    res = d["f"].shape[0] - 1
    W = (V + 0.5) * res * cell
    W[:, 0] += u0
    W[:, 1] += u0
    W[:, 2] += z0
    np.savez(dst, V=W, F=F)


if __name__ == "__main__":
    main()
