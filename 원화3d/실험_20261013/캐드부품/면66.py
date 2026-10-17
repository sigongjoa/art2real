# 판정기준66 — 면65 를 두 곳 고침: 맞춤 받기는 영역 모든 점으로 · 뚫림 / 막힘은 연결 덩어리로 나누고 작은 덩어리(< 30)만 뒤집음 · 10-17
# 사용(venv · ART_MEM_GB=8): 면66.py [일꾼=4] [QUICK] → out/설명/캐드부품/면66/ · 결과판정66.json
import sys, os, json, numpy as np
from multiprocessing import Pool
from scipy.ndimage import label
import 면65 as M5
O = "G:/art2real/out/설명/캐드부품/"; D = O + "면66/"; os.makedirs(D, exist_ok=True); 문턱, 조각, 안비 = .7, 30, .95
def 받나(z, f):   # 영역 모든 점 기준 — 65 의 버그(버린 점은 안 잼) 고침
    r = np.abs(z - f); return np.sqrt(np.mean(r ** 2)) <= 문턱 and (r <= 1).mean() >= 안비
def 덩어리맞춤(xx, yy, z, rng):
    for 차 in (1, 2):
        f, _ = M5.맞춤(xx, yy, z, 차)
        if 받나(z, f): return f
    f = M5.랜삭(xx.astype(float), yy.astype(float), z, rng); return np.where(np.isnan(f), z, f)
def 면묶기(층, 선, seed=0):
    L, n = label(~선); out = 층.astype(float).copy(); rng = np.random.default_rng(seed)
    for r in range(1, n + 1):
        m = L == r
        if m.sum() < 6: continue
        통 = m & (층 == 17); 막 = m & (층 != 17)
        for 쪽, 반대 in ((통, 막), (막, 통)):   # 작은 덩어리 뒤집기(뚫림 속 작은 막힘 → 뚫림 · 막힘 속 작은 구멍 → 막힘)
            Lc, nc = label(쪽)
            for q in range(1, nc + 1):
                c = Lc == q
                if c.sum() < 조각 and 반대.sum() >= 조각: 쪽[c] = False; 반대[c] = True
        out[통] = 17
        Lm, nm = label(막)
        for q in range(1, nm + 1):
            c = Lm == q; yy, xx = np.nonzero(c); z = np.where(층[c] == 17, np.nan, 층[c]).astype(float)
            if np.isnan(z).all(): continue
            z = np.where(np.isnan(z), np.nanmedian(z), z)   # 뒤집혀 막힘이 된 작은 구멍 = 덩어리 가운데 값에서 시작 · 맞춤이 채움
            out[c] = 덩어리맞춤(xx, yy, z, rng) if c.sum() >= 6 else z
    return np.clip(np.round(out), 0, 17).astype(np.uint8)
def 하나(job):   # 일꾼 프로세스에서도 고친 면묶기를 쓰게
    M5.면묶기 = 면묶기; return M5.하나(job)
if __name__ == "__main__":
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    P = np.load(O + "학습51나_판0전체/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]
    L = json.load(open(O + "목록.json", encoding="utf-8")); 쓸 = range(8) if "QUICK" in sys.argv else range(len(예부))
    일 = [(k, L[예부[k]], np.array(P[범[k]]), np.array(입[예부[k], :, 0]) > 0, 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in 쓸]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4, maxtasksperchild=20) as pool: 출 = pool.map(하나, 일, chunksize=2)
    R = np.array([o[0] for o in 출], float); V4 = np.load(O + "영역64/값.npy")[: len(R)]; V5 = np.load(O + "면65/값.npy")[: len(R)]
    if "QUICK" in sys.argv: print(np.round(np.c_[V4[:, 0], V4[:, 1], V5[:, 0], R], 3)); sys.exit()
    np.save(D + "값.npy", R); np.save(D + "칸.npy", np.stack([o[1] for o in 출])); R0 = np.nan_to_num(R); c0 = np.nan_to_num(V4[:, 0]); 망 = int((R0[:, 0] < c0 - .05).sum())
    결과 = {"712 F 대조": float(c0.mean()), "712 F 판정64": float(np.nan_to_num(V4[:, 1]).mean()), "712 F 판정65": float(np.nan_to_num(V5[:, 0]).mean()), "712 F 판정66": float(R0[:, 0].mean()), "712 IoU 판정66": float(R0[:, 1].mean()),
          "평평함 대조": float(R0[:, 2].mean()), "평평함 판정66": float(R0[:, 3].mean()), "F 0.05 넘게 떨어진 부품": 망, "F 오른 부품(+0.01)": int((R0[:, 0] > c0 + .01).sum()), "실패": int(np.isnan(R[:, 0]).sum()),
          "판정": {"F ≥ 대조 + 0.005": bool(R0[:, 0].mean() >= c0.mean() + .005), "평평함 절반": bool(R0[:, 3].mean() <= R0[:, 2].mean() / 2), "망침 ≤ 50": 망 <= 50}}
    json.dump(결과, open("결과판정66.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
