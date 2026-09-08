# -*- coding: utf-8 -*-
"""`torch_cluster.fps` 만 대신한다 — Windows 에 휠이 없고 nvcc 가 없어 소스 빌드가 안 된다.

PartCrafter 가 쓰는 곳은 `src/models/autoencoders/autoencoder_kl_triposg.py` 한 줄뿐이고
그것도 **인코더 경로**다. 추론(디코딩)에서는 안 불릴 수 있지만, 임포트만으로 죽는 걸
막고 불리더라도 맞게 돌도록 순수 torch 로 구현한다.

ponytail: O(N*k) 반복 최원점 추출. 점 수가 수만이면 느리다 —
그때는 torch_cluster 정품을 리눅스에서 깔거나 청크로 나눌 것.
"""
import torch

__all__ = ["fps"]


def fps(x: torch.Tensor, batch: torch.Tensor = None, ratio: float = 0.5,
        random_start: bool = True) -> torch.Tensor:
    """최원점 샘플링. x (N, D), batch (N,) 배치 인덱스 -> 뽑힌 점의 전역 인덱스 (M,)."""
    if x.dim() != 2:
        raise ValueError("fps expects (N, D), got %s" % (tuple(x.shape),))
    n = x.size(0)
    if batch is None:
        batch = x.new_zeros(n, dtype=torch.long)
    out = []
    for b in torch.unique(batch):
        idx = (batch == b).nonzero(as_tuple=True)[0]
        p = x[idx]
        m = max(int(round(float(ratio) * idx.numel())), 1)
        start = int(torch.randint(idx.numel(), (1,)).item()) if random_start else 0
        sel = [start]
        d = torch.cdist(p[start:start+1], p).squeeze(0)
        for _ in range(m - 1):
            nxt = int(torch.argmax(d).item())
            sel.append(nxt)
            d = torch.minimum(d, torch.cdist(p[nxt:nxt+1], p).squeeze(0))
        out.append(idx[torch.tensor(sel, device=x.device, dtype=torch.long)])
    return torch.cat(out) if out else x.new_empty(0, dtype=torch.long)


def _demo():
    torch.manual_seed(0)
    x = torch.randn(200, 3)
    i = fps(x, ratio=0.1, random_start=False)
    assert i.numel() == 20 and i.unique().numel() == 20, (i.numel(), i.unique().numel())
    b = torch.cat([torch.zeros(100, dtype=torch.long), torch.ones(100, dtype=torch.long)])
    j = fps(x, b, ratio=0.1, random_start=False)
    assert j.numel() == 20, j.numel()
    assert (b[j] == 0).sum() == 10 and (b[j] == 1).sum() == 10
    # 첫 점에서 제일 먼 점이 두 번째로 뽑혀야 한다
    y = torch.tensor([[0., 0.], [1., 0.], [10., 0.]])
    k = fps(y, ratio=2/3, random_start=False)
    assert set(k.tolist()) == {0, 2}, k.tolist()
    print("shim fps 자체검사 통과")


if __name__ == "__main__":
    _demo()
