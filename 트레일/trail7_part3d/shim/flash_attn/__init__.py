# -*- coding: utf-8 -*-
"""flash_attn 대역 — torch SDPA 로. 리눅스 휠밖에 없어 윈도우에서 못 깐다.

OmniPart(=TRELLIS) 의 **희소 어텐션**은 sdpa 를 고를 수가 없다. 백엔드 목록이
`['xformers', 'flash_attn']` 뿐이라(`modules/part_synthesis/modules/sparse/__init__.py`)
env 로 못 피한다. xformers 도 윈도우 휠이 없다(0.0.28.post3 은 sdist 만 → 긴 경로에서 깨진다).
그래서 소스를 고치는 대신 **이름을 빌려준다** — 세 파일이 부르는 함수 6개만 채운다.

레이아웃 규약(flash-attn 원본): 배치형 [B, N, H, C], 가변길이형 [총토큰, H, C] + cu_seqlens.
SDPA 는 [B, H, N, C] 를 받으므로 축만 바꿔 끼운다. 인과마스크·드롭아웃은 안 쓴다(호출부가 안 준다).

    python shim/flash_attn/__init__.py     # 순진한 어텐션과 대조하는 자체검사

ponytail: 가변길이는 조각마다 파이썬 루프다. 조각이 수백 개면 느려진다 —
그때는 패딩해서 한 번에 부르거나 리눅스에서 정품을 쓸 것.
"""
import torch
import torch.nn.functional as F

__all__ = [
    "flash_attn_func", "flash_attn_qkvpacked_func", "flash_attn_kvpacked_func",
    "flash_attn_varlen_func", "flash_attn_varlen_qkvpacked_func", "flash_attn_varlen_kvpacked_func",
]


def _sdpa(q, k, v):
    """q,k,v [B, N, H, C] -> [B, N, H, C]."""
    o = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2))
    return o.transpose(1, 2)


def flash_attn_func(q, k, v, *a, **kw):
    return _sdpa(q, k, v)


def flash_attn_qkvpacked_func(qkv, *a, **kw):
    q, k, v = qkv.unbind(dim=2)                       # [B, N, 3, H, C]
    return _sdpa(q, k, v)


def flash_attn_kvpacked_func(q, kv, *a, **kw):
    k, v = kv.unbind(dim=2)                           # [B, M, 2, H, C]
    return _sdpa(q, k, v)


def _varlen(q, k, v, cu_q, cu_kv):
    """[총토큰, H, C] 를 조각마다 잘라 돌리고 다시 잇는다."""
    out = torch.empty_like(q)
    for i in range(len(cu_q) - 1):
        a, b = int(cu_q[i]), int(cu_q[i+1])
        c, d = int(cu_kv[i]), int(cu_kv[i+1])
        if b <= a:
            continue
        out[a:b] = _sdpa(q[a:b][None], k[c:d][None], v[c:d][None])[0]
    return out


def flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_k, *a, **kw):
    return _varlen(q, k, v, cu_seqlens_q, cu_seqlens_k)


def flash_attn_varlen_qkvpacked_func(qkv, cu_seqlens, *a, **kw):
    q, k, v = qkv.unbind(dim=1)                       # [총토큰, 3, H, C]
    return _varlen(q, k, v, cu_seqlens, cu_seqlens)


def flash_attn_varlen_kvpacked_func(q, kv, cu_seqlens_q, cu_seqlens_k, *a, **kw):
    k, v = kv.unbind(dim=1)                           # [총토큰, 2, H, C]
    return _varlen(q, k, v, cu_seqlens_q, cu_seqlens_k)


if __name__ == "__main__":
    torch.manual_seed(0)

    def naive(q, k, v):                                # [B, N, H, C]
        s = torch.einsum("bqhc,bkhc->bhqk", q, k) / q.shape[-1] ** 0.5
        return torch.einsum("bhqk,bkhc->bqhc", s.softmax(-1), v)

    B, N, H, C = 2, 7, 3, 8
    q, k, v = (torch.randn(B, N, H, C, dtype=torch.float64) for _ in range(3))
    assert torch.allclose(flash_attn_func(q, k, v), naive(q, k, v), atol=1e-9)
    qkv = torch.stack([q, k, v], dim=2)
    assert torch.allclose(flash_attn_qkvpacked_func(qkv), naive(q, k, v), atol=1e-9)
    assert torch.allclose(flash_attn_kvpacked_func(q, torch.stack([k, v], dim=2)), naive(q, k, v), atol=1e-9)

    # 가변길이: 길이 [3, 4] 두 조각이 배치 2개와 같은 답을 내야 한다
    cu = torch.tensor([0, 3, 7])
    qf, kf, vf = (x.reshape(-1, H, C) for x in (q[:1, :3], k[:1, :3], v[:1, :3]))
    q2 = torch.cat([q[0, :3], q[1, :4]]); k2 = torch.cat([k[0, :3], k[1, :4]]); v2 = torch.cat([v[0, :3], v[1, :4]])
    got = flash_attn_varlen_func(q2, k2, v2, cu, cu)
    want = torch.cat([naive(q[0:1, :3], k[0:1, :3], v[0:1, :3])[0], naive(q[1:2, :4], k[1:2, :4], v[1:2, :4])[0]])
    assert torch.allclose(got, want, atol=1e-9), (got - want).abs().max()
    got = flash_attn_varlen_qkvpacked_func(torch.stack([q2, k2, v2], dim=1), cu)
    assert torch.allclose(got, want, atol=1e-9)
    got = flash_attn_varlen_kvpacked_func(q2, torch.stack([k2, v2], dim=1), cu, cu)
    assert torch.allclose(got, want, atol=1e-9)
    print("flash_attn shim 자체검사 통과")
