# 판정기준84 회전 낱말 — 세 장 중 원으로 보이는 장을 축으로, 다른 두 장 윤곽을 반단면으로 돌린 몸통과 교차해 깎는다 · 10-18
# 사용(venv · ART_MEM_GB=8): 회전84.py → out/설명/캐드부품/회전84/ 결과판정84.json
import sys, os, json, numpy as np, cv2
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; D = O + "회전84/"; N = 128; g = (np.arange(N) + .5) * 1.1 / N - .55
def 대칭(m):   # 채운 윤곽 회전 대칭 점수 · 무게중심 (행, 열)
    ys, xs = np.nonzero(m)
    if len(ys) < 30: return 0., (0, 0)
    c = (float(xs.mean()), float(ys.mean())); u = m.astype(np.uint8); s = []
    for a in range(30, 360, 30):
        r = cv2.warpAffine(u, cv2.getRotationMatrix2D(c, a, 1.), (N, N), flags=cv2.INTER_NEAREST) > 0; s.append((r & m).sum() / max((r | m).sum(), 1))
    return float(np.mean(s)), (c[1], c[0])
def 회전장(X, F, S):   # 선 그림 셋 → ((축 글자, 덧장 함수), 점수) · 축이 안 잡히면 (None, 점수)
    import 입력51 as I
    rows, cols = np.mgrid[0:N, 0:N]; 장 = {"위": (I._채움(X) > 0, {"y": -g[rows], "x": g[cols]}), "앞": (I._채움(F) > 0, {"z": -g[rows], "x": g[cols]}), "옆": (I._채움(S) > 0, {"z": -g[rows], "y": g[cols]})}
    축장 = {"위": "z", "앞": "y", "옆": "x"}; 점 = {n: 대칭(m) for n, (m, _) in 장.items()}; n0 = max(점, key=lambda n: 점[n][0]); 값, (cr, cc) = 점[n0]
    if 값 < .9: return None, 값
    a = 축장[n0]; m0, c0 = 장[n0]; 중 = {t: float(c0[t][int(round(cr)), int(round(cc))]) for t in c0}   # 축 장의 무게중심 = 축이 지나는 점(축에 수직인 두 좌표)
    r = np.full(N, -1.)
    for n, (m, c) in 장.items():
        if n == n0: continue
        t = [q for q in c if q != a][0]; h = c[a][m]; d = np.abs(c[t][m] - 중[t]); i = np.clip(np.round((h + .55) / (1.1 / N) - .5).astype(int), 0, N - 1); np.maximum.at(r, i, d)
    r = np.where(r >= 0, r + 1.1 / N / 2, -1.); 축i = "xyz".index(a); 가 = [j for j in range(3) if j != 축i]; 중심 = [중["xyz"[j]] for j in 가]
    def 덧(P):
        rr = np.interp(P[:, 축i], g, r, left=-1., right=-1.); return (rr - np.hypot(P[:, 가[0]] - 중심[0], P[:, 가[1]] - 중심[1])).astype(np.float32)
    return (a, 덧), 값
def _시험():   # 원통(축 z · 반지름 .3 · 높이 ±.2)의 세 장 → 축 z · 덧장이 안 · 밖을 맞게 가르는지
    m = np.zeros((N, N), np.uint8); cv2.circle(m, (64, 64), int(.3 / (1.1 / N)), 1, -1); 옆 = np.zeros((N, N), np.uint8); r0, r1 = int((.55 - .2) / (1.1 / N)), int((.55 + .2) / (1.1 / N)); 옆[r0:r1, 64 - 35:64 + 35] = 1
    선 = lambda q: (q - cv2.erode(q, np.ones((3, 3), np.uint8))).astype(np.uint8)
    (a, 덧), 값 = 회전장(선(m), 선(옆), 선(옆)); P = np.array([[0, 0, 0], [.25, 0, 0], [.35, 0, 0], [0, 0, .3]], np.float32); v = 덧(P)
    assert a == "z" and 값 > .9 and v[0] > 0 and v[1] > 0 and v[2] < 0 and v[3] < 0, (a, 값, v); print("시험 통과", a, round(값, 3), np.round(v, 3))
