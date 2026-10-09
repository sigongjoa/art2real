# -*- coding: utf-8 -*-
"""조각 어휘와 미분되는 SDF · 렌더(6 방향 실루엣 · 깊이) — 조각0 (10-08)
좌표는 단위 상자 [0,1]³ · 각 칸 = (종류 확률, 중심 3, 크기 3)"""
import torch
종류 = {"빈칸": 0, "상자": 1, "원통z": 1, "원통x": 1, "원통y": 1, "공": 1, "구멍z": -1, "구멍x": -1, "구멍y": -1, "사각구멍": -1}
이름 = list(종류); 부호 = torch.tensor([종류[k] for k in 이름], dtype=torch.float32)

def _box(p, c, s):   # p (...,G,3) c,s (...,1,3)
    q = (p - c).abs() - s / 2
    return q.clamp(min=0).norm(dim=-1) + q.max(-1).values.clamp(max=0)

def _cyl(p, c, s, ax):
    d = p - c; o = [i for i in range(3) if i != ax]
    r = (s[..., o[0]] + s[..., o[1]]) / 4; h = s[..., ax] / 2
    q = torch.stack([d[..., o].norm(dim=-1) - r, d[..., ax].abs() - h], -1)
    return q.clamp(min=0).norm(dim=-1) + q.max(-1).values.clamp(max=0)

def 회전행렬(r):   # r (...,3) 라디안 x·y·z → (...,3,3) = Rz Ry Rx
    cx, cy, cz = r.cos().unbind(-1); sx, sy, sz = r.sin().unbind(-1); o, z = torch.ones_like(cx), torch.zeros_like(cx)
    Rx = torch.stack([o, z, z, z, cx, -sx, z, sx, cx], -1).reshape(*r.shape[:-1], 3, 3)
    Ry = torch.stack([cy, z, sy, z, o, z, -sy, z, cy], -1).reshape(*r.shape[:-1], 3, 3)
    Rz = torch.stack([cz, -sz, z, sz, cz, z, z, z, o], -1).reshape(*r.shape[:-1], 3, 3)
    return Rz @ Ry @ Rx

def sdf(p, c, s, r=None):
    """p (B,G,3) · c,s (B,K,3) · r (B,K,3) 회전(라디안 · 없으면 축 정렬) → (B,K,T,G) 종류별 SDF (빈칸은 큰 값)
    10-09 어휘 v2: 회전 — 기울인 상자를 빼면 쐐기 · 빗면 · 모따기(사전0 에서 빠진 것)"""
    p = p[:, None] - c[:, :, None]; s = s[:, :, None]
    if r is not None: p = p @ 회전행렬(r)[:, :, None].squeeze(2)   # 조각 좌표계로: q = Rᵀ(p − c) (행 벡터라 p @ R)
    c = torch.zeros_like(s)
    b = _box(p, c, s); cz, cx, cy = _cyl(p, c, s, 2), _cyl(p, c, s, 0), _cyl(p, c, s, 1)
    sp = p.norm(dim=-1) - s.mean(-1) / 2
    return torch.stack([torch.full_like(b, 9.0), b, cz, cx, cy, sp, cz, cx, cy, b], 2)

def 점유(p, prob, c, s, tau, r=None):
    """prob (B,K,T) → 전체 점유 (B,G): 더하기는 합집합, 빼기는 그 위에서 깎음 (확률로 섞음)"""
    o = torch.sigmoid(-sdf(p, c, s, r) / tau)                                   # (B,K,T,G)
    sg = 부호.to(p.device)
    add = (prob * (sg > 0))[..., None].mul(o).sum(2); sub = (prob * (sg < 0))[..., None].mul(o).sum(2)   # (B,K,G)
    A = 1 - torch.exp(torch.log1p(-add.clamp(max=1 - 1e-5)).sum(1)); S = torch.exp(torch.log1p(-sub.clamp(max=1 - 1e-5)).sum(1))
    return A * S

