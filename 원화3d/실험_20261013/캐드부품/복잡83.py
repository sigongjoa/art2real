# 어려운 묶음 얼리기 — 사용자 10-18 「곤충같이 복잡한 걸로 봐야지 · 다른 건 간단해서 쉽게 통과」 · 모델 결과는 안 봄 · 10-18
# 1 판 겉넓이^1.5/부피 는 얇은 판 · 속 빈 상자를 골라 버림(딱정벌레 빠짐) → 2 판 둘레²/(4π 넓이) 도 얇은 판 옆 그림(가는 띠)이 커서 판이 올라옴 → 3 판 들쭉 = 위 · 앞 · 옆 채운 윤곽 둘레 / 볼록 껍질 둘레 평균(얇아도 오목함 없으면 1 · 다리 · 갈래 · 홈이 많을수록 큼) · 거른 450 상위 20
# 사용(venv): 복잡83.py → out/설명/캐드부품/복잡83.json (부품 번호 · 복잡도) · 썸네일 복잡83.png
import json, numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 잼(i):   # 정답에서 뽑은 입력 그림(데이터 · 위 · 앞 · 옆) 의 채운 윤곽
    import cv2, 입력51 as I; d = np.load(O + "데이터.npz", mmap_mode="r"); e = np.load(O + "데이터_앞옆.npz", mmap_mode="r"); r = []
    for g in (d["X"][i], e["F"][i], e["S"][i]):
        m = I._채움(g).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs: return np.nan, False
        P = sum(cv2.arcLength(c, True) for c in cs); H = cv2.arcLength(cv2.convexHull(np.concatenate(cs)), True); r.append(P / max(H, 1e-6))
    return float(np.mean(r)), True
if __name__ == "__main__":
    시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8")); 거 = np.load(O + "거름62.npy")
    ks = np.nonzero(거)[0]
    import sys; sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); R = [잼(int(예부[k])) for k in ks]
    c = np.array([r[0] for r in R]); w = np.array([r[1] for r in R]); ok = np.isfinite(c) & w
    고 = ks[ok][np.argsort(-c[ok])][:20]; json.dump({"부품": [int(k) for k in 고], "복잡도": [round(float(c[ks == k][0]), 1) for k in 고], "기준": "오목함 없는 윤곽 = 1", "잰 수": int(ok.sum())}, open(O + "복잡83.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from mpl_toolkits.mplot3d.art3d import Poly3DCollection; import 짓기 as J
    f = plt.figure(figsize=(15, 12)); 빛 = matplotlib.colors.LightSource(315, 40)
    for n, k in enumerate(고):
        v, fc, _ = J.정규메시(L[예부[k]]); a = f.add_subplot(4, 5, n + 1, projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(28, -50)
        a.add_collection3d(Poly3DCollection(np.asarray(v)[np.asarray(fc)], facecolors="#9bd3a8", edgecolors="#9bd3a8", linewidths=0, shade=True, lightsource=빛)); a.set_title("%d · %.2f" % (k, c[ks == k][0]), fontsize=10)
    plt.tight_layout(); f.savefig(O + "복잡83.png", dpi=55); print(고.tolist())
