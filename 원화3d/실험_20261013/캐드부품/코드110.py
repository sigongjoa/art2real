# 판정기준110 — 기하 처리 → 코드 → 고르기 → 깎기 · 단계 1 천장: 영역마다 신탁 고르기(정답과 평균 |차| 최소) · 10-20
# 영역 = 방향마다 제 도면의 닫힌 영역(입력51 선 아닌 안 화소 4-연결 · 30 화소 이상) · 후보 = 다른 두 도면 넓은 선(후보101) 을 8-연결 선 조각으로 나눠 조각마다 「열 → 깊이 칸」 · 영역 열 범위의 절반 넘게 지나면 후보 · + 껍질 · 관통
# 사용(venv · ART_MEM_GB=12): 코드110.py 천장 [일꾼=4] → out/설명/캐드부품/코드110/ 층.npy(712 × 6 × 128²) · 값.npy · 결과.json
import sys, os, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
import 후보96 as H, 후보101 as P
O = "G:/art2real/out/설명/캐드부품/"; D = O + "코드110/"; N = 128; K = 32
d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
z = np.load(O + "데이터51.npz"); 반, 틀51, 정51 = z["반"], z["틀"], z["정답"]; I = np.load(O + "후보96_색인.npy").astype(np.int64)
입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍32 = np.load(O + "껍질32.npy", mmap_mode="r"); 층32 = np.load(O + "층32.npy", mmap_mode="r")
세 = lambda M: M[::-1].T > 0
def 칸층표(i, n):   # 칸 → 층(후보96.하나 와 같은 내림)
    k = H.방[n]; a, s = H.축[k]; hh = float(반[i][n]); w = s * H.g + H.칸 / 2
    return np.clip(np.floor((hh - w) / (2 * hh / K) + 1e-6), 0, K - 1).astype(np.int64) if hh > 0 else None
def 조각들(L, 뜀=2):   # L[열, 칸] bool → 선 조각마다 (열들, 열마다 칸) · 열을 따라가며 이음 — 한 열에 깊이가 여럿이면 갈라짐(연결 성분 평균은 0 과 16 을 섞어 10 을 만들었음)
    사슬 = []; 열린 = []
    for x in range(L.shape[0]):
        c = np.nonzero(L[x])[0]
        if not len(c): 열린 = []; continue
        끊 = np.nonzero(np.diff(c) > 1)[0]; 토막 = [t.mean() for t in np.split(c, 끊 + 1)]; 새 = []
        for v in 토막:
            가 = [k for k in 열린 if abs(사슬[k][1][-1] - v) <= 뜀 and 사슬[k][0][-1] == x - 1]
            if 가: k = min(가, key=lambda k: abs(사슬[k][1][-1] - v)); 사슬[k][0].append(x); 사슬[k][1].append(v); 새.append(k)
            else: 사슬.append(([x], [v])); 새.append(len(사슬) - 1)
        열린 = 새
    return [(np.array(a), np.array(b)) for a, b in 사슬 if len(a) >= 3]
def 영역후보(i, n, 열, 실열=None):   # → 영역 목록 [(마스크, [(이름, 층 지도 값(영역 화소 순서), 덧(출처 · 덮음 · 실선 몫))...])] · 실열 = 실선만으로 만든 열 후보(실선 몫 재기)
    표 = 칸층표(i, n)
    if 표 is None: return []
    a = H.축[H.방[n]][0]; 조 = [조각들(열[a][0]), 조각들(열[a][1])]; 안 = 입[i, n, 1] > 0; 껍 = 껍32[i, n].astype(np.int64)
    m_, lab = cv2.connectedComponents(((입[i, n, 0] == 0) & 안).astype(np.uint8), connectivity=4); out = []
    크 = np.bincount(lab.ravel(), minlength=m_); lab = np.where(크[lab] >= 8, lab, 0)   # 10-20 고침: 선 화소 · 작은 영역(8 화소 아래 · 고침 2 에서 30 → 8: 얇은 고리가 큰 영역에 먹혔음)을 가장 가까운 영역에 붙임(깎인 속의 31 % 가 선 화소였음)
    if (lab > 0).any(): _, (yy, xx) = distance_transform_edt(lab == 0, return_indices=True); lab = np.where(안, lab[yy, xx], 0)
    for r in range(1, m_):
        m = lab == r
        if m.sum() < 8: continue
        후 = [("껍질", 껍[m], (-1, 1., 1.)), ("관통", np.full(m.sum(), K), (-2, 1., 1.))]
        for j in (0, 1):
            col = I[n, j][m]; 범 = np.unique(col)
            for t, (열들, 칸) in enumerate(조[j]):
                덮 = np.isin(범, 열들).mean()
                if 덮 <= .5: continue
                실 = float(실열[a][j][열들, np.clip(np.round(칸).astype(int), 0, N - 1)].mean()) if 실열 is not None else 1.
                c = np.interp(col, 열들, 칸); 후.append((f"{'AB'[j]}{t}", np.maximum(표[np.clip(np.round(c).astype(int), 0, N - 1)], 껍[m]), (j, float(덮), 실)))
        후 += 기운평면(i, n, r, m, 조, 표, 껍)
        후 += 회전후보(i, n, m, 표, 껍)
        out.append((m, 후))
    return out