def 격자(n, dev):
    g = (torch.stack(torch.meshgrid(*[torch.arange(n, device=dev)] * 3, indexing="ij"), -1).float() + .5) / n * 1.1 - .05   # 상자 밖 조금
    return g.reshape(-1, 3)

def 보기(occ, n):
    """occ (B,n³) → 6 방향 (실루엣, 깊이) 각 (B,6,n,n) — 부드러운 첫 표면(투과율)"""
    o = occ.reshape(-1, n, n, n); S, D = [], []
    z = (torch.arange(n, device=occ.device).float() + .5) / n
    for ax in range(3):
        for fl in (False, True):
            v = o.movedim(ax + 1, -1); v = v.flip(-1) if fl else v
            T = torch.cumprod(torch.cat([torch.ones_like(v[..., :1]), 1 - v[..., :-1]], -1), -1); w = T * v
            S.append(w.sum(-1)); D.append((w * z).sum(-1) + (1 - w.sum(-1)))   # 빈 곳 깊이 = 1
    return torch.stack(S, 1), torch.stack(D, 1)

def 모서리(D):
    kx = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], device=D.device, dtype=D.dtype)[None, None]
    x = D.reshape(-1, 1, *D.shape[-2:])
    gx = torch.nn.functional.conv2d(x, kx, padding=1); gy = torch.nn.functional.conv2d(x, kx.transpose(-1, -2), padding=1)
    return (gx.abs() + gy.abs()).reshape(D.shape)

def 정답칸(Q, K):
    """정답 조각 목록 → (prob 원핫, c, s) K 칸 (남는 칸은 빈칸)"""
    P = torch.zeros(K, len(이름)); C = torch.full((K, 3), .5); S = torch.full((K, 3), .01); P[:, 0] = 1
    for i, (t, c, s) in enumerate(Q[:K]): P[i] = 0; P[i, 이름.index(t)] = 1; C[i] = torch.tensor(c); S[i] = torch.tensor(s)
    return P, C, S

def 정답칸r(Q, K):
    """v2: 조각에 회전(4 번째 값 · 없으면 0)까지 → (P, C, S, R)"""
    P, C, S = 정답칸([q[:3] for q in Q], K); Rt = torch.zeros(K, 3)
    for i, q in enumerate(Q[:K]):
        if len(q) > 3: Rt[i] = torch.tensor(q[3])
    return P, C, S, Rt

if __name__ == "__main__":   # 자기 검사: 상자에 z 구멍 → 위에서 본 실루엣 가운데가 비고, 옆에서 본 건 꽉 참
    n = 32; p = 격자(n, "cpu")[None]
    Q = [("상자", [.5, .5, .5], [.8, .8, .4]), ("구멍z", [.5, .5, .5], [.2, .2, 3])]; P, C, S = 정답칸(Q, 4)
    occ = 점유(p, P[None], C[None], S[None], 0.01); Sil, D = 보기(occ, n)
    assert Sil[0, 4, n // 2, n // 2] < .1 and Sil[0, 4, n // 2, n // 5] > .9, "위에서 본 구멍"
    assert Sil[0, 0, n // 2, n // 2] > .9, "옆에서 본 몸통"
    # v2: 45° 돌린 상자는 위에서 보면 마름모 — 축 정렬 모서리 칸은 비고 가운데는 참
    import math
    P, C, S, Rr = 정답칸r([("상자", [.5, .5, .5], [.5, .5, .3], [0, 0, math.pi / 4])], 2); o2 = 점유(p, P[None], C[None], S[None], 0.01, Rr[None]); Sl, _ = 보기(o2, n)
    assert Sl[0, 4, n // 2, n // 2] > .9 and Sl[0, 4, int(n * .3), int(n * .3)] < .1, "돌린 상자"
    assert torch.allclose(점유(p, P[None], C[None], S[None], 0.01), 점유(p, P[None], C[None], S[None], 0.01, torch.zeros(1, 2, 3)), atol=1e-5), "회전 0 = 예전과 같음"
    print("ok", float(occ.mean()))
