# 판정기준97 무작위 기준선 — 시험 300 · 규칙마다 깎인 속 정답 ±1 몫 대 같은 후보 수를 32 층에서 무작위로 골랐을 때의 몫 · 10-20
# 사용(venv · ART_MEM_GB=10): 후보101_우연.py → out/설명/캐드부품/후보101_우연.json
import json, numpy as np
import 후보101 as P, 어려움102 as A
O = P.O; K = 32; N = 128
d = np.load(O + "데이터.npz"); P.X = d["X"]; 시 = d["시험"]; e = np.load(O + "데이터_앞옆.npz"); P.F, P.S = e["F"], e["S"]
h = np.load(O + "숨은선88.npz"); P.HX, P.HF, P.HS = h["HX"], h["HF"], h["HS"]; P.반 = np.load(O + "데이터51.npz")["반"]
I = np.load(O + "후보96_색인.npy").astype(np.int64); 층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
규칙 = ["96 수평 ∩", "넓게 ∩", "넓게 ∪"]; a = {r: np.zeros(3) for r in 규칙}
for i in np.nonzero(시)[0][:300]:
    for 넓게 in (False, True):
        C = P.후보(i, 넓게)
        for 합 in ((False,) if not 넓게 else (False, True)):
            r = 규칙[0] if not 넓게 else 규칙[2 if 합 else 1]
            for n in range(6):
                q = ((C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]) if 합 else (C[n, 0][I[n, 0]] & C[n, 1][I[n, 1]])).astype(np.int64)
                g = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (g < K); 깎 = 안 & (g >= 껍[i, n].astype(np.int64) + 2)
                bit = lambda L: ((q >> np.clip(L, 0, 31)) & 1) > 0; 곁 = bit(g) | bit(g - 1) | bit(g + 1)
                c = np.unpackbits(q.astype("<u4").view(np.uint8).reshape(N, N, 4), axis=-1).sum(-1)
                a[r] += [깎.sum(), (곁 & 깎).sum(), A.우연(c, g)[깎].sum()]
결 = {r: {"깎인 속 ±1": round(v[1] / v[0], 3), "무작위 같은 수 ±1": round(v[2] / v[0], 3), "차": round((v[1] - v[2]) / v[0], 3)} for r, v in a.items()}
print(결); json.dump(결, open(O + "후보101_우연.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
