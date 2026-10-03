# -*- coding: utf-8 -*-
"""부리 판 셋을 점수로 맞추기 — 학습처럼 (10-03 사용자 「붙이기는 학습시키는 것처럼 metric 을 기준으로 피드백 구조를 한다면?」 → 「ㄱㄱ」).
틀 = 도면 틀(x = 정면 px − cu · z = −행 · 깊이 d: 눈 = 0, 앞 −). 판 = 미늘1(코판) · 미늘2 · 턱판(마스크 · 부품ID 대응표).
  판 모양 = 정면 칸 그대로(정면 점수는 구성상 만점 → 맞추지 않음)
  배울 값(판마다 4) = 앞면 깊이 평면 d(x, z) = d0 + gz·(z − zc) + gx·|x − x0|(좌우 대칭 V) · 두께 t
  학습 손실 = 1 − IoU(옆 원화의 같은 이름 칸 · 옆 카메라 = 블록아웃 B 맞춤) — 판마다 따로(짝이 이름으로 정해져 있음)
  검증 = 3/4 원화의 같은 이름 칸과 IoU — 맞출 때 안 씀. 3/4 카메라는 부리와 무관한 점 9 개(눈 · 눈구멍 · 번개 · 안테나 뿌리 · 볼날개)로 따로 풂
  대조군 = 판얹기 1 판의 놓기(부리 쐐기 앞면 · 두께 4)
미리 적은 성공 기준: 검증(3/4) IoU 가 대조군보다 오르고 · 겹침 그림에서 부리 판 계단이 원화 쪽으로 감.
출력 out/오메가몬2/블렌더/부리학습.json · 부리학습_곡선.png · 부리학습_겹침.png"""
import os, json, numpy as np, cv2
from scipy.optimize import differential_evolution, least_squares
from scipy.spatial import ConvexHull
os.environ["PAIR"] = "B"
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "도형블록아웃.py")}
exec(open(G["__file__"], encoding="utf-8").read(), G)
O, B, f, s2, cu, beak = G["O"], G["B"], G["f"], G["s"], G["cu"], G["beak"]
k, t_, c_, xm, ex, ey = G["k"], G["t"], G["c"], G["xm"], G["ex"], G["ey"]
ct, st = np.cos(t_), np.sin(t_); Ai = np.linalg.inv(np.array([[k * ct, -k * st], [k * st, k * ct]])); b0 = np.array([-k * (ex * ct - ey * st), -k * xm * st + c_])
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]
def 칸지도(n):
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0_ = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
    return L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0_ + 2 * px, 0, L.shape[1] - 1)] * m
def 표면칸(n, 표면):
    cs = [c for e in 대응[n] if e.get("부품") == "H02 마스크" and e.get("표면") == 표면 for c in e["칸"]]; return np.isin(칸지도(n), cs) if cs else None
판들 = ["코판", "미늘2", "턱판"]
F1 = {p: 표면칸("1", p) for p in 판들}; S2 = {p: 표면칸("2", p) for p in 판들}; S3 = {p: 표면칸("3", p) for p in 판들}
print({p: (int(F1[p].sum()), None if S2[p] is None else int(S2[p].sum()), None if S3[p] is None else int(S3[p].sum())) for p in 판들})
x0 = np.mean([(f[a + "/오른"][0] + f[a + "/왼"][0]) / 2 for a in ("눈", "눈구멍 바깥", "번개")]) - cu
def 옆(P): v = (Ai @ np.stack([P[:, 1] - b0[0], -P[:, 2] - b0[1]])).T; return v[:, 0], v[:, 1]
# 3/4 카메라(부리와 무관한 점만): 정면 x · z + 옆 d → 3/4 화소
def T(p): return G["T"](p)
pts3 = {}
for nm in ("눈", "눈구멍 안", "눈구멍 바깥", "번개", "안테나 뿌리"):
    d, _ = T(s2[nm + "/오른"])
    for side in ("오른", "왼"):
        if nm + "/" + side in f: pts3[nm + "/" + side] = np.array([f[nm + "/" + side][0] - cu, d, -f[nm + "/" + side][1]])
d, _ = T(s2["볼날개 끝/오른"]); pts3["볼날개 끝/오른"] = np.array([f["볼날개 끝/오른"][0] - cu, d, -f["볼날개 끝/오른"][1]])
P3 = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))["3"]; ks = [q for q in pts3 if q in P3]
def Rm(yaw, pitch, roll):
    a, b, r = np.radians([yaw, pitch, roll]); Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]]); Ry = np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]]); return Ry @ Rx @ Rz
def 셋(P, q):   # 정사영: 회전 뒤 (x, z) → 화소 · 카메라는 앞(−d)에서 봄
    R = Rm(*q[:3]); v = P @ R.T; return q[3] * v[:, 0] + q[4], -q[3] * v[:, 2] + q[5]
