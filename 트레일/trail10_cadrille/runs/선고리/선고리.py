# -*- coding: utf-8 -*-
"""선 고리 시험 (10-10 흐름도 선고리흐름.png 0~6) — 그림의 닫힌 선을 스케치로 쓰고 깊이만 정해 평평한 포켓으로 판다 · 학습 없음
python runs/선고리/선고리.py <부품 번호> [gif]   →  결과_A/NN.json · 결과_B/NN.json (+ gif 면 단계 GIF)"""
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "깊이학습"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
N = 128; TH = 0.02; MINA = int(os.environ.get("MINA", 40)); CHECK = os.environ.get("CHECK") == "1"; 꼬리 = os.environ.get("OUTS", "");   # 10-10 2 판: MINA 4 · CHECK = 판 뒤 조각이 늘면 되돌림
쪽들 = tuple(int(c) for c in os.environ.get("VIEWS", "0,2,4").split(","))   # 기본 = 앞 · 옆 · 위           # 앞 · 옆 · 위 = 각 축의 낮은 쪽에서 본 그림
PL = {0: "YZ", 1: "XZ", 2: "XY"}
세계 = lambda r, c: ((r + .5) / N * 1.1 - .05, (c + .5) / N * 1.1 - .05)

def 모서리선(m, D, S, k, 각=30.0, n=N):
    """가 판: 메시 모서리 중 두 면이 각 ≥ 30° 로 꺾인 선 · 보이는 것만 → 128² 선 그림 (+ 실루엣 윤곽) · m 은 단위 상자 메시 · D · S = 그 쪽 깊이 · 실루엣"""
    ax = k // 2; fl = k % 2 == 1; o = [j for j in range(3) if j != ax]
    e = m.face_adjacency_edges[m.face_adjacency_angles > np.radians(각)]; V = m.vertices; L = np.zeros((n, n), np.uint8)
    for a, b in e:
        p0, p1 = V[a], V[b]; t = np.linspace(0, 1, max(2, int(np.linalg.norm(p1 - p0) * n * 2)))[:, None]; P = p0 + (p1 - p0) * t
        r = ((P[:, o[0]] + .05) / 1.1 * n - .5).round().astype(int); c = ((P[:, o[1]] + .05) / 1.1 * n - .5).round().astype(int)
        d = (P[:, ax] + .05) / 1.1; d = 1 - d if fl else d; ok = (r >= 0) & (r < n) & (c >= 0) & (c < n)
        r, c, d = r[ok], c[ok], d[ok]; 보임 = d <= D[r, c] + 1.5 / n            # 그 화소의 첫 표면보다 앞(또는 거의 같은 깊이)이면 보인다
        L[r[보임], c[보임]] = 1
    s8 = (S > .5).astype(np.uint8); L |= s8 - cv2.erode(s8, np.ones((3, 3), np.uint8)); return (L > 0).astype(np.float32)

def 면나누기(S, L):
    """2·3 단계: 선으로 나뉜 면 = 고리. 선 폭만큼 줄어든 면을 1 칸 불려 선 가운데로 돌려놓는다"""
    안 = ((S > .5) & (L < .5)).astype(np.uint8); n, lab = cv2.connectedComponents(안, connectivity=4); 면 = []
    for j in range(1, n):
        m = (lab == j).astype(np.uint8)
        if m.sum() < MINA: 면.append(("작음", m)); continue
        면.append(("고리", cv2.dilate(m, np.ones((3, 3), np.uint8)) & (S > .5).astype(np.uint8)))
    return 면

