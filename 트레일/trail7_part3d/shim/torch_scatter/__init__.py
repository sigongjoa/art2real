# -*- coding: utf-8 -*-
"""`scatter_mean`/`scatter_max`/`scatter_add` 만 대신한다 — Windows 에 휠이 없고
nvcc 가 없어 소스 빌드가 안 된다. shim/torch_cluster 와 같은 이유.

OmniPart 가 쓰는 곳은 PartField 인코더 두 파일뿐이다
(`modules/PartField/partfield/model/PVCNN/{conv_pointnet,encoder_pc}.py`).
torch 2.x 의 `scatter_reduce_` 가 셋 다 그대로 한다.
"""
import torch

__all__ = ["scatter_mean", "scatter_max", "scatter_add"]


def _prep(src, index, dim, dim_size):
    if dim < 0:
        dim = src.dim() + dim
    if dim_size is None:
        dim_size = int(index.max()) + 1 if index.numel() else 0
    shape = list(src.shape)
    shape[dim] = dim_size
    # index 를 src 와 같은 랭크로 넓힌다 (torch_scatter 규약: 뒤차원 브로드캐스트)
    while index.dim() < src.dim():
        index = index.unsqueeze(-1)
    return dim, dim_size, shape, index.expand_as(src)


def _reduce(src, index, dim, out, dim_size, mode, init):
    dim, dim_size, shape, idx = _prep(src, index, dim, dim_size)
    if out is None:
        out = src.new_full(shape, init)
    return out.scatter_reduce_(dim, idx, src, reduce=mode, include_self=False)


def scatter_add(src, index, dim=-1, out=None, dim_size=None):
    return _reduce(src, index, dim, out, dim_size, "sum", 0)


def scatter_mean(src, index, dim=-1, out=None, dim_size=None):
    return _reduce(src, index, dim, out, dim_size, "mean", 0)


def scatter_max(src, index, dim=-1, out=None, dim_size=None):
    """torch_scatter 는 (값, argmax) 쌍을 준다. argmax 를 쓰는 데가 없어 인덱스는 -1 로 둔다.

    ponytail: argmax 미구현. 쓰는 코드가 생기면 그때 채울 것.
    """
    v = _reduce(src, index, dim, out, dim_size, "amax", float("-inf"))
    v = torch.nan_to_num(v, neginf=0.0)
    return v, torch.full_like(v, -1, dtype=torch.long)


if __name__ == "__main__":
    s = torch.tensor([1., 2., 3., 4.])
    i = torch.tensor([0, 0, 1, 1])
    assert torch.allclose(scatter_add(s, i, dim=0, dim_size=2), torch.tensor([3., 7.]))
    assert torch.allclose(scatter_mean(s, i, dim=0, dim_size=2), torch.tensor([1.5, 3.5]))
    assert torch.allclose(scatter_max(s, i, dim=0, dim_size=2)[0], torch.tensor([2., 4.]))

    # 뒤차원 브로드캐스트 — PartField 인코더가 쓰는 모양이다 (N, C)
    s2 = torch.arange(8.).reshape(4, 2)
    assert torch.allclose(scatter_mean(s2, i, dim=0, dim_size=2), torch.tensor([[1., 2.], [5., 6.]]))

    # 빈 칸은 0 이어야 한다 (include_self=False 라 -inf 가 새면 안 된다)
    assert torch.allclose(scatter_max(s, i, dim=0, dim_size=3)[0], torch.tensor([2., 4., 0.]))
    print("torch_scatter shim 자체검사 통과")
