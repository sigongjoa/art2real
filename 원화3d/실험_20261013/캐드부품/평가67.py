# 판정기준67 C 평가 — 학습67_<이름>/예측.npy(시험 1003 × 6 × 128²) → 판0 과 같은 깎기 → 48³ → F@1 칸 · IoU · 울퉁 · 대조 판0(영역64) 와 판정 · 10-17
# 사용(venv · ART_MEM_GB=8): 평가67.py <이름> [일꾼=4] → out/설명/캐드부품/학습67_<이름>/값.npy · 칸.npy · 결과판정67.json
import sys, json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 하나(job):
    k, p, 층, 반, 틀b, 정b = job
    import trimesh, 짓기 as J, 평가51나 as E, 천장쪼개기52 as C, 자63 as A, 울퉁67 as U
    풀 = U.풀; 틀, 정 = 풀(틀b), 풀(정b); v = C.깎(틀, E.지도(층, 반), 48, True, [float(x) for x in 반])
    try:
        vv, ff, _ = J.정규메시(p); 점 = trimesh.sample.sample_surface(trimesh.Trimesh(vv, ff, process=False), A.점수, seed=0)[0]; F = A.F(A.칸표면(v, 1), 점)
    except Exception: F = np.nan
    return [F, float((v & 정).sum() / max((v | 정).sum(), 1)), *U.울퉁(v, 정)], np.packbits(v)
if __name__ == "__main__":
    이름 = sys.argv[1]; D = O + "학습67_%s/" % 이름; 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    P = np.load(D + "예측.npy", mmap_mode="r"); assert (np.load(D + "예측부품.npy") == te).all(); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    일 = [(k, L[예부[k]], np.array(P[범[k]]), 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in range(len(예부))]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4, maxtasksperchild=20) as pool: 출 = pool.map(하나, 일, chunksize=2)
    R = np.array([o[0] for o in 출], float); np.save(D + "값.npy", R); np.save(D + "칸.npy", np.stack([o[1] for o in 출]))
    V0 = np.load(O + "영역64/값.npy"); U0 = np.load(O + "울퉁67.npy")[:, 2]; 거 = np.load(O + "거름62.npy"); R0 = np.nan_to_num(R); c0 = np.nan_to_num(V0[:, 0])
    울 = lambda a, m: float(a[m, 0].sum() / max(a[m, 1].sum(), 1)); 전 = np.ones(len(R), bool); 망 = int((R0[:, 0] < c0 - .05).sum())
    결과 = {"판0 F 712 · 450": [float(c0.mean()), float(c0[거].mean())], "67 F 712 · 450": [float(R0[:, 0].mean()), float(R0[거, 0].mean())], "판0 울퉁 712 · 450": [울(U0, 전), 울(U0, 거)], "67 울퉁 712 · 450": [울(R0[:, 2:], 전), 울(R0[:, 2:], 거)],
          "67 IoU 712": float(R0[:, 1].mean()), "F 0.05 넘게 떨어진 부품": 망, "F 오른 부품(+0.01)": int((R0[:, 0] > c0 + .01).sum()), "실패": int(np.isnan(R[:, 0]).sum())}
    결과["판정"] = {"450 울퉁 ≤ 판0 × 0.7": 결과["67 울퉁 712 · 450"][1] <= .7 * 결과["판0 울퉁 712 · 450"][1], "450 F ≥ 판0 − 0.005": 결과["67 F 712 · 450"][1] >= 결과["판0 F 712 · 450"][1] - .005, "712 F ≥ 판0 − 0.005": 결과["67 F 712 · 450"][0] >= 결과["판0 F 712 · 450"][0] - .005, "빨간 선 망침 ≤ 50": 망 <= 50,
                   "목표(450 F ≥ 0.90 · 울퉁 ≤ 2 %)": 결과["67 F 712 · 450"][1] >= .9 and 결과["67 울퉁 712 · 450"][1] <= .02}
    json.dump(결과, open("결과판정67.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
