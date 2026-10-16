# 판정기준56 — 숨은선(위 · 앞 · 옆) → 여섯 방향 지역 화소(지역틀.그림맞춤 · 보이는 선과 같은 맞춤) · 10-16
# 사용(venv): 입력56.py → out/설명/캐드부품/숨은선56.npy (10000 × 6 × 128 × 128 uint8) + G0 판정 출력
import sys, json, glob, numpy as np
import 여섯방향 as S6, 지역틀 as T
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    fs = sorted(glob.glob(O + "숨은선_0*.npz")); z = [np.load(f) for f in fs]; HX, HF, HS = (np.concatenate([q[k] for q in z]) for k in ("HX", "HF", "HS")); n = len(HX)
    assert n == len(json.load(open(O + "목록.json", encoding="utf-8"))), n
    M = np.lib.format.open_memmap(O + "숨은선56.npy", mode="w+", dtype=np.uint8, shape=(n, 6, 128, 128))
    for i in range(n):
        for j, k in enumerate(S6.방향): M[i, j] = T.그림맞춤(HX[i], HF[i], HS[i], k)
    M.flush()
    입 = np.load(O + "입력51.npy", mmap_mode="r"); te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 범 = json.load(open(O + "범위46.json")); B = json.load(open("묶음54_B112.json", encoding="utf-8"))["자리"]
    def 쓸모(i):   # 세 방향(위 0 · 앞 2 · 옆 4) 숨은선 합 > 100 이고 방향마다 숨은선 ≤ 채운 윤곽의 30 %
        h = [int(M[i, j].sum()) for j in (0, 2, 4)]; 채 = [int(입[i, j, 1].sum()) for j in (0, 2, 4)]
        return sum(h) > 100 and all(a <= .3 * max(b, 1) for a, b in zip(h, 채)), h, 채
    r = [쓸모(int(te[범[k]])) for k in B]; 좋 = sum(x[0] for x in r); 칠 = sum(sum(x[1]) > 100 and not x[0] for x in r)
    print(json.dumps({"B112 쓸모 있음": 좋, "숨은선 있으나 칠해짐(> 30 %)": 칠, "없음(합 ≤ 100)": sum(sum(x[1]) <= 100 for x in r), "G0 (≥ 56)": 좋 >= 56,
                      "전체 1 만 숨은선 있는 부품": int(sum(M[i].sum() > 100 for i in range(0, n, 10))) * 10}, ensure_ascii=False))