def 하나(job):
    k, p, 층정, 층판, 반, 선, 그림 = job
    import 곡면79 as Q, 계단80 as T, 짓기 as J, 여섯방향 as S6
    축, 값 = 회전장(*그림)
    if 축 is None: return k, None, 값
    _, 덧 = 축; gv, gf, _ = J.정규메시(p); 정 = T.깊이들(gv, gf); u = np.tile(S6.g, (N, 1)); v = -u.T; out = {}
    def 층위(층):
        위들 = []
        for j, h in enumerate(반):
            단 = 2 * h / 32; d = np.where(층[j] == 32, np.nan, 층[j] * 단); d, _ = Q.맞추기(Q.조각(선[j], 층[j]), np.nan_to_num(d), 단, u, v); 위들.append(h - d)
        return 위들
    빈 = [np.full((N, N), h + .5) for h in 반]   # 깊이 없음 = 위 끝까지 다 있음(실루엣 부호 거리만 남음 → 세 윤곽 교차)
    for 팔, 위들, 쓰기 in (("판0맞춤", 층위(층판), False), ("판0맞춤+회전", None, True), ("단32맞춤", 층위(층정), False), ("단32맞춤+회전", None, True), ("회전만", 빈, True)):
        if 위들 is None: 위들 = 앞위
        mm = Q.장메시(위들, 반, 덧 if 쓰기 else None); 앞위 = 위들
        if mm is None: out[팔] = [np.nan] * 6; continue
        vv, ff = mm; np.savez_compressed(D + "%s_%d.npz" % (팔, k), v=np.asarray(vv, np.float32), f=np.asarray(ff, np.int32)); out[팔] = T.계단(T.깊이들(vv, ff), 정) + Q.메시F(vv, ff, gv, gf)[:2]
    print(k, round(값, 3), {a: [round(x, 3) for x in b] for a, b in out.items()}, flush=True); return k, out, 값
if __name__ == "__main__":
    _시험(); os.makedirs(D, exist_ok=True); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    묶 = {"어려움": json.load(open(O + "복잡83.json", encoding="utf-8"))["부품"], "보통": json.load(open(O + "곡면79/결과.json", encoding="utf-8"))["요약"]["부품"]}
    층32 = np.load(O + "층32.npy", mmap_mode="r"); P = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 반 = np.load(O + "데이터51.npz")["반"]
    X = np.load(O + "데이터.npz")["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 결 = {}
    for 이름, ks in 묶.items():
        일 = [(k, L[예부[k]], np.array(층32[예부[k]]), np.array(P[범[k]]), 반[예부[k]], np.array(입[예부[k], :, 0]), (X[예부[k]], F[예부[k]], S[예부[k]])) for k in ks]
        with Pool(4, maxtasksperchild=4) as pool: R = pool.map(하나, 일, chunksize=1)
        잡 = [r for r in R if r[1]]; 팔들 = ["판0맞춤", "판0맞춤+회전", "단32맞춤", "단32맞춤+회전", "회전만"]
        평 = {팔: [round(float(np.nanmean([r[1][팔][j] for r in 잡])), 4) for j in range(6)] for 팔 in 팔들} if 잡 else {}
        떨 = sum(r[1]["판0맞춤+회전"][5] < r[1]["판0맞춤"][5] - .05 for r in 잡)
        결[이름] = {"축 잡힌 부품": [r[0] for r in 잡], "대칭 점수": {str(r[0]): round(r[2], 3) for r in R}, "팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫, 메시 F 1 칸, 반 칸]": 평, "반 칸 F 0.05 넘게 떨어진 부품": int(떨), "부품별": {str(r[0]): r[1] for r in 잡}}
    h = 결["어려움"]["팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫, 메시 F 1 칸, 반 칸]"]
    결["판정"] = {"통과": bool(h and h["판0맞춤+회전"][5] >= h["판0맞춤"][5] + .03 and h["판0맞춤+회전"][1] <= h["판0맞춤"][1]), "망침 경고(1/4 넘게 떨어짐)": bool(결["어려움"]["반 칸 F 0.05 넘게 떨어진 부품"] > len(결["어려움"]["축 잡힌 부품"]) / 4)}
    json.dump(결, open("결과판정84.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps({a: ({x: y for x, y in b.items() if x != "부품별"} if isinstance(b, dict) and "부품별" in b else b) for a, b in 결.items()}, ensure_ascii=False, indent=1))
