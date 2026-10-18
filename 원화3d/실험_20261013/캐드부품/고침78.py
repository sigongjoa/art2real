# 판정기준78 고침 — 정답 없이 그림 한 장에서 미세 조정: 만든 깊이에서 뽑은 선을 그 그림 선에 맞춤(선손실) + 처음 예측 닻(KL) · 10-18
# 사용(venv · ART_MEM_GB=8): 고침78.py 시험 [망=판0] → 재투영78/고침_시험_<망>.json (CAD 40 개 전 · 후)
#                          고침78.py 실제 <그림.png> [망=판0] → 실제입력/<이름>_고침_<망>/ 칸.npy · 겹침 · 점수
import sys, os, json, copy, numpy as np
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; N = 128; 걸음 = int(os.environ.get("GO", 60)); 학률 = float(os.environ.get("LR", 1e-4)); 진 = [0, 2, 4]
def 망읽기(이름):
    import torch, torch.nn as nn, 학습 as T
    class 모(nn.Module):   # 학습69 와 같은 망
        def __init__(s): super().__init__(); s.u = T.U만들기(10)(); s.u.o = nn.Conv2d(32, 33, 1)
        def forward(s, x):
            u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
            c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
    m = 모().cuda(); m.load_state_dict(torch.load(O + "학습69_%s/망.pt" % 이름)); m.eval(); return m
def 입력(a):   # 입력51 한 부품 (6, 3, N, N) → 망 입력 · 껍질 층
    import torch; a = torch.tensor(np.asarray(a), device="cuda").float(); 껍 = torch.where(a[:, 2] == 17, 32., a[:, 2] * 2)
    return torch.cat([a[:, :1], a[:, 1:2], 껍[:, None] / 32, 껍[:, None] / 32, torch.eye(6, device="cuda")[:, :, None, None].expand(-1, -1, N, N)], 1), 껍.long()
def 고치기(m0, a, 반, n=걸음):   # → 층 (6, N, N) · n = 0 이면 고치기 전
    import torch, torch.nn.functional as Fn, 학습69 as L9
    x, 껍 = 입력(a); h = torch.tensor(np.asarray(반, np.float32), device="cuda")
    with torch.no_grad(): lo0 = m0(x); p0 = torch.log_softmax(lo0, 1)
    if n:
        m = copy.deepcopy(m0); m.eval(); opt = torch.optim.Adam(m.parameters(), 학률)
        for _ in range(n):
            lo = m(x); loss = L9.선손실(lo[진], x[진], h[진]) + Fn.kl_div(torch.log_softmax(lo, 1), p0, log_target=True, reduction="none").sum(1).mean()
            opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad(): lo0 = m(x)
    return torch.maximum(lo0.argmax(1), 껍).cpu().numpy()
if __name__ == "__main__":
    import 평가69 as E, 재투영78 as R, 입력51 as I
    if sys.argv[1] == "시험":
        망 = sys.argv[2] if len(sys.argv) > 2 else "판0"; m0 = 망읽기(망)
        시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]; 거 = np.load(O + "거름62.npy")
        ks = np.random.default_rng(78).choice(np.nonzero(거)[0], 40, replace=False); L = json.load(open(O + "목록.json", encoding="utf-8"))
        입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]
        X = np.load(O + "데이터.npz")["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 행 = []
        for k in ks:
            i = 예부[k]; r = {"k": int(k)}
            for 이름, n in (("전", 0), ("후", 걸음)):
                층 = 고치기(m0, 입[i], 반[i], n); 값, 칸b = E.하나((k, L[i], 층, 반[i], 틀[i], 정[i])); v = np.unpackbits(칸b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
                rp = [R.점수(a_, g > 0, I._채움(g))[2] for a_, g in zip(R.그리기(*R.칸메시(v)), (X[i], F[i], S[i]))] if v.any() else [0.] * 3
                r[이름] = {"F": 값[0], "울": 값[2:], "재투영F": float(np.mean(rp))}
            행.append(r); print(k, "F %.3f → %.3f · 재투영 %.3f → %.3f" % (r["전"]["F"], r["후"]["F"], r["전"]["재투영F"], r["후"]["재투영F"]), flush=True)
        A = lambda w, f: float(np.nanmean([q[w][f] for q in 행])); 울 = lambda w: float(sum(q[w]["울"][0] for q in 행) / max(sum(q[w]["울"][1] for q in 행), 1))
        요 = {"F@1 전 · 후": [A("전", "F"), A("후", "F")], "울퉁 전 · 후": [울("전"), 울("후")], "재투영 F 전 · 후": [A("전", "재투영F"), A("후", "재투영F")], "F 0.05 넘게 떨어진 부품": int(sum(q["후"]["F"] < q["전"]["F"] - .05 for q in 행))}
        요["판정"] = {"F ≥ 전 + 0.005": 요["F@1 전 · 후"][1] >= 요["F@1 전 · 후"][0] + .005, "울퉁 ≤ 전": 요["울퉁 전 · 후"][1] <= 요["울퉁 전 · 후"][0], "재투영 F ≥ 전 + 0.02": 요["재투영 F 전 · 후"][1] >= 요["재투영 F 전 · 후"][0] + .02, "빨간 선 ≤ 5": 요["F 0.05 넘게 떨어진 부품"] <= 5}
        json.dump({"요약": 요, "부품": 행}, open(O + "재투영78/고침_시험_%s_%d.json" % (망, 걸음), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1))
