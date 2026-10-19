# 판정기준69 — 학습51나 판0 그대로 · 깊이만 32 단계(33 갈래 · 32 = 통째) · 정답 층32.npy · 껍질 층 입력 = 16 단계 × 2 · 10-17
# 판정기준51 (나) — 여섯 방향 깊이 층 모델 · 방향마다 [선 그림 · 채운 윤곽 · 껍질 층 · 앞 판 층 · 방향 원핫 6] → 층 18 갈래(0 ~ 16 · 17 통째) · 10-15
# 10-18 판정기준78: LINE=λ 면 선 손실(재투영 — 위 · 앞 · 옆 세 방향의 기대 깊이에서 뽑은 선을 입력 선 그림과 맞춤) 을 더한다 · 없으면 예전과 같음
# 사용(venv): 학습51나.py <이름> [앞판.npy | -] [묶음 0~4 | -1] · 앞판 = (부품, 6, 128, 128) uint8 층 · 없으면 껍질 층 · 묶음 k 면 학습에서 k 를 빼고 k 를 예측
# 출력 out/설명/캐드부품/학습51나_<이름>/: 망.pt · 기록.json · 예측.npy(예측한 부품 × 6 × 128² uint8 · 껍질보다 얕게는 안 냄)
import sys, os, json, time, numpy as np
import 학습 as T
O = "G:/art2real/out/설명/캐드부품/"; 에폭 = int(os.environ.get("EPOCHS", 8)); 배치 = 32   # 10-18 판정기준81: EPOCHS · INIT=<이름> 이어 배우기
from 묶음51 import 묶음   # 조립 폴더 해시(판정기준51 고침 · 감사: 부품 번호 묶음은 형제 부품이 갈렸다) · 학습51가 도 이것을 가져간다
def 선손실(lo, x, h):   # 판정기준78 — lo (B, 33, N, N) · x 입력(0 선 · 1 채운 윤곽) · h (B,) 반높이 · 실제 그림 방향만 넣는다 · 데이터.py 선 규칙의 소프트판
    import torch, torch.nn.functional as Fn
    h = h[:, None, None]; E = (torch.softmax(lo, 1) * torch.arange(33, device=lo.device).float()[None, :, None, None]).sum(1); d = -E * (2 * h / 32)
    gx = (d[:, 1:] - d[:, :-1]).abs(); gx = torch.cat([gx, gx[:, -1:] * 0], 1); gy = (d[:, :, 1:] - d[:, :, :-1]).abs(); gy = torch.cat([gy, gy[:, :, -1:] * 0], 2)
    p = torch.cat([d[:, :1], d, d[:, -1:]], 1); cx = (p[:, 2:] - 2 * p[:, 1:-1] + p[:, :-2]).abs(); p = torch.cat([d[:, :, :1], d, d[:, :, -1:]], 2); cy = (p[:, :, 2:] - 2 * p[:, :, 1:-1] + p[:, :, :-2]).abs()
    g = torch.maximum(gx, gy); 재 = torch.maximum(torch.sigmoid((g - .03) / .01), torch.sigmoid((torch.maximum(cx, cy) - .004) / .002))
    t = (h * 2 / 32 * 1.5).clamp_min(.03); 정 = torch.sigmoid((g - t) / (.3 * t))
    L = x[:, 0]; 안 = -Fn.max_pool2d(-x[:, 1:2], 3, 1, 1)[:, 0]; 근 = Fn.max_pool2d(L[:, None], 3, 1, 1)[:, 0]
    양 = (L * 안) > 0; 음 = (근 == 0) & (안 > 0); 재 = Fn.max_pool2d(재[:, None], 3, 1, 1)[:, 0]
    return -(재[양] + 1e-4).log().mean().nan_to_num(0) - (1 - 정[음] + 1e-4).log().mean().nan_to_num(0)