A3 = np.array([pts3[q] for q in ks]); B3 = np.array([P3[q] for q in ks], float)
r3 = lambda q: np.r_[np.subtract(셋(A3, q), [B3[:, 0], B3[:, 1]]).ravel()]
cam3 = least_squares(r3, [-35, 5, 0, 1.0, 200, 150], bounds=([-80, -40, -30, 0.3, -500, -500], [0, 40, 30, 3, 900, 900])).x
e3 = np.sqrt((np.array(셋(A3, cam3)).T - B3) ** 2).sum(1); print("3/4 카메라", np.round(cam3, 2), "점 어긋남 중앙", round(float(np.median(e3)), 1), "점", len(ks))
def 부피(p, prm, 층=6):
    yy, xx = np.nonzero(F1[p]); X = xx - cu; Z = -yy.astype(float); zc = Z.mean(); d0, gz, gx, th = prm
    D = d0 + gz * (Z - zc) + gx * np.abs(X - x0); return np.concatenate([np.c_[X, D + th * l / (층 - 1), Z] for l in range(층)])
def 찍기(sx, sy, shape):
    img = np.zeros(shape, np.uint8); xi, yi = np.round(sx).astype(int), np.round(sy).astype(int); ok = (xi >= 0) & (xi < shape[1]) & (yi >= 0) & (yi < shape[0]); img[yi[ok], xi[ok]] = 1
    return cv2.dilate(img, np.ones((3, 3), np.uint8)) > 0
iou = lambda a, b: float((a & b).sum() / max(1, (a | b).sum()))
# 대조군: 판얹기 1 판(쐐기 앞면 · 두께 4)
h = ConvexHull(beak.vertices); Aq, bq = h.equations[:, :3], h.equations[:, 3]
def 대조부피(p, 층=6):
    yy, xx = np.nonzero(F1[p]); X = xx - cu; Z = -yy.astype(float); D = np.full(len(X), np.nan)
    for dd in np.arange(80, -160, -1.0):
        ins = np.all(np.c_[X, np.full(len(X), dd), Z] @ Aq.T + bq <= 1.0, axis=1); D[ins] = dd
    D = np.where(np.isnan(D), np.nanmedian(D) if np.isfinite(D).any() else 0, D); return np.concatenate([np.c_[X, D + 4 * l / (층 - 1), Z] for l in range(층)])
결과 = {"3/4 카메라(yaw · pitch · roll · 크기 · tx · ty)": np.round(cam3, 2).tolist(), "판": {}}; 곡선 = {}
최종 = {}; 경로 = {}
for p in 판들:
    if S2[p] is None or S2[p].sum() < 20: 결과["판"][p] = "옆 칸 없음"; continue
    sh2 = S2[p].shape; hist = []
    def loss(prm):
        sx, sy = 옆(부피(p, prm)); return 1 - iou(찍기(sx, sy, sh2), S2[p])
    def cb(xk, convergence=None): hist.append(loss(xk)); 경로.setdefault(p, []).append(np.array(xk))
    r = differential_evolution(loss, [(-170, 40), (-3, 3), (-1.5, 1.5), (2, 80)], maxiter=60, popsize=14, seed=1, callback=cb, tol=1e-6, polish=False)
    최종[p] = r.x; 곡선[p] = hist
    Pc = 대조부피(p); sxc, syc = 옆(Pc); P_ = 부피(p, r.x)
    rec = {"배운 값(d0 · gz · gx · 두께)": np.round(r.x, 2).tolist(), "옆 IoU(학습)": {"대조": round(iou(찍기(sxc, syc, sh2), S2[p]), 3), "배운 뒤": round(1 - r.fun, 3)}}
    if S3[p] is not None and S3[p].sum() > 20:
        sh3 = S3[p].shape; a3, b3 = 셋(Pc, cam3); a4, b4 = 셋(P_, cam3)
        rec["3/4 IoU(검증)"] = {"대조": round(iou(찍기(a3, b3, sh3), S3[p]), 3), "배운 뒤": round(iou(찍기(a4, b4, sh3), S3[p]), 3)}
    결과["판"][p] = rec; print(p, rec)
