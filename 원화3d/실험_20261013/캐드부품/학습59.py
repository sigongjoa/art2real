# 진단59 — 학습51나 판0 그대로 + 환경변수 FRAC(학습 부품 비율 · 씨앗 59 로 고름) · WIDE(망 폭 배수) · 10-16 사용자 「추론 말고 학습 스킬 돌려서 문제 확인」
# (아래는 학습51나 머리말) 판정기준51 (나) — 여섯 방향 깊이 층 모델 · 방향마다 [선 그림 · 채운 윤곽 · 껍질 층 · 앞 판 층 · 방향 원핫 6] → 층 18 갈래(0 ~ 16 · 17 통째) · 10-15
# 사용(venv): 학습51나.py <이름> [앞판.npy | -] [묶음 0~4 | -1] · 앞판 = (부품, 6, 128, 128) uint8 층 · 없으면 껍질 층 · 묶음 k 면 학습에서 k 를 빼고 k 를 예측
# 출력 out/설명/캐드부품/학습51나_<이름>/: 망.pt · 기록.json · 예측.npy(예측한 부품 × 6 × 128² uint8 · 껍질보다 얕게는 안 냄)
import sys, os, json, time, numpy as np
import 학습 as T
O = "G:/art2real/out/설명/캐드부품/"; 에폭 = 8; 배치 = 32
from 묶음51 import 묶음   # 조립 폴더 해시(판정기준51 고침 · 감사: 부품 번호 묶음은 형제 부품이 갈렸다) · 학습51가 도 이것을 가져간다
if __name__ == "__main__":
    import torch, torch.nn as nn, torch.nn.functional as Fn
    이름 = sys.argv[1]; 앞 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None; 묶 = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    D = O + "진단59_%s/" % 이름; os.makedirs(D, exist_ok=True); torch.manual_seed(31); dev = "cuda"
    입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 층, ok = z["층"], z["ok"]; 시 = np.load(O + "데이터.npz")["시험"]
    앞판 = np.load(앞, mmap_mode="r") if 앞 else None
    부 = np.arange(len(ok)); 찬 = np.load(O + "데이터51.npz")["정답"].any(1); tr = 부[~시 & ok & 찬]; 예부 = 부[시]   # 10-15 감사: 정답 칸이 빈 학습 부품 171 개(얇은 판)는 「다 비워라」를 가르쳐서 뺀다 · 예측(시험)은 그대로
    if os.environ.get("FRAC"): tr = np.sort(np.random.default_rng(59).choice(tr, int(len(tr) * float(os.environ["FRAC"])), replace=False))
    if 묶 >= 0: 예부 = tr[np.array([묶음(i) == 묶 for i in tr])]; tr = tr[np.array([묶음(i) != 묶 for i in tr])]
    if os.environ.get("QUICK"): tr, 예부, 에폭 = tr[:64], 예부[:8], 1   # 연기 시험(망 · 입출력만)
    print("학습 부품", len(tr), "예측 부품", len(예부), flush=True)
    class 모(nn.Module):
        def __init__(s):
            super().__init__(); K = int(os.environ.get("WIDE", 1)); s.u = T.U만들기(10, K)(); s.u.o = nn.Conv2d(32 * K, 18, 1)
        def forward(s, x):
            u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
            c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
    m = 모().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); 눈 = torch.eye(6, device=dev); 칸값 = torch.arange(18, device=dev).float()
    def 입력(idx, 방):   # idx 부품 · 방 방향 → (B, 10, 128, 128)
        a = torch.tensor(np.stack([입[i, k] for i, k in zip(idx, 방)]), device=dev).float()
        p = torch.tensor(np.stack([앞판[i, k] for i, k in zip(idx, 방)]), device=dev).float()[:, None] if 앞판 is not None else a[:, 2:3]
        o = 눈[torch.tensor(방, device=dev)][:, :, None, None].expand(-1, -1, 128, 128)
        return torch.cat([a[:, :1], a[:, 1:2], a[:, 2:3] / 17, p / 17, o], 1), a[:, 2].long()
    def 예측(부품):
        m.eval(); out = np.zeros((len(부품), 6, 128, 128), np.uint8)
        with torch.no_grad():
            쌍 = [(n, i, k) for n, i in enumerate(부품) for k in range(6)]
            for s in range(0, len(쌍), 64):
                c = 쌍[s:s + 64]; x, 껍 = 입력([i for _, i, _ in c], [k for _, _, k in c]); y = torch.maximum(m(x).argmax(1), 껍).cpu().numpy()
                for (n, _, k), yy in zip(c, y): out[n, k] = yy
        m.train(); return out
    기록 = []; t0 = time.time(); 쌍 = np.array([(i, k) for i in tr for k in range(6)])
    for ep in range(에폭):
        perm = np.random.default_rng(ep).permutation(len(쌍)); 합 = 0.0
        for s in range(0, len(perm), 배치):
            c = 쌍[perm[s:s + 배치]]; x, _ = 입력(c[:, 0], c[:, 1]); y = torch.tensor(np.stack([층[i, k] for i, k in c]), device=dev).long(); lo = m(x)
            기대 = (torch.softmax(lo, 1) * 칸값[None, :, None, None]).sum(1)   # 기대 층 — 가까운 층으로 틀리면 덜 벌함
            loss = Fn.cross_entropy(lo, y) + .1 * (기대 - y.float()).abs().mean(); opt.zero_grad(); loss.backward(); opt.step(); 합 += loss.item() * len(c)
        기록.append({"에폭": ep + 1, "손실": 합 / len(perm), "초": time.time() - t0}); print("에폭 %d · 손실 %.4f · %.0f 초" % (ep + 1, 합 / len(perm), time.time() - t0), flush=True); json.dump(기록, open(D + "기록.json", "w"))
    torch.save(m.state_dict(), D + "망.pt"); P = 예측(예부); np.save(D + "예측.npy", P); np.save(D + "예측부품.npy", 예부)
    정 = 층[예부]; print("예측 층 맞음 %.3f · 통째 아닌 곳 층 맞음 %.3f" % ((P == 정).mean(), (P == 정)[정 != 17].mean()), flush=True)
