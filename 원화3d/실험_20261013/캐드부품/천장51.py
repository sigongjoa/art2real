# 판정기준51 0 · 1 단계 — 정답 감사 + CAD 여섯 방향 천장(정답 깊이) · 712 개 · 48³ · 조각 저장 · 10-15
# 사용(프로젝트 venv): 천장51.py <시작> <끝> · 천장51.py 판정
import sys, os, json, time, collections, numpy as np
from multiprocessing import Pool
import 짓기 as J, 여섯방향 as S6, 여섯방향_빠른 as S6빠
O = "G:/art2real/out/설명/캐드부품/"; 조 = O + "천장51c/"   # 10-15 지킴짓기 판(속도51: 불리언 한 번 · 7.7 배) · 51/ 은 철회 · 51b/(다각섬4 불리언)는 너무 느려 멈춤
def 하나(job):   # → dict
    p, 그림 = job; t0 = time.time()
    try:
        import trimesh
        from scipy.ndimage import label
        v, f, H = J.정규메시(p); 정 = J.점유_메시(v, f); 정96 = J.점유_메시(v, f, 96); K = np.ones((3, 3, 3))
        닫 = bool(trimesh.Trimesh(v, f, process=False).is_watertight); d48, d96 = int(label(정, K)[1]), int(label(정96, K)[1])
        몸, _ = J.몸통37(그림, H); 틀 = J.점유_캐드(몸); 지 = S6.깊이지도(v, f); k = S6.칸깎기(틀, 몸, 지)
        try: s, 정보 = S6빠.지킴짓기(몸, 지); 버 = 정보.get("퍼지다시", 0); c = J.점유_캐드(s); 유 = bool(s.val().isValid()); 초과 = False
        except TimeoutError: c = np.zeros_like(틀); 버 = 0; 유 = False; 초과 = True
        r = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
        return {"틀": r(틀, 정), "CAD": r(c, 정), "칸": r(k, 정), "CAD대칸": r(c, k), "유효": 유, "시간초과": 초과, "버린": 버, "닫힘": 닫, "덩48": d48, "덩96": d96, "빈": int(정.sum() == 0), "초": time.time() - t0, "실패": ""}
    except Exception as ex: return {"실패": type(ex).__name__ + " " + str(ex)[:60], "초": time.time() - t0}
if __name__ == "__main__":
    os.makedirs(조, exist_ok=True); 범 = json.load(open(O + "범위46.json"))
    if sys.argv[1] == "판정":
        v = {}; [v.update({k: x for k, x in zip(d["자리"], d["값"])}) for d in (json.load(open(조 + fn, encoding="utf-8")) for fn in os.listdir(조))]
        if len(v) < len(범): sys.exit("아직 %d / %d" % (len(v), len(범)))
        R = [v[k] for k in range(len(범))]; 실 = collections.Counter(x["실패"] for x in R if x["실패"]); ok = [x for x in R if not x["실패"]]; n = len(R)
        깨 = [x["빈"] or not x["닫힘"] or x["덩96"] > x["덩48"] + 3 for x in ok]
        m = lambda key, xs: float(np.mean([x.get(key, 0.0) for x in xs])) if xs else 0.0
        R0 = [x if not x["실패"] else {"틀": 0, "CAD": 0, "칸": 0} for x in R]
        결과 = {"부품": n, "실패": dict(실), "평균(실패 0 점)": {k: m(k, R0) for k in ("틀", "CAD", "칸")}, "CAD 대 칸": m("CAD대칸", ok), "CAD 유효": int(sum(x["유효"] for x in ok)), "시간초과": int(sum(x.get("시간초과", False) for x in ok)), "버린 합": int(sum(x["버린"] for x in ok)),
              "정답 감사": {"빈": int(sum(x["빈"] for x in ok)), "안 닫힘": int(sum(not x["닫힘"] for x in ok)), "96 덩어리 > 48 + 3": int(sum(x["덩96"] > x["덩48"] + 3 for x in ok)), "깨짐 합": int(sum(깨))},
              "깨짐 뺀 평균": {k: m(k, [x for x, b in zip(ok, 깨) if not b]) for k in ("틀", "CAD", "칸")}, "초 합": float(sum(x["초"] for x in R))}
        결과["판정"] = {"천장 ≥ 0.80": 결과["평균(실패 0 점)"]["CAD"] >= .8, "CAD 대 칸 ≥ 0.95": 결과["CAD 대 칸"] >= .95, "CAD 유효 100 %": 결과["CAD 유효"] == len(ok) and not 실, "시간초과 0": 결과["시간초과"] == 0}
        json.dump(결과, open(O + "결과51c_천장.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); json.dump(R, open(O + "천장51c_전부.json", "w", encoding="utf-8"), ensure_ascii=False); print(json.dumps(결과, ensure_ascii=False)); sys.exit()
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e; L = json.load(open(O + "목록.json", encoding="utf-8"))
    ks = list(range(int(sys.argv[1]), min(int(sys.argv[2]), len(범)))); 일꾼 = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    pool = Pool(일꾼, maxtasksperchild=10); 일 = [pool.apply_async(하나, ((L[te[범[k]]], (X[범[k]], F[범[k]], S[범[k]])),)) for k in ks]; t1 = time.time(); r = []
    for k, a in zip(ks, 일):   # 부품 하나가 OCC 안에서 멈추면 마감이 못 잡는다(10-15 · 600 조각 21 분) — 일 하나당 200 초 넘으면 강제 시간초과로 적고 끝에 일꾼을 죽인다
        try: r.append(a.get(timeout=200))
        except Exception as ex: r.append({"실패": "강제 시간초과 " + type(ex).__name__, "초": 200.0}); print("강제 시간초과", k, flush=True)
    pool.terminate()
    실 = collections.Counter(x["실패"] for x in r if x["실패"]); print(ks[0], "~", ks[-1], "실패", sum(실.values()), dict(실), "CAD %.3f" % np.mean([x.get("CAD", 0) for x in r]), "%.0f 초" % sum(x["초"] for x in r), flush=True)
    if 실 and 실.most_common(1)[0][1] > len(r) // 2: sys.exit("절반 넘게 실패 — 환경부터 본다")
    json.dump({"자리": ks, "값": r}, open(조 + "%04d.json" % ks[0], "w", encoding="utf-8"), ensure_ascii=False)
