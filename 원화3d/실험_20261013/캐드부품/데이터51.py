# 판정기준51 2 단계 데이터 — 부품 10,000 개마다: 틀 칸 48³ · 정답 칸 48³ · 여섯 방향 깊이 층(0 ~ 16 · 17 = 통째 · uint8 128²) · 방향마다 틀 반높이 · 10-15
# 깊이 층은 여섯방향.층 과 같은 내림 — CAD 깎기에 그대로 넣으면 천장51 과 같은 고체 · 조각 저장(npz) · 사용(venv): 데이터51.py <시작> <끝> [일꾼] · 데이터51.py 합치기
import sys, os, json, time, numpy as np
from multiprocessing import Pool
import 짓기 as J, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; 조 = O + "데이터51/"
def 하나(job):
    p, 그림 = job
    try:
        v, f, H = J.정규메시(p); 몸, _ = J.몸통37(그림, H); 지 = S6.깊이지도(v, f); 층, 반 = [], []
        for k, (축, 도) in S6.방향.items():
            h = S6.반높이(몸, S6.R(축, 도)); 단 = 2 * h / S6.층수; d = S6.층(지[k], h); 층.append(np.where(d > 2 * h, 17, np.round(d / 단)).astype(np.uint8)); 반.append(h)
        return np.packbits(J.점유_캐드(몸)), np.packbits(J.점유_메시(v, f)), np.stack(층), np.array(반, np.float32), ""
    except Exception as ex: return None, None, None, None, type(ex).__name__ + " " + str(ex)[:60]
if __name__ == "__main__":
    os.makedirs(조, exist_ok=True)
    if sys.argv[1] == "합치기":
        fs = sorted(f for f in os.listdir(조) if f.endswith(".npz")); 모 = {k: [] for k in ("틀", "정답", "층", "반", "ok")}
        for fn in fs:
            z = np.load(조 + fn); [모[k].append(z[k]) for k in 모]
        모 = {k: np.concatenate(v) for k, v in 모.items()}; print("부품", len(모["ok"]), "실패", int((~모["ok"]).sum())); np.savez(O + "데이터51.npz", **모); sys.exit()
    d = np.load(O + "데이터.npz"); n = len(d["H"]); X = d["X"]; del d; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    a, b = int(sys.argv[1]), min(int(sys.argv[2]), n); 일꾼 = int(sys.argv[3]) if len(sys.argv) > 3 else 4; t0 = time.time()
    with Pool(일꾼, maxtasksperchild=20) as pool: r = pool.map(하나, [(L[i], (X[i], F[i], S[i])) for i in range(a, b)], chunksize=2)
    실 = [x[4] for x in r if x[4]]; z0 = np.zeros(48 ** 3 // 8, np.uint8)
    np.savez(조 + "%05d.npz" % a, 틀=np.stack([x[0] if x[0] is not None else z0 for x in r]), 정답=np.stack([x[1] if x[1] is not None else z0 for x in r]),
             층=np.stack([x[2] if x[2] is not None else np.zeros((6, 128, 128), np.uint8) for x in r]), 반=np.stack([x[3] if x[3] is not None else np.zeros(6, np.float32) for x in r]), ok=np.array([not x[4] for x in r]))
    print(a, "~", b - 1, "실패", len(실), 실[:3], "%.0f 초" % (time.time() - t0), flush=True)
