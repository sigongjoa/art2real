# 학습 이상 의심 — 입력(입력51 채운 윤곽 · 선)과 정답(층32 < 32 윤곽)이 화소 단위로 맞나 · 방향마다 IoU · 뒤집기 · 1~2 화소 밀기 중 최선 · 10-20
# 사용: 정렬104.py → 출력만
import numpy as np, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; 입 = np.load(O + "입력51.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r"); ok = np.load(O + "데이터51.npz")["ok"]
idx = np.nonzero(ok)[0][::40][:200]
변 = {"그대로": lambda a: a, "좌우": lambda a: a[:, ::-1], "상하": lambda a: a[::-1], "전치": lambda a: a.T}
for dy in (-2, -1, 1, 2): 변[f"세로 {dy:+d}"] = lambda a, d=dy: np.roll(a, d, 0)
for dx in (-2, -1, 1, 2): 변[f"가로 {dx:+d}"] = lambda a, d=dx: np.roll(a, d, 1)
for n, k in enumerate(S6.방향):
    s = {v: [0, 0] for v in 변}
    for i in idx:
        a = 입[i, n, 1] > 0; g = 층[i, n] < 32
        for v, f in 변.items(): b = f(g); s[v][0] += (a & b).sum(); s[v][1] += (a | b).sum()
    r = {v: x[0] / max(x[1], 1) for v, x in s.items()}; best = max(r, key=r.get)
    print(f"{k}: 그대로 IoU {r['그대로']:.4f} · 최선 {best} {r[best]:.4f} · " + " ".join(f"{v} {r[v]:.3f}" for v in 변 if v != "그대로"))
