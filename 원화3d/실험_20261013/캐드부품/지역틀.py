# 판정기준51 — 여섯 방향 「지역 틀」로 그림 · 칸을 옮긴다(numpy · CAD 안 씀) · 10-15
# 지역 화소 (행 y, 열 x) · 지역 층 k(0 = 지역 w 의 위 끝 쪽) ↔ 세계 칸 128³(g 격자) — 여섯방향.R 과 같은 회전
import numpy as np
import 여섯방향 as S6
N = 128; g = S6.g; 칸 = S6.칸
def _세계칸(p): return np.clip(np.round((p + .55) / 칸 - .5).astype(int), 0, N - 1)
_모 = {}
def 모으기(k):   # → (3, N, N, N) 세계 칸 번호 [y, x, 층] · 층 0 = 지역 w 가장 큼
    if k not in _모:
        r = S6.R(*S6.방향[k]); Y, Xx, K = np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij")
        L = np.stack([g[Xx], -g[Y], g[::-1][K]], -1); _모[k] = np.moveaxis(_세계칸(L @ r.T), -1, 0)
    return _모[k]
def 그림맞춤(X, F, S, k):   # 그 방향 법선 축의 선 그림을 지역 화소로 → (N, N) · 아래 · 뒤 · 반옆은 같은 그림의 거울
    r = S6.R(*S6.방향[k]); 축 = int(np.argmax(np.abs(r[:, 2]))); Y, Xx = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    p = np.stack([g[Xx], -g[Y], np.zeros_like(g[Xx])], -1) @ r.T; i = _세계칸(p)   # 세계 x · y · z 칸 번호
    if 축 == 2: return X[N - 1 - i[..., 1], i[..., 0]]   # 위 그림: 행 = −y · 열 = x
    if 축 == 1: return F[N - 1 - i[..., 2], i[..., 0]]   # 앞 그림: 행 = −z · 열 = x
    return S[N - 1 - i[..., 2], i[..., 1]]               # 옆 그림: 행 = −z · 열 = y
def 껍질(Xm, Fm, Sm):   # 채운 윤곽 셋 → 세계 칸 128³ [x, y, z]
    위 = Xm[::-1].T[:, :, None]          # Xm[행 = N−1−y, 열 = x] → [x, y]
    앞 = Fm[::-1].T[:, None, :]          # Fm[행 = N−1−z, 열 = x] → [x, z]
    옆 = Sm[::-1].T[None, :, :]          # Sm[행 = N−1−z, 열 = y] → [y, z]
    return 위 & 앞 & 옆
def 깊이층(칸128, k, h):   # 세계 칸 → 지역 깊이 층(0 ~ 16 · 17 = 통째) · 여섯방향.층 과 같은 내림
    i = 모으기(k); 기둥 = 칸128[i[0], i[1], i[2]]; 있 = 기둥.any(-1); 첫 = 기둥.argmax(-1)
    w = np.where(있, g[::-1][첫] + 칸 / 2, np.nan); d = S6.층(w, h); 단 = 2 * h / S6.층수
    return np.where(d > 2 * h, 17, np.round(d / 단)).astype(np.uint8)
