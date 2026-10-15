# 판정기준54 (나) — 학습51나 와 같은 망 · 입력 10 · 8 에폭 · 씨앗 31 · 바뀌는 건 손실뿐 · 10-15
# 손실 = 층 교차 엔트로피 + 0.1 × 기대 층 L1(지금 것) + λ₁ × Chamfer(여섯 방향 기대 깊이 → 3D 점 구름 ↔ 정답 표면 점 2,048) + λ₂ × (1 − 부드러운 칸 깎기 48³ 와 정답 칸의 부피 IoU)
# 표본 = 부품 단위(배치 = 부품 5 × 6 방향 = 30 장 · 판0 32 장과 비슷) · 학습 중 CAD 안 지음 · 예측 · 출력 파일 꼴은 학습51나 와 같다
# 사용(venv): 학습54나.py <이름> [앞판.npy | -] [묶음 0~4 | -1] · 환경변수 L1 · L2 로 λ 바꿈 · QUICK=1 연기 시험(부품 64 · 1 에폭)
# 출력 out/설명/캐드부품/학습54나_<이름>/: 망.pt · 기록.json(+ 세 손실 항) · 예측.npy · 예측부품.npy
import sys, os, json, time, numpy as np, torch
import 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; 에폭 = 8; 부배치 = 5; 표본 = 4096
λ1 = float(os.environ.get("L1", 9.0)); λ2 = float(os.environ.get("L2", 0.6)); τ = 1.1 / 48 * float(os.environ.get("TAU", .0625))   # λ 근거: 판0 학습 끝 망으로 학습 부품 200 개에서 층 0.207 · Chamfer 0.023 · 1−IoU 0.327 → 세 항이 ≈ 0.2 로 같게(처음 망은 3.65 · 0.097 · 1.00) · τ = 48³ 칸 폭 × 1/16 — 칸 폭 1 이면 여섯 방향 곱이 틀 겉 칸까지 깎아 numpy 칸깎기와 IoU 0.68 · 1/8 은 20 개 최소 0.958 · 1/16 최소 0.997(검사54나 ①)
from 묶음51 import 묶음
_G = (np.arange(48) + .5) / 48 * 1.1 - .55; _P = np.stack(np.meshgrid(_G, _G, _G, indexing="ij"), -1).reshape(-1, 3)   # 변환51.층에서칸 · 여섯방향.칸깎기 와 같은 격자
_R = np.stack([S6.R(*v) for v in S6.방향.values()])   # (6, 3, 3) · 세계 = R @ 지역
_표 = {}
def 칸표(dev):   # 방향마다 한 번: 48³ 칸 가운데 → 화소 번호(y·128 + x) · 지역 w  — 여섯방향.칸깎기 그대로(np.round · clip)
    if dev not in _표:
        I, W = [], []
        for r in _R:
            L = _P @ r; x = np.clip(np.round((L[:, 0] + .55) / S6.칸 - .5).astype(int), 0, 127); y = np.clip(np.round((-L[:, 1] + .55) / S6.칸 - .5).astype(int), 0, 127)
            I.append(y * 128 + x); W.append(L[:, 2])
        _표[dev] = (torch.tensor(np.stack(I), device=dev), torch.tensor(np.stack(W), device=dev).float(), torch.tensor(S6.g, device=dev).float(), torch.tensor(_R, device=dev).float())
    return _표[dev]
def 부드러운칸(p, 반, 틀):   # p (B, 6, 18, 128, 128) 층 확률 · 반 (B, 6) · 틀 (B, 48³) 0/1 → 「남음」 확률 (B, 48³)
    I, Lw, _, _ = 칸표(p.device); h = 반[:, :, None]; 단 = 2 * h / S6.층수; k = torch.arange(17, device=p.device).float()
    q = p.flatten(3); 깊 = (q[:, :, :17] * k[None, None, :, None]).sum(2) * 단 + q[:, :, 17] * (2 * h + .1)   # 기대 깎을 깊이 · 통째 = 2h + .1(여섯방향.층)
    깊 = torch.gather(깊, 2, I[None].expand(len(p), -1, -1))   # (B, 6, 48³)
    return torch.sigmoid((h - 깊 - Lw[None]) / τ).prod(1) * 틀
