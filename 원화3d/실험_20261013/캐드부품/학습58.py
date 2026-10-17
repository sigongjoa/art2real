# 판정기준58 — 세 장을 함께 보는 3D 모델: 위 · 앞 · 옆 선 그림(+ 채운 윤곽) → 같은 2D 인코더 → 정사영이라 특징을 보는 축으로 그대로 들어 올려(48³) 세 장을 더함 → 3D U-Net → 48³ 칸 점유 · 10-17
# 진단59: 데이터 두 배마다 +0.032 → +0.012 · 방향마다 따로 보는 2D 깊이 층 모델(판0)은 0.696 근처에서 멈춤 · 깎기 천장 0.803 — 이 모델은 깊이 층 · 깎기를 거치지 않고 칸을 바로 낸다(속 빈 곳 · 언더컷도 표현 가능)
# 축: 지역틀.껍질 과 같음 — 위 X[::-1].T → [x, y] · 앞 F[::-1].T → [x, z] · 옆 S[::-1].T → [y, z] (확인: 들어 올린 실루엣 대 저장된 틀 IoU 중앙 0.955)
# 사용(venv · ART_MEM_GB=12): 학습58.py <이름> · QUICK=1 연기 · HARD=1 어려운 학습 부품만 · INIT=<판> 이어 배우기 · LR · 출력 out/설명/캐드부품/학습58_<이름>/: 망.pt · 기록.json · 결과.json · 부피IoU.npy(712 × [모델, 틀])
import sys, os, json, time, numpy as np
O = "G:/art2real/out/설명/캐드부품/"; 에폭 = int(os.environ.get("EPOCHS", 8)); 배치 = 8
if __name__ == "__main__":
    import torch, torch.nn as nn, torch.nn.functional as Fn
    sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); import 입력51 as I
    이름 = sys.argv[1]; D = O + "학습58_%s/" % 이름; os.makedirs(D, exist_ok=True); torch.manual_seed(31); dev = "cuda"
    d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; z = np.load(O + "데이터51.npz"); 정b, 틀b, ok = z["정답"], z["틀"], z["ok"]
    풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48)
    부 = np.arange(len(ok)); tr = 부[~시 & ok & 정b.any(1)]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]   # 학습 부품은 판0 과 같게 · 시험은 712
    if os.environ.get("HARD"): tr = tr[np.load(O + "난이도57.npy")[tr, 0] < .5]   # 10-17 사용자 「어려운 것만 모아서」 — 학습 부품 중 틀 IoU < 0.5(시험 어려운 217 과 같은 선)
    if os.environ.get("QUICK"): tr, 예부, 에폭 = tr[:64], 예부[:16], 1
    print("학습 부품", len(tr), "시험", len(예부), flush=True)
    _채 = {}
    def 그림(i):   # (3, 2, 128, 128) [선, 채운 윤곽] × 위 · 앞 · 옆
        if i not in _채: _채[i] = np.stack([np.stack([v[i], I._채움(v[i])]) for v in (X, F, S)]).astype(np.uint8)
        return _채[i]
    def 블(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU())
    def 블3(i, o): return nn.Sequential(nn.Conv3d(i, o, 3, 1, 1), nn.BatchNorm3d(o), nn.ReLU(), nn.Conv3d(o, o, 3, 1, 1), nn.BatchNorm3d(o), nn.ReLU())
    C = 24
    class 모(nn.Module):
        def __init__(s):
            super().__init__(); s.e = nn.Sequential(블(2 + 3, 32), nn.MaxPool2d(2), 블(32, 48), 블(48, C))   # 128 → 64 → (48 으로 줄임) · 뷰 원핫 3
            s.d1, s.d2, s.d3 = 블3(C + 1, 32), 블3(32, 64), 블3(64, 128); s.p = nn.MaxPool3d(2)
            s.u2, s.c2 = nn.ConvTranspose3d(128, 64, 2, 2), 블3(128, 64); s.u1, s.c1 = nn.ConvTranspose3d(64, 32, 2, 2), 블3(64, 32); s.o = nn.Conv3d(32, 1, 1); nn.init.constant_(s.o.bias, 2.)   # 처음엔 틀(들어 올린 덩어리 전부 참)에서 출발 — 연기 1 에폭에서 다 비운 칸(0.0)을 냄
        def forward(s, x, 껍):   # x (B, 3, 2, 128, 128) · 껍 (B, 48, 48, 48) 들어 올린 실루엣 교집합
            B = len(x); 원 = torch.eye(3, device=x.device)[None, :, :, None, None].expand(B, -1, -1, 128, 128)
            f = s.e(torch.cat([x, 원], 2).flatten(0, 1).float()); f = Fn.interpolate(f, (48, 48), mode="area").view(B, 3, C, 48, 48)
            t = lambda m: m.flip(-2).transpose(-1, -2)   # [행 = −a, 열 = b] → [b, a] (넘파이 m[::-1].T 와 같음)
            v = t(f[:, 0])[:, :, :, :, None] + t(f[:, 1])[:, :, :, None, :] + t(f[:, 2])[:, :, None, :, :]   # 위 [x,y] · 앞 [x,z] · 옆 [y,z] → (B, C, 48, 48, 48)
            a = s.d1(torch.cat([v, 껍[:, None]], 1)); b = s.d2(s.p(a)); c = s.d3(s.p(b))
            b2 = s.c2(torch.cat([s.u2(c), b], 1)); a2 = s.c1(torch.cat([s.u1(b2), a], 1)); return s.o(a2)[:, 0]
    def 껍질(g):   # g (B, 3, 2, 128, 128) → (B, 48, 48, 48) — 채운 윤곽을 들어 올린 교집합
        m = Fn.interpolate(g[:, :, 1].float(), (48, 48), mode="area") > .5; t = lambda q: q.flip(-2).transpose(-1, -2)
        return t(m[:, 0])[:, :, :, None] & t(m[:, 1])[:, :, None, :] & t(m[:, 2])[:, None, :, :]
    def 묶음(idx):
        g = torch.tensor(np.stack([그림(int(i)) for i in idx]), device=dev); 껍 = 껍질(g); y = torch.tensor(np.stack([풀(정b[i]) for i in idx]), device=dev).float(); return g, 껍, y
    m = 모().to(dev); os.environ.get("INIT") and m.load_state_dict(torch.load(O + "학습58_%s/망.pt" % os.environ["INIT"], map_location=dev)); opt = torch.optim.Adam(m.parameters(), float(os.environ.get("LR", 1e-3)))   # INIT = 이어 배울 판 이름; 척 = torch.amp.GradScaler(); 기록 = []; t0 = time.time()
    print("파라미터 %.2f M" % (sum(p.numel() for p in m.parameters()) / 1e6), flush=True)
    for ep in range(에폭):
        perm = np.random.default_rng(ep).permutation(tr); 합 = 0.0; m.train()
        for s_ in range(0, len(perm), 배치):
            g, 껍, y = 묶음(perm[s_:s_ + 배치])
            with torch.autocast("cuda", dtype=torch.float16):
                lo = m(g, 껍.float()); lo = lo.masked_fill(~껍, -20.)   # 들어 올린 덩어리 밖은 비움(정답의 0.8 % 만 밖)
            p = torch.sigmoid(lo.float()); 소 = 1 - (p * y).sum((1, 2, 3)) / (p + y - p * y).sum((1, 2, 3)).clamp_min(1)
            loss = Fn.binary_cross_entropy_with_logits(lo.float(), y) + 소.mean(); opt.zero_grad(); 척.scale(loss).backward(); 척.step(opt); 척.update(); 합 += loss.item() * len(y)
        기록.append({"에폭": ep + 1, "손실": 합 / len(perm), "초": time.time() - t0}); print("에폭 %d · 손실 %.4f · %.0f 초" % (ep + 1, 합 / len(perm), time.time() - t0), flush=True); json.dump(기록, open(D + "기록.json", "w"))
    torch.save(m.state_dict(), D + "망.pt"); m.eval(); R = []
    from scipy.ndimage import label
    with torch.no_grad():
        for s_ in range(0, len(예부), 8):
            idx = 예부[s_:s_ + 8]; g, 껍, y = 묶음(idx)
            with torch.autocast("cuda", dtype=torch.float16): lo = m(g, 껍.float()).masked_fill(~껍, -20.)
            P = (lo > 0).cpu().numpy(); Y = y.bool().cpu().numpy(); T = np.stack([풀(틀b[i]).astype(bool) for i in idx])
            for p_, y_, t_ in zip(P, Y, T): R.append([(p_ & y_).sum() / max((p_ | y_).sum(), 1), (t_ & y_).sum() / max((t_ | y_).sum(), 1), label(p_, np.ones((3, 3, 3)))[1], label(y_, np.ones((3, 3, 3)))[1]])
    R = np.array(R, float); np.save(D + "부피IoU.npy", R); 판0 = np.load(O + "학습51나_판0전체/부피IoU.npy")[: len(R)]
    결과 = {"712 칸 평균(모델)": float(R[:, 0].mean()), "틀(저장된 틀 · 판0 틀 열과 같아야)": float(R[:, 1].mean()), "판0 틀 열": float(판0[:, 2].mean()), "판0 칸 열": float(판0[:, 1].mean()), "판0 CAD 열": float(판0[:, 0].mean()),
          "망침(모델 < 틀 − 0.01)": int((R[:, 0] < R[:, 1] - .01).sum()), "조각내기(정답 한 덩어리 · 모델 여럿)": int(((R[:, 3] == 1) & (R[:, 2] > 1)).sum()), "부품": len(R), "마지막 손실": 기록[-1]["손실"]}
    json.dump(결과, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