def 날열(i, a):   # 날 선(세로선 안 지움 · 실선 ∪ 숨은선) 을 [열, 칸] 으로 — 후보96.열후보 와 같은 배치
    Lxy, Lxz, Lyz = 세(np.maximum(X[i], HX[i])), 세(np.maximum(F[i], HF[i])), 세(np.maximum(S[i], HS[i]))
    return {2: (Lxz, Lyz), 1: (Lxy, Lyz.T), 0: (Lxy.T, Lxz.T)}[a]
def 프로파일(L, 표, k):   # 열마다 보는 쪽(층 작은 쪽)에서 k 번째 선 토막의 층 · 없으면 nan
    out = np.full(N, np.nan)
    for p in range(N):
        c = np.nonzero(L[p])[0]
        if not len(c): continue
        층 = sorted({int(np.median(표[t])) for t in np.split(c, np.nonzero(np.diff(c) > 1)[0] + 1)})
        if len(층) > k: out[p] = 층[k]
    return out
def 회전후보(i, n, m, 표, 껍, 최대잔차=1.5, 몇=3):   # 판정기준113 — 영역 바깥 윤곽이 원이면 그 중심을 지나는 깊이 축 둘레로 다른 도면의 단면 프로파일(보는 쪽에서 k 번째 선)을 돌림 · 공 = 첫 선(바깥 윤곽) · 그릇 안 = 둘째 · 셋째(숨은선) · 선 조각은 세로선 지우기로 원 윤곽이 끊겨 못 씀(3504 조각 23 개)
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return []
    c0 = max(cs, key=len)[:, 0, :].astype(float)
    if len(c0) < 20: return []
    A_ = np.c_[2 * c0, np.ones(len(c0))]; b_ = (c0 ** 2).sum(1); (cx, cy, k_), *_ = np.linalg.lstsq(A_, b_, rcond=None); R = np.sqrt(k_ + cx ** 2 + cy ** 2)   # 대수 원 맞춤(x, y)
    if R < 4 or np.abs(np.hypot(c0[:, 0] - cx, c0[:, 1] - cy) - R).mean() > 최대잔차: return []
    yy, xx = np.nonzero(m); rr = np.hypot(yy - cy, xx - cx); out = []; iy, ix = int(np.clip(round(cy), 0, N - 1)), int(np.clip(round(cx), 0, N - 1))
    a = H.축[H.방[n]][0]; Ls = 날열(i, a)
    for j in (0, 1):
        cp = I[n, j][iy, ix]
        for k in range(몇):
            pr = 프로파일(Ls[j], 표, k); 값 = []
            for s in (1, -1):
                q = np.clip(np.round(cp + s * rr).astype(int), 0, N - 1); 값.append(pr[q])
            v = np.nanmean(np.stack(값), 0) if np.isfinite(np.stack(값)).any() else None
            if v is None or np.isfinite(v).mean() < .6: continue
            v = np.where(np.isfinite(v), v, np.nanmedian(v))
            out.append((f"회전{'AB'[j]}{k}", np.maximum(np.round(v).astype(np.int64), 껍[m]), (3, float(np.isfinite(v).mean()), 1.)))
    return out
