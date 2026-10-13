# 1c 근본 원인 조사(systematic-debugging 1 단계) — 고치지 않고 경계마다 잰다 · 10-13
# ① 점수기: 정답 칸을 깎으면 IoU 가 오르나  ② 아무 데나 깎은 후보가 점수를 올리는 비율  ③ 처음 모델이 찍는 위치  ④ 정답 근처 ± 흔들 폭에서 오르나
import numpy as np, json
from multiprocessing import Pool
import 캐드점수2 as K, 학습3 as T
없음 = [(0, 0, 0, 0, 0)] * 3
if __name__ == "__main__":
    import torch
    g = np.random.default_rng(2027); P = [K.무작위(g) for _ in range(200)]
    with Pool(6) as pool:
        M = pool.map(K.정답, P); keep = [i for i, m in enumerate(M) if m is not None and any(c[0] for c in P[i]["칸"])][:60]
        P = [P[i] for i in keep]; M = [M[i] for i in keep]; X = np.stack([K.그림(p) for p in P]); Bs = [T.바탕맞춤(x) for x in X]
        바 = np.array(pool.map(T.점수, [(b, 없음, m) for b, m in zip(Bs, M)]))
        정 = np.array(pool.map(T.점수, [(b, p["칸"], m) for b, p, m in zip(Bs, P, M)]))
        print("① 점수기 — 특징 있는 시험 60: 바탕만 %.3f · 정답 칸 깎기 %.3f (오른 비율 %.0f%%)" % (바.mean(), 정.mean(), 100 * (정 > 바 + 1e-3).mean()))
        r = np.random.default_rng(1); 잡 = []
        for b, m in zip(Bs, M):
            for _ in range(10):
                t = int(r.integers(1, 4)); 잡.append((b, [(t, r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(1, 12), r.uniform(1.5, 4.5))] + 없음[:2], m))
        무 = np.array(pool.map(T.점수, 잡)).reshape(len(Bs), 10)
        print("② 아무 데나 한 칸 깎기 600 후보: 바탕만보다 오른 비율 %.1f%% · 평균 변화 %+.3f" % (100 * (무 > 바[:, None] + 1e-3).mean(), (무 - 바[:, None]).mean()))
        m_ = T.망만들기()(); m_.eval()
        with torch.no_grad(): cl, cv = m_(torch.tensor(X))
        xy = cv[..., :2].numpy(); print("③ 처음 모델이 찍는 위치: x 평균 %.2f 표준편차 %.2f · y 평균 %.2f 표준편차 %.2f (그림마다 다른가)" % (xy[..., 0].mean(), xy[..., 0].std(), xy[..., 1].mean(), xy[..., 1].std()))
        for s in (0.3, 1.0, 1.65):
            잡 = []
            for b, p, m in zip(Bs, P, M):
                c0 = next(c for c in p["칸"] if c[0]);
                for _ in range(10): 잡.append((b, [(c0[0], c0[1] + r.normal(0, s), c0[2] + r.normal(0, s), c0[3] + r.normal(0, s), c0[4] + r.normal(0, s))] + 없음[:2], m))
            근 = np.array(pool.map(T.점수, 잡)).reshape(len(Bs), 10)
            print("④ 정답 첫 칸 ± 흔들 폭 %.2f mm: 바탕만보다 오른 비율 %.1f%% · 평균 변화 %+.3f" % (s, 100 * (근 > 바[:, None] + 1e-3).mean(), (근 - 바[:, None]).mean()))
