# 판정기준96 — 학습 없이 규칙만: 영역마다 후보96 깊이로 깎아 → 위 · 앞 · 옆 다시 그림 → 원래 도면과 맞대 고르기(구조99 를 시험 300 으로) · 10-20
# 팔: R = 다시 그려 맞대 고름 · R* = 정답 3D 와 IoU 로 고름(이 영역 · 후보 틀의 천장) · 대조 = 학습69_판0
# 사용(venv · ART_MEM_GB=12): 맞대100.py 감사 → 정답 칸을 다시 그려 원래 도면과 F (방향 맞춤 확인)
#                             맞대100.py [수=300] [일꾼=4] → out/설명/캐드부품/맞대100/ 층.npy · 결과.json
import sys, os, json, numpy as np, cv2
import 후보96 as H, 천장쪼개기52 as C, 울퉁67 as U, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; D = O + "맞대100/"; N = 128; K = 32; k3 = np.ones((3, 3), np.uint8)
d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]
층32 = np.load(O + "층32.npy", mmap_mode="r"); 껍32 = np.load(O + "껍질32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r")
CAND = np.load(O + "후보96.npy", mmap_mode="r"); I = np.load(O + "후보96_색인.npy").astype(np.int64); te = np.nonzero(시)[0]
작 = lambda a: cv2.resize(a.astype(np.uint8), (48, 48), interpolation=cv2.INTER_AREA) > 0
def 깎(i, t):   # 여섯 방향 층 (6, N, N) → 48³
    hh = [float(x) for x in 반[i]]; w = {k: np.where(t[j] == 32, np.nan, hh[j] - t[j] * (2 * hh[j] / 32)) for j, k in enumerate(S6.방향)}
    return C.깎(U.풀(틀[i]), w, 48, False, hh)
def 선(v, 뛰=2):   # v[u, 깊이, w] 를 깊이 + 끝에서 본 선 · 구조99 투영과 같은 규칙(구간 수 바뀜 · 경계 뜀) · 실선 ∪ 점선
    n = v.shape[0]; dd = np.diff(np.pad(v, ((0, 0), (1, 1), (0, 0))).astype(np.int8), axis=1); 수 = (dd == 1).sum(1)
    idx = np.where(dd != 0, np.arange(n + 1)[None, :, None], -99); 경 = -np.sort(-idx, axis=1)[:, :6]   # 앞(+ 끝)부터 경계 6 개
    out = np.zeros((n, n), bool)
    for 축 in (0, 1):
        a = [slice(None)] * 2; b = [slice(None)] * 2; a[축] = slice(1, None); b[축] = slice(None, -1); a, b = tuple(a), tuple(b)
        out[a] |= (수[a] != 수[b]) | (np.abs(경.transpose(0, 2, 1)[a] - 경.transpose(0, 2, 1)[b]) > 뛰).any(-1)
    return out
보기 = {"위": lambda v: v.transpose(0, 2, 1), "앞": lambda v: v, "옆": lambda v: v.transpose(1, 0, 2)}   # 깊이 축을 가운데로
맞춤 = {k: tuple(v) for k, v in json.load(open(D + "맞춤.json")).items()} if os.path.exists(D + "맞춤.json") else {}   # 감사에서 고른 방향 맞춤(전치 · 뒤집기)
def 놓기(a, m): a = a.T if m[0] else a; a = a[::-1] if m[1] else a; return a[:, ::-1] if m[2] else a
def 다시그림(v): return np.stack([놓기(선(f(v)), 맞춤[k]) for k, f in 보기.items()])
def 원도면(i): return np.stack([작((X[i] > 0) | (HX[i] > 0)), 작((F[i] > 0) | (HF[i] > 0)), 작((S[i] > 0) | (HS[i] > 0))])
def Fs(a, b):   # 선 F(3×3 허용)
    ad, bd = [np.stack([cv2.dilate(x.astype(np.uint8), k3) > 0 for x in y]) for y in (a, b)]
    p = (b & ad).sum() / max(b.sum(), 1); r = (a & bd).sum() / max(a.sum(), 1); return 2 * p * r / max(p + r, 1e-9)
