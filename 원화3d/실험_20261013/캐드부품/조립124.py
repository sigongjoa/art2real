# 판정기준124 — 복잡한 부품 생성기: 설계116 몸 1~6 개를 축(z · x · y)으로 눕히고 서로 붙여 합침 · 긴 막대 · 얇은 판 비율 포함 · 10-21
# 사용(cadrille venv · ART_MEM_GB=10): 조립124.py 예시 → out/설명/캐드부품/모델124/예시.png
import sys, os, json, numpy as np
import 설계116 as S
K = 6; 축들 = ("z", "x", "y")
def 몸(rng):   # 설계116 몸 하나 · 기울임 없음 · 3 분의 1 은 막대 · 판 비율
    s = S.무작위(rng); s["기울임"] = 0.; b = s["바탕"]; u = rng.random()
    if u < .2 and b["종류"] in ("원기둥", "계단축"): b["r"] = float(rng.uniform(3, 10)); b["h"] = float(rng.uniform(5, 9)) * b["r"]
    if b["종류"] == "계단축": b["r2"] = min(b.get("r2", b["r"] * .6), .75 * b["r"]); b["h1"] = min(b.get("h1", b["h"] * .4), .6 * b["h"])
    if u > .85 and b["종류"] == "상자": b["h"] = float(rng.uniform(2, 5)); b["w"] = float(rng.uniform(40, 90))
    return s
def 무작위(rng):
    n = int(rng.choice([1, 2, 3, 4, 5, 6], p=[.12, .2, .2, .18, .15, .15])); 몸들 = []
    for i in range(n):
        s = 몸(rng); s["축"] = str(rng.choice(축들, p=[.5, .25, .25])); s["자리"] = [0., 0., 0.]
        if i: s["붙임"] = [int(rng.integers(i)), int(rng.integers(6))]   # 붙일 몸 · 면(+x −x +y −y +z −z)
        몸들.append(s)
    return {"몸": 몸들}
def _놓기(w, s):
    if s["축"] == "x": w = w.rotate((0, 0, 0), (0, 1, 0), 90)
    if s["축"] == "y": w = w.rotate((0, 0, 0), (1, 0, 0), -90)
    bb = w.val().BoundingBox(); return w.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -(bb.zmin + bb.zmax) / 2))   # 몸 가운데를 원점에
def 짓기(c, tol=None):   # 몸마다 짓고 → 눕히고 → 붙일 몸의 면 가운데에 반쯤 박아 합침 · 자리(가운데 좌표)를 사양에 적음 · tol = OCC 퍼지 합치기(재시도용)
    ws, 상 = [], []
    for i, s in enumerate(c["몸"]):
        w = _놓기(S.짓기(s), s); bb = w.val().BoundingBox(); 반 = np.array([bb.xlen, bb.ylen, bb.zlen]) / 2
        if i:
            j, f = s["붙임"]; a = f // 2; sg = 1 if f % 2 == 0 else -1; p = np.array(c["몸"][j]["자리"], float).copy()
            p[a] += sg * (상[j][a] + 반[a] * .6)   # 반쯤 박힘(겹쳐야 한 덩어리)
            s["자리"] = [float(x) for x in p]; w = w.translate(tuple(s["자리"]))
        ws.append(w); 상.append(반)
    out = ws[0]
    for w in ws[1:]: out = out.union(w, tol=tol)
    return out
def 짓기_자리(c):   # 자리를 그대로 쓰는 짓기(모델 예측용 · 몸이 없으면 오류)
    ws = [_놓기(S.짓기(s), s).translate(tuple(s["자리"])) for s in c["몸"]]
    out = ws[0]
    for w in ws[1:]: out = out.union(w)
    return out
def 메시(w): return S.메시(w)
if __name__ == "__main__" and sys.argv[1] == "예시":
    import 데이터117 as Q, 모델120 as M
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    D = "G:/art2real/out/설명/캐드부품/모델124/"; os.makedirs(D, exist_ok=True); fig, ax = plt.subplots(3, 6, figsize=(18, 9))
    for t in range(18):
        rng = np.random.default_rng(124000 + t); c = 무작위(rng)
        try: w = 짓기(c); ok = w.val().isValid(); im = Q.렌더(메시(w)[0])[0]
        except Exception as ex: im = np.full((256, 256, 3), 255, np.uint8); ok = str(ex)[:20]
        a = ax[t // 6, t % 6]; a.imshow(im); a.axis("off"); a.set_title(f"몸 {len(c['몸'])} · {ok}", fontsize=10)
    plt.tight_layout(); plt.savefig(D + "예시.png", dpi=60); print("끝")
