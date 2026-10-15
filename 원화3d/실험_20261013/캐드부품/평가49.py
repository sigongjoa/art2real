# 판정기준49 — 채점 격자 48³ → 96³ · 학습 없음 · 42 만 · 판정46 과 같은 712 개 · 10-15
import sys, json, time, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; N = 96
def 잼(job):   # 짓기.부피IoU 의 그림 길을 격자 N 으로 · → (IoU, 틀 IoU, 실패 이유) · 실패는 0 점으로 세되 이유를 찍는다(10-15 open3d 없는 파이썬이 말없이 전부 0)
    p, Y, D, 그림 = job
    try:
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f, N); 몸, _ = J.몸통37(그림, H); s = J.깎기(몸, Y, D, H, True)
        r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1)); return (r(J.점유_캐드(s, N)), r(J.점유_캐드(몸, N)), "")
    except Exception as ex: return (0.0, 0.0, type(ex).__name__ + " " + str(ex)[:60])
if __name__ == "__main__":
    몇 = int(sys.argv[1]) if len(sys.argv) > 1 else 0   # 몇 > 0: 앞에서 몇 개만(시간 · 결정성 확인)
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    범위 = json.load(open(O + "범위46.json")); v48 = np.load(O + "부피IoU_46_42.npy"); 범 = 범위[:몇] if 몇 else 범위
    M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
    jobs = [(L[te[j]], P[j], PD[j], (X[j], Fr[j], S[j])) for j in 범]; t = time.time()
    with Pool(2, maxtasksperchild=20) as pool: r = pool.map(잼, jobs, chunksize=4)
    실 = collections.Counter(x[2] for x in r if x[2]); v = np.array([x[:2] for x in r])
    print("실패", sum(실.values()), dict(실), flush=True)
    if 실 and 실.most_common(1)[0][1] > len(r) // 2: sys.exit("절반 넘게 실패 — 환경부터 본다")
    print("부품", len(범), "초/부품 %.1f" % ((time.time() - t) / len(범)), flush=True)
    if 몇: print(np.c_[v48[:몇], v].round(3)); sys.exit()
    np.save(O + "부피IoU_49_42.npy", v); n = len(범); 낮 = v48[:, 1] < .3
    결과 = {"부품": n, "96": {"평균": float(v[:, 0].mean()), "틀": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "망침": int((v[:, 0] < v[:, 1] - .01).sum()), "크게망침": int((v[:, 0] < v[:, 1] - .1).sum())},
          "48": {"평균": float(v48[:, 0].mean()), "틀": float(v48[:, 1].mean())},
          "틀<0.3(48)": {"수": int(낮.sum()), "틀48": float(v48[낮, 1].mean()), "틀96": float(v[낮, 1].mean()), "42_48": float(v48[낮, 0].mean()), "42_96": float(v[낮, 0].mean())}}
    a, b = 결과["96"], 결과["틀<0.3(48)"]
    결과["판정"] = {"A": a["평균"] >= a["틀"] + .01, "B": b["틀96"] >= b["틀48"] + .1, "C": a["망침"] / n < 354 / 803}
    json.dump(결과, open(O + "결과49.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
