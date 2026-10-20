# 판정기준97 — 후보 넓히기: 깊이 축에 수직인 선만(후보96) → 세로가 아닌 선 전부(기운 선 · 곡선) · 두 도면 교집합 / 합집합 · 학습 없이 천장만 · 10-20
# 사용(venv · ART_MEM_GB=10): 후보101.py → 시험 300 · 규칙마다 정답 층이 후보 안(± 1) 몫 · 속 깎임(정답 ≥ 껍질32 + 2) · 화소당 후보 수
import sys, json, numpy as np, cv2
import 후보96 as H
O = "G:/art2real/out/설명/캐드부품/"; N = 128; K = 32
def 세로뺌(L, ax):   # ax 가 깊이 축 방향 · 그 방향으로 5 화소 넘게 이어진 선(세로 윤곽)만 뺀다 → 기운 선 · 곡선 · 수평선이 남음
    k = np.ones((5, 1) if ax == 0 else (1, 5), np.uint8); 세 = cv2.dilate(cv2.erode(L.astype(np.uint8), k), k) > 0; return (L & ~세) | H.이음(L, 1 - ax)   # 수평선(후보96)은 늘 남김 — 세로선과 맞닿은 화소가 빠지던 것 고침
def 열후보_넓게(Lxy, Lxz, Lyz):   # 후보96.열후보 와 같은 꼴 · 이음(L, 다른 축) 대신 세로뺌(L, 깊이 축)
    z = (세로뺌(Lxz, 1), 세로뺌(Lyz, 1)); y = (세로뺌(Lxy, 1), 세로뺌(Lyz, 0).T); x = (세로뺌(Lxy, 0).T, 세로뺌(Lxz, 0).T)
    return {2: z, 1: y, 0: x}
def 후보(i, 넓게):
    H.열후보 = 열후보_넓게 if 넓게 else 원열후보; return H.하나(X[i], F[i], S[i], HX[i], HF[i], HS[i], 반[i])
원열후보 = H.열후보
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
    반 = np.load(O + "데이터51.npz")["반"]; I = np.load(O + "후보96_색인.npy").astype(np.int64)
    층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
    규칙 = ["96 수평 ∩", "넓게 ∩", "넓게 ∪"]; a = {r: np.zeros(7) for r in 규칙}
    for i in np.nonzero(시)[0][:300]:
        for 넓게 in (False, True):
            C = 후보(i, 넓게)
            for 합 in ((False,) if not 넓게 else (False, True)):
                r = 규칙[0] if not 넓게 else 규칙[2 if 합 else 1]
                for n in range(6):
                    q = (C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]) if 합 else (C[n, 0][I[n, 0]] & C[n, 1][I[n, 1]]); q = q.astype(np.int64)
                    g = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (g < K); s = 껍[i, n].astype(np.int64); 깎 = 안 & (g >= s + 2)
                    bit = lambda L: ((q >> np.clip(L, 0, 31)) & 1) > 0; 맞 = bit(g); 곁 = 맞 | bit(g - 1) | bit(g + 1)
                    a[r] += [안.sum(), (맞 & 안).sum(), (곁 & 안).sum(), 깎.sum(), (맞 & 깎).sum(), (곁 & 깎).sum(), int(np.unpackbits(q[안].astype('<u4').view(np.uint8)).sum())]
    결 = {r: {"안 정답∈후보": round(v[1] / v[0], 3), "안 ±1": round(v[2] / v[0], 3), "속 깎임 정답∈후보": round(v[4] / v[3], 3), "속 깎임 ±1": round(v[5] / v[3], 3), "화소당 후보": round(v[6] / v[0], 2)} for r, v in a.items()}
    for r in 결: print(r, 결[r])
    json.dump(결, open(O + "후보101.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