json.dump(결과, open(os.path.join(B, "부리학습.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 곡선
cv_ = np.full((300, 600, 3), 255, np.uint8)
for i, (p, hs) in enumerate(곡선.items()):
    col = [(220, 60, 60), (60, 160, 60), (60, 60, 220)][i]
    pts = np.array([[20 + 560 * j / max(1, len(hs) - 1), 280 - 260 * (1 - v)] for j, v in enumerate(hs)], np.int32); cv2.polylines(cv_, [pts], False, col, 2)
    cv2.putText(cv_, p.encode("ascii", "ignore").decode() or str(i), (20, 20 + 18 * i), 0, 0.5, col, 1)
cv2.imencode(".png", cv_)[1].tofile(os.path.join(B, "부리학습_곡선.png"))
# 겹침 그림: 옆 · 3/4 원화 위 — 흰 = 원화의 그 칸 · 빨강 = 대조 · 초록 = 배운 뒤
def 겹(n, proj, targets, art_path, bright):
    a = cv2.imdecode(np.fromfile(art_path, np.uint8), 1); a = cv2.convertScaleAbs(a, alpha=bright, beta=10)
    for p in 판들:
        if targets[p] is None or p not in 최종: continue
        for m, col in ((targets[p], (255, 255, 255)), ):
            cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(a, cs, -1, col, 1)
        for P_, col in ((대조부피(p), (60, 60, 230)), (부피(p, 최종[p]), (60, 230, 60))):
            u, v = proj(P_); m = 찍기(u, v, a.shape[:2]).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(a, cs, -1, col, 1)
    return cv2.resize(a, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
g2 = 겹("2", 옆, S2, os.path.join(O, "판_2_원화.png"), 2.0); g3 = 겹("3", lambda P_: 셋(P_, cam3), S3, os.path.join(O, "판_3_원화.png"), 1.0)
Hh = max(g2.shape[0], g3.shape[0]); g2 = cv2.copyMakeBorder(g2, 0, Hh - g2.shape[0], 0, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255)); g3 = cv2.copyMakeBorder(g3, 0, Hh - g3.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
cv2.imencode(".png", np.hstack([g2, g3]))[1].tofile(os.path.join(B, "부리학습_겹침.png"))

# ── 단계마다 보이기(사용자 「각 step 마다 보여 줘야지」) ──
from PIL import Image, ImageDraw, ImageFont
Fn = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22)
def 그림(path, br): a = cv2.imdecode(np.fromfile(path, np.uint8), 1); return cv2.convertScaleAbs(a, alpha=br, beta=10)
색 = {"코판": (60, 60, 230), "미늘2": (60, 200, 60), "턱판": (230, 120, 40)}
def 윤곽(a, m, col, w=1):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(a, cs, -1, col, w)
타일 = []
a = 그림(os.path.join(O, "판_1_원화.png"), 1.0)
for p in 판들: 윤곽(a, F1[p], 색[p], 2)
타일.append((a, "1 판 모양 = 정면 칸(빨강 코판 · 초록 미늘2 · 주황 턱판)"))
a = 그림(os.path.join(O, "판_2_원화.png"), 2.0)
for p in 판들:
    if S2[p] is not None: 윤곽(a, S2[p], 색[p], 2)
타일.append((a, "2 학습 정답 = 옆 칸(같은 색)"))
a = 그림(os.path.join(O, "판_3_원화.png"), 1.0)
for p in 판들:
    if S3[p] is not None: 윤곽(a, S3[p], 색[p], 2)
u, v = 셋(A3, cam3)
for (x_, y_), (bx, by) in zip(zip(u, v), B3): cv2.circle(a, (int(bx), int(by)), 4, (255, 255, 255), 2); cv2.line(a, (int(bx), int(by)), (int(x_), int(y_)), (0, 255, 255), 1); cv2.circle(a, (int(x_), int(y_)), 3, (0, 255, 255), -1)
타일.append((a, "3 검증 정답 = 3/4 칸 · 카메라 점(흰 = 찍은 점 · 노랑 = 카메라로 옮긴 점)"))
for p in 판들:
    if p not in 경로: continue
    ws = 경로[p]; pick = sorted(set([0, len(ws) // 8, len(ws) // 4, len(ws) // 2, len(ws) - 1]))
    for i in pick:
        a = 그림(os.path.join(O, "판_2_원화.png"), 2.0); 윤곽(a, S2[p], (255, 255, 255), 2)
        uu, vv = 옆(부피(p, ws[i])); 윤곽(a, 찍기(uu, vv, a.shape[:2]), 색[p], 2)
        sc = 1 - 곡선[p][i]; 타일.append((a, f"4 학습 {p} · {i + 1} 바퀴 · 옆 IoU {sc:.2f}"))
    a = 그림(os.path.join(O, "판_3_원화.png"), 1.0)
    if S3[p] is not None: 윤곽(a, S3[p], (255, 255, 255), 2)
    uu, vv = 셋(부피(p, 최종[p]), cam3); 윤곽(a, 찍기(uu, vv, a.shape[:2]), 색[p], 2); 타일.append((a, f"5 검증 {p} · 3/4 (흰 정답 · 색 = 배운 판)"))
T_ = 360; ims = []
for a, t in 타일:
    im = Image.fromarray(a[:, :, ::-1]); im.thumbnail((T_ * 1.6, T_)); c = Image.new("RGB", (int(T_ * 1.6), T_ + 34), (20, 20, 24)); c.paste(im, ((c.width - im.width) // 2, 34)); ImageDraw.Draw(c).text((6, 6), t, font=Fn, fill=(255, 232, 58)); ims.append(c)
cols = 3; rows = (len(ims) + cols - 1) // cols; W_, H_ = ims[0].size; sheet = Image.new("RGB", (W_ * cols, H_ * rows), (20, 20, 24))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * W_, (i // cols) * H_))
sheet.save(os.path.join(B, "부리학습_단계.png")); print("단계 그림", len(ims))
