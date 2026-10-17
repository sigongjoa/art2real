# 판정기준69 평가 — 학습69_<이름>/예측.npy(32 단계) → 같은 깎기(층수 32 · 내림 없이 깊이 = 층 × 단) → 48³ → F@1 칸 · IoU · 울퉁 · 대조 판0(영역64) 와 판정 · 10-17
# 사용(venv · ART_MEM_GB=8): 평가69.py <이름 | 천장32> [일꾼=4] → out/설명/캐드부품/학습69_<이름>/ (천장32 = 정답 32 단계 층을 그대로 깎음) · 결과판정69_<이름>.json
import sys, json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 하나(job):
    k, p, 층, 반, 틀b, 정b = job
    import trimesh, 짓기 as J, 평가51나 as E, 천장쪼개기52 as C, 자63 as A, 울퉁67 as U
    풀 = U.풀; 틀, 정 = 풀(틀b), 풀(정b); h = [float(x) for x in 반]; w = {d: np.where(층[j] == 32, np.nan, hh - 층[j] * (2 * hh / 32)) for j, (d, hh) in enumerate(zip(__import__("여섯방향").방향, h))}; v = C.깎(틀, w, 48, False, h)
    try:
        vv, ff, _ = J.정규메시(p); 점 = trimesh.sample.sample_surface(trimesh.Trimesh(vv, ff, process=False), A.점수, seed=0)[0]; F = A.F(A.칸표면(v, 1), 점)
    except Exception: F = np.nan
    return [F, float((v & 정).sum() / max((v | 정).sum(), 1)), *U.울퉁(v, 정)], np.packbits(v)
if __name__ == "__main__":
    이름 = sys.argv[1]; D = O + ("학습69_%s/" % 이름 if 이름 != "천장32" else "천장32/"); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    import os; os.makedirs(D, exist_ok=True); 층32 = np.load(O + "층32.npy", mmap_mode="r"); P = 층32[te] if 이름 == "천장32" else np.load(D + "예측.npy", mmap_mode="r"); assert 이름 == "천장32" or (np.load(D + "예측부품.npy") == te).all(); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    일 = [(k, L[예부[k]], np.array(P[범[k]]), 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in range(len(예부))]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4, maxtasksperchild=20) as pool: 출 = pool.map(하나, 일, chunksize=2)
    R = np.array([o[0] for o in 출], float); np.save(D + "값.npy", R); np.save(D + "칸.npy", np.stack([o[1] for o in 출]))
    V0 = np.load(O + "영역64/값.npy"); U0 = np.load(O + "울퉁67.npy")[:, 2]; 거 = np.load(O + "거름62.npy"); R0 = np.nan_to_num(R); c0 = np.nan_to_num(V0[:, 0])
    울 = lambda a, m: float(a[m, 0].sum() / max(a[m, 1].sum(), 1)); 전 = np.ones(len(R), bool); 망 = int((R0[:, 0] < c0 - .05).sum())
    결과 = {"판0 F 712 · 450": [float(c0.mean()), float(c0[거].mean())], "새 F 712 · 450": [float(R0[:, 0].mean()), float(R0[거, 0].mean())], "판0 울퉁 712 · 450": [울(U0, 전), 울(U0, 거)], "새 울퉁 712 · 450": [울(R0[:, 2:], 전), 울(R0[:, 2:], 거)],
          "새 IoU 712": float(R0[:, 1].mean()), "F 0.05 넘게 떨어진 부품": 망, "F 오른 부품(+0.01)": int((R0[:, 0] > c0 + .01).sum()), "실패": int(np.isnan(R[:, 0]).sum())}
    결과["판정"] = {"450 울퉁 ≤ 판0 − 1 %p": 결과["새 울퉁 712 · 450"][1] <= 결과["판0 울퉁 712 · 450"][1] - .01, "450 F ≥ 판0 − 0.005": 결과["새 F 712 · 450"][1] >= 결과["판0 F 712 · 450"][1] - .005, "712 F ≥ 판0 − 0.005": 결과["새 F 712 · 450"][0] >= 결과["판0 F 712 · 450"][0] - .005, "빨간 선 망침 ≤ 50": 망 <= 50,
                   "목표(450 F ≥ 0.90 · 울퉁 ≤ 32 천장 + 1 %p)": "천장32 결과와 맞대어 봄"}
    json.dump(결과, open("결과판정69_%s.json" % 이름, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
