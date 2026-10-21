# 모델124 짓기 실패 133 다시 짓기 — 그냥 다시(임시 파일 오류) → OCC 퍼지 합치기 tol 1e-3 → 1e-2 · 한 부품 120 초 넘으면 다음 판 · 10-21
# 사용(cadrille · ART_MEM_GB=10): 재시도124.py → 사양/ · 도면/ 덮어씀 · 「재시도」 칸에 쓴 tol 을 적음
import os, json, glob, numpy as np
import 모델124 as T, 모델120 as M, 조립124 as C
def 실패(i): return "실패" in open(T.D + f"사양/{i:05d}.json", encoding="utf-8").read()
def _하나(a):
    import 모델123 as Y
    i, tol = a; p = T.D + f"사양/{i:05d}.json"
    try:
        c = C.무작위(np.random.default_rng(124000 + i)); w = C.짓기(c, tol); assert w.val().isValid(), "isValid"; m = C.메시(w)[0]
        for nm, im in zip(T.뷰, Y.도면(m=m)): M.저장(T.D + f"도면/{i:05d}_{nm}.png", im)
        json.dump({"i": i, "코드": c, "가운데": [float(x) for x in m.bounds.mean(0)], "크기": float(m.extents.max()), "재시도": tol}, open(p, "w", encoding="utf-8"), ensure_ascii=False); return True
    except Exception: return False
if __name__ == "__main__":
    import time
    from multiprocessing import Process
    남 = sorted(json.load(open(p, encoding="utf-8"))["i"] for p in glob.glob(T.D + "사양/*.json") if "실패" in open(p, encoding="utf-8").read())
    print("실패", len(남), flush=True)
    for tol in (None, 1e-3, 1e-2):   # 걸린 일꾼이 다른 일을 막지 않게 부품마다 프로세스 하나 · 4 개씩 · 120 초 넘으면 terminate
        for b in range(0, len(남), 4):
            ps = [Process(target=_하나, args=((i, tol),)) for i in 남[b:b + 4]]; [q.start() for q in ps]; t0 = time.time()
            for q in ps: q.join(max(1, 120 - (time.time() - t0))); q.is_alive() and q.terminate()
        다음 = [i for i in 남 if 실패(i)]; print("tol", tol, "살림", len(남) - len(다음), "남음", len(다음), flush=True); 남 = 다음
    json.dump(남, open(T.D + "재시도_남음.json", "w")); print("끝 남음", len(남))