def 부드러운IoU(q, t): return ((q * t).sum(1) / (q + t - q * t).sum(1).clamp_min(1e-6))   # 부품마다
def 점구름(p, 반, 윤곽, gen=None):   # → [(점 (n, 3), 무게 (n,))] 부품마다 · 윤곽 (B, 6, 128, 128) bool · 층 0~16 깊이 = 층 × 단 · 무게 = 1 − p17
    _, _, g, R = 칸표(p.device); k = torch.arange(17, device=p.device).float(); out = []
    v, u = -g[:, None].expand(128, 128), g[None, :].expand(128, 128)   # [y, x]
    for b in range(len(p)):
        h = 반[b][:, None, None]; 무 = 1 - p[b, :, 17]; d = (p[b, :, :17] * k[None, :, None, None]).sum(1) / 무.clamp_min(1e-4) * (2 * h / S6.층수)
        L = torch.stack([u.expand(6, -1, -1), v.expand(6, -1, -1), h - d], -1)   # (6, 128, 128, 3) 지역
        X = torch.einsum("nij,nyxj->nyxi", R, L)[윤곽[b]]; w = 무[윤곽[b]]
        if len(X) > 표본: s = torch.randperm(len(X), device=p.device, generator=gen)[:표본]; X, w = X[s], w[s]
        out.append((X, w))
    return out
def 챔퍼(X, w, Q):   # 양방향 평균 최근접 거리 · 예측 → 정답은 무게 평균 · 정답 → 예측은 무게 낮은 점에 (1 − w) 만큼 거리를 더해 「없는 점」으로
    if len(X) == 0: return Q.new_tensor(1.0)
    d = torch.cdist(X[None], Q[None])[0]; a = (w * d.min(1).values).sum() / w.sum().clamp_min(1e-6); b = (d + (1 - w)[:, None]).min(0).values.mean(); return (a + b) / 2
def 표면점(부품, 목록):   # 표면점54.npz 가 있으면 그것 · 없으면 정답 메시에서 즉석 2,048(표면점54.py 와 같은 셈 · 연기 시험 · 검사용)
    f = O + "표면점54.npz"
    if os.path.exists(f): z = np.load(f); P, ok = z["P"], z["ok"]; return {int(i): P[i].astype(np.float32) for i in 부품 if ok[i]}   # npz 키는 꺼낼 때마다 통째로 읽으니 한 번만
    import trimesh, 짓기 as J; out = {}
    for i in 부품:
        try: v, fc, _ = J.정규메시(목록[i]); out[int(i)] = trimesh.sample.sample_surface(trimesh.Trimesh(v, fc, process=False), 2048, seed=54)[0].astype(np.float32)
        except Exception: pass
    return out
