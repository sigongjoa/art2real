# 선 기반 영역 추론 싼 확인 셋(사용자 10-15 「구조가 복잡해지면 선이 많아지고 인식을 못 한다 · 선 기반 영역 추론은?」) · 712 개 · 칸 깎기(numpy · CAD 대 칸 0.96)
# 영역 = 방향마다 맞춘 선 그림에서 채운 윤곽 안 · 선이 아닌 화소의 4 이웃 덩어리 · 선 화소는 제 값을 둔다
# ① 선 화소 수 · 영역 수 대 (나) 점수 상관  ② 정답 층을 영역마다 중앙값 하나로 → 천장  ③ (나) 예측 층을 영역마다 최빈값으로(학습 없음)
import sys, json, numpy as np, cv2
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
import 짓기 as J, 여섯방향 as S6, 지역틀 as T, 평가51나 as E, 천장쪼개기52 as C
O = "G:/art2real/out/설명/캐드부품/"
def 영역들(그):   # → (라벨 (N, N) · 0 = 선 또는 바깥, 영역 수)
    import 입력51 as I
    안 = I._채움(그) & (그 == 0); n, lab = cv2.connectedComponents(안.astype(np.uint8), connectivity=4); return lab, n - 1
def 영역값(층, lab, n, 방법):   # 방법: 중앙 · 최빈 · 평면(영역마다 층 = a 열 + b 행 + c 최소제곱 · 통째(17) 화소는 따로 다수결)
    out = 층.copy(); Y, Xg = np.mgrid[:층.shape[0], :층.shape[1]]
    for r in range(1, n + 1):
        m = lab == r
        if m.sum() == 0: continue
        v = 층[m]
        if 방법 == "평면":
            통 = v == 17
            if 통.mean() > .5: out[m] = 17; continue
            A = np.c_[Xg[m][~통], Y[m][~통], np.ones((~통).sum())]
            if len(A) < 3: continue
            c = np.linalg.lstsq(A, v[~통].astype(float), rcond=None)[0]; out[m] = np.clip(np.round(np.c_[Xg[m], Y[m], np.ones(m.sum())] @ c), 0, 16).astype(np.uint8)
        else: out[m] = int(np.median(v)) if 방법 == "중앙" else int(np.bincount(v, minlength=18).argmax())
    return out
def 하나(job):
    p, 그림, 정층, 예층, 반, 정칸, 틀칸 = job
    try:
        v, f, H = J.정규메시(p); 몸, _ = J.몸통37(그림, H); 선수, 영수 = 0, 0; 정영, 예영 = 정층.copy(), 예층.copy(); 정평, 예평, 정평3 = 정층.copy(), 예층.copy(), 정층.copy()
        for n_, k in enumerate(S6.방향):
            그 = T.그림맞춤(*그림, k); lab, n = 영역들(그); 선수 += int(그.sum()); 영수 += n
            정영[n_] = 영역값(정층[n_], lab, n, "중앙"); 예영[n_] = 영역값(예층[n_], lab, n, "최빈"); 정평[n_] = 영역값(정층[n_], lab, n, "평면"); 예평[n_] = 영역값(예층[n_], lab, n, "평면")
            if k in ("위", "앞", "옆"): 정평3[n_] = 정평[n_]   # 그려진 세 방향만 영역 · 나머지 셋은 그대로
        h들 = [float(x) for x in 반]; r = lambda a: float((a & 정칸).sum() / max((a | 정칸).sum(), 1))
        깎 = lambda 층: C.깎(틀칸, E.지도(층, 반), 48, True, h들)
        return [r(깎(정층)), r(깎(정영)), r(깎(예층)), r(깎(예영)), 선수, 영수, r(깎(정평)), r(깎(예평)), r(깎(정평3)), ""]
    except Exception as ex: return [0] * 9 + [type(ex).__name__ + " " + str(ex)[:50]]
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; del e
    L = json.load(open(O + "목록.json", encoding="utf-8")); 범 = json.load(open(O + "범위46.json")); z = np.load(O + "데이터51.npz"); 층, 반, 정, 틀 = z["층"], z["반"], z["정답"], z["틀"]
    D = O + "학습51나_판0전체/"; P = np.load(D + "예측.npy", mmap_mode="r"); 자 = {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}; 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
    jobs = [(L[te[j]], (X[j], F[j], S[j]), 층[te[j]], np.array(P[자[int(te[j])]]), 반[te[j]], 풀(정[te[j]]), 풀(틀[te[j]])) for j in 범]
    with Pool(4, maxtasksperchild=20) as pool: R = pool.map(하나, jobs, chunksize=4)
    a = np.array([x[:9] for x in R], float); 실 = [x[9] for x in R if x[9]]; 나 = np.load(D + "부피IoU.npy")[:, 0]; np.save(O + "영역53.npy", a)
    from scipy.stats import spearmanr
    결과 = {"실패": len(실), "① 상관(스피어만) 나 CAD 대 선 화소 수": float(spearmanr(나, a[:, 4])[0]), "① 상관 나 CAD 대 영역 수": float(spearmanr(나, a[:, 5])[0]),
          "① 나 대 천장 틈(천장 − 나) 대 영역 수": float(spearmanr(a[:, 0] - 나, a[:, 5])[0]),
          "② 정답 층 그대로(칸)": float(a[:, 0].mean()), "② 정답 층 영역 중앙값": float(a[:, 1].mean()),
          "③ 나 예측 그대로(칸)": float(a[:, 2].mean()), "③ 나 예측 영역 최빈값": float(a[:, 3].mean()), "④ 정답 층 영역 평면": float(a[:, 6].mean()), "④ 나 예측 영역 평면": float(a[:, 7].mean()), "④ 정답 평면 · 그려진 세 방향만": float(a[:, 8].mean()), "③ 오른 부품(> +0.01)": int((a[:, 3] > a[:, 2] + .01).sum()), "③ 내린 부품(< −0.01)": int((a[:, 3] < a[:, 2] - .01).sum())}
    for q in (0, 1, 2, 3): m = a[:, 5] >= np.quantile(a[:, 5], q / 4); 결과["영역 수 사분위 %d 이상: 나 %.3f · 천장 %.3f" % (q, 나[m].mean(), a[m, 0].mean())] = int(m.sum())
    json.dump(결과, open(O + "결과_영역53.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