def 감사(n=40):
    import itertools; 쌍 = list(itertools.product((0, 1), repeat=3)); 합 = {k: np.zeros(8) for k in 보기}
    for i in te[:n]:
        v = U.풀(정[i]); 원 = 원도면(i)
        for j, (k, f) in enumerate(보기.items()):
            l = 선(f(v)); 합[k] += [Fs(원[j:j + 1], 놓기(l, m)[None]) for m in 쌍]
    for k in 보기: b = int(np.argmax(합[k])); 맞춤[k] = 쌍[b]; print(k, "맞춤", 쌍[b], "F %.3f" % (합[k][b] / n), "· 다음 %.3f" % (np.sort(합[k])[-2] / n))
    json.dump(맞춤, open(D + "맞춤.json", "w"));
def 영역들(i, Q):   # 방향마다 닫힌 영역(제 선 밖 · 안쪽 · 30 화소 넘게) → (방향, 마스크, 후보 층들)
    out = []
    for k in range(6):
        안 = 입[i, k, 1] > 0; n, lab = cv2.connectedComponents(((입[i, k, 0] == 0) & 안).astype(np.uint8), connectivity=4)
        for r in range(1, n):
            m = lab == r
            if m.sum() < 30: continue
            q = Q[k][m]; 후 = [c for c in range(K) if (((q >> c) & 1) > 0).mean() > .5]
            out.append((k, m, 후))
    return sorted(out, key=lambda t: -t[1].sum())
def 하나(i):   # → R 층 · R* 층 (6, N, N)
    Q = H.펴기(np.asarray(CAND[i]), I).astype(np.int64); 껍 = np.asarray(껍32[i]).astype(np.int64); 원 = 원도면(i); 정v = U.풀(정[i]); 결과 = {}
    for 팔 in ("R", "R*"):
        t = 껍.copy(); 지금 = 깎(i, t)
        for k, m, 후 in 영역들(i, Q)[:24]:   # ponytail: 큰 영역 24 개까지 · 탐욕(한 번씩) · 영역 사이 조합은 안 봄
            가 = sorted({max(c, int(껍[k][m].max())) for c in 후} | {32}) ; 가 = [c for c in 가 if c > 껍[k][m].min()]
            if not 가: continue
            판들 = [(None, 지금)]
            for c in 가: tt = t.copy(); tt[k][m] = np.maximum(c, 껍[k][m]); 판들.append((tt, 깎(i, tt)))
            if 팔 == "R":
                그림들 = [다시그림(v) for _, v in 판들]; 다름 = np.logical_or.reduce(그림들) & ~np.logical_and.reduce(그림들)
                다름 = np.stack([cv2.dilate(x.astype(np.uint8), k3) > 0 for x in 다름]); 점 = [Fs(원 & 다름, g & 다름) if 다름.any() else 0 for g in 그림들]
            else: 점 = [(v & 정v).sum() / max((v | 정v).sum(), 1) for _, v in 판들]
            b = int(np.argmax(점))   # 같으면 앞(안 깎음)
            if b: t, 지금 = 판들[b]
        결과[팔] = t.astype(np.uint8)
    return i, 결과["R"], 결과["R*"]
if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    if sys.argv[1:2] == ["감사"]: 감사(); sys.exit()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    from multiprocessing import Pool
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4) as pool: 출 = pool.map(하나, list(te[:n]), chunksize=1)
    np.save(D + "부품.npy", np.array([o[0] for o in 출])); np.save(D + "R.npy", np.stack([o[1] for o in 출])); np.save(D + "R별.npy", np.stack([o[2] for o in 출])); print("끝", n)
