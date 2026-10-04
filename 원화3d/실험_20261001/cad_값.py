# -*- coding: utf-8 -*-
"""CAD v1 입력값 — 원화에서 숫자 · 윤곽만 뽑아 JSON (10-04 사용자 「CAD 도안을 바탕으로 가자」).
좌표: x = 정면 판 화소 − 축 A · y 깊이(눈 0 · 앞 −) · z = −행. FreeCAD 는 이 값만 읽어 솔리드를 짓는다(cad_짓기.py).
  속 타원체 E: 머리판.py 와 같은 맞춤(정면 몸통 반폭 최소제곱 · 옆 돔 칸 앞 끝 · 처마 높이 뒤 끝)
  얼굴 구멍: 정면 칸(눈 조립 · 마스크 · 볼날개) 합집합 윤곽 — 투구 앞쪽을 이 윤곽대로 뚫음
  차양: 정면 칸 14 · 16 오른쪽 반 다각형(9 점) → 거울
출력 out/오메가몬2/cad/값_v1.json"""
import os, json, numpy as np, cv2, contextlib, io
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; O = r"G:\art2real\원화3d\out\오메가몬2\cad"; os.makedirs(O, exist_ok=True)
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
J = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 축 = J["층(정면 판 화소 행)"], J["정면 축(판 화소 열)"]; xa = 축["A 중심"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
def 칸지도(n):
    z = np.load(os.path.join(A, f"{n}.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
    m = np.load(os.path.join(A, f"판_{n}_Z.npz"))["m"]; h, w = m.shape; py, px = np.mgrid[0:h, 0:w]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m
C1 = 칸지도("1"); C2 = cv2.warpAffine(칸지도("2").astype(np.float32), Ma, (ND, H), flags=cv2.INTER_NEAREST).astype(int)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
Fa, Sa = 몸(m1), 몸(S2)
rows = np.array([r for r in range(H) if Fa[r].any()]); hw = np.array([(np.nonzero(Fa[r])[0].max() - np.nonzero(Fa[r])[0].min()) / 2 for r in rows])
top = rows.min(); 턱 = 층["L2 턱 끝"]; best = None
for c in np.arange(60, 160, 2):
    for zc in np.arange(top + 40, 턱, 2):
        q = 1 - ((rows - zc) / c) ** 2; ok = (q > 0.05) & (rows <= 턱)
        if ok.sum() < 30: continue
        s = np.sqrt(q[ok]); a = float((hw[ok] * s).sum() / (s * s).sum()); e = ((hw[ok] - a * s) ** 2).mean()
        if best is None or e < best[0]: best = (e, a, c, zc)
_, a, c, zc = best
r6 = 층["L6 처마"]; 돔칸 = cv2.dilate((C2 == 1).astype(np.uint8), np.ones((3, 3), np.uint8)); dr = [r for r in range(int(top), int(r6) + 1) if 돔칸[r].any()]
yf6 = min(np.nonzero(돔칸[r])[0].min() for r in dr) + D0; yb6 = np.nonzero(Sa[int(r6)])[0].max() + D0
s6 = np.sqrt(max(0.05, 1 - ((r6 - zc) / c) ** 2)); y0 = (yf6 + yb6) / 2; f = (yb6 - yf6) / 2 / s6
def 윤곽(mask, eps=1.5, 오른쪽=False):
    m = mask.astype(np.uint8).copy()
    if 오른쪽: m[:, :int(round(xa))] = 0
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return [[[float(p[0] - xa), float(-p[1])] for p in cv2.approxPolyDP(cn, eps, True).reshape(-1, 2)] for cn in cs if cv2.contourArea(cn) > 30]
칸 = lambda cs: cv2.dilate(np.isin(C1, cs).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
얼굴 = 칸([11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 27] + list(range(29, 43)) + [7, 10, 25, 26, 28]) & m1.astype(np.uint8)
얼굴 = cv2.morphologyEx(얼굴, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
# v2: 머리 몸통 = 정면 윤곽 밀기 ∩ 옆 윤곽 밀기 ∩ 위 윤곽(돔 바닥 타원) 밀기 — 조사 패턴 2(두 방향 밀기의 교집합)
정몸 = cv2.morphologyEx(m1.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))); 정몸[int(턱) + 1:] = 0
옆몸 = cv2.morphologyEx(S2.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))); 옆몸[int(턱) + 1:] = 0
def 윤곽2(m, u0, eps=2.0):
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cn = max(cs, key=cv2.contourArea)
    return [[float(p[0] - u0), float(-p[1])] for p in cv2.approxPolyDP(cn, eps, True).reshape(-1, 2)]
# 돔 단면: 위 반은 돔 — 앞뒤 축 5 단면(y), 각 단면 = 그 깊이에서 정면 윤곽 위쪽을 높이 비율로 줄인 다각형(꼭짓점 9 개 고정)
# v3: ① 몸 윤곽 eps 2 → 4(짧은 계단 변 없앰) · 꼭대기 = 옆 돔 칸 맨 위(뿔 · 안테나 뿌리 돌기 자름)
돔위 = min(r for r in range(H) if 돔칸[r].any()); 정몸[:돔위] = 0; 옆몸[:돔위] = 0
# ② 마스크 판 셋: 정면 칸 묶음 윤곽(대칭 평균) · 앞 끝 = 옆 마스크 칸 그 판 행 범위 가장 앞 · 판 행 범위
판정의 = [("코판", [30, 33, 34, 37], [5, 12]), ("미늘2", [36, 38, 39, 41], [14, 15, 16, 19]), ("턱판", [40, 42], [20])]
판들 = []
for nm, fc, sc in 판정의:
    mk = cv2.morphologyEx(칸(fc) & m1.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mk = mk | mk[:, ::-1][:, :] if False else mk
    ys_, xs_ = np.nonzero(mk)
    if not len(ys_): continue
    r0, r1 = int(ys_.min()), int(ys_.max()); hw_ = float(max(xa - xs_.min(), xs_.max() - xa))
    sm = cv2.dilate(np.isin(C2, sc).astype(np.uint8), np.ones((3, 3), np.uint8)); rr = [r for r in range(r0, r1 + 1) if sm[r].any()]
    tip = float(min(np.nonzero(sm[r])[0].min() for r in rr) + D0) if rr else -60.0
    판들.append({"이름": nm, "윤곽": 윤곽(mk, 2.0)[0] if 윤곽(mk, 2.0) else [], "위": float(-r0), "아래": float(-r1), "반폭": hw_, "앞 끝": tip})
# v4~: 뿔 돌기 — 정면 몸 행 반폭이 최대의 35 % 아래인 맨 위 행들 = 뿔 · 안테나 뿌리 → 그 위를 자름(정면 · 옆 같이)
_hw = np.array([(np.nonzero(정몸[r])[0].max() - np.nonzero(정몸[r])[0].min()) / 2 if 정몸[r].any() else 0 for r in range(H)])
꼭대기 = int(np.nonzero(_hw >= 0.35 * _hw.max())[0].min()); 정4 = 정몸.copy(); 옆4 = 옆몸.copy(); 정4[:꼭대기] = 0; 옆4[:꼭대기] = 0
def 옆윤곽(m, eps): return [[float(p[0] + D0), float(-p[1])] for p in cv2.approxPolyDP(max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea), eps, True).reshape(-1, 2)]
옆뿔 = cv2.dilate((C2 == 2).astype(np.uint8), np.ones((3, 3), np.uint8)); 정뿔 = cv2.dilate(np.isin(C1, [1, 2]).astype(np.uint8), np.ones((3, 3), np.uint8))
눈 = [[[float(p[0] - xa), float(-p[1])] for p in P] for P in json.load(open(os.path.join(os.path.dirname(A.rstrip("/\\")).replace("지표", "블렌더"), "저폴리눈_앞윤곽.json"), encoding="utf-8")).values()]
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV)
노 = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 40) & (hsv[:, :, 1] > 60)).astype(np.uint8); n_, lab = cv2.connectedComponents(노); 안테나 = []
ys9, xs9 = np.nonzero(C2 == 9); 뒤9 = float(xs9.max() + D0) if len(xs9) else 60.0
for k in range(1, n_):
    yy, xx = np.nonzero(lab == k)
    if len(xx) < 40: continue
    pts = np.c_[xx, yy].astype(float); cc = pts.mean(0); u = np.linalg.svd(pts - cc)[2][0]; t = (pts - cc) @ u; p0, p1 = cc + u * t.min(), cc + u * t.max()
    if np.hypot(*(p0 - [xa, 150])) > np.hypot(*(p1 - [xa, 150])): p0, p1 = p1, p0
    안테나.append([[float(p0[0] - xa), float(-p0[1])], [float(p1[0] - xa), float(-p1[1])]])
