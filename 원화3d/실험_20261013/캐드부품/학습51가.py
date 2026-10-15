# 판정기준51 (가) — 3D 칸 모델 · 선 그림 셋(위 · 앞 · 옆 · 채운 윤곽 포함)을 2D 로 줄여 각 축으로 늘려 포갬 + 틀 칸 + 앞 판 칸 → 작은 3D U-Net → 칸마다 재료 · 10-15
# 사용(venv): 학습51가.py <이름> [앞판.npy | -] [묶음 0~4 | -1] · 앞판 = (부품, 48, 48, 48) uint8/bool · 없으면 틀 · 묶음 k 면 학습에서 k 를 빼고 k 를 예측 · QUICK=1 연기 시험
# 출력 out/설명/캐드부품/학습51가_<이름>/: 망.pt · 기록.json · 예측.npy(예측한 부품 × 13824 packbits · 48³ [x, y, z] · 틀 밖 0) · 예측부품.npy
# 좌표: 칸 [x, y, z] = 짓기.점유_캐드 · 위 그림 [행 = N−1−y, 열 = x] · 앞 [행 = N−1−z, 열 = x] · 옆 [행 = N−1−z, 열 = y] — 지역틀.껍질 과 같다 · 검사는 좌표검사51가.py
import sys, os, json, time, numpy as np
from 학습51나 import 묶음
O = "G:/art2real/out/설명/캐드부품/"; 에폭 = int(os.environ.get("A_EPOCH", 8)); 배치 = int(os.environ.get("A_BATCH", 8)); 폭 = int(os.environ.get("A_WIDTH", 1)); n = 48   # 10-15 판정기준51b: 학습량(에폭 · 폭 · 배치)을 환경변수로
def 풀기(a): return np.unpackbits(a, axis=-1).reshape(*a.shape[:-1], n, n, n).astype(bool)   # packbits 13824 → 48³
def 그림들(X, F, S, idx):   # 부품 → (B, 3, 2, 128, 128) [선 · 채운 윤곽] uint8
    import 입력51 as I
    return np.stack([[[g[i], I._채움(g[i])] for g in (X, F, S)] for i in idx]).astype(np.uint8)
def 늘림(위, 앞, 옆):   # (B, C, 48, 48) 그림 틀 [행, 열] 셋 → (B, 3C, 48, 48, 48) [x, y, z]
    import torch
    위 = 위.flip(2).transpose(2, 3)[..., None]     # [N−1−y, x] → [x, y] → z 로 늘림
    앞 = 앞.flip(2).transpose(2, 3)[:, :, :, None]  # [N−1−z, x] → [x, z] → y 로 늘림
    옆 = 옆.flip(2).transpose(2, 3)[:, :, None]     # [N−1−z, y] → [y, z] → x 로 늘림
    s = (위.shape[0], 위.shape[1], n, n, n); return torch.cat([위.expand(s), 앞.expand(s), 옆.expand(s)], 1)
def 모만들기(c=8, w=1):   # c = 그림마다 채널 · w = 채널 배수
    import torch, torch.nn as nn, torch.nn.functional as Fn
    b3 = lambda i, o: nn.Sequential(nn.Conv3d(i, o, 3, 1, 1), nn.BatchNorm3d(o), nn.ReLU(), nn.Conv3d(o, o, 3, 1, 1), nn.BatchNorm3d(o), nn.ReLU())
    class 모(nn.Module):
        def __init__(s):
            super().__init__()   # 2D 인코더는 셋 따로(위 · 앞 · 옆은 보는 것이 다르다)
            s.en = nn.ModuleList([nn.Sequential(nn.Conv2d(2, 16 * w, 3, 1, 1), nn.BatchNorm2d(16 * w), nn.ReLU(), nn.Conv2d(16 * w, 32 * w, 3, 2, 1), nn.BatchNorm2d(32 * w), nn.ReLU(), nn.Conv2d(32 * w, 32 * w, 3, 1, 1), nn.ReLU()) for _ in range(3)])
            cw = c * w; s.to2 = nn.ModuleList([nn.Conv2d(32 * w, cw, 1) for _ in range(3)])
            s.e1, s.e2, s.e3 = b3(3 * cw + 2, 24 * w), b3(24 * w, 48 * w), b3(48 * w, 96 * w); s.p = nn.MaxPool3d(2)   # 48 → 24 → 12
            s.u2, s.d2 = nn.ConvTranspose3d(96 * w, 48 * w, 2, 2), b3(96 * w, 48 * w); s.u1, s.d1 = nn.ConvTranspose3d(48 * w, 24 * w, 2, 2), b3(48 * w, 24 * w); s.o = nn.Conv3d(24 * w, 1, 1)
        def forward(s, 그, 틀, 앞):   # 그 (B, 3, 2, 128, 128) · 틀 · 앞 (B, 48, 48, 48) → 로짓 (B, 48, 48, 48)
            f = [s.to2[k](Fn.interpolate(s.en[k](그[:, k]), size=(n, n), mode="bilinear", align_corners=False)) for k in range(3)]   # 64 → 48 · 범위가 같아 칸 가운데가 맞는다
            x = torch.cat([늘림(*f), 틀[:, None], 앞[:, None]], 1); a = s.e1(x); b_ = s.e2(s.p(a)); c_ = s.e3(s.p(b_))
            b2 = s.d2(torch.cat([s.u2(c_), b_], 1)); a2 = s.d1(torch.cat([s.u1(b2), a], 1)); return s.o(a2)[:, 0]
    return 모
