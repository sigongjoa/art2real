# 1 단계 진단(학습 없이 판결 바꾸지 않음) — 처음부터 직사각형으로 쏠렸나 · 원기둥 후보가 뽑혔나 · 뽑히면 점수가 낮았나 · 10-13
# venv python 진단_원기둥.py → out/설명/구멍/학습2/진단_원기둥.json
import json, numpy as np
from multiprocessing import Pool
import 캐드점수2 as K, 학습2 as T
O = "G:/art2real/out/설명/구멍/학습2/"
if __name__ == "__main__":
    import torch
    torch.manual_seed(27); m = T.망만들기()(); opt = torch.optim.Adam(m.parameters(), 1e-3)
    with Pool(6) as pool:
        Ptr, Xtr, Mtr = T.묶음(pool, 600, 27)
        X = torch.tensor(Xtr)
        with torch.no_grad(): p0 = torch.softmax(m(X)[0], -1)[:, 1]
        기록 = {"처음_원기둥확률_평균": float(p0.mean()), "처음_원기둥확률_최소최대": [float(p0.min()), float(p0.max())], "처음_원기둥으로_고른_비율(argmax)": float((p0 > .5).float().mean()), "걸음": []}
        for st in range(50):
            idx = np.random.default_rng(st).choice(len(Ptr), 16, replace=False); bl, b, cl, cv = m(X[idx])
            dB = torch.distributions.Categorical(logits=bl[:, None].expand(-1, 8, -1)); db = torch.distributions.Normal(b[:, None].expand(-1, 8, -1), torch.exp(m.로그폭b))
            dC = torch.distributions.Categorical(logits=cl[:, None].expand(-1, 8, -1, -1)); dc = torch.distributions.Normal(cv[:, None].expand(-1, 8, -1, -1), torch.exp(m.로그폭칸))
            sB, sb, sC, sc = dB.sample(), db.sample(), dC.sample(), dc.sample()
            R = np.array(pool.map(K.점수, [(T.프로그램(sB[i, k], sb[i, k], sC[i, k], sc[i, k]), Mtr[idx[i]]) for i in range(16) for k in range(8)])).reshape(16, 8)
            원표 = np.array([Ptr[i]["바탕"] == 1 for i in idx]); 뽑원 = sB.numpy() == 1
            def 평균(mask): return float(R[mask].mean()) if mask.any() else None
            기록["걸음"].append({"걸음": st, "원기둥_뽑힌비율": float(뽑원.mean()), "원기둥문제_원기둥후보점수": 평균(원표[:, None] & 뽑원), "원기둥문제_상자후보점수": 평균(원표[:, None] & ~뽑원)})
            이득 = torch.tensor((R - R.mean(1, keepdims=True)) / (R.std(1, keepdims=True) + 1e-4), dtype=torch.float32)
            쓰임 = (sC > 0).float(); bmask = torch.stack([(sB == 0).float(), (sB == 0).float(), (sB == 1).float()], -1)
            lp = dB.log_prob(sB) + (db.log_prob(sb) * bmask).sum(-1) + dC.log_prob(sC).sum(-1) + (dc.log_prob(sc).sum(-1) * 쓰임).sum(-1)
            loss = -(이득 * lp).mean(); opt.zero_grad(); loss.backward(); opt.step()
    json.dump(기록, open(O + "진단_원기둥.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    g = 기록["걸음"]; f = lambda k, a, b: np.nanmean([x[k] if x[k] is not None else np.nan for x in g[a:b]])
    print("처음 원기둥 확률 평균 %.2f (최소 %.2f 최대 %.2f) · argmax 로 원기둥 고른 비율 %.2f" % (기록["처음_원기둥확률_평균"], *기록["처음_원기둥확률_최소최대"], 기록["처음_원기둥으로_고른_비율(argmax)"]))
    for a, b in ((0, 10), (20, 30), (40, 50)): print("걸음 %d~%d · 원기둥 뽑힌 비율 %.2f · 원기둥 문제에서 원기둥 후보 %.3f · 상자 후보 %.3f" % (a, b - 1, f("원기둥_뽑힌비율", a, b), f("원기둥문제_원기둥후보점수", a, b), f("원기둥문제_상자후보점수", a, b)))