blue = ((hsv[:, :, 0] >= 95) & (hsv[:, :, 0] <= 130) & (hsv[:, :, 1] > 90) & (m1 > 0)).astype(np.uint8)
fp = [np.array(v, float) for k2, v in json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8"))["1"].items() if k2.startswith("번개")]
nb, lb = cv2.connectedComponents(blue); 번개 = []
for k in range(1, nb):
    yy, xx = np.nonzero(lb == k)
    if len(xx) >= 6 and min(np.hypot(xx - q[0], yy - q[1]).min() for q in fp) < 15:
        cn = max(cv2.findContours((lb == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=len)
        번개.append([[float(p[0] - xa), float(-p[1])] for p in cv2.approxPolyDP(cn, 0.8, True).reshape(-1, 2)])
v4 = {"정면 몸": 윤곽2(정4, xa, 4.0), "옆 몸": 옆윤곽(옆4, 6.0), "뿔 정면": 윤곽2(정뿔, xa, 1.5), "뿔 옆": 옆윤곽(옆뿔, 1.5), "눈": 눈,
      "안테나": 안테나, "안테나 끝 y": 뒤9, "볼날개": 윤곽(칸([7, 10, 25, 26, 28]) & m1.astype(np.uint8), 2.0), "번개": 번개, "꼭대기 z": float(-꼭대기)}
값 = {"v4": v4, "마스크 판": 판들, "정면 몸": 윤곽2(정몸, xa, 4.0), "옆 몸": 윤곽2(옆몸, -D0 * 0 + 0) if False else [[float(p[0] + D0), float(-p[1])] for p in cv2.approxPolyDP(max(cv2.findContours(옆몸, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea), 4.0, True).reshape(-1, 2)],
      "E": {"a": float(a), "c": float(c), "zc": float(-zc), "y0": float(y0), "f": float(f)}, "껍질": 1.8, "턱 z": float(-턱),
     "얼굴 구멍": 윤곽(얼굴, 2.0), "차양 오른쪽": 윤곽(칸([14, 16]) & m1.astype(np.uint8), 1.5, True), "차양 두께": 6.0}
json.dump(값, open(os.path.join(O, "값_v3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) else f"{len(v)} 윤곽 · {[len(p) for p in v]} 점") for k, v in 값.items()})
