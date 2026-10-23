# 하네스 과제 「선지도」 — CNN 백본만: 3면도 → 화소마다 선 종류(없음 · 직선 · 곡선 · 곡면 테) · 숨은선 · 꼭짓점 열 지도 · 정답은 하네스/선정답.py(CAD 형상 투영) · 10-22
# 머리는 얇게: 8×8 특징 칸 하나 → 1×1 합성곱 하나 → pixel shuffle 16 (업샘플 · 건너뛰기 없음 → 맞히면 CNN 특징 덕)
# 인코더: cnn(127 의 4 블록) | 화소(16×16 화소를 그대로 같은 머리에 — 대조)
import os, sys, numpy as np
뿌리 = "G:/art2real"; 저장 = f"{뿌리}/out/하네스/선정답/"; K = 4; 출 = K + 2   # 종류 4 · 숨음 1 · 꼭짓점 1
종류이름 = ["없음", "직선", "곡선", "곡면테"]
def 자료(dev, cfg):
    import torch, 모델124 as B, 모델127 as M7
    z = np.load(M7.D + "그림.npz"); 전 = {n: k for k, n in enumerate(z["이름"])}; 전X = z["X"]; 이, Xs, 지, 숨, 점 = [], [], [], [], []   # z["X"] 는 꺼낼 때마다 600 MB 를 다시 읽음 — 한 번만
    for f in sorted(os.listdir(저장)):
        if not f.endswith(".npz") or f[:5] not in 전: continue
        d = np.load(저장 + f); 이.append(f[:5]); Xs.append(전X[전[f[:5]]]); 지.append(d["지도"]); 숨.append(d["숨"]); 점.append(d["점"])
    Xnp = np.stack(Xs); 열 = 열지도(np.stack(점))
    if cfg is not None and cfg.get("선지도", {}).get("맞춤"): 지 = [맞춤(x, t) for x, t in zip(Xnp, 지)]   # 132~: 정답 선 = 입력 선 화소
    지 = list(지); 시 = np.array([int(n) >= B.NT for n in 이])
    T = lambda a: torch.tensor(a).to(dev)
    Y = {"지도": T(np.stack(지).astype(np.int64)), "숨": T(np.stack(숨)), "열": T(열)}
    print("선지도 자료", len(이), "학습", int((~시).sum()), "시험", int(시.sum()), flush=True)
    return T(Xnp), Y, None, torch.tensor(np.nonzero(~시)[0]), torch.tensor(np.nonzero(시)[0]), 이, Xnp
