# 판정기준51 (나) 평가 — 예측 깊이 층(여섯 방향) → 틀에서 CadQuery 여섯 방향 깎기 → 712 개 새 채점기 48³ · 조각 저장 · 10-15
# 사용(venv): 평가51나.py <이름> <시작> <끝> [일꾼] · 평가51나.py <이름> 판정
import sys, os, json, time, collections, numpy as np
from multiprocessing import Pool
from scipy.ndimage import label
import 짓기 as J, 여섯방향 as S6, 여섯방향_빠른 as S6빠
O = "G:/art2real/out/설명/캐드부품/"
def 지도(층, 반):   # 층(6, 128, 128) → 여섯방향.깎기 가 받는 지역 w(같은 층으로 내려감)
    out = {}
    for n, k in enumerate(S6.방향):
        h = float(반[n]); 단 = 2 * h / S6.층수; out[k] = np.where(층[n] == 17, np.nan, h - 층[n] * 단)
    return out
def 하나(job):
    p, 그림, 층, 반 = job; t0 = time.time()
    try:
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37(그림, H); 틀 = J.점유_캐드(몸); 지 = 지도(층, 반); k = S6.칸깎기(틀, 몸, 지)
        r = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1)); K = np.ones((3, 3, 3))
        try: s, 정보 = S6빠.지킴짓기(몸, 지); 버 = 정보.get("퍼지다시", 0); 빈 = not s.vals(); c = np.zeros_like(틀) if 빈 else J.점유_캐드(s); 유 = True if 빈 else bool(s.val().isValid()); 초과 = False
        except TimeoutError: c = np.zeros_like(틀); 버 = 0; 유 = False; 초과 = True
        return {"틀": r(틀, 정), "CAD": r(c, 정), "칸": r(k, 정), "유효": 유, "시간초과": 초과, "버린": 버, "덩정": int(label(정, K)[1]), "덩CAD": int(label(c, K)[1]), "초": time.time() - t0, "실패": ""}
    except Exception as ex: return {"실패": type(ex).__name__ + " " + str(ex)[:60], "초": time.time() - t0}
if __name__ == "__main__":
    이름 = sys.argv[1]; D = O + "학습51나_%s/" % 이름; 조 = D + "평가/"; os.makedirs(조, exist_ok=True); 범 = json.load(open(O + "범위46.json"))
    if sys.argv[2] == "판정":
        v = {}; [v.update({k: x for k, x in zip(d["자리"], d["값"])}) for d in (json.load(open(조 + fn, encoding="utf-8")) for fn in os.listdir(조))]
        if len(v) < len(범): sys.exit("아직 %d / %d" % (len(v), len(범)))
        R = [v[k] for k in range(len(범))]; R0 = [x if not x["실패"] else {"틀": 0, "CAD": 0, "칸": 0} for x in R]; ok = [x for x in R if not x["실패"]]
        a = np.array([x["CAD"] for x in R0]); 틀 = np.array([x["틀"] for x in R0]); 칠천장 = np.load(O + "부피IoU_50.npy")[:, 1]; 낮 = 칠천장 < .5
        결과 = {"부품": len(R), "실패": dict(collections.Counter(x["실패"] for x in R if x["실패"])), "CAD 평균": float(a.mean()), "칸 평균": float(np.mean([x["칸"] for x in R0])), "틀": float(틀.mean()),
              "망침": int((a < 틀 - .01).sum()), "크게망침": int((a < 틀 - .1).sum()), "칠 천장 < 0.5 인 168": float(a[낮].mean()), "조각내기": int(sum(x["덩정"] == 1 and x["덩CAD"] > 1 for x in ok)),
              "CAD 유효": int(sum(x["유효"] for x in ok)), "시간초과": int(sum(x["시간초과"] for x in ok)), "버린 합": int(sum(x["버린"] for x in ok))}
        결과["판정(첫 판)"] = {"A ≥ 0.683": 결과["CAD 평균"] >= .683, "B 망침 ≤ 213": 결과["망침"] <= 213, "C 168 ≥ 0.30": 결과["칠 천장 < 0.5 인 168"] >= .3, "E 유효 100 %": 결과["CAD 유효"] == len(R)}
        np.save(D + "부피IoU.npy", np.array([[x["CAD"], x["칸"], x["틀"]] for x in R0])); json.dump(결과, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False)); sys.exit()
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    반 = np.load(O + "데이터51.npz")["반"]; P = np.load(D + "예측.npy", mmap_mode="r"); 예부 = list(np.load(D + "예측부품.npy")); 자 = {int(i): n for n, i in enumerate(예부)}
    ks = list(range(int(sys.argv[2]), min(int(sys.argv[3]), len(범)))); 일꾼 = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    pool = Pool(일꾼, maxtasksperchild=10); 일 = [pool.apply_async(하나, ((L[te[범[k]]], (X[범[k]], F[범[k]], S[범[k]]), np.array(P[자[int(te[범[k]])]]), 반[te[범[k]]]),)) for k in ks]; r = []
    for k, a in zip(ks, 일):   # 천장51 과 같이 — OCC 안에서 멈춘 부품은 200 초에 강제 시간초과(판정기준51 고침)
        try: r.append(a.get(timeout=200))
        except Exception as ex: r.append({"실패": "강제 시간초과 " + type(ex).__name__, "초": 200.0}); print("강제 시간초과", k, flush=True)
    pool.terminate()
    실 = collections.Counter(x["실패"] for x in r if x["실패"]); print(ks[0], "~", ks[-1], "실패", sum(실.values()), dict(실), "CAD %.3f" % np.mean([x.get("CAD", 0) for x in r]), flush=True)
    if 실 and 실.most_common(1)[0][1] > len(r) // 2: sys.exit("절반 넘게 실패 — 환경부터 본다")
    json.dump({"자리": ks, "값": r}, open(조 + "%04d.json" % ks[0], "w", encoding="utf-8"), ensure_ascii=False)
