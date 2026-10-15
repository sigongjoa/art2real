import sys, json, numpy as np
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품")
O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; Hs = d["H"]
범 = json.load(open(O + "범위46.json")); a = np.load(O + "영역53.npy"); c = json.load(open(O + "천장51c_전부.json", encoding="utf-8"))
z = np.load(O + "데이터51.npz"); 정 = z["정답"]
idx = np.array([te[j] for j in 범]); low = a[:, 0] < .5
cnt = np.array([np.unpackbits(정[i]).sum() for i in idx])
H = Hs[idx]
print("H 89:", np.percentile(H[low], [0, 10, 50, 90, 100]).round(4), " 나머지:", np.percentile(H[~low], [0, 10, 50, 90, 100]).round(4))
print("H*48/1.1 칸수 89 중앙:", np.median(H[low] * 48 / 1.1), " 나머지:", np.median(H[~low] * 48 / 1.1))
print("정칸 수 89:", np.percentile(cnt[low], [0, 10, 50, 90, 100]), " 나머지:", np.percentile(cnt[~low], [0, 10, 50, 90, 100]))
print("정칸 0 인 것:", (cnt[low] == 0).sum())
print("CAD 89 평균:", np.mean([c[k]["CAD"] for k in np.nonzero(low)[0]]), "틀:", np.mean([c[k]["틀"] for k in np.nonzero(low)[0]]))
print("H<1칸 이면서 89:", ((H * 48 / 1.1 < 1) & low).sum(), " H<1칸 전체:", (H * 48 / 1.1 < 1).sum())
