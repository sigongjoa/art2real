# 판정기준51 대조군 다시 — 판정50 과 같고 깎기만 다각섬4(감사 고침) · 42 예측 · 정답 칠 천장 · 48³ · 712 개 · 조각 저장 · 10-15
# 사용(프로젝트 venv): 평가50.py <시작> <끝> · 평가50.py 판정
import sys, os, json, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; 조 = O + "평가52대조/"
def 잼(job):   # → (42 새, 정답칠 새, 정답칠 옛, 버린 수, 실패 이유)
    p, Y, D, Yt, Dt, 그림 = job
    try:
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37(그림, H); J.버린.clear()
        r = lambda s: float((J.점유_캐드(s) & 정).sum() / max((J.점유_캐드(s) | 정).sum(), 1))
        a = (r(J.깎기(몸, Y, D, H, True, J.다각섬4)), r(J.깎기(몸, Yt, Dt, H, True, J.다각섬4))); b = sum(J.버린.values()); return a + (r(J.옛깎기(몸, Yt, Dt, H, True)), b, "")
    except Exception as ex: return (0.0, 0.0, 0.0, 0, type(ex).__name__ + " " + str(ex)[:60])
if __name__ == "__main__":
    os.makedirs(조, exist_ok=True); v46 = np.load(O + "부피IoU_46_42.npy")
    if sys.argv[1] == "판정":
        v = {}; [v.update({k: x for k, x in zip(d["자리"], d["값"])}) for d in (json.load(open(조 + fn, encoding="utf-8")) for fn in os.listdir(조))]
        if len(v) < len(v46): sys.exit("아직 %d / %d" % (len(v), len(v46)))
        a = np.array([v[k][:4] for k in range(len(v46))]); 틀 = v46[:, 1]; n = len(a); 실 = collections.Counter(v[k][4] for k in v if v[k][4])
        결과 = {"부품": n, "실패": dict(실), "42": {"옛": float(v46[:, 0].mean()), "새": float(a[:, 0].mean()), "틀": float(틀.mean()), "망침 옛": int((v46[:, 0] < 틀 - .01).sum()), "망침 새": int((a[:, 0] < 틀 - .01).sum()), "나아짐 새": int((a[:, 0] > 틀 + .01).sum()), "크게망침 새": int((a[:, 0] < 틀 - .1).sum())},
              "정답칠 천장": {"옛": float(a[:, 2].mean()), "새": float(a[:, 1].mean())}, "버린 합": int(a[:, 3].sum()), "버린 부품": int((a[:, 3] > 0).sum()), "새가 옛보다 0.05 넘게 오른 부품": int((a[:, 0] > v46[:, 0] + .05).sum()), "내린 부품": int((a[:, 0] < v46[:, 0] - .05).sum())}
        g = 결과["42"]; 결과["판정"] = {"A": g["새"] >= g["옛"] + .005, "B": g["망침 새"] <= 247, "C": 결과["버린 합"] <= .05 * n}
        np.save(O + "부피IoU_52대조.npy", a); json.dump(결과, open(O + "결과52대조.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False)); sys.exit()
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Yt, Dt = d["Y"][te], d["D"][te].astype(np.float32); del d
    e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    범 = json.load(open(O + "범위46.json")); M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
    ks = list(range(int(sys.argv[1]), min(int(sys.argv[2]), len(범))))
    with Pool(2, maxtasksperchild=20) as pool: r = pool.map(잼, [(L[te[범[k]]], P[범[k]], PD[범[k]], Yt[범[k]], Dt[범[k]], (X[범[k]], F[범[k]], S[범[k]])) for k in ks], chunksize=2)
    실 = collections.Counter(x[4] for x in r if x[4]); print(ks[0], "~", ks[-1], "실패", sum(실.values()), dict(실), "버린", sum(x[3] for x in r), flush=True)
    if 실 and 실.most_common(1)[0][1] > len(r) // 2: sys.exit("절반 넘게 실패 — 환경부터 본다")
    json.dump({"자리": ks, "값": r}, open(조 + "%04d.json" % ks[0], "w", encoding="utf-8"), ensure_ascii=False)
