# 천장 쪼개기 — 「정답 깊이를 넣어도 왜 0.80 인가」(사용자 10-15) · 여섯 방향 칸 깎기(numpy · CAD 안 지음 · CAD 대 칸 0.96)에서 손실을 하나씩 끈다 · 712 개
# ① 지금(틀 · 깊이 16 층 · 48³)  ② 층 내림 끔(깊이 그대로)  ③ ② + 틀 대신 상자  ④ ③ 을 96³ 로 채점  ⑤ 정답 칸 48³ 대 96³ 을 48 로 줄인 것(채점 격자만의 몫)
# 남는 틈 = 여섯 방향에서 안 보이는 모양(속 빈 곳 · 언더컷)
import sys, json, numpy as np
from multiprocessing import Pool
import 짓기 as J, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"
def 깎(바탕, 지도, n, 내림, h들):   # 바탕 칸 n³ 에서 여섯 방향 깊이로 깎기 · 내림=False 면 깊이 그대로
    G = (np.arange(n) + .5) / n * 1.1 - .55; P = np.stack(np.meshgrid(G, G, G, indexing="ij"), -1).reshape(-1, 3); q = 바탕.reshape(-1).copy()
    for (k, (축, 도)), h in zip(S6.방향.items(), h들):
        r = S6.R(축, 도); w = 지도[k]; 깊 = S6.층(w, h) if 내림 else np.where(np.isnan(w), 2 * h + .1, h - w); L = P @ r
        x = np.clip(np.round((L[:, 0] + .55) / S6.칸 - .5).astype(int), 0, S6.N - 1); y = np.clip(np.round((-L[:, 1] + .55) / S6.칸 - .5).astype(int), 0, S6.N - 1)
        q &= ~(L[:, 2] > h - 깊[y, x])
    return q.reshape(n, n, n)
def 하나(job):
    p, 그림 = job
    try:
        v, f, H = J.정규메시(p); 몸, _ = J.몸통37(그림, H); 지 = S6.깊이지도(v, f); r = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
        h틀 = [S6.반높이(몸, S6.R(*S6.방향[k])) for k in S6.방향]; lo, hi = v.min(0), v.max(0); 꼭 = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        h상자 = [float((꼭 @ S6.R(*S6.방향[k]))[:, 2].max()) for k in S6.방향]; 정48, 정96 = J.점유_메시(v, f), J.점유_메시(v, f, 96)
        틀48 = J.점유_캐드(몸); 상자 = lambda n: np.ones((n,) * 3, bool)
        a = r(깎(틀48, 지, 48, True, h틀), 정48); b = r(깎(틀48, 지, 48, False, h틀), 정48); c = r(깎(상자(48), 지, 48, False, h상자), 정48); d = r(깎(상자(96), 지, 96, False, h상자), 정96)
        줄 = 정96.reshape(48, 2, 48, 2, 48, 2).any((1, 3, 5)); e = r(줄, 정48)
        return [a, b, c, d, e, ""]
    except Exception as ex: return [0, 0, 0, 0, 0, type(ex).__name__]
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8")); 범 = json.load(open(O + "범위46.json"))
    with Pool(4, maxtasksperchild=20) as pool: R = pool.map(하나, [(L[te[j]], (X[j], F[j], S[j])) for j in 범], chunksize=4)
    a = np.array([x[:5] for x in R], float); 실 = sum(1 for x in R if x[5]); np.save(O + "천장쪼개기52.npy", a)
    이름 = ["① 지금(틀 · 16 층 · 48³)", "② 층 내림 끔", "③ ② + 틀 대신 상자", "④ ③ 을 96³ 로 채점", "⑤ 정답 96³ 를 48 로 줄여 정답 48³ 와(채점 격자 몫)"]
    결과 = {n: float(v) for n, v in zip(이름, a.mean(0))}; 결과["실패"] = 실; 결과["0.9 넘음(④)"] = int((a[:, 3] >= .9).sum())
    json.dump(결과, open(O + "결과_천장쪼개기52.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
