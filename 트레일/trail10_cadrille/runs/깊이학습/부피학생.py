# -*- coding: utf-8 -*-
"""3D 학생 — 세 짝수 방향 그림(실루엣 · 선 · 교차 깊이)을 64³ 격자로 들어 올려 함께 본다 · 판정기준18 B · 10-12
좌표: 축 a 그림의 행 = o[0] · 열 = o[1] · 뒤집기 없음 · unit 상자 칸 중심 (좌표시험: 들어 올린 실루엣 AND 가 정답과 IoU 0.54 = 교차)
python 부피학생.py 준비   → 부피정답.npy(학습 부품 점유 64³ 압축) · 부피정답_검증2.npy
python 부피학생.py 학습 [에폭=8]   → 부피학생.pt · 부피학생.log
python 부피학생.py 평가   → 부피학생.json (검증 모델 IoU 대 교차 · 재심 세트 진짜 홈 바닥 오차 대 2D 학생)"""
import os, sys, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub"), os.path.join(R, "조각0")]
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; n = 64; dev = "cuda"
class 부피망(nn.Module):
    def __init__(s, c=16):
        super().__init__(); s.c = c
        s.e = nn.Sequential(nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, stride=2, padding=1), nn.ReLU(), nn.Conv2d(32, c, 3, padding=1))   # 128 → 64
        s.v = nn.Parameter(torch.zeros(3, c, 1, 1))   # 방향 표시
        b = lambda i, o: nn.Sequential(nn.Conv3d(i, o, 3, padding=1), nn.BatchNorm3d(o), nn.ReLU())
        s.d1, s.d2, s.d3 = b(3 * c + 1, 24), b(24, 48), b(48, 64); s.u2, s.u1 = b(64 + 48, 48), b(48 + 24, 24); s.o = nn.Conv3d(24, 1, 1)
    def forward(s, x):   # x (B, 3 방향, 3 채널, 128, 128) → 점유 로짓 (B, 64, 64, 64)
        B = x.shape[0]; f = s.e(x.flatten(0, 1)).view(B, 3, s.c, n, n) + s.v
        V = torch.cat([f[:, 0][:, :, None, :, :].expand(-1, -1, n, -1, -1), f[:, 1][:, :, :, None, :].expand(-1, -1, -1, n, -1), f[:, 2][:, :, :, :, None].expand(-1, -1, -1, -1, n)], 1)
        sil = F.max_pool2d(x[:, :, 0], 2) > .5; hull = (sil[:, 0][:, None] & sil[:, 1][:, :, None] & sil[:, 2][:, :, :, None]).float()[:, None]   # 교차 = 들어 올린 실루엣 AND
        a = s.d1(torch.cat([V, hull], 1)); b_ = s.d2(F.max_pool3d(a, 2)); c_ = s.d3(F.max_pool3d(b_, 2))
        u = s.u2(torch.cat([F.interpolate(c_, scale_factor=2), b_], 1)); u = s.u1(torch.cat([F.interpolate(u, scale_factor=2), a], 1))
        return s.o(u)[:, 0] + 8 * (hull[:, 0] - 1)   # 교차 밖은 거의 0 (그림자 밖엔 아무것도 없다)
def 입력(X): return np.stack([X[:3, 2 * a] for a in range(3)]).astype(np.float32)   # (3 방향, 3 채널, 128, 128)
def 점유(p):
    import trimesh
    from s0 import unit
    from 모양자 import _occ
    g = (np.indices((n, n, n)).reshape(3, -1).T + .5) / n; return np.packbits(_occ(unit(trimesh.load(RR + p, force="mesh")), g))
def 깊이지도(O, k):   # 점유 (64³ bool) → k 방향 깊이(0~1 · 128 칸 규약과 같은 「낮은 쪽 (i+.5)/n · 높은 쪽 1−(i+.5)/n」) · 빈 곳 1
    a = k // 2; v = np.moveaxis(O, a, -1); 있 = v.any(-1); lo = v.argmax(-1); hi = n - 1 - v[..., ::-1].argmax(-1)
    d = (lo + .5) / n if k % 2 == 0 else 1 - (hi + .5) / n; return np.where(있, d, 1.0)
