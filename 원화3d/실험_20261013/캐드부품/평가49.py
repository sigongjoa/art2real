# 판정기준49 — 채점 격자 48³ → 96³ · 학습 없음 · 42 만 · 판정46 과 같은 712 개 · 10-15
# 사용(프로젝트 venv): 평가49.py 시험 8 · 평가49.py 낮|전부 <시작> <끝>(조각 · 조각마다 저장) · 평가49.py 판정 낮|전부
import sys, os, json, time, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; N = 96; 조 = O + "평가49/"
def 잼(job):   # 짓기.부피IoU 의 그림 길을 격자 N 으로 · → (IoU, 틀 IoU, 실패 이유) · 실패는 0 점으로 세되 이유를 찍는다(10-15 open3d 없는 파이썬이 말없이 전부 0)
    p, Y, D, 그림 = job
    try:
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f, N); 몸, _ = J.몸통37(그림, H); s = J.깎기(몸, Y, D, H, True)
        r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1)); return (r(J.점유_캐드(s, N)), r(J.점유_캐드(몸, N)), "")
    except Exception as ex: return (0.0, 0.0, type(ex).__name__ + " " + str(ex)[:60])
def 순번(무엇, v48): return [k for k in range(len(v48)) if v48[k, 1] < .3] if 무엇 == "낮" else list(range(len(v48)))   # 범위46 안의 자리
if __name__ == "__main__":
    무엇 = sys.argv[1]; v48 = np.load(O + "부피IoU_46_42.npy"); os.makedirs(조, exist_ok=True)
    if 무엇 == "판정":
        대 = sys.argv[2]; ks = 순번(대, v48); v = np.full((len(v48), 2), np.nan); 실 = collections.Counter()
        for fn in sorted(os.listdir(조)):
            if fn.endswith(".json"): d = json.load(open(조 + fn, encoding="utf-8")); [v.__setitem__(k, x[:2]) or (x[2] and 실.update([x[2]])) for k, x in zip(d["자리"], d["값"])]
        빠 = [k for k in ks if np.isnan(v[k, 0])]
        if 빠: sys.exit("아직 안 잰 자리 %d 개 (첫 %s)" % (len(빠), 빠[:5]))
        낮 = 순번("낮", v48); 결과 = {"실패": dict(실), "틀<0.3(48)": {"수": len(낮), "틀48": float(v48[낮, 1].mean()), "틀96": float(v[낮, 1].mean()), "42_48": float(v48[낮, 0].mean()), "42_96": float(v[낮, 0].mean())}}
        결과["판정"] = {"B": 결과["틀<0.3(48)"]["틀96"] >= 결과["틀<0.3(48)"]["틀48"] + .1}
        if 대 == "전부":
            n = len(v); a = {"평균": float(v[:, 0].mean()), "틀": float(v[:, 1].mean()), "0점": int((v[:, 0] == 0).sum()), "망침": int((v[:, 0] < v[:, 1] - .01).sum()), "크게망침": int((v[:, 0] < v[:, 1] - .1).sum())}
            결과.update({"부품": n, "96": a, "48": {"평균": float(v48[:, 0].mean()), "틀": float(v48[:, 1].mean())}}); 결과["판정"].update({"A": a["평균"] >= a["틀"] + .01, "C": a["망침"] / n < 354 / 803}); np.save(O + "부피IoU_49_42.npy", v)
        json.dump(결과, open(O + "결과49_%s.json" % 대, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False)); sys.exit()
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d
    e = np.load(O + "데이터_앞옆.npz"); Fr = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    범위 = json.load(open(O + "범위46.json")); M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
    ks = list(range(int(sys.argv[2]))) if 무엇 == "시험" else 순번(무엇, v48)[int(sys.argv[2]):int(sys.argv[3])]
    jobs = [(L[te[범위[k]]], P[범위[k]], PD[범위[k]], (X[범위[k]], Fr[범위[k]], S[범위[k]])) for k in ks]; t = time.time()
    with Pool(2, maxtasksperchild=20) as pool: r = pool.map(잼, jobs, chunksize=2)
    실 = collections.Counter(x[2] for x in r if x[2]); print("부품", len(ks), "초/부품 %.1f" % ((time.time() - t) / max(len(ks), 1)), "실패", sum(실.values()), dict(실), flush=True)
    if 실 and 실.most_common(1)[0][1] > len(r) // 2: sys.exit("절반 넘게 실패 — 환경부터 본다")
    if 무엇 == "시험": print(np.c_[v48[:len(ks)], np.array([x[:2] for x in r])].round(3)); sys.exit()
    json.dump({"자리": ks, "값": r}, open(조 + "%s_%04d.json" % (무엇, int(sys.argv[2])), "w", encoding="utf-8"), ensure_ascii=False)