if __name__ == "__main__":
    import torch, torch.nn as nn, torch.nn.functional as Fn
    교차쓰기 = os.environ.get("CROSS") == "1"   # 판정기준86
    숨쓰기 = os.environ.get("HIDDEN") == "1"; 폭 = int(os.environ.get("WIDTH", 1))   # 판정기준90 폭 배수   # 판정기준89 그 방향 뷰의 숨은선 1 채널(숨은입력89.npy)
    이름 = sys.argv[1]; 앞 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None; 묶 = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    D = O + "학습69_%s/" % 이름; os.makedirs(D, exist_ok=True); torch.manual_seed(31); dev = "cuda"
    입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); ok = z["ok"]; 층 = np.load(O + "층32.npy", mmap_mode="r"); 시 = np.load(O + "데이터.npz")["시험"]
    앞판 = np.load(앞, mmap_mode="r") if 앞 else None
    부 = np.arange(len(ok)); 찬 = np.load(O + "데이터51.npz")["정답"].any(1); tr = 부[~시 & ok & 찬]; 예부 = 부[시]   # 10-15 감사: 정답 칸이 빈 학습 부품 171 개(얇은 판)는 「다 비워라」를 가르쳐서 뺀다 · 예측(시험)은 그대로
    if 묶 >= 0: 예부 = tr[np.array([묶음(i) == 묶 for i in tr])]; tr = tr[np.array([묶음(i) != 묶 for i in tr])]
    if os.environ.get("QUICK"): tr, 예부, 에폭 = tr[:64], 예부[:8], 1   # 연기 시험(망 · 입출력만)
    if os.environ.get("OVERFIT"): tr = tr[:int(os.environ["OVERFIT"])]; 예부 = tr   # 10-19 외우기 시험: 적은 부품을 오래 배워 그 부품을 맞히나(구조 검사)
    print("학습 부품", len(tr), "예측 부품", len(예부), flush=True)
    class 모(nn.Module):
        def __init__(s):
            super().__init__(); s.u = T.U만들기(10 + 64 * 교차쓰기 + 숨쓰기, 폭)(); s.u.o = nn.Conv2d(32 * 폭, 33, 1)
        def forward(s, x):
            u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
            c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
    선λ = float(os.environ.get("LINE", 0)); 반 = z["반"]; 진 = torch.tensor([0, 2, 4], device=dev)   # 위 · 앞 · 옆 = 실제 그림이 있는 방향(아래 · 뒤 · 반옆은 같은 그림의 거울)
    def 선손실_(lo, x, idx, 방):   # 학습 묶음 → 실제 그림 방향만 골라 선손실
        k = torch.isin(torch.tensor(방, device=dev), 진)
        if not k.any(): return lo.sum() * 0
        return 선손실(lo[k], x[k], torch.tensor(반[idx, 방], device=dev).float()[k])
    숨89 = np.load(O + "숨은입력89.npy", mmap_mode="r") if 숨쓰기 else None
    if 교차쓰기:
        import 교차86 as X86; _d = np.load(O + "데이터.npz")["X"]; _e = np.load(O + "데이터_앞옆.npz"); 뷰86 = X86.준비(_d, _e["F"], _e["S"], dev); del _d, _e
    m = 모().to(dev); os.environ.get("INIT") and m.load_state_dict(torch.load(O + "학습69_%s/망.pt" % os.environ["INIT"])); opt = torch.optim.Adam(m.parameters(), 1e-3); 눈 = torch.eye(6, device=dev); 칸값 = torch.arange(33, device=dev).float()
    def 입력(idx, 방):   # idx 부품 · 방 방향 → (B, 10, 128, 128)
        a = torch.tensor(np.stack([입[i, k] for i, k in zip(idx, 방)]), device=dev).float(); 껍 = torch.where(a[:, 2] == 17, 32., a[:, 2] * 2)   # 16 단계 껍질 → 32 단계 아래 한계
        o = 눈[torch.tensor(방, device=dev)][:, :, None, None].expand(-1, -1, 128, 128)
        x = torch.cat([a[:, :1], a[:, 1:2], 껍[:, None] / 32, 껍[:, None] / 32, o], 1)
        if 교차쓰기: x = torch.cat([x, X86.교차(뷰86, np.asarray(idx), torch.tensor(방, device=dev), torch.tensor(반[np.asarray(idx), np.asarray(방)], device=dev))], 1)   # 판정기준86 다른 두 뷰 선 × 깊이 칸
        if 숨쓰기: x = torch.cat([x, torch.tensor(np.stack([숨89[i, k] for i, k in zip(idx, 방)]), device=dev).float()[:, None]], 1)
        return x, 껍.long()
    def 예측(부품):
        m.eval(); out = np.zeros((len(부품), 6, 128, 128), np.uint8)
        with torch.no_grad():
            쌍 = [(n, i, k) for n, i in enumerate(부품) for k in range(6)]
            for s in range(0, len(쌍), 64):
                c = 쌍[s:s + 64]; x, 껍 = 입력([i for _, i, _ in c], [k for _, _, k in c]); y = torch.maximum(m(x).argmax(1), 껍).cpu().numpy()
                for (n, _, k), yy in zip(c, y): out[n, k] = yy
        m.train(); return out
    if os.environ.get("TT"):   # 10-19 판정기준90 ① 채점만: 학습 부품 300 · 시험 부품 300 깊이 화소(정답 < 32 · 채운 윤곽 안) 층 맞음
        m.load_state_dict(torch.load(D + "망.pt")); r = {}
        for 꼴, 부품 in (("학습", tr[:300]), ("시험", 부[시][:300])):
            P = 예측(부품); 정 = np.array(층[부품]); 안 = (np.array(입[부품])[:, :, 1] > 0) & (정 < 32); r[꼴] = round(float((P == 정)[안].mean()), 4)
        print("층 맞음", r, flush=True); json.dump(r, open(D + "층맞음.json", "w", encoding="utf-8"), ensure_ascii=False); sys.exit()
    기록 = []; t0 = time.time(); 쌍 =np.array([(i, k) for i in tr for k in range(6)]); 시작 = 0
    if os.path.exists(D + "진행.pt"):   # 10-19 세션이 끊겨 5/8 에폭을 잃음 → 에폭마다 저장 · 있으면 이어서
        ck = torch.load(D + "진행.pt"); m.load_state_dict(ck["망"]); opt.load_state_dict(ck["opt"]); 시작 = ck["에폭"]; 기록 = ck["기록"]; print("이어서", 시작, "에폭부터", flush=True)
    걸음수 = 에폭 * -(-len(쌍) // 배치); 줄임 = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 걸음수, 1e-5) if os.environ.get("LRDECAY") else None   # 판정기준93 D1
    tb = None; 걸음 = 시작 * -(-len(쌍) // 배치)
    if os.environ.get("TB"):   # 판정기준93 TensorBoard 진단 — 손실 둘 · lr · 블록별 기울기 크기 · 갱신/무게 비 · 거리 칸별 층 맞음 · 히스토그램
        from torch.utils.tensorboard import SummaryWriter; import 거리93; tb = SummaryWriter(O + "tb93/" + 이름); 블록 = ["e1", "e2", "e3", "e4", "u3", "d3", "u2", "d2", "u1", "d1", "o"]
        def 진단(ep):
            P = 예측(예부[:64]); s = np.zeros((5, 2))
            for n, i in enumerate(예부[:64]):
                for k in range(6): s += np.array(거리93.칸(입[i, k], 층[i, k].astype(int), P[n, k].astype(int)))
            tb.add_scalars("층맞음/거리칸", {"%d-%d" % c: a / max(b, 1) for c, (a, b) in zip(거리93.칸들, s)}, ep); tb.add_scalar("층맞음/전체(껍질 어긋남 뺌)", s[:, 0].sum() / s[:, 1].sum(), ep)
            if ep % 25 == 0:
                for nm, p in m.named_parameters():
                    tb.add_histogram("무게/" + nm, p, ep); p.grad is not None and tb.add_histogram("기울기/" + nm, p.grad, ep)
            return s[:, 0].sum() / s[:, 1].sum()
    for ep in range(시작, 에폭):
        perm = np.random.default_rng(ep).permutation(len(쌍)); 합 = 0.0
        for s in range(0, len(perm), 배치):
            c = 쌍[perm[s:s + 배치]]; x, _ = 입력(c[:, 0], c[:, 1]); y = torch.tensor(np.stack([층[i, k] for i, k in c]), device=dev).long(); lo = m(x)
            기대 = (torch.softmax(lo, 1) * 칸값[None, :, None, None]).sum(1)   # 기대 층 — 가까운 층으로 틀리면 덜 벌함
            ce = Fn.cross_entropy(lo, y); l1 = (기대 - y.float()).abs().mean(); loss = ce + .1 * l1
            if 선λ: loss = loss + 선λ * 선손실_(lo, x, c[:, 0], c[:, 1])
            opt.zero_grad(); loss.backward()
            재기 = tb is not None and 걸음 % 10 == 0
            if 재기:
                전 = {b: torch.cat([p.detach().flatten() for p in getattr(m.u, b).parameters()]).clone() for b in 블록}
                for b in 블록: tb.add_scalar("기울기크기/" + b, torch.cat([p.grad.flatten() for p in getattr(m.u, b).parameters()]).norm().item(), 걸음)
            opt.step(); 줄임 and 줄임.step(); 합 += loss.item() * len(c)
            if 재기:
                for b in 블록: w = torch.cat([p.detach().flatten() for p in getattr(m.u, b).parameters()]); tb.add_scalar("갱신비/" + b, ((w - 전[b]).norm() / w.norm()).item(), 걸음)
                tb.add_scalars("손실", {"CE": ce.item(), "L1x0.1": .1 * l1.item()}, 걸음); tb.add_scalar("lr", opt.param_groups[0]["lr"], 걸음)
            걸음 += 1
        if tb is not None and ((ep + 1) % 10 == 0 or ep == 0): print("에폭 %d 진단 층 맞음 %.3f" % (ep + 1, 진단(ep + 1)), flush=True)
        기록.append({"에폭": ep + 1, "손실": 합 / len(perm), "초": time.time() - t0}); print("에폭 %d · 손실 %.4f · %.0f 초" % (ep + 1, 합 / len(perm), time.time() - t0), flush=True); torch.save({"망": m.state_dict(), "opt": opt.state_dict(), "에폭": ep + 1, "기록": 기록}, D + "진행.pt"); json.dump(기록, open(D + "기록.json", "w"))
    tb and tb.close(); torch.save(m.state_dict(), D + "망.pt"); P = 예측(예부); np.save(D + "예측.npy", P); np.save(D + "예측부품.npy", 예부)
    정 = np.array(층[예부]); print("예측 층 맞음 %.3f · 통째 맞음 IoU %.3f" % ((P == 정).mean(), ((P == 32) & (정 == 32)).sum() / max(((P == 32) | (정 == 32)).sum(), 1)), flush=True)