def 벡터(m):
    """고리 테두리 → 직선 다각형(1.2 칸 단순화 · 거의 수평/수직이면 맞춤) 또는 원(둥글기 검사)"""
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
    (cx, cy), r = cv2.minEnclosingCircle(c); d = np.linalg.norm(c[:, 0, :] - [cx, cy], axis=1)
    if r > 3 and d.std() / r < .06 and cv2.contourArea(c) / (np.pi * r * r) > .85: return ("원", (cy, cx, d.mean()))
    a = cv2.approxPolyDP(c, 1.2, True)[:, 0, :].astype(float)            # (x=열, y=행)
    for i in range(len(a)):                                               # 스냅: 이웃 꼭짓점과 1 칸 안이면 같은 줄
        j = (i + 1) % len(a)
        if abs(a[i, 0] - a[j, 0]) <= 1: a[j, 0] = a[i, 0]
        if abs(a[i, 1] - a[j, 1]) <= 1: a[j, 1] = a[i, 1]
    return ("선", [(y, x) for x, y in a])

def _오츠(v):
    v = np.sort(v); n = len(v); best, th = -1, None
    for q in np.linspace(.05, .95, 37):
        t = v[int(q * (n - 1))]; a, b = v[v <= t], v[v > t]
        if len(a) == 0 or len(b) == 0: continue
        g = len(a) * len(b) * (a.mean() - b.mean()) ** 2
        if g > best: best, th = g, t
    return th

