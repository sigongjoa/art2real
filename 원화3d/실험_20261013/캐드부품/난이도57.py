# 판정기준57 준비 — 학습 부품의 난이도: 틀 IoU(실루엣만) · 천장(정답 깊이 칸 깎기 48³) → 쉬움(틀 ≥ .9) · 배울 것(틀 < .9 · 천장 ≥ .8) · 못 배움(천장 < .8) · 10-16 사용자 「쉬운 거 40 어려운 거 60 · 가르는 기준은?」
# 사용(venv): 난이도57.py [일꾼=2] → out/설명/캐드부품/난이도57.npy (부품 × [틀, 천장]) · 결과_난이도57.json
import sys, json, numpy as np
from multiprocessing import Pool
import 여섯방향 as S6, 평가51나 as E, 천장쪼개기52 as C
O = "G:/art2real/out/설명/캐드부품/"; 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
def 하나(job):
    층, 반, 정, 틀 = job; 정, 틀 = 풀(정), 풀(틀); r = lambda a: float((a & 정).sum() / max((a | 정).sum(), 1))
    try: return [r(틀), r(C.깎(틀, E.지도(층, 반), 48, True, [float(x) for x in 반]))]
    except Exception: return [r(틀), -1.0]
if __name__ == "__main__":
    z = np.load(O + "데이터51.npz"); 층, 반, 정, 틀, ok = z["층"], z["반"], z["정답"], z["틀"], z["ok"]; 시 = np.load(O + "데이터.npz")["시험"]; n = len(층)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2, maxtasksperchild=200) as pool: R = np.array(pool.map(하나, [(층[i], 반[i], 정[i], 틀[i]) for i in range(n)], chunksize=16))
    np.save(O + "난이도57.npy", R); 찬 = 정.any(1); tr = ~시 & ok & 찬; t, c = R[:, 0], R[:, 1]
    묶 = lambda m: {"쉬움(틀 ≥ .9)": int((m & (t >= .9)).sum()), "배울 것(틀 < .9 · 천장 ≥ .8)": int((m & (t < .9) & (c >= .8)).sum()), "못 배움(천장 < .8)": int((m & (c < .8)).sum()), "합": int(m.sum()), "천장 실패": int((m & (c < 0)).sum())}
    결과 = {"학습(판0 이 쓴 부품)": 묶(tr), "시험": 묶(시), "학습 틀 평균": float(t[tr].mean()), "학습 천장 평균": float(c[tr][c[tr] >= 0].mean()), "틀 분위(학습 10·25·50·75·90)": [float(x) for x in np.percentile(t[tr], [10, 25, 50, 75, 90])]}
    json.dump(결과, open(O + "결과_난이도57.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