def _옛회전후보(n, m, 조, 표, 껍, 최대잔차=1.5):   # 선 조각을 돌리던 첫 판 — 원 윤곽이 끊겨 후보가 거의 안 나옴(3504 부품 전체 2 개) · 안 씀
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return []
    c0 = max(cs, key=len)[:, 0, :].astype(float)
    if len(c0) < 20: return []
    A_ = np.c_[2 * c0, np.ones(len(c0))]; b_ = (c0 ** 2).sum(1); (cx, cy, k_), *_ = np.linalg.lstsq(A_, b_, rcond=None); R = np.sqrt(k_ + cx ** 2 + cy ** 2)   # 대수 원 맞춤(x, y)
    if R < 4 or np.abs(np.hypot(c0[:, 0] - cx, c0[:, 1] - cy) - R).mean() > 최대잔차: return []
    yy, xx = np.nonzero(m); rr = np.hypot(yy - cy, xx - cx); out = []; iy, ix = int(np.clip(round(cy), 0, N - 1)), int(np.clip(round(cx), 0, N - 1))
    for j in (0, 1):
        cp = I[n, j][iy, ix]   # 중심의 그 도면 열
        for t, (열들, 칸) in enumerate(조[j]):
            값 = []
            for s in (1, -1):
                q = cp + s * rr; 안 = (q >= 열들.min()) & (q <= 열들.max())
                if 안.mean() < .6: continue
                v = np.where(안, np.interp(q, 열들, 칸), np.nan); 값.append(v)
            if not 값: continue
            v = np.nanmean(np.stack(값), 0); v = np.where(np.isnan(v), np.nanmedian(v), v)
            out.append((f"회전{'AB'[j]}{t}", np.maximum(표[np.clip(np.round(v).astype(int), 0, N - 1)], 껍[m]), (3, float(len(값) / 2), 1.)))
    return out
