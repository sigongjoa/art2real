# 판정기준64 — 영역마다 높이 하나: 판0 깊이 층(여섯 방향 · 화소마다) → 그 방향 선 그림의 닫힌 영역마다 최빈값 → 같은 깎기 → 48³ · 대조(묶기 없음)와 표면 F · 평평함 · 10-17
# 사용(venv · ART_MEM_GB=8): 영역64.py [일꾼=4] [QUICK] → out/설명/캐드부품/영역64/ 칸 예측 둘(packbits) · 결과.json
import sys, os, json, numpy as np
from multiprocessing import Pool
from scipy.ndimage import label
O = "G:/art2real/out/설명/캐드부품/"; D = O + "영역64/"; os.makedirs(D, exist_ok=True)
def 묶기(층, 선):   # 층(128²) · 선(128² bool) → 영역(선 아닌 4 이웃 덩어리)마다 최빈 층 · 선 화소는 그대로
    L, n = label(~선); out = 층.copy()
    for r in range(1, n + 1):
        m = L == r; out[m] = np.bincount(층[m], minlength=18).argmax()
    return out
def 어긋(층, 선):   # 평평함 — 영역 안에서 최빈값과 다른 화소 비율
    L, n = label(~선); 다 = 전 = 0
    for r in range(1, n + 1):
        v = 층[L == r]; 다 += (v != np.bincount(v, minlength=18).argmax()).sum(); 전 += len(v)
    return 다 / max(전, 1)
def 하나(job):
    k, p, 층, 선, 반, 틀b, 정b = job
    import trimesh, 짓기 as J, 평가51나 as E, 천장쪼개기52 as C, 자63 as A
    풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
    묶 = np.stack([묶기(층[d], 선[d]) for d in range(6)]); 틀, 정 = 풀(틀b), 풀(정b); r = []
    for q in (층, 묶):
        v = C.깎(틀, E.지도(q, 반), 48, True, [float(x) for x in 반]); r.append(v)
    try:
        vv, ff, _ = J.정규메시(p); 점 = trimesh.sample.sample_surface(trimesh.Trimesh(vv, ff, process=False), A.점수, seed=0)[0]
        F = [A.F(A.칸표면(v, 1), 점) for v in r]
    except Exception: F = [np.nan, np.nan]
    iou = [float((v & 정).sum() / max((v | 정).sum(), 1)) for v in r]
    return F + iou + [어긋(층[0], 선[0]), 어긋(묶[0], 선[0])], [np.packbits(v) for v in r]
if __name__ == "__main__":
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]
    P = np.load(O + "학습51나_판0전체/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]
    L = json.load(open(O + "목록.json", encoding="utf-8")); 쓸 = range(8) if "QUICK" in sys.argv else range(len(예부))
    일 = [(k, L[예부[k]], np.array(P[범[k]]), np.array(입[예부[k], :, 0]) > 0, 반[예부[k]], 틀[예부[k]], 정[예부[k]]) for k in 쓸]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4, maxtasksperchild=20) as pool: 출 = pool.map(하나, 일, chunksize=2)
    R = np.array([o[0] for o in 출], float)
    if "QUICK" in sys.argv: print(np.round(R, 3)); sys.exit()
    np.save(D + "값.npy", R); np.save(D + "칸_대조.npy", np.stack([o[1][0] for o in 출])); np.save(D + "칸_묶기.npy", np.stack([o[1][1] for o in 출]))
    R0 = np.nan_to_num(R); 망 = int((R0[:, 1] < R0[:, 0] - .05).sum())
    결과 = {"712 F 대조": float(R0[:, 0].mean()), "712 F 묶기": float(R0[:, 1].mean()), "712 IoU 대조": float(R0[:, 2].mean()), "712 IoU 묶기": float(R0[:, 3].mean()),
          "평평함(위 영역 안 어긋 비율) 대조": float(R0[:, 4].mean()), "평평함 묶기": float(R0[:, 5].mean()), "F 0.05 넘게 떨어진 부품": 망, "F 오른 부품(+0.01)": int((R0[:, 1] > R0[:, 0] + .01).sum()), "실패": int(np.isnan(R[:, 0]).sum()),
          "판정": {"F 안 떨어짐": bool(R0[:, 1].mean() >= R0[:, 0].mean() - .005), "평평함 절반": bool(R0[:, 5].mean() <= R0[:, 4].mean() / 2), "빨간 선 망침 ≤ 50": 망 <= 50}}
    json.dump(결과, open("결과판정64.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