풀 = lambda a: np.unpackbits(a, axis=-1).astype(np.float32)   # (B, 13824) → (B, 48³) [x, y, z]
if __name__ == "__main__":
    import torch.nn as nn, torch.nn.functional as Fn
    import 학습 as T
    이름 = sys.argv[1]; 앞 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None; 묶 = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    D = O + "학습54나_%s/" % 이름; os.makedirs(D, exist_ok=True); torch.manual_seed(31); dev = "cuda"
    입 = np.load(O + "입력51.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); 층, ok, 반all, 틀all, 정all = z["층"], z["ok"], z["반"], z["틀"], z["정답"]; 시 = np.load(O + "데이터.npz")["시험"]
    앞판 = np.load(앞, mmap_mode="r") if 앞 else None; 목록 = json.load(open(O + "목록.json", encoding="utf-8"))
    부 = np.arange(len(ok)); 찬 = 정all.any(1); tr = 부[~시 & ok & 찬]; 예부 = 부[시]   # 정답 빈 학습 부품 뺌(학습51나 와 같다)
    if 묶 >= 0: 예부 = tr[np.array([묶음(i) == 묶 for i in tr])]; tr = tr[np.array([묶음(i) != 묶 for i in tr])]
    QUICK = bool(os.environ.get("QUICK"))
    if QUICK: tr, 예부, 에폭 = tr[:64], 예부[:8], 1
    if not QUICK and not os.path.exists(O + "표면점54.npz"): sys.exit("표면점54.npz 없음 — 표면점54.py 먼저")
    Qs = 표면점(tr, 목록); 빠 = len(tr) - len(Qs); tr = np.array([i for i in tr if int(i) in Qs])
    print("학습 부품", len(tr), "(표면점 없어 뺌 %d)" % 빠, "예측 부품", len(예부), "· λ1 %.3g λ2 %.3g τ %.4f" % (λ1, λ2, τ), flush=True)
    class 모(nn.Module):
        def __init__(s):
            super().__init__(); s.u = T.U만들기(10)(); s.u.o = nn.Conv2d(32, 18, 1)
        def forward(s, x):
            u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
            c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
    m = 모().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); 눈 = torch.eye(6, device=dev); 칸값 = torch.arange(18, device=dev).float()
    def 입력(idx, 방):   # 학습51나 그대로
        a = torch.tensor(np.stack([입[i, k] for i, k in zip(idx, 방)]), device=dev).float()
        p = torch.tensor(np.stack([앞판[i, k] for i, k in zip(idx, 방)]), device=dev).float()[:, None] if 앞판 is not None else a[:, 2:3]
        o = 눈[torch.tensor(방, device=dev)][:, :, None, None].expand(-1, -1, 128, 128)
        return torch.cat([a[:, :1], a[:, 1:2], a[:, 2:3] / 17, p / 17, o], 1), a[:, 2].long()
    def 예측(부품):   # 학습51나 그대로
        m.eval(); out = np.zeros((len(부품), 6, 128, 128), np.uint8)
        with torch.no_grad():
            쌍 = [(n, i, k) for n, i in enumerate(부품) for k in range(6)]
            for s in range(0, len(쌍), 64):
                c = 쌍[s:s + 64]; x, 껍 = 입력([i for _, i, _ in c], [k for _, _, k in c]); y = torch.maximum(m(x).argmax(1), 껍).cpu().numpy()
                for (n, _, k), yy in zip(c, y): out[n, k] = yy
        m.train(); return out
    기록 = []; t0 = time.time(); torch.cuda.reset_peak_memory_stats(); gen = torch.Generator(device=dev); gen.manual_seed(31)
    for ep in range(에폭):
        perm = np.random.default_rng(ep).permutation(len(tr)); 합 = np.zeros(4); 장 = 0; te = time.time()
        for s in range(0, len(perm), 부배치):
            c = tr[perm[s:s + 부배치]]; B = len(c); idx = np.repeat(c, 6); 방 = np.tile(np.arange(6), B)
            x, _ = 입력(idx, 방); y = torch.tensor(층[c].reshape(-1, 128, 128), device=dev).long(); lo = m(x)
            기대 = (torch.softmax(lo, 1) * 칸값[None, :, None, None]).sum(1)
            층손 = Fn.cross_entropy(lo, y) + .1 * (기대 - y.float()).abs().mean()
            p = torch.softmax(lo.float(), 1).view(B, 6, 18, 128, 128); h = torch.tensor(반all[c], device=dev)
            칸 = 부드러운칸(p, h, torch.tensor(풀(틀all[c]), device=dev)); 부피 = 1 - 부드러운IoU(칸, torch.tensor(풀(정all[c]), device=dev)).mean()
            윤 = x[:, 1].view(B, 6, 128, 128) > .5; 챔 = torch.stack([챔퍼(X, w, torch.tensor(Qs[int(i)], device=dev)) for (X, w), i in zip(점구름(p, h, 윤, gen), c)]).mean()
            loss = 층손 + λ1 * 챔 + λ2 * 부피; opt.zero_grad(); loss.backward(); opt.step()
            합 += np.array([loss.item(), 층손.item(), 챔.item(), 부피.item()]) * B; 장 += B
            if QUICK and s == 0: print("첫 배치 · 층 %.4f · Chamfer %.4f · 1−IoU %.4f" % tuple(합[1:] / B), flush=True)
        a = 합 / 장; 기록.append({"에폭": ep + 1, "손실": a[0], "층손실": a[1], "Chamfer": a[2], "1-IoU": a[3], "초": time.time() - t0})
        print("에폭 %d · 손실 %.4f (층 %.4f · Chamfer %.4f → ×λ1 %.4f · 1−IoU %.4f → ×λ2 %.4f) · %.0f 초 · 부품당 %.3f 초 · GPU 최고 %.2f GB" % (
            ep + 1, a[0], a[1], a[2], λ1 * a[2], a[3], λ2 * a[3], time.time() - t0, (time.time() - te) / 장, torch.cuda.max_memory_allocated() / 2 ** 30), flush=True)
        json.dump(기록, open(D + "기록.json", "w"))
    torch.save(m.state_dict(), D + "망.pt"); P = 예측(예부); np.save(D + "예측.npy", P); np.save(D + "예측부품.npy", 예부)
    정 = 층[예부]; print("예측 층 맞음 %.3f · 통째 맞음 IoU %.3f" % ((P == 정).mean(), ((P == 17) & (정 == 17)).sum() / max(((P == 17) | (정 == 17)).sum(), 1)), flush=True)
