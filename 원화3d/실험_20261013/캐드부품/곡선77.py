# 사용자 가설(10-18) 「모델이 곡선 · 임의 기울기를 못 배워 다각형으로 묘사한다」 — 부품마다 「축에 안 맞는 면 넓이 비율」(법선이 x · y · z 축과 8° 넘게 어긋난 면)
# → 450 개를 세 묶음(적음 · 중간 · 많음)으로 나눠 모델(학습69 판0) 대 천장(정답 32 단계 깎기)의 F · 울퉁 · 학습 부품 1000 개의 같은 비율 분포 · 10-18
# 사용(venv · ART_MEM_GB=8): 곡선77.py → 결과곡선77.json
import json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 비율(p):
    try:
        import 짓기 as J, trimesh
        v, f, _ = J.정규메시(p); m = trimesh.Trimesh(v, f, process=False); n = np.abs(m.face_normals); a = m.area_faces
        return float(a[n.max(1) < np.cos(np.radians(8))].sum() / max(a.sum(), 1e-12))
    except Exception: return np.nan
if __name__ == "__main__":
    L = json.load(open(O + "목록.json", encoding="utf-8")); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    tr = np.random.default_rng(77).choice(np.nonzero(~시)[0], 1000, replace=False)
    with Pool(6) as pool: r예 = np.array(pool.map(비율, [L[i] for i in 예부], chunksize=8)); r학 = np.array(pool.map(비율, [L[i] for i in tr], chunksize=8))
    거 = np.load(O + "거름62.npy"); M = np.nan_to_num(np.load(O + "학습69_판0/값.npy")); C = np.nan_to_num(np.load(O + "천장32/값.npy"))
    울 = lambda a, m: float(a[m, 2].sum() / max(a[m, 3].sum(), 1)); 결과 = {"학습 1000 비율 사분위(25 · 50 · 75 %)": np.nanpercentile(r학, [25, 50, 75]).round(3).tolist(), "시험 450 비율 사분위": np.nanpercentile(r예[거], [25, 50, 75]).round(3).tolist(), "묶음": {}}
    for 이름, lo, hi in [("적음 < 5 %", -1, .05), ("중간 5 ~ 30 %", .05, .3), ("많음 ≥ 30 %", .3, 2)]:
        m = 거 & (r예 >= lo) & (r예 < hi)
        결과["묶음"][이름] = {"부품": int(m.sum()), "모델 F": round(float(M[m, 0].mean()), 3), "천장 F": round(float(C[m, 0].mean()), 3), "모델 울퉁 %": round(100 * 울(M, m), 1), "천장 울퉁 %": round(100 * 울(C, m), 1)}
    np.save(O + "곡선77.npy", r예); json.dump(결과, open("결과곡선77.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
