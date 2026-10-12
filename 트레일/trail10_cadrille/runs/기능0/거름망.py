# -*- coding: utf-8 -*-
"""학습 거름망 — 학생 깊이가 내놓은 「홈」 후보 중 진짜 홈만 고른다 · 판정기준16 · 10-12
python 거름망.py 후보   → 거름망_후보.npz (학습 부품 · 검증목록2 모델 뺌 · 특징 · 라벨 · 모델 이름)
python 거름망.py 학습   → 거름망.pt · 거름망.json(문턱 · 검증 정밀도 / 재현율)
짓기에서: from 거름망 import 후보들, 고르기"""
import os, sys, json, numpy as np, torch, torch.nn as nn
from scipy import ndimage
import cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); 깊 = os.path.join(R, "깊이학습"); sys.path.insert(0, 깊)
칸 = 1 / 128
def 후보들(X, Z):   # X (4, 6, 128, 128) = 실루엣 · 선 · 교차 깊이 · (정답 깊이) · Z (6, 128, 128) 학생 깊이 → [(쪽, 덩이 마스크, 특징)]
    out = []
    for k in range(6):
        S = X[0][k] > .5; L = cv2.dilate((X[1][k] > .5).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0; Dh = X[2][k]; z = Z[k]
        lab, n = ndimage.label(S & (z - Dh > 3 * 칸)); Se = S & ~ndimage.binary_erosion(S)
        for j in range(1, n + 1):
            m = lab == j; a = int(m.sum())
            if a < 60: continue
            e = m & ~ndimage.binary_erosion(m); dz = (z - Dh)[m] / 칸; zz = z[m] / 칸; P = max(int(e.sum()), 1)
            f = [np.log(a), a / max(S.sum(), 1), dz.mean(), np.median(dz), np.subtract(*np.percentile(dz, [75, 25])), np.subtract(*np.percentile(zz, [75, 25])),
                 (L & e).sum() / P, 4 * np.pi * a / P ** 2, (ndimage.binary_dilation(Se) & e).sum() / P]
            out.append((k, m, np.array(f, np.float32)))
    return out
def 틀(m):   # 덩이 둘레 네모(25 % 여유) — (y0, y1, x0, x1, 덧댐)
    ys, xs = np.nonzero(m); cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2; h = max(ys.max() - ys.min(), xs.max() - xs.min(), 8) * .625 + 2
    return int(cy - h), int(cy + h), int(cx - h), int(cx + h), int(h) + 2
def 자르기(c, b, n=48):
    y0, y1, x0, x1, P = b; return cv2.resize(np.pad(c, P)[y0 + P:y1 + P, x0 + P:x1 + P].astype(np.float32), (n, n), interpolation=cv2.INTER_AREA)
def 조각(X, Z, k, m, n=48):   # 덩이 둘레 네모를 48 칸으로 — 실루엣 · 선 · 교차 깊이 · 학생 깊이 · 덩이 · 학생 − 교차
    b = 틀(m); ch = [X[0][k], X[1][k], X[2][k], Z[k], m.astype(np.float32), (Z[k] - X[2][k]) * 10]
    return np.stack([자르기(c, b, n) for c in ch]).astype(np.float16)
def 정답조각(X, Z, k, m, n=48):   # 판정기준17: 진짜 파인 곳 마스크(조각 안) · 바닥 보정(칸)
    T = (X[0][k] > .5) & (X[3][k] - X[2][k] > 2 * 칸); b = 틀(m); t = 자르기(T.astype(np.float32), b, n) > .5
    lab, nn_ = ndimage.label(T & ndimage.binary_dilation(m, iterations=3)); 겹 = np.isin(lab, np.unique(lab[m & (lab > 0)])) if nn_ else T & m
    o = (np.median(X[3][k][겹]) - np.median(Z[k][m])) / 칸 if 겹.any() else 0.0
    return t.astype(np.uint8), np.float32(o)
def 되돌림(p48, b, 모양=(128, 128)):   # 48 칸 예측 → 128 칸 격자
    y0, y1, x0, x1, P = b; out = np.zeros((모양[0] + 2 * P, 모양[1] + 2 * P), np.float32); out[y0 + P:y1 + P, x0 + P:x1 + P] = cv2.resize(p48.astype(np.float32), (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    return out[P:P + 모양[0], P:P + 모양[1]]
class 망3(nn.Module):   # 작은 U-Net — 마스크 48×48 + 바닥 보정
    def __init__(s):
        super().__init__(); c = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU())
        s.d1, s.d2, s.d3 = c(6, 16), c(16, 32), c(32, 64); s.u2, s.u1 = c(64 + 32, 32), c(32 + 16, 16); s.m = nn.Conv2d(16, 1, 1); s.o = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(s, x):
        a = s.d1(x); b = s.d2(nn.functional.max_pool2d(a, 2)); c_ = s.d3(nn.functional.max_pool2d(b, 2))
        u = s.u2(torch.cat([nn.functional.interpolate(c_, scale_factor=2), b], 1)); u = s.u1(torch.cat([nn.functional.interpolate(u, scale_factor=2), a], 1))
        return s.m(u)[:, 0], s.o(c_)[:, 0]
def 다듬기(X, Z, hs):   # [(쪽, 덩이, …)] → [(쪽, 새 마스크 128, 바닥)] · 거름망3.pt
    if not hs: return []
    m3 = 망3(); m3.load_state_dict(torch.load(os.path.join(H, "거름망3.pt"))); m3.eval(); out = []
    with torch.no_grad():
        ml, ol = m3(torch.tensor(np.stack([조각(X, Z, k, m_) for k, m_, *_ in hs])).float())
    for (k, m_, *_), p, o in zip(hs, torch.sigmoid(ml).numpy(), ol.numpy()):
        M = (되돌림(p, 틀(m_)) > .5) & (X[0][k] > .5); lab, n = ndimage.label(M)
        if n: M = lab == (1 + int(np.argmax(ndimage.sum(M, lab, range(1, n + 1)))))
        if M.sum() >= 30: out.append((k, M, float(np.median(Z[k][m_]) + o * 칸)))
    return out
class 망2(nn.Module):   # 작은 CNN + 손 특징 9
    def __init__(s):
        super().__init__(); b = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
        s.c = nn.Sequential(b(6, 16), b(16, 32), b(32, 64), nn.AdaptiveAvgPool2d(1), nn.Flatten()); s.h = nn.Sequential(nn.Linear(64 + 9, 64), nn.ReLU(), nn.Dropout(.2), nn.Linear(64, 1))
    def forward(s, x, f): return s.h(torch.cat([s.c(x), f], 1))[:, 0]
def 라벨(X, Z, k, m):   # 정답 깊이로 진짜 평평한 홈인가 — 학생이 짚은 바닥 깊이가 정답 바닥과 맞는가까지
    D, Dh = X[3][k], X[2][k]; d = D[m]
    if os.environ.get("LABEL") == "1":   # 1 판: 바닥 깊이까지 맞아야 진짜
        return float(((d - Dh[m]) > 2 * 칸).mean() >= .8 and abs(np.median(d) - np.median(Z[k][m])) <= 2.5 * 칸 and np.subtract(*np.percentile(d, [75, 25])) <= 3 * 칸)
    return float(((d - Dh[m]) > 2 * 칸).mean() >= .8 and np.subtract(*np.percentile(d, [75, 25])) <= 3 * 칸)   # 2 판(10-12): 「여기 평평한 홈이 있나」만 — 깊이는 선 그림에 거의 안 보임
class 망(nn.Module):
    def __init__(s, n=9): super().__init__(); s.f = nn.Sequential(nn.Linear(n, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(s, x): return s.f(x)[:, 0]
def 고르기2(cs, fs):   # 조각 · 특징 → 통과 여부(거름망2.json 문턱)
    if not fs: return []
    J = json.load(open(os.path.join(H, "거름망2.json"), encoding="utf-8")); m = 망2(); m.load_state_dict(torch.load(os.path.join(H, "거름망2.pt"))); m.eval()
    f = (torch.tensor(np.stack(fs)) - torch.tensor(J["평균"])) / torch.tensor(J["표준"])
    with torch.no_grad(): p = torch.sigmoid(m(torch.tensor(np.stack(cs)).float(), f.float())).numpy()
    return list(p >= J["문턱"])
def 고르기(fs):   # 특징 목록 → 통과 여부(거름망.json 문턱)
    if not fs: return []
    J = json.load(open(os.path.join(H, "거름망.json"), encoding="utf-8")); m = 망(); m.load_state_dict(torch.load(os.path.join(H, "거름망.pt"))); m.eval()
    x = (torch.tensor(np.stack(fs)) - torch.tensor(J["평균"])) / torch.tensor(J["표준"])
    with torch.no_grad(): p = torch.sigmoid(m(x)).numpy()
    return list(p >= J["문턱"])
if __name__ == "__main__":
    if sys.argv[1] == "후보":
        from 학습 import 망 as 깊이망
        dm = 깊이망().cuda(); dm.load_state_dict(torch.load(os.path.join(깊, "모델T_검증뺌2.pt"))); dm.eval()
        목록 = json.load(open(os.path.join(R, "실물학습", "목록.json"), encoding="utf-8")); 키 = sorted(목록); 뺄 = set(json.load(open(os.path.join(깊, "검증목록2.json"), encoding="utf-8"))["학습빼기"])
        XA = np.load(os.path.join(깊, "학습.npy"), mmap_mode="r"); F_, Y_, G_, C_, T_, O_ = [], [], [], [], [], []
        for i in range(len(키)):
            if i in 뺄: continue
            X = np.asarray(XA[i]).astype(np.float32)
            with torch.no_grad(): Z = dm(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
            for k, m, f in 후보들(X, Z): F_.append(f); Y_.append(라벨(X, Z, k, m)); G_.append(목록[키[i]].split("/")[0]); C_.append(조각(X, Z, k, m)); t_, o_ = 정답조각(X, Z, k, m); T_.append(t_); O_.append(o_)
            if i % 300 == 0: print(i, len(F_), round(float(np.mean(Y_)) if Y_ else 0, 3), flush=True)
        np.savez(os.path.join(H, "거름망_후보.npz"), F=np.stack(F_), Y=np.array(Y_, np.float32), G=np.array(G_), C=np.stack(C_), T=np.stack(T_), O=np.array(O_, np.float32)); print("ok 후보", len(F_), "진짜 비율", float(np.mean(Y_)))
    elif sys.argv[1] == "학습":
        d = np.load(os.path.join(H, "거름망_후보.npz")); F_, Y_, G_ = d["F"], d["Y"], d["G"]; 모 = sorted(set(G_)); rng = np.random.default_rng(0); rng.shuffle(모); 검모 = set(모[:len(모) // 10])
        v = np.array([g in 검모 for g in G_]); mu, sd = F_[~v].mean(0), F_[~v].std(0) + 1e-6; x = torch.tensor((F_ - mu) / sd); y = torch.tensor(Y_)
        torch.manual_seed(0); m = 망(); opt = torch.optim.Adam(m.parameters(), 1e-3, weight_decay=1e-4); pw = torch.tensor((1 - Y_[~v].mean()) / max(Y_[~v].mean(), 1e-3))
        tr = torch.tensor(~v)
        for ep in range(300):
            l = nn.functional.binary_cross_entropy_with_logits(m(x[tr]), y[tr], pos_weight=pw); opt.zero_grad(); l.backward(); opt.step()
        m.eval()
        with torch.no_grad(): p = torch.sigmoid(m(x[~tr])).numpy()
        yv = Y_[v]; 문턱, 표 = 0.99, []
        for t in np.arange(.05, .99, .01):
            s = p >= t; tp = (s & (yv == 1)).sum(); 정 = tp / max(s.sum(), 1); 재 = tp / max((yv == 1).sum(), 1); 표.append((round(float(t), 2), round(float(정), 3), round(float(재), 3)))
        ok = [q for q in 표 if q[1] >= .8 and q[2] > 0]; 문턱, 정, 재 = ok[0] if ok else (0.99, 0.0, 0.0)
        torch.save(m.state_dict(), os.path.join(H, "거름망.pt"))
        json.dump({"문턱": 문턱, "검증 정밀도": 정, "검증 재현율": 재, "평균": mu.tolist(), "표준": sd.tolist(), "후보": int(len(Y_)), "진짜 비율": float(Y_.mean()), "검증 모델": len(검모), "표": 표[::10]},
                  open(os.path.join(H, "거름망.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ok 문턱", 문턱, "정밀도", 정, "재현율", 재, "후보", len(Y_), "진짜", round(float(Y_.mean()), 3))

    elif sys.argv[1] == "학습2":   # CNN — 같은 모델 단위 나눔 · 같은 문턱 규칙(정밀도 ≥ 0.8)
        d = np.load(os.path.join(H, "거름망_후보.npz")); F_, Y_, G_, C_ = d["F"], d["Y"], d["G"], d["C"]; 모 = sorted(set(G_)); rng = np.random.default_rng(0); rng.shuffle(모); 검모 = set(모[:len(모) // 10])
        v = np.array([g in 검모 for g in G_]); mu, sd = F_[~v].mean(0), F_[~v].std(0) + 1e-6; Fn = ((F_ - mu) / sd).astype(np.float32); dev = "cuda"
        torch.manual_seed(0); m = 망2().to(dev); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-3); pw = torch.tensor((1 - Y_[~v].mean()) / max(Y_[~v].mean(), 1e-3), device=dev)
        ti, vi = np.nonzero(~v)[0], np.nonzero(v)[0]
        def 배(ix, aug=False):
            x = torch.tensor(C_[ix].astype(np.float32), device=dev); f = torch.tensor(Fn[ix], device=dev)
            if aug:
                if rng.random() < .5: x = x.flip(-1)
                x = x.rot90(int(rng.integers(4)), (-2, -1))
            return x, f
        for ep in range(25):
            rng.shuffle(ti); m.train()
            for j in range(0, len(ti), 128):
                ix = ti[j:j + 128]; x, f = 배(ix, True); l = nn.functional.binary_cross_entropy_with_logits(m(x, f), torch.tensor(Y_[ix], device=dev), pos_weight=pw); opt.zero_grad(); l.backward(); opt.step()
        m.eval(); p = []
        with torch.no_grad():
            for j in range(0, len(vi), 512): x, f = 배(vi[j:j + 512]); p.append(torch.sigmoid(m(x, f)).cpu().numpy())
        p = np.concatenate(p); yv = Y_[vi]; 표 = []
        for t in np.arange(.05, .995, .01):
            s_ = p >= t; tp = (s_ & (yv == 1)).sum(); 표.append((round(float(t), 2), round(float(tp / max(s_.sum(), 1)), 3), round(float(tp / max((yv == 1).sum(), 1)), 3)))
        ok = [q for q in 표 if q[1] >= .8 and q[2] > 0]; 문턱, 정, 재 = ok[0] if ok else (0.99, 0.0, 0.0)
        torch.save(m.cpu().state_dict(), os.path.join(H, "거름망2.pt"))
        json.dump({"문턱": 문턱, "검증 정밀도": 정, "검증 재현율": 재, "평균": mu.tolist(), "표준": sd.tolist(), "후보": int(len(Y_)), "진짜 비율": float(Y_.mean()), "표": 표[::5]},
                  open(os.path.join(H, "거름망2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ok 문턱", 문턱, "정밀도", 정, "재현율", 재, "| 표", 표[::10])

    elif sys.argv[1] == "학습3":   # 판정기준17 — 진짜 홈(Y = 1)만 · 마스크 + 바닥 보정
        d = np.load(os.path.join(H, "거름망_후보.npz")); Y_, G_, C_, T_, O_ = d["Y"], d["G"], d["C"], d["T"], d["O"]; 모 = sorted(set(G_)); rng = np.random.default_rng(0); rng.shuffle(모); 검모 = set(모[:len(모) // 10])
        v = np.array([g in 검모 for g in G_]); ti, vi = np.nonzero(~v & (Y_ == 1))[0], np.nonzero(v & (Y_ == 1))[0]; dev = "cuda"
        torch.manual_seed(0); m = 망3().to(dev); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-4)
        def 배(ix, aug=False):
            x = torch.tensor(C_[ix].astype(np.float32), device=dev); t = torch.tensor(T_[ix].astype(np.float32), device=dev); o = torch.tensor(O_[ix], device=dev)
            if aug:
                if rng.random() < .5: x, t = x.flip(-1), t.flip(-1)
                r = int(rng.integers(4)); x, t = x.rot90(r, (-2, -1)), t.rot90(r, (-2, -1))
            return x, t, o
        for ep in range(30):
            rng.shuffle(ti); m.train()
            for j in range(0, len(ti), 64):
                x, t, o = 배(ti[j:j + 64], True); ml, ol = m(x); l = nn.functional.binary_cross_entropy_with_logits(ml, t) + .1 * nn.functional.huber_loss(ol, o); opt.zero_grad(); l.backward(); opt.step()
        m.eval(); iu, iu0, e, e0 = [], [], [], []
        with torch.no_grad():
            for j in range(0, len(vi), 256):
                x, t, o = 배(vi[j:j + 256]); ml, ol = m(x); p = torch.sigmoid(ml) > .5; t = t > .5; c0 = x[:, 4] > .5
                iu += ((p & t).sum((1, 2)) / (p | t).sum((1, 2)).clamp(min=1)).tolist(); iu0 += ((c0 & t).sum((1, 2)) / (c0 | t).sum((1, 2)).clamp(min=1)).tolist(); e += (ol - o).abs().tolist(); e0 += o.abs().tolist()
        torch.save(m.cpu().state_dict(), os.path.join(H, "거름망3.pt"))
        r = {"검증 진짜 홈": int(len(vi)), "마스크 IoU 배움": round(float(np.mean(iu)), 3), "마스크 IoU 후보 그대로": round(float(np.mean(iu0)), 3), "바닥 오차 중앙(칸) 배움": round(float(np.median(e)), 2), "바닥 오차 중앙(칸) 보정 없음": round(float(np.median(e0)), 2)}
        r["기준"] = bool(r["마스크 IoU 배움"] >= r["마스크 IoU 후보 그대로"] + .10 and r["바닥 오차 중앙(칸) 배움"] < r["바닥 오차 중앙(칸) 보정 없음"])
        json.dump(r, open(os.path.join(H, "거름망3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", r)