if __name__ == "__main__":
    목록 = json.load(open(os.path.join(R, "실물학습", "목록.json"), encoding="utf-8")); 키 = sorted(목록)
    if sys.argv[1] == "준비":
        from multiprocessing import Pool
        with Pool(4) as po: Y = po.map(점유, [목록[k] for k in 키], chunksize=16)
        np.save(os.path.join(H, "부피정답.npy"), np.stack(Y)); 부2 = np.load(os.path.join(H, "검증2.npz"))["부품"]
        with Pool(4) as po: Y2 = po.map(점유, [str(p) for p in 부2])
        np.save(os.path.join(H, "부피정답_검증2.npy"), np.stack(Y2)); print("ok", len(Y), len(Y2))
    elif sys.argv[1] == "학습":
        E = int(sys.argv[2]) if len(sys.argv) > 2 else 8; XA = np.load(os.path.join(H, "학습.npy"), mmap_mode="r"); YA = np.load(os.path.join(H, "부피정답.npy"))
        뺄 = set(json.load(open(os.path.join(H, "검증목록2.json"), encoding="utf-8"))["학습빼기"]); 모 = sorted({목록[k].split("/")[0] for k in 키}); rng = np.random.default_rng(0); rng.shuffle(모); 검모 = set(모[:len(모) // 10])
        ti = [i for i in range(len(키)) if i not in 뺄 and 목록[키[i]].split("/")[0] not in 검모]; vi = [i for i in range(len(키)) if i not in 뺄 and 목록[키[i]].split("/")[0] in 검모]
        torch.manual_seed(0); m = 부피망().to(dev); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-4); B = 4; nb = len(ti) // B
        sch = torch.optim.lr_scheduler.OneCycleLR(opt, 1e-3, total_steps=E * nb, pct_start=.05); sc = torch.amp.GradScaler(); log = open(os.path.join(H, "부피학생.log"), "w", encoding="utf-8"); t0 = time.time(); best = 0
        def 배(ix):
            x = torch.tensor(np.stack([입력(np.asarray(XA[i]).astype(np.float32)) for i in ix]), device=dev); y = torch.tensor(np.stack([np.unpackbits(YA[i])[:n ** 3].reshape(n, n, n) for i in ix]).astype(np.float32), device=dev); return x, y
        def 재기(ix):
            m.eval(); iu, iu0 = [], []
            with torch.no_grad():
                for j in range(0, len(ix), 8):
                    x, y = 배(ix[j:j + 8])
                    with torch.autocast("cuda", dtype=torch.float16): p = m(x) > 0
                    h = (F.max_pool2d(x[:, :, 0], 2) > .5); h = h[:, 0][:, None] & h[:, 1][:, :, None] & h[:, 2][:, :, :, None]; y = y > .5
                    iu += ((p & y).sum((1, 2, 3)) / (p | y).sum((1, 2, 3)).clamp(min=1)).tolist(); iu0 += ((h & y).sum((1, 2, 3)) / (h | y).sum((1, 2, 3)).clamp(min=1)).tolist()
            m.train(); return float(np.mean(iu)), float(np.mean(iu0))
        for ep in range(E):
            rng.shuffle(ti); tl = []
            for j in range(nb):
                x, y = 배(ti[j * B:(j + 1) * B])
                if rng.random() < .5: pass   # ponytail: 뒤집기 증강 없음 — 방향 · 축이 얽혀 있어 같이 뒤집어야 함
                with torch.autocast("cuda", dtype=torch.float16): l = F.binary_cross_entropy_with_logits(m(x), y)
                opt.zero_grad(); sc.scale(l).backward(); sc.step(opt); sc.update(); sch.step(); tl.append(l.item())
            vi_iou, vh = 재기(vi); msg = "에폭 %d 손실 %.4f 검증 IoU %.3f (교차 %.3f) %.0f 초" % (ep, np.mean(tl), vi_iou, vh, time.time() - t0); print(msg, flush=True); log.write(msg + "\n"); log.flush()
            if vi_iou > best: best = vi_iou; torch.save(m.state_dict(), os.path.join(H, "부피학생.pt"))
        print("ok 최고 검증 IoU", best)
    elif sys.argv[1] == "평가":   # 재심 세트 진짜 홈 바닥 오차 — 3D 학생 대 2D 학생(모델T_검증뺌2)
        from scipy import ndimage
        sys.path.insert(0, H); from 학습 import 망   # 조각0/학습.py 가 이름을 가림
        m = 부피망().to(dev); m.load_state_dict(torch.load(os.path.join(H, "부피학생.pt"))); m.eval(); d2 = 망().to(dev); d2.load_state_dict(torch.load(os.path.join(H, "모델T_검증뺌2.pt"))); d2.eval()
        X2 = np.load(os.path.join(H, "검증2.npz"))["X"].astype(np.float32); Y2 = np.load(os.path.join(H, "부피정답_검증2.npy")); e3, e2, iu, iu0 = [], [], [], []
        for i in range(len(X2)):
            X = X2[i]
            with torch.no_grad():
                with torch.autocast("cuda", dtype=torch.float16): O = (m(torch.tensor(입력(X)[None], device=dev)) > 0)[0].cpu().numpy()
                Z = d2(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).to(dev))[:, 0].cpu().numpy()
            y = np.unpackbits(Y2[i])[:n ** 3].reshape(n, n, n).astype(bool); s0 = [np.asarray(X[0][2 * a] > .5).reshape(n, 2, n, 2).max((1, 3)) for a in range(3)]; h = s0[0][None] & s0[1][:, None] & s0[2][:, :, None]
            iu.append((O & y).sum() / max((O | y).sum(), 1)); iu0.append((h & y).sum() / max((h | y).sum(), 1))
            for k in (0, 2, 4):   # 짝수 방향 · 진짜 홈 = 실루엣 안 정답 깊이 − 교차 > 2 칸 덩이(≥ 60)
                lab, nl = ndimage.label((X[0][k] > .5) & (X[3][k] - X[2][k] > 2 / 128)); D3 = np.kron(깊이지도(O, k), np.ones((2, 2)))
                for j in range(1, nl + 1):
                    mm = lab == j
                    if mm.sum() < 60: continue
                    g = np.median(X[3][k][mm]); e3.append(abs(np.median(D3[mm]) - g) * 128); e2.append(abs(np.median(Z[k][mm]) - g) * 128)
        r = {"재심 세트 점유 IoU 3D 학생": round(float(np.mean(iu)), 3), "재심 세트 점유 IoU 교차": round(float(np.mean(iu0)), 3), "진짜 홈 수": len(e3),
             "홈 바닥 오차 중앙(128 칸) 3D 학생": round(float(np.median(e3)), 2), "홈 바닥 오차 중앙 2D 학생": round(float(np.median(e2)), 2)}
        r["기준"] = bool(r["재심 세트 점유 IoU 3D 학생"] >= r["재심 세트 점유 IoU 교차"] + .10 and r["홈 바닥 오차 중앙(128 칸) 3D 학생"] <= 3.0)
        json.dump(r, open(os.path.join(H, "부피학생.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", r)

    elif sys.argv[1] == "메시":   # 판정기준19 F — 재심 세트 40 · 점유 확률 → 128³ 보간 · 가우시안 → 마칭 큐브 → 가장 큰 덩이 · unit 상자
        import trimesh
        from scipy import ndimage
        from skimage.measure import marching_cubes
        m = 부피망().to(dev); m.load_state_dict(torch.load(os.path.join(H, "부피학생.pt"))); m.eval(); X2 = np.load(os.path.join(H, "검증2.npz"))["X"].astype(np.float32)
        O = os.path.join(R, "기능0", "B_F_검증2"); os.makedirs(O, exist_ok=True)
        for i in range(len(X2)):
            with torch.no_grad():
                with torch.autocast("cuda", dtype=torch.float16): p_ = torch.sigmoid(m(torch.tensor(입력(X2[i])[None], device=dev)).float())
            P = ndimage.gaussian_filter(F.interpolate(p_[:, None], scale_factor=2, mode="trilinear")[0, 0].cpu().numpy(), 1.0); P = np.pad(P, 1)
            v, f, _, _ = marching_cubes(P, .5); M = trimesh.Trimesh((v - 1 + .5) / (2 * n), f); M = max(M.split(only_watertight=False), key=lambda q: len(q.faces))
            M.apply_translation([-.5] * 3); M.apply_scale(2.0); M.export(os.path.join(O, "%02d.stl" % i)); print(i, len(M.faces), flush=True)
        print("ok")
