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
실 = np.load(O + "후보101_실패.npz"); 실부 = list(실["부품"]); 실지 = np.unpackbits(실["지도"], axis=-1) > 0; 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
어 = np.load(O + "어려움102/자료.npz")
def 원(i):   # 부품 번호(데이터셋) 또는 어려움102 이름 → 같은 꼴 · 빠 = 넓은 ∪ 에 정답 ±1 없는 지역 화소(없으면 None)
    if isinstance(i, str):
        g = lambda a: 어[f"{i}__{a}"]; return dict(X=g("X"), F=g("F"), S=g("S"), HX=g("HX"), HF=g("HF"), HS=g("HS"), 반=g("반"), 층=g("층"), 입=g("입"), 껍=g("껍"), 빠=g("빠"))
    t = 실부.index(i) if i in 실부 else None
    return dict(X=X[i], F=F[i], S=S[i], HX=HX[i], HF=HF[i], HS=HS[i], 반=반[i], 층=층[i], 입=입[i], 껍=껍[i], 빠=None if t is None else 실지[t])
for i in [a if not a.isdigit() else int(a) for a in sys.argv[1:]] or ["렉스", "오메가몬머리", "거미다리", 2741, 1588, 1034, 904, 2228, 574, 66, 59, 14, 0]:
    z = 원(i)
    세 = lambda M: M[::-1].T > 0   # 원본 → [가로축, 세로축] 세계 칸
    선 = {"xy": (세(z["X"]), 세(z["HX"])), "xz": (세(z["F"]), 세(z["HF"])), "yz": (세(z["S"]), 세(z["HS"]))}
    열 = P.열후보_넓게(선["xy"][0] | 선["xy"][1], 선["xz"][0] | 선["xz"][1], 선["yz"][0] | 선["yz"][1])   # {축: (A[열, 칸], B[열, 칸])}
    빠 = np.zeros((6, N, N), bool); 깎w = np.zeros((6, N, N), bool); t = z["빠"]
    정 = np.full((6, N, N), 255, np.uint8); 칸층 = np.zeros((6, N), np.int64); 층중심 = np.full((6, K), np.nan)
    for n, k in enumerate(H.방):
        a, s = H.축[k]; hh = float(z["반"][n]); w = s * H.g + H.칸 / 2
        칸층[n] = np.clip(np.floor((hh - w) / (2 * hh / K) + 1e-6), 0, K - 1) if hh > 0 else -1
        if hh > 0: lf = (hh - w) / (2 * hh / K); o = np.argsort(lf); 층중심[n] = np.interp(np.arange(K) + .5, lf[o], np.arange(N)[o])   # 층 가운데 칸 · 자르기 전 값으로(층 0 · 31 에 몰린 바깥 칸 평균 쓰면 띠가 생김)
        g = z["층"][n]; m = (z["입"][n, 1] > 0) & (g < K); 정[n][I[n, 0][m], I[n, 1][m]] = g[m]   # 지역 화소 → 세계 (앞 축, 뒤 축) · 축 순서 오름차순
        k2 = m & (g >= z["껍"][n].astype(np.int64) + 2); 깎w[n][I[n, 0][k2], I[n, 1][k2]] = True
        if t is not None: 빠[n][I[n, 0][t[n]], I[n, 1][t[n]]] = True   # 넓은 ∪ 후보에 정답 ±1 없음 (후보101_실패)
    out["부품"][str(i)] = {"선": {k: [비트(v[0]), 비트(v[1])] for k, v in 선.items()}, "열": {str(a): [비트(v[0]), 비트(v[1])] for a, v in 열.items()},
                         "정답": b64(정), "칸층": 칸층.tolist(), "층중심": np.nan_to_num(층중심, nan=-1).round(2).tolist(), "깎": 비트(깎w), "빠": 비트(빠), "시험": t is not None}
json.dump(out, open(D + "자료.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장", os.path.getsize(D + "자료.json"))
틀 = open("후보3d_틀.html", encoding="utf-8").read(); open(D + "후보3d.html", "w", encoding="utf-8").write(틀.replace("__DATA__", json.dumps(out, ensure_ascii=False))); print("html")