def 고리들(X, P=None):
    """0~4 단계 · X = 시험.npz 한 부품 (4, 6, N, N) = S · L · Dh · D · P = AI 깊이 (6, N, N)
    SPLIT=1 (나 판): 고리 안 깊이가 두 덩어리면 깊은 쪽을 새 고리로 (판마다 따로 · f["만"])"""
    S, L, Dh, D = X; out = []; SPLIT = os.environ.get("SPLIT") == "1"
    for k in 쪽들:
        for 종, m in 면나누기(S[k], L[k]):
            f = {"쪽": k, "종": 종, "m": m}
            if 종 == "고리":
                f["벡터"] = 벡터(m); 안 = m > 0
                f["바탕"] = float(np.median(Dh[k][안])); f["A"] = float(np.median(D[k][안])); f["B"] = float(np.median(P[k][안])) if P is not None else None
                if SPLIT:
                    for 키, Z in (("A", D[k]), ("B", P[k] if P is not None else None)):
                        if Z is None: continue
                        z = Z[안]; t = _오츠(z)
                        if t is None: continue
                        깊 = 안 & (Z > t); 얕 = 안 & (Z <= t)
                        if 깊.sum() < .1 * 안.sum() or 얕.sum() < .1 * 안.sum() or np.median(Z[깊]) - np.median(Z[얕]) <= TH: continue
                        mm = cv2.morphologyEx(깊.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                        nn, lab = cv2.connectedComponents(mm, connectivity=4)
                        for j in range(1, nn):
                            sub = (lab == j).astype(np.uint8)
                            if sub.sum() < max(MINA, 4): continue
                            g = {"쪽": k, "종": "고리", "m": sub, "만": 키, "나눔": 1, "벡터": 벡터(sub)}; i_ = sub > 0
                            g["바탕"] = float(np.median(Dh[k][i_])); g["A"] = g["B"] = float(np.median(Z[i_])); out.append(g)
            out.append(f)
    return out

def 포켓(f, d):
    """5 단계: 고리 스케치 → 낮은 쪽에서 깊이 d 까지 밀어낸 기둥 (×100 · 제자리)"""
    import cadquery as cq
    ax = f["쪽"] // 2; lo, hi = -0.2, d * 1.1 - .05; 종, v = f["벡터"]
    if 종 == "원":
        r, c, rad = v; u, w = 세계(r, c); s_ = cq.Workplane(PL[ax]).center(u * 100, w * 100).circle(rad / N * 110).extrude((hi - lo) * 100)
    else: s_ = cq.Workplane(PL[ax]).polyline([tuple(np.array(세계(r, c)) * 100) for r, c in v]).close().extrude((hi - lo) * 100)
    bb = s_.val().BoundingBox(); off = [0, 0, 0]; off[ax] = lo * 100 - (bb.xmin, bb.ymin, bb.zmin)[ax]; return s_.translate(tuple(off))

def 짓기(바탕, fs, 판, 찍기=None):
    r = 바탕; n = 0
    for f in fs:
        if f["종"] != "고리" or f.get("만", 판) != 판 or f[판] - f["바탕"] <= TH: continue
        try:
            r2 = r.cut(포켓(f, f[판])); v0, v1 = r.val().Volume(), r2.val().Volume()
            if CHECK and len(r2.solids().vals()) > len(r.solids().vals()): f.setdefault("되돌림", []).append(판); continue   # 떨어진 조각이 생기면 이 파기는 안 받음
            if 0 < v1 < v0 - 1: r = r2; n += 1; f.setdefault("판것", []).append(판)
            if 찍기: 찍기(r, f)
        except Exception: pass
    return r, n

def 부스러기(m):
    """6 단계 자: 떨어진 조각 수(가장 큰 것 빼고) + 얇은 부피 비율(128³ 복셀 열기로 사라지는 몫)"""
    from scipy import ndimage
    조각 = max(len(m.split(only_watertight=False)) - 1, 0)
    v = m.voxelized(2 / N).fill().matrix; o = ndimage.binary_opening(v, iterations=1)
    return 조각, float((v.sum() - o.sum()) / max(v.sum(), 1))

if __name__ == "__main__":
    import torch, cadquery as cq
    from 학습 import 망
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    i = int(sys.argv[1]); GIF = "gif" in sys.argv[2:]
    T = np.load(os.path.join(R, "깊이학습", "시험.npz")); X = T["X"][i].astype(np.float32); 부품 = str(T["부품"][i])
    m_ = 망().cuda(); m_.load_state_dict(torch.load(os.path.join(R, "깊이학습", "모델.pt"))); m_.eval()
    with torch.no_grad(): P = m_(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
    if os.environ.get("LINES") == "mesh":   # 가 판: 고리 찾기에만 새 선 (AI 입력 X[:3] 은 학습 때 선 그대로 → P 는 위에서 이미 구함)
        mu = unit(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + 부품, force="mesh"))
        X = X.copy(); X[1] = np.stack([모서리선(mu, X[3][k], X[0][k], k) for k in range(6)])
    fs = 고리들(X, P)
    gt = unit(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + 부품, force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i); 기록 = {}
    for 판 in ("A", "B"):
        찍 = []
        r, n = 짓기(cq.importers.importStep(sp), fs, 판, (lambda r, f: 찍.append(메시로(r))) if GIF else None)
        pm = 메시로(r); res = 재기(pm, gt); 조각, 얇음 = 부스러기(pm)
        O = os.path.join(H, "결과_" + 판 + 꼬리); os.makedirs(O, exist_ok=True); pm.export(os.path.join(O, "%02d_선고리.stl" % i))
        기록[판] = {"idx": i, "부품": 부품, "판 수": n, "되돌림": sum(판 in f.get("되돌림", []) for f in fs), "MINA": MINA, "CHECK": CHECK, "edge_f1": res["edge_f1"], "iou": res["iou"], "조각": 조각, "얇음": round(얇음, 4)}
        json.dump(기록[판], open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, 판, "판 %d 개 · edge %.3f · 조각 %d · 얇음 %.3f" % (n, res["edge_f1"], 조각, 얇음), flush=True)
        if GIF: 기록[판]["찍"] = 찍
    if GIF:
        import pickle; pickle.dump({"X": X, "P": P, "fs": [{k: v for k, v in f.items()} for f in fs], "기록": {k: {kk: vv for kk, vv in v.items() if kk != "찍"} for k, v in 기록.items()},
                                    "찍A": [(np.asarray(m.vertices), np.asarray(m.faces)) for m in 기록["A"]["찍"]], "찍B": [(np.asarray(m.vertices), np.asarray(m.faces)) for m in 기록["B"]["찍"]], "부품": 부품},
                                   open(os.path.join(H, "단계_%02d.pkl" % i), "wb")); print("단계 저장")
