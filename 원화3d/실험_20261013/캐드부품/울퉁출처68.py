# 판정기준68 — 울퉁 출처: (가) 판0 층 (나) 정답 층 여섯 방향 (다) 판0 에서 한 방향만 정답 층 · 같은 깎기 · 울퉁 · IoU · 10-17
# 사용(venv · ART_MEM_GB=8): 울퉁출처68.py [일꾼=4] → out/설명/캐드부품/울퉁출처68.npy · 결과판정68.json
import sys, json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 하나(job):
    층p, 층t, 반, 틀b, 정b = job
    import 평가51나 as E, 천장쪼개기52 as C, 울퉁67 as U
    틀, 정 = U.풀(틀b), U.풀(정b); 깎 = lambda q: C.깎(틀, E.지도(q, 반), 48, True, [float(x) for x in 반])
    판들 = [층p, 층t] + [np.where(np.arange(6)[:, None, None] == d, 층t, 층p) for d in range(6)]
    out = []
    for q in 판들:
        v = 깎(q); out += [*U.울퉁(v, 정), float((v & 정).sum() / max((v | 정).sum(), 1))]
    return out
if __name__ == "__main__":
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    P = np.load(O + "학습51나_판0전체/예측.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 층, 반, 틀, 정 = z["층"], z["반"], z["틀"], z["정답"]
    일 = [(np.array(P[범[k]]), 층[예부[k]], 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in range(len(예부))]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4, maxtasksperchild=50) as pool: R = np.array(pool.map(하나, 일, chunksize=4), float).reshape(len(예부), 8, 3)
    np.save(O + "울퉁출처68.npy", R); 거 = np.load(O + "거름62.npy"); 울 = lambda m, j: float(R[m, j, 0].sum() / max(R[m, j, 1].sum(), 1))
    이름 = ["(가) 판0", "(나) 정답 층"] + ["(다) 방향 %d 만 정답" % d for d in range(6)]; 전 = np.ones(len(R), bool)
    결과 = {nm: {"울퉁 450": 울(거, j), "울퉁 712": 울(전, j), "IoU 712": float(R[:, j, 2].mean())} for j, nm in enumerate(이름)}
    a, b = 결과["(가) 판0"]["울퉁 450"], 결과["(나) 정답 층"]["울퉁 450"]
    결과["읽기"] = "표현이 주범" if b >= .7 * a else "모델이 주범" if b <= .3 * a else "둘 다"
    json.dump(결과, open("결과판정68.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
