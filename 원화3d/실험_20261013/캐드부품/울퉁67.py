# 판정기준67 A — 새 자 「울퉁」: 정답이 평평한 곳에서 답 면이 꺾인 비율(여섯 축 깊이 지도 2 차 차분) · 낮을수록 좋음 · 10-17
# 사용(venv): 울퉁67.py → out/설명/캐드부품/울퉁67.npy(712 × 열) · 결과울퉁67.json · import 해서 울퉁(답, 정답) 도 씀
import json, numpy as np
O = "G:/art2real/out/설명/캐드부품/"; n = 48
풀 = lambda b: np.unpackbits(b)[:n ** 3].reshape(n, n, n).astype(bool)
def 깊이(v):   # 여섯 축 방향 깊이 지도(처음 찬 칸 번호 · 빈 기둥 nan)
    out = []
    for ax in range(3):
        for rev in (False, True):
            w = np.flip(v, ax) if rev else v; has = w.any(ax); d = np.argmax(w, ax).astype(float); d[~has] = np.nan; out.append(d)
    return out
def d2(d):   # 두 축 2 차 차분(가장자리 · nan 이웃은 nan)
    a = np.full(d.shape, np.nan); b = np.full(d.shape, np.nan)
    a[1:-1, :] = d[2:, :] - 2 * d[1:-1, :] + d[:-2, :]; b[:, 1:-1] = d[:, 2:] - 2 * d[:, 1:-1] + d[:, :-2]; return a, b
def 울퉁(답, 정):   # → (꺾임 수, 평평 화소 수)
    if 답.sum() == 0 or 정.sum() == 0: return 0, 0
    k = 전 = 0
    for p, t in zip(깊이(답), 깊이(정)):
        pa, pb = d2(p); ta, tb = d2(t); 평 = (np.abs(ta) <= 1) & (np.abs(tb) <= 1) & ~np.isnan(pa) & ~np.isnan(pb)
        k += int((평 & ((np.abs(pa) >= 2) | (np.abs(pb) >= 2))).sum()); 전 += int(평.sum())
    return k, 전
if __name__ == "__main__":
    z = np.load(O + "데이터51.npz"); 정b, 틀b = z["정답"], z["틀"]; 시 = np.load(O + "데이터.npz")["시험"]; 예부 = np.nonzero(시)[0][json.load(open(O + "범위46.json"))]
    판 = {"정답 칸": None, "틀": None, "판0": np.load(O + "영역64/칸_대조.npy"), "58": np.load(O + "학습58_판0예측/예측.npy"), "H": np.load(O + "학습58_H/예측.npy"), "64": np.load(O + "영역64/칸_묶기.npy"), "65": np.load(O + "면65/칸.npy"), "66": np.load(O + "면66/칸.npy")}
    R = np.zeros((len(예부), len(판), 2))
    for k, i in enumerate(예부):
        t = 풀(정b[i])
        for j, (nm, A) in enumerate(판.items()):
            v = t if nm == "정답 칸" else 풀(틀b[i]) if nm == "틀" else 풀(A[k]); R[k, j] = 울퉁(v, t)
    np.save(O + "울퉁67.npy", R); 거 = np.load(O + "거름62.npy"); 비 = lambda m, j: float(R[m, j, 0].sum() / max(R[m, j, 1].sum(), 1))
    부품 = R[:, :, 0] / np.maximum(R[:, :, 1], 1)
    import 그림63 as G; 판k = int(G.고른[1][1])
    결과 = {nm: {"712": 비(np.ones(len(예부), bool), j), "거른 450": 비(거, j), "부품 중앙(712)": float(np.median(부품[:, j]))} for j, nm in enumerate(판)}
    결과["자 감사"] = {"정답 칸 울퉁(712) ≤ 0.5 %": 결과["정답 칸"]["712"] <= .005, "모터 판 58 울퉁": float(부품[판k, 3]), "58 부품 중앙": 결과["58"]["부품 중앙(712)"], "모터 판 > 중앙": bool(부품[판k, 3] > 결과["58"]["부품 중앙(712)"])}
    json.dump(결과, open("결과울퉁67.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