def 기운평면(i, n, r, m, 조, 표, 껍, 반복=200, 최대=2):   # 10-20 고침 2 — 면은 다른 두 도면에 선으로 그려진 모서리로 둘러싸임 → 영역 경계 화소마다 선 조각 깊이(그 열에서만) → RANSAC 평면 층 = a·y + b·x + c
    경 = m & (cv2.dilate((~m).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); ys, xs = np.nonzero(경)
    if len(ys) < 6: return []
    점 = []
    for j in (0, 1):
        col = I[n, j][ys, xs]
        for 열들, 칸 in 조[j]:
            k = np.isin(col, 열들)
            if k.sum() < 2: continue
            c = np.interp(col[k], 열들, 칸); 점.append(np.stack([ys[k], xs[k], 표[np.clip(np.round(c).astype(int), 0, N - 1)]], 1))
    if not 점: return []
    점 = np.concatenate(점).astype(float); 화 = ys * N + xs; 점화 = 점[:, 0] * N + 점[:, 1]; rng = np.random.default_rng(i * 1000 + n * 100 + r); 찾 = []
    for _ in range(반복):
        q = 점[rng.choice(len(점), 3, replace=False)]; A = np.c_[q[:, :2], np.ones(3)]
        if abs(np.linalg.det(A)) < 1e-6: continue
        w = np.linalg.solve(A, q[:, 2]); 맞 = np.abs(점[:, :2] @ w[:2] + w[2] - 점[:, 2]) <= 1
        if abs(w[0]) + abs(w[1]) < 1e-3: continue   # 수평면은 선 조각 후보가 이미 냄
        찾.append((len(np.unique(점화[맞])) / len(화), w))
    out = []; 찾.sort(key=lambda x: -x[0]); yy, xx = np.nonzero(m)
    for f, w in 찾:
        if f < .4 or len(out) >= 최대: break
        v = np.clip(np.round(yy * w[0] + xx * w[1] + w[2]), 0, K - 1).astype(np.int64)
        if any(np.abs(v - o[1]).mean() < 1 for o in out): continue
        out.append((f"평면{len(out)}", np.maximum(v, 껍[m]), (2, float(f), 1.)))
    return out
def 펴기(i, n, 영, 고름):   # 영역마다 고른 후보 → (N, N) 층 · 선 화소 · 작은 영역은 가장 가까운 영역 값 · 윤곽 밖 32
    t = np.full((N, N), -1, np.int64)
    for (m, 후), k in zip(영, 고름): t[m] = 후[k][1]
    안 = 입[i, n, 1] > 0; 됨 = t >= 0
    if 됨.any():
        _, (yy, xx) = distance_transform_edt(~됨, return_indices=True); t = t[yy, xx]
    else: t = 껍32[i, n].astype(np.int64)
    return np.where(안, np.maximum(t, 껍32[i, n].astype(np.int64)), K).astype(np.uint8)
def 천장(i):   # 신탁: 영역마다 정답과 평균 |차| 최소
    선 = (세(np.maximum(X[i], HX[i])), 세(np.maximum(F[i], HF[i])), 세(np.maximum(S[i], HS[i]))); 열 = P.열후보_넓게(*선); out = np.zeros((6, N, N), np.uint8); 수 = []
    for n in range(6):
        영 = 영역후보(i, n, 열); g = 층32[i, n].astype(np.int64)
        고름 = [int(np.argmin([np.abs(v - g[m]).mean() for _, v, _ in 후])) for m, 후 in 영]; out[n] = 펴기(i, n, 영, 고름); 수 += [len(후) for _, 후 in 영]
    return out, (float(np.mean(수)) if 수 else 0.)
def 일(job):
    k, i, p = job; import 평가69 as E
    t, 수 = 천장(i); r, 칸 = E.하나((k, p, t, 반[i], 틀51[i], 정51[i])); return t, r, 수
if __name__ == "__main__":
    os.makedirs(D, exist_ok=True); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예 = te[범]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    if sys.argv[1:2] == ["시험"]:   # 부품 59 하나 · 위 방향 영역 · 후보
        선 = (세(np.maximum(X[59], HX[59])), 세(np.maximum(F[59], HF[59])), 세(np.maximum(S[59], HS[59]))); 열 = P.열후보_넓게(*선)
        for m, 후 in 영역후보(59, 0, 열): print("영역", m.sum(), "화소 · 후보", [(nm, int(np.median(v))) for nm, v, _ in 후], "· 정답 중앙", int(np.median(층32[59, 0][m])))
        t, 수 = 천장(59); g = 층32[59, 0]; 안 = (입[59, 0, 1] > 0) & (g < K); print("59 위 천장 층 맞음", ((t[0] == g) & 안).sum() / 안.sum()); sys.exit()
    from multiprocessing import Pool
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4, maxtasksperchild=20) as pool: 출 = pool.map(일, [(k, int(i), L[i]) for k, i in enumerate(예)], chunksize=2)
    T = np.stack([o[0] for o in 출]); R = np.array([o[1] for o in 출], float); np.save(D + "층.npy", T); np.save(D + "값.npy", R); np.save(D + "부품.npy", 예)
    거 = np.load(O + "거름62.npy"); R0 = np.nan_to_num(R); 울 = lambda m: float(R0[m, 2].sum() / max(R0[m, 3].sum(), 1))
    결 = {"450 F@1": float(R0[거, 0].mean()), "450 울퉁": 울(거), "712 F": float(R0[:, 0].mean()), "712 IoU": float(R0[:, 1].mean()), "영역당 후보 평균": float(np.mean([o[2] for o in 출])), "실패": int(np.isnan(R[:, 0]).sum())}
    a = np.zeros(4)
    for k, i in enumerate(예):
        g = 층32[i].astype(int); s = 껍32[i].astype(int); 안 = (입[i][:, 1] > 0) & (g < K); 깎 = 안 & (g >= s + 2); e_ = np.abs(T[k].astype(int) - g); a += [안.sum(), (안 & (e_ <= 1)).sum(), 깎.sum(), (깎 & (e_ <= 1)).sum()]
    결["안 ±1"] = a[1] / a[0]; 결["깎인 속 ±1"] = a[3] / a[2]; print(json.dumps(결, ensure_ascii=False, indent=1)); json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
