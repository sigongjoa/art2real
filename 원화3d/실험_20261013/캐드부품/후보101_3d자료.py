# 판정기준97 3D 보기용 자료 — 부품마다 세계 칸(x, y, z) 기준 도면 선 · 걸러낸 열 후보 · 여섯 방향 정답 층 · 층↔칸 표 → json(base64) · 10-20
# 사용(venv · ART_MEM_GB=8): 후보101_3d자료.py [부품...] → out/설명/캐드부품/후보3d/자료.json
import sys, os, json, base64, numpy as np
import 후보96 as H, 후보101 as P
O = P.O; N = 128; K = 32; D = O + "후보3d/"; os.makedirs(D, exist_ok=True)
d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
반 = np.load(O + "데이터51.npz")["반"]; I = np.load(O + "후보96_색인.npy").astype(np.int64); 층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r")
b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
비트 = lambda m: b64(np.packbits(m.astype(bool).ravel()))
out = {"방향": [[k, *H.축[k]] for k in H.방], "부품": {}}
for i in [int(a) for a in sys.argv[1:]] or [66, 59, 14, 0]:
    세 = lambda M: M[::-1].T > 0   # 원본 → [가로축, 세로축] 세계 칸
    선 = {"xy": (세(X[i]), 세(HX[i])), "xz": (세(F[i]), 세(HF[i])), "yz": (세(S[i]), 세(HS[i]))}
    열 = P.열후보_넓게(선["xy"][0] | 선["xy"][1], 선["xz"][0] | 선["xz"][1], 선["yz"][0] | 선["yz"][1])   # {축: (A[열, 칸], B[열, 칸])}
    정 = np.full((6, N, N), 255, np.uint8); 칸층 = np.zeros((6, N), np.int64)
    for n, k in enumerate(H.방):
        a, s = H.축[k]; hh = float(반[i][n]); w = s * H.g + H.칸 / 2
        칸층[n] = np.clip(np.floor((hh - w) / (2 * hh / K) + 1e-6), 0, K - 1) if hh > 0 else -1
        g = 층[i, n]; m = (입[i, n, 1] > 0) & (g < K); 정[n][I[n, 0][m], I[n, 1][m]] = g[m]   # 지역 화소 → 세계 (앞 축, 뒤 축) · 축 순서 오름차순
    out["부품"][str(i)] = {"선": {k: [비트(v[0]), 비트(v[1])] for k, v in 선.items()}, "열": {str(a): [비트(v[0]), 비트(v[1])] for a, v in 열.items()},
                         "정답": b64(정), "칸층": 칸층.tolist()}
json.dump(out, open(D + "자료.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장", os.path.getsize(D + "자료.json"))
틀 = open("후보3d_틀.html", encoding="utf-8").read(); open(D + "후보3d.html", "w", encoding="utf-8").write(틀.replace("__DATA__", json.dumps(out, ensure_ascii=False))); print("html")