if __name__ == "__main__":
    import torch, torch.nn.functional as Fn
    이름 = sys.argv[1]; 앞 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None; 묶 = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    D = O + "학습51가_%s/" % 이름; os.makedirs(D, exist_ok=True); torch.manual_seed(31); dev = "cuda"
    z = np.load(O + "데이터51.npz"); 틀p, 정p, ok = z["틀"], z["정답"], z["ok"]; d = np.load(O + "데이터.npz"); 시, X = d["시험"], d["X"]; del d; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; del e
    앞판 = np.load(앞, mmap_mode="r") if 앞 else None
    부 = np.arange(len(ok)); 찬 = np.load(O + "데이터51.npz")["정답"].any(1); tr = 부[~시 & ok & 찬]; 예부 = 부[시]   # 10-15 감사: 정답 칸이 빈 학습 부품 171 개(얇은 판)는 「다 비워라」를 가르쳐서 뺀다 · 예측(시험)은 그대로
    if 묶 >= 0: 예부 = tr[np.array([묶음(i) == 묶 for i in tr])]; tr = tr[np.array([묶음(i) != 묶 for i in tr])]
    전체 = len(tr)
    if os.environ.get("QUICK"): tr, 예부, 에폭 = tr[:64], 예부[:8], 1   # 연기 시험(망 · 입출력만)
    print("학습 부품", len(tr), "예측 부품", len(예부), flush=True); t0 = time.time()
    쓸 = np.union1d(tr, 예부)
    G = dict(zip(쓸, 그림들(X, F, S, 쓸))); del X, F, S; print("채운 윤곽 %.0f 초" % (time.time() - t0), flush=True)   # ponytail: 부품마다 3 × 2 × 128² = 98 KB · 1 만이면 1 GB 램
    m = 모만들기(w=폭)().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); 줄 = torch.optim.lr_scheduler.CosineAnnealingLR(opt, max(에폭, 1))
    범 = json.load(open(O + "범위46.json")); 시험712 = np.nonzero(시)[0][범]; 곡선 = []   # 판정기준51b: 2 에폭마다 712 개 칸 IoU(학습 곡선)
    def 점수712():
        P7 = 예측(시험712); 합 = []   # 64 개씩 풀어 잰다(10-15 한 번에 풀다 메모리 상한에 걸려 학습이 죽음)
        for s in range(0, len(시험712), 64):
            a, b = 풀기(P7[s:s + 64]), 풀기(정p[시험712[s:s + 64]]); 합 += list((a & b).sum((1, 2, 3)) / np.maximum((a | b).sum((1, 2, 3)), 1))
        return float(np.mean(합))
    def 입력(idx):
        g = torch.tensor(np.stack([G[i] for i in idx]), device=dev).float(); t = torch.tensor(풀기(틀p[idx]), device=dev).float()
        p = torch.tensor(np.stack([np.asarray(앞판[i]) for i in idx]) > 0, device=dev).float() if 앞판 is not None else t
        return g, t, p
    def 예측(부품):
        m.eval(); out = np.zeros((len(부품), n ** 3 // 8), np.uint8)
        with torch.no_grad():
            for s in range(0, len(부품), 8):
                c = 부품[s:s + 8]; g, t, p = 입력(c); y = ((torch.sigmoid(m(g, t, p)) * t) > .5).cpu().numpy(); out[s:s + len(c)] = np.packbits(y.reshape(len(c), -1), axis=-1)
        m.train(); return out
    기록 = []; t0 = time.time()
    for ep in range(에폭):
        perm = np.random.default_rng(ep).permutation(tr); 합 = 0.0
        for s in range(0, len(perm), 배치):
            c = np.sort(perm[s:s + 배치]); g, t, p = 입력(c); y = torch.tensor(풀기(정p[c]), device=dev).float(); lo = m(g, t, p)
            bce = (Fn.binary_cross_entropy_with_logits(lo, y, reduction="none") * t).sum() / t.sum().clamp(min=1)   # 틀 안 칸만 — 틀 밖은 출력이 0 으로 묶임
            q = torch.sigmoid(lo) * t; iou = ((q * y).sum((1, 2, 3)) / (q + y - q * y).sum((1, 2, 3)).clamp(min=1)).mean()
            loss = bce + (1 - iou); opt.zero_grad(); loss.backward(); opt.step(); 합 += loss.item() * len(c)
            if ep == 0 and s == 배치: t1 = time.time()   # 첫 두 배치(준비 · cudnn 고르기)는 예상에서 뺀다
        if ep == 0: print("1 에폭 예상(학습 부품 %d) %.0f 초" % (전체, (time.time() - t1) / (len(perm) - 2 * 배치) * 전체), flush=True)
        기록.append({"에폭": ep + 1, "손실": 합 / len(perm), "초": time.time() - t0}); print("에폭 %d · 손실 %.4f · %.0f 초 · GPU 최고 %.2f GB" % (ep + 1, 합 / len(perm), time.time() - t0, torch.cuda.max_memory_allocated() / 2 ** 30), flush=True); json.dump(기록, open(D + "기록.json", "w"))
        줄.step()
        if 묶 < 0 and not os.environ.get("QUICK") and ((ep + 1) % 2 == 0 or ep + 1 == 에폭): 곡선.append({"에폭": ep + 1, "712": 점수712()}); print("  712 개 칸 IoU %.4f" % 곡선[-1]["712"], flush=True); json.dump(곡선, open(D + "곡선.json", "w"))
    torch.save(m.state_dict(), D + "망.pt"); P = 예측(예부); np.save(D + "예측.npy", P); np.save(D + "예측부품.npy", 예부)
    pp, 정, 틀 = 풀기(P), 풀기(정p[예부]), 풀기(틀p[예부]); r = lambda a, b: ((a & b).sum((1, 2, 3)) / np.maximum((a | b).sum((1, 2, 3)), 1)).mean()
    print("예측 부피 IoU %.3f · 틀만 %.3f" % (r(pp, 정), r(틀, 정)), flush=True)
