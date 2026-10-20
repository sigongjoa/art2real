# 판정기준110 단계 2 — 코드 후보 고르기 학습: 영역 × 후보마다 특징 → 작은 MLP 점수 → 영역 안 소프트맥스(정답 = 신탁 고르기) · 화소 argmax 없음 · 10-20
# 사용(venv · ART_MEM_GB=12): 고르기110.py 특징 [일꾼=3] → 코드110/특징_학습.npz · 특징_시험.npz / 고르기110.py 학습 → 망 · 층.npy · 값.npy · 결과.json
import sys, os, json, numpy as np
import 코드110 as C
O = C.O; D = C.D; N = 128; K = 32
def 특징(i):   # → [(방향, 마스크 색인, 후보 층들(list of arr), 특징 (c, f), 신탁 번호)]
    X, F, S, HX, HF, HS = C.X[i], C.F[i], C.S[i], C.HX[i], C.HF[i], C.HS[i]; 세 = C.세
    열 = C.P.열후보_넓게(세(np.maximum(X, HX)), 세(np.maximum(F, HF)), 세(np.maximum(S, HS))); 실열 = C.P.열후보_넓게(세(X), 세(F), 세(S)); out = []
    for n in range(6):
        g = C.층32[i, n].astype(np.int64); 영 = C.영역후보(i, n, 열, 실열); 크 = 16384.
        for m, 후 in 영:
            중 = np.array([np.median(v) for _, v, _ in 후]); 껍중 = 중[0]; 선중 = [중[k] for k in range(2, len(후))]; 줄 = np.argsort(np.argsort(중))
            fs = []
            for k, (nm, v, (j, 덮, 실)) in enumerate(후):
                맞 = float(any(abs(중[k] - 중[q]) <= 1 and 후[q][2][0] not in (j, -1, -2) for q in range(2, len(후)))) if j >= 0 else 0.   # 다른 도면에도 같은 깊이 선(교집합 증거)
                fs.append([j == -1, j == -2, j == 0, j == 1, (중[k] - 껍중) / K, 중[k] / K, 덮, 실, 맞, 줄[k] / max(len(후) - 1, 1), np.std(v) / K, m.sum() / 크, len(후) / 20, *(np.arange(6) == n)])
            신 = int(np.argmin([np.abs(v - g[m]).mean() for _, v, _ in 후])); out.append((n, np.flatnonzero(m).astype(np.int32), [v.astype(np.uint8) for _, v, _ in 후], np.array(fs, np.float32), 신))
    return i, out
if __name__ == "__main__":
    import pickle
    시 = np.load(O + "데이터.npz")["시험"]; ok = C.z["ok"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예 = te[범]
    if sys.argv[1] == "특징":
        from multiprocessing import Pool
        tr = np.nonzero(~시 & ok)[0]; tr = np.random.default_rng(110).choice(tr, 2000, replace=False)
        for 꼴, 부 in (("시험", 예), ("학습", tr)):
            with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 3, maxtasksperchild=20) as pool: R = pool.map(특징, [int(i) for i in 부], chunksize=4)
            pickle.dump(R, open(D + f"특징_{꼴}.pkl", "wb")); print(꼴, len(R), "부품 · 영역", sum(len(r[1]) for r in R), flush=True)
        sys.exit()
    import torch, torch.nn as nn
    torch.manual_seed(110); 학 = pickle.load(open(D + "특징_학습.pkl", "rb")); 시험 = pickle.load(open(D + "특징_시험.pkl", "rb"))
    망 = nn.Sequential(nn.Linear(19, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 1)); opt = torch.optim.Adam(망.parameters(), 1e-3)
    묶 = [(torch.tensor(f), 신) for _, rs in 학 for (_, _, _, f, 신) in rs]; print("학습 영역", len(묶))
    for ep in range(15):
        perm = np.random.default_rng(ep).permutation(len(묶)); 합 = 0.; 맞 = 0
        for s in range(0, len(perm), 256):
            loss = 0.
            for k in perm[s:s + 256]:
                f, 신 = 묶[k]; z = 망(f)[:, 0]; loss = loss + nn.functional.cross_entropy(z[None], torch.tensor([신])); 맞 += int(z.argmax() == 신)
            opt.zero_grad(); (loss / len(perm[s:s + 256])).backward(); opt.step(); 합 += float(loss)
        if ep % 5 == 4 or ep == 0: print("에폭", ep + 1, "손실 %.4f · 학습 영역 신탁 맞힘 %.3f" % (합 / len(묶), 맞 / len(묶)), flush=True)
    torch.save(망.state_dict(), D + "고르기망.pt")
    def 펴(i, rs):   # 고른 후보 → (6, N, N) 층 (코드110.펴기 와 같은 채움)
        out = np.zeros((6, N, N), np.uint8)
        for n in range(6):
            영 = []; 고름 = []
            for (nn_, idx, vs, f, 신) in rs:
                if nn_ != n: continue
                m = np.zeros(N * N, bool); m[idx] = True; m = m.reshape(N, N); 영.append((m, [(None, v.astype(np.int64), None) for v in vs]))
                with torch.no_grad(): 고름.append(int(망(torch.tensor(f))[:, 0].argmax()))
            out[n] = C.펴기(i, n, 영, 고름)
        return out
    맞 = sum(int(망(torch.tensor(f))[:, 0].argmax() == 신) for _, rs in 시험 for (_, _, _, f, 신) in rs); 전 = sum(len(rs) for _, rs in 시험); print("시험 영역 신탁 맞힘 %.3f" % (맞 / 전))
    T = np.stack([펴(i, rs) for i, rs in 시험]); np.save(D + "고르기층.npy", T)
    from multiprocessing import Pool
    import 평가69 as E
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(3, maxtasksperchild=20) as pool: 출 = pool.map(E.하나, [(k, L[i], T[k], C.반[i], C.틀51[i], C.정51[i]) for k, (i, _) in enumerate(시험)], chunksize=2)
    R = np.nan_to_num(np.array([o[0] for o in 출], float)); np.save(D + "고르기값.npy", R); 거 = np.load(O + "거름62.npy")
    결 = {"시험 영역 신탁 맞힘": 맞 / 전, "450 F@1": float(R[거, 0].mean()), "450 울퉁": float(R[거, 2].sum() / max(R[거, 3].sum(), 1)), "712 F": float(R[:, 0].mean()), "712 IoU": float(R[:, 1].mean())}
    print(json.dumps(결, ensure_ascii=False, indent=1)); json.dump(결, open(D + "고르기결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
