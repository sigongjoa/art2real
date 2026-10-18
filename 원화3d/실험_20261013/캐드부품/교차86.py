# 판정기준86 — 다른 두 뷰의 선을 그 방향의 깊이 칸(32)에 맞춘 입력 · 화소 (u, v) · 칸 l 의 세계 점을 다른 두 뷰에 투영해 그 자리에 선(3×3 부풀림)이 있나 · 10-18
# 사람은 앞 · 옆 뷰에 그려진 높이를 읽는다(조사 research_CAD제작과정 B) — 지금 모델은 자기 뷰 선 + 바깥 윤곽 껍질만 봤다
import numpy as np, torch, torch.nn.functional as Fn
N = 128; 칸 = 1.1 / N; 층 = 32
def 준비(X, F, S, dev):   # (부품, N, N) 선 그림 셋 → (부품, 3, N, N) bool(부풀림) · GPU
    return Fn.max_pool2d(torch.tensor(np.stack([X, F, S], 1), device=dev).float(), 3, 1, 1) > 0
def _틀():
    import 여섯방향 as S6
    R = torch.tensor(np.stack([S6.R(*S6.방향[d]) for d in S6.방향]), dtype=torch.float32); 축 = R[:, :, 2].abs().argmax(1)
    다른 = {2: (1, 2), 1: (0, 2), 0: (0, 1)}; return R, torch.tensor([다른[int(a)] for a in 축])
_R, _다른 = _틀()
def 교차(뷰, idx, 방, 반):   # 뷰 (P, 3, N, N) bool · idx (B,) 부품 · 방 (B,) 방향 · 반 (B,) 반높이 → (B, 64, N, N) float
    dev = 뷰.device; B = len(idx); g = (torch.arange(N, device=dev) + .5) * 칸 - .55; out = []
    R = _R.to(dev)[방]; 다 = _다른.to(dev)[방]; h = 반.to(dev).float()
    for s in range(0, B, 8):
        sl = slice(s, s + 8); b = R[sl].shape[0]; hh = h[sl][:, None]
        w = hh - (torch.arange(층, device=dev).float()[None] + .5) * (2 * hh / 층)   # (b, 32)
        U = g[None, None, None, :].expand(b, 층, N, N); V = -g[None, None, :, None].expand(b, 층, N, N); W = w[:, :, None, None].expand(b, 층, N, N)
        L = torch.stack([U, V, W], -1); P = torch.einsum("bijkl,bml->bijkm", L, R[sl])   # 세계 = R @ 지역
        i = torch.clamp(torch.round((P + .55) / 칸 - .5), 0, N - 1).long(); ix, iy, iz = i[..., 0], i[..., 1], i[..., 2]
        행 = {0: N - 1 - iy, 1: N - 1 - iz, 2: N - 1 - iz}; 열 = {0: ix, 1: ix, 2: iy}   # 위: 행 = −y · 열 = x / 앞: 행 = −z · 열 = x / 옆: 행 = −z · 열 = y
        pi = torch.as_tensor(idx[sl], device=dev).long()[:, None, None, None].expand(b, 층, N, N); ch = []
        for c in range(2):
            v = 다[sl, c][:, None, None, None].expand(b, 층, N, N); r_ = torch.zeros_like(ix); q_ = torch.zeros_like(ix)
            for vv in range(3): m = v == vv; r_ = torch.where(m, 행[vv], r_); q_ = torch.where(m, 열[vv], q_)
            ch.append(뷰[pi, v, r_, q_])
        out.append(torch.cat(ch, 1).float())
    return torch.cat(out, 0)
