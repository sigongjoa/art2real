# 진단58 — 판0 이 덜 배웠나(학습 부품도 낮음) · 외웠나(학습 부품만 높음): 학습 부품 712 개(씨앗 58 · 학습에 쓴 부품에서)에 판0 망으로 예측 → 시험과 같은 채점(지킴짓기 CAD · 48³ IoU) · 10-16 사용자 「모델 성능 업데이트 · 지금 방식으로는 한계」
# 사용(venv · ART_MEM_GB=12): 진단58.py 예측 → 진단58.py 평가 <시작> <끝> → 진단58.py 판정
import sys, os, json, collections, numpy as np
O = "G:/art2real/out/설명/캐드부품/"; D = O + "진단58_판0학습부품/"; os.makedirs(D + "평가/", exist_ok=True)
def 고르기():
    z = np.load(O + "데이터51.npz"); 시 = np.load(O + "데이터.npz")["시험"]; tr = np.nonzero(~시 & z["ok"] & z["정답"].any(1))[0]   # 학습51나 판0 이 쓴 학습 부품 그대로
    return np.sort(np.random.default_rng(58).choice(tr, 712, replace=False))
if __name__ == "__main__":
    부 = 고르기()
    if sys.argv[1] == "예측":
        import torch, torch.nn as nn, 학습 as T
        class 모(nn.Module):   # 학습51나 의 망 그대로
            def __init__(s):
                super().__init__(); s.u = T.U만들기(10)(); s.u.o = nn.Conv2d(32, 18, 1)
            def forward(s, x):
                u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
                c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
        dev = "cuda"; m = 모().to(dev); m.load_state_dict(torch.load(O + "학습51나_판0전체/망.pt", map_location=dev)); m.eval(); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 눈 = torch.eye(6, device=dev)
        out = np.zeros((len(부), 6, 128, 128), np.uint8); 쌍 = [(n, i, k) for n, i in enumerate(부) for k in range(6)]
        with torch.no_grad():
            for s in range(0, len(쌍), 64):
                c = 쌍[s:s + 64]; a = torch.tensor(np.stack([입[i, k] for _, i, k in c]), device=dev).float(); o = 눈[torch.tensor([k for _, _, k in c], device=dev)][:, :, None, None].expand(-1, -1, 128, 128)
                x = torch.cat([a[:, :1], a[:, 1:2], a[:, 2:3] / 17, a[:, 2:3] / 17, o], 1); y = torch.maximum(m(x).argmax(1), a[:, 2].long()).cpu().numpy()
                for (n, _, k), yy in zip(c, y): out[n, k] = yy
        np.save(D + "예측.npy", out); np.save(D + "예측부품.npy", 부); 정 = np.load(O + "데이터51.npz")["층"][부]; print("층 맞음 %.3f · 통째 아닌 곳 %.3f" % ((out == 정).mean(), (out == 정)[정 != 17].mean())); sys.exit()
    if sys.argv[1] == "평가":
        import 평가51나 as E; from multiprocessing import Pool
        d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; L = json.load(open(O + "목록.json", encoding="utf-8")); 반 = np.load(O + "데이터51.npz")["반"]; P = np.load(D + "예측.npy", mmap_mode="r")
        ks = list(range(int(sys.argv[2]), min(int(sys.argv[3]), len(부)))); pool = Pool(4, maxtasksperchild=10)
        일 = [pool.apply_async(E.하나, ((L[부[k]], (X[부[k]], F[부[k]], S[부[k]]), np.array(P[k]), 반[부[k]]),)) for k in ks]; r = []
        for k, a in zip(ks, 일):
            try: r.append(a.get(timeout=200))
            except Exception as ex: r.append({"실패": "강제 시간초과 " + type(ex).__name__, "초": 200.0})
        pool.terminate(); json.dump({"자리": ks, "값": r}, open(D + "평가/%04d.json" % ks[0], "w", encoding="utf-8"), ensure_ascii=False); print(ks[0], "~", ks[-1], "CAD %.3f" % np.mean([x.get("CAD", 0) for x in r]), flush=True); sys.exit()
    if sys.argv[1] == "판정":
        v = {}; [v.update(dict(zip(q["자리"], q["값"]))) for q in (json.load(open(D + "평가/" + f, encoding="utf-8")) for f in os.listdir(D + "평가/"))]
        R = [v[int(k)] if int(k) in v else v[str(k)] for k in range(len(부))] if len(v) >= len(부) else sys.exit("아직 %d" % len(v))
        R0 = [x if not x.get("실패") else {"틀": 0, "CAD": 0} for x in R]; a = np.array([x["CAD"] for x in R0]); 틀 = np.array([x["틀"] for x in R0])
        시험 = np.load(O + "학습51나_판0전체/부피IoU.npy"); 결과 = {"학습 부품 712 CAD 평균": float(a.mean()), "학습 부품 틀": float(틀.mean()), "학습 부품 망침": int((a < 틀 - .01).sum()), "실패": dict(collections.Counter(x.get("실패") for x in R if x.get("실패"))),
              "시험 712 CAD": float(시험[:, 0].mean()), "시험 틀": float(시험[:, 2].mean()), "차(학습 − 시험)": float(a.mean() - 시험[:, 0].mean()),
              "읽기(돌리기 전 정함)": "차 < 0.03 이면 덜 배움(모델 힘 · 구조 문제 → A · B) · 차 ≥ 0.08 이면 외움(일반화 문제 → 사전학습 · 데이터) · 그 사이는 둘 다"}
        json.dump(결과, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