def 맞춤(x, t, 반경=2):   # 투영 정답은 입력 선과 1 화소씩 어긋남(정확히 겹침 64.5 % · 1 화소 안 98.7 % · 10-22) → 선 = 입력 선 화소 · 종류 = 가장 가까운 투영 선
    import cv2
    out = np.zeros_like(t)
    for v in range(3):
        선 = x[v] > 0
        if not (t[v] > 0).any(): continue
        _, 라 = cv2.distanceTransformWithLabels((t[v] == 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
        yx = np.argwhere(t[v] > 0); 표 = np.zeros(라.max() + 1, t.dtype)
        idx = 라[yx[:, 0], yx[:, 1]]; 표[idx] = t[v][yx[:, 0], yx[:, 1]]
        거 = cv2.distanceTransform((t[v] == 0).astype(np.uint8), cv2.DIST_L2, 3)
        out[v] = np.where(선 & (거 <= 반경), 표[라], 0)
    return out
def 열지도(점, s=1.5, N=128):   # (n, 3, M, 2) NaN 채움 → (n, 3, 128, 128) float16 가우스 최대
    yy, xx = np.mgrid[:N, :N].astype(np.float32); out = np.zeros(점.shape[:2] + (N, N), np.float16)
    for i in range(점.shape[0]):
        for v in range(3):
            q = 점[i, v][~np.isnan(점[i, v, :, 0])]
            if len(q): out[i, v] = np.exp(-((xx[None] - q[:, 0, None, None]) ** 2 + (yy[None] - q[:, 1, None, None]) ** 2) / (2 * s * s)).max(0)
    return out
층지표 = ("선_자리", "선_자리헛선", "선_종류", "선_직선", "선_곡선", "점_F1")
층폭 = {1: 32, 2: 64, 3: 128}   # 블록 k 출력 채널 · 해상도 128 / 2^k
def 망(인코더, 탐침=False, 합침="없음"):   # 합침: 없음(블록 4 만) | 블록1(블록 4 를 8 배 키워 블록 1 과 이어 읽음 · 136 — 135 탐침: 얕은 층 = 어디 · 깊은 층 = 무엇)
    import torch, torch.nn as nn, torch.nn.functional as F
    torch.manual_seed(0)
    def 블(a, b): return nn.Sequential(nn.Conv2d(a, b, 3, 2, 1), nn.GroupNorm(8, b), nn.GELU(), nn.Conv2d(b, b, 3, 1, 1), nn.GroupNorm(8, b), nn.GELU())
    class 선망(nn.Module):   # (b, 3, 128, 128) uint8 → (b, 3, 6 × (1 + 탐침 3), 128, 128) · 앞 6 = 본 머리(블록 4)
        def __init__(s):
            super().__init__(); s.인코더 = 인코더; s.탐침 = 탐침 and 인코더 == "cnn"
            if 인코더 == "cnn": s.cnn = nn.Sequential(블(1, 32), 블(32, 64), 블(64, 128), 블(128, 256))   # 127 과 같은 백본
            s.합침 = 합침 if 인코더 == "cnn" else "없음"
            s.머리 = nn.Conv2d(256, 16 * 16 * 출, 1) if s.합침 == "없음" else nn.Conv2d(256 + 층폭[1] + (층폭[2] + 층폭[3] if s.합침 == "전부" else 0), 4 * 출, 1)   # 전부(137): 블록 1 ~ 4 를 64 칸에 모아 읽음(FPN 꼴 · 136 곡선 옆 직선을 곡선으로 번짐)
            if s.탐침: s.탐머리 = nn.ModuleList([nn.Conv2d(층폭[k], 4 ** k * 출, 1) for k in (1, 2, 3)])   # 블록 k 를 같은 얇은 머리로 읽음
        def forward(s, x):
            b = len(x); x = x.reshape(b * 3, 1, 128, 128).float() / 255.
            if s.인코더 != "cnn": return F.pixel_shuffle(s.머리(F.pixel_unshuffle(x, 16)), 16).reshape(b, 3, 출, 128, 128)
            fs = []; f = x
            for 블록 in s.cnn: f = 블록(f); fs.append(f)
            if s.합침 == "블록1": o = [F.pixel_shuffle(s.머리(torch.cat([F.interpolate(f, scale_factor=8, mode="nearest"), fs[0]], 1)), 2)]   # 64 칸에서 읽고 2 배로 펼침
            elif s.합침 == "전부": o = [F.pixel_shuffle(s.머리(torch.cat([F.interpolate(f, scale_factor=8, mode="nearest"), F.interpolate(fs[2], scale_factor=4, mode="nearest"), F.interpolate(fs[1], scale_factor=2, mode="nearest"), fs[0]], 1)), 2)]
            else: o = [F.pixel_shuffle(s.머리(f), 16)]
            if s.탐침: o += [F.pixel_shuffle(h(fs[k - 1].detach()), 2 ** k) for k, h in zip((1, 2, 3), s.탐머리)]   # detach: 탐침은 본 학습을 안 바꿈
            return torch.cat(o, 1).reshape(b, 3, 출 * len(o), 128, 128)
    return 선망()
def 손실함수(빈가중=.05): return lambda o, Y, 쓰=None: 손실(o, Y, 빈가중=빈가중)
def 손실(o, Y, 쓰=None, 빈가중=.05):   # Y 는 이미 배치로 잘린 dict · 탐침 머리가 붙었으면 머리마다 같은 손실을 더함(탐침은 detach 라 백본엔 본 머리 기울기만)
    if o.shape[2] > 출: return sum(손실(o[:, :, h:h + 출], Y, 빈가중=빈가중) for h in range(0, o.shape[2], 출))
    import torch, torch.nn.functional as F
    지 = Y["지도"]; 선 = 지 > 0; w = torch.tensor([빈가중, 1., 1., 1.], device=o.device)   # 없음 화소가 97 % — 가중(130: 0.05 → 선 둘레를 덩어리째 칠함)
    l종 = F.cross_entropy(o[:, :, :K].permute(0, 1, 3, 4, 2).reshape(-1, K), 지.reshape(-1), weight=w)
    l숨 = F.binary_cross_entropy_with_logits(o[:, :, K][선], Y["숨"][선].float()) if 선.any() else o.sum() * 0
    t = Y["열"].float(); p = torch.sigmoid(o[:, :, K + 1]); l점 = (((p - t) ** 2) * (1 + 30 * t)).mean() * 10
    return l종 + l숨 + l점
def 자르기(Y, ix): return {k: v[ix] for k, v in Y.items()}
def 지표(o, Y):   # 시험 지표 — o, Y 는 같은 부품들 · 본 머리(앞 6 채널)만
    import torch, torch.nn.functional as F
    o = o[:, :, :출].float(); 지 = Y["지도"]; 예 = o[:, :, :K].argmax(2); r = {}
    for k in (1, 2, 3): m = 지 == k; r[f"선_{종류이름[k]}"] = round(float((예[m] == k).float().mean()), 4) if m.any() else None   # 그 종류 화소를 그 종류로 맞힘(재현율)
    선 = 지 > 0; r["선_숨음"] = round(float(((o[:, :, K][선] > 0) == Y["숨"][선]).float().mean()), 4)
    r["선_헛선"] = round(float((예[~선] > 0).float().mean()), 4)   # 선 없는 화소에 선을 그림
    pr = o[:, :, :K].float().softmax(2); 있 = (1 - pr[:, :, 0]) > .5; 종 = pr[:, :, 1:].argmax(2) + 1   # 「선이냐」 먼저 · 종류는 그다음(132: 선이라 알아도 확률을 셋에 나눠 「없음」이 1 등)
    곡곁 = F.max_pool2d((지 == 2).float().reshape(-1, 1, 128, 128), 7, 1, 3).reshape(지.shape) > 0; 직곁 = (지 == 1) & 곡곁   # 곡선 3 화소 안의 직선(136 진단: 틀린 직선의 56 %)
    r["선_곡선옆직선오류"] = round(float((종[직곁] == 2).float().mean()), 4) if 직곁.any() else None
    r["선_자리"] = round(float(있[선].float().mean()), 4); r["선_자리헛선"] = round(float(있[~선].float().mean()), 4); r["선_종류"] = round(float((종[선] == 지[선]).float().mean()), 4)
    p = torch.sigmoid(o[:, :, K + 1]).float(); 봉 = (p == F.max_pool2d(p.reshape(-1, 1, 128, 128), 5, 1, 2).reshape(p.shape)) & (p > .3)
    t = Y["열"].float(); 참 = (t == F.max_pool2d(t.reshape(-1, 1, 128, 128), 3, 1, 1).reshape(t.shape)) & (t > .9)
    가까이 = lambda a: F.max_pool2d(a.float().reshape(-1, 1, 128, 128), 5, 1, 2).reshape(a.shape) > 0   # 2 화소 안
    정밀 = float((봉 & 가까이(참)).sum() / 봉.sum().clamp(min=1)); 재현 = float((참 & 가까이(봉)).sum() / 참.sum().clamp(min=1))
    r["점_정밀"], r["점_재현"] = round(정밀, 4), round(재현, 4); r["점_F1"] = round(2 * 정밀 * 재현 / max(정밀 + 재현, 1e-9), 4)
    return r
def 예측(net, X, 배=32):
    import torch
    net.eval()
    with torch.no_grad(): return torch.cat([net(X[i:i + 배]).half() for i in range(0, len(X), 배)])   # 탐침 머리까지 299 장이면 float32 로 1.4 GB
def 점검(cfg, 폴더, net, 기록, X, Y, vx, 이, Xnp, 실행):   # 이 판 지표 + 같은 에폭으로 학습한 화소 대조 · 그림
    import torch, json
    from omegaconf import OmegaConf
    o = 예측(net, X[vx]); 지 = {"시험loss": round(기록[-1]["시험"], 4), "학습loss": round(기록[-1]["학습"], 4)} | 지표(o, 자르기(Y, vx))
    for h, k in enumerate((1, 2, 3), 1):   # 탐침: 블록 k 를 같은 얇은 머리로 읽은 값(본 머리 = 블록 4)
        if o.shape[2] > h * 출: 지 |= {f"층{k}_{m}": v for m, v in 지표(o[:, :, h * 출:(h + 1) * 출], 자르기(Y, vx)).items() if m in 층지표}
    if o.shape[2] > 출: 지 |= {f"층4_{m}": 지[m] for m in 층지표}
    c2 = OmegaConf.merge(cfg, {"인코더": "화소"}); 대폴더 = 폴더 + "대조_화소/"; os.makedirs(대폴더, exist_ok=True)
    net2, 록2 = 실행(c2, 대폴더); o2 = 예측(net2, X[vx]); 대 = 지표(o2, 자르기(Y, vx)); json.dump(대, open(폴더 + "대조_화소.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in 대.items(): 지[f"{k}_화소"] = v
    for k in ("선_곡선", "선_직선", "선_곡면테", "점_F1"):
        if 지.get(k) is not None and 대.get(k) is not None: 지[f"{k}_차"] = round(지[k] - 대[k], 4)
    그림(폴더, X[vx], 자르기(Y, vx), o, o2, 기록, 록2, 지, 이, vx); return 지
def 그림(폴더, X, Y, o, o2, 록, 록2, 지, 이, vx, 몇=(0, 7, 50)):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from PIL import Image
    plt.rcParams["font.family"] = "Malgun Gothic"; 색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8)
    def 칠(지도, 열):
        rgb = 색[지도].astype(float); a = np.clip(열, 0, 1)[..., None]; return (rgb * (1 - a) + np.array([216, 38, 43]) * a).astype(np.uint8)
    import torch
    p = lambda oo, i, v: 칠(oo[i, v, :K].argmax(0).cpu().numpy(), torch.sigmoid(oo[i, v, K + 1]).float().cpu().numpy())
    fig, ax = plt.subplots(len(몇), 4, figsize=(20, 5.2 * len(몇))); fig.suptitle("판 시트 — 입력 · 정답 · CNN · 화소 대조 (앞 뷰 · 시험 부품)", fontsize=20, weight="bold")
    for r, i in enumerate(몇):
        도 = 255 - X[i, 1].cpu().numpy(); 정 = 칠(Y["지도"][i, 1].cpu().numpy(), Y["열"][i, 1].float().cpu().numpy())
        for c, (im, t) in enumerate(((도, f"입력 {이[int(vx[i])]}"), (정, "정답(CAD 투영)"), (p(o, i, 1), "CNN"), (p(o2, i, 1), "화소 그대로 대조"))):
            ax[r, c].imshow(im, cmap="gray" if c == 0 else None); ax[r, c].set_title(t, fontsize=14); ax[r, c].axis("off")
    fig.savefig(폴더 + "시트.png", dpi=60, bbox_inches="tight"); plt.close(fig)
    Image.fromarray(np.kron(255 - X[몇[0], 1].cpu().numpy(), np.ones((5, 5), np.uint8))).save(폴더 + "도면_앞.png")
    Image.fromarray(np.kron(칠(Y["지도"][몇[0], 1].cpu().numpy(), Y["열"][몇[0], 1].float().cpu().numpy()), np.ones((5, 5, 1), np.uint8))).save(폴더 + "정답.png")
    Image.fromarray(np.kron(p(o, 몇[0], 1), np.ones((5, 5, 1), np.uint8))).save(폴더 + "예측전체.png")
if __name__ == "__main__":   # 자체 시험: 모양 · 손실 유한 · 지표 범위 · 완벽 예측이면 재현율 1
    import torch
    for e in ("cnn", "화소"):
        n = 망(e); x = torch.randint(0, 255, (2, 3, 128, 128), dtype=torch.uint8); o = n(x); assert o.shape == (2, 3, 출, 128, 128), o.shape
        지 = torch.zeros(2, 3, 128, 128, dtype=torch.long); 지[:, :, 40, 10:100] = 1; 지[:, :, 60:90, 70] = 2; 숨 = torch.zeros(2, 3, 128, 128, dtype=torch.bool); 숨[:, :, 40, 50:100] = True
        점 = np.full((2, 3, 96, 2), np.nan, np.float32); 점[:, :, 0] = (70, 40); Y = {"지도": 지, "숨": 숨, "열": torch.tensor(열지도(점))}
        l = 손실(o, Y); assert torch.isfinite(l), l
        완 = torch.full((2, 3, 출, 128, 128), -9.); 완[:, :, :K] = torch.nn.functional.one_hot(지, K).permute(0, 1, 4, 2, 3) * 18 - 9; 완[:, :, K] = 숨.float() * 18 - 9; 완[:, :, K + 1] = torch.logit(Y["열"].float().clamp(1e-4, 1 - 1e-4))
        r = 지표(완, Y); assert r["선_직선"] == 1 and r["선_곡선"] == 1 and r["선_숨음"] == 1 and r["선_헛선"] == 0 and r["점_F1"] == 1, r
    print("과제선지도 시험 통과", r)
