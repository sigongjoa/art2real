# 하네스 점검 「특징」 — 실제 3면도에서 CNN · 어텐션이 곡선 · 접합 · 겹친 곳을 찾나 · 학습 없음 · 10-22
# 조각(8×8 = 토큰 칸) 라벨을 선 화소 규칙으로: 0 빈칸 · 1 직선 · 2 곡선 · 3 접합 · 교차 · 4 실선×숨은선
# ① 쏠림: 칸 주의가 그 라벨 조각에 「조각 비율보다」 얼마나 더 가나(배수 · 1 = 고르게) ② CNN 탐침: 마지막 CNN 조각 특징으로 라벨 맞히기(균형 정확도) · 대조 = 무작위 CNN · 화소 그대로
# 사용: python 하네스/특징.py <판이름>   (out/하네스/<판>/점검/마지막.pt · 하네스/판/<판>/설정.yaml) · 하네스 점검 목록에 「특징」을 넣으면 판마다 자동
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품"); sys.path.insert(0, 뿌리 + "/하네스")
import 모델124 as B
라벨이름 = ["빈칸", "직선", "곡선", "접합·교차", "실선×숨은선"]; 라벨색 = ["#00000000", "#4a7bd1", "#28a050", "#d8262b", "#d9a020"]
def 라벨(X3):   # (3, 128, 128) uint8(선 255 · 숨은선 115) → (3, 8, 8)
    from skimage.morphology import skeletonize
    from scipy.ndimage import convolve, label as cc
    out = np.zeros((3, 8, 8), np.int64)
    for v in range(3):
        x = X3[v]; 선 = x > 0; 숨 = (x > 0) & (x < 255); s = skeletonize(선).astype(np.uint8)
        링 = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]; p = np.pad(s, 1)
        고리 = np.stack([p[1 + dy:129 + dy, 1 + dx:129 + dx] for dy, dx in 링]); 넘 = (고리 != np.roll(고리, 1, 0)).sum(0) // 2   # 0→1 바뀜 수
        접 = (s == 1) & (넘 >= 3); 숨곁 = convolve(숨.astype(np.uint8), np.ones((5, 5), np.uint8), mode="constant") > 0; 실곁 = convolve((x == 255).astype(np.uint8), np.ones((5, 5), np.uint8), mode="constant") > 0
        for i in range(8):
            for j in range(8):
                sl = (slice(i * 16, i * 16 + 16), slice(j * 16, j * 16 + 16))
                if not 선[sl].any(): continue
                if 접[sl].any(): out[v, i, j] = 4 if (접[sl] & 숨곁[sl] & 실곁[sl]).any() else 3; continue
                휨 = False; c, n = cc(s[sl], np.ones((3, 3)))
                for k in range(1, n + 1):
                    yx = np.argwhere(c == k).astype(float)
                    if len(yx) < 8: continue
                    yx -= yx.mean(0); 휨 |= np.linalg.svd(yx, compute_uv=False)[1] / np.sqrt(len(yx)) > .75   # 둘째 주축 RMS(화소) — 직선이면 ≈ 0
                out[v, i, j] = 2 if 휨 else 1
    return out
def 재기(net, Xnp, 이, 폴더, 학습수=300):
    import torch, 층보기127 as V, 탐침128 as P
    net = net.cpu().eval(); 시 = [n for n in 이 if int(n) >= B.NT]; 학 = [n for n in 이 if int(n) < B.NT][::40][:학습수]
    def 조각(ns, 망_):
        F, L, 주 = [], [], []
        for s in range(0, len(ns), 32):
            x = torch.tensor(Xnp[[이.index(n) for n in ns[s:s + 32]]])
            with torch.no_grad(): d = V.펼침(망_, x)
            끝 = [k for k in d if k.startswith("CNN")][-1]; f = d[끝]   # (b, 3, C, 8, 8)
            F.append(f.permute(0, 1, 3, 4, 2).reshape(-1, f.shape[2]).numpy()); 주.append(np.stack([d[f"주의{i}"].mean(1).numpy() for i in range(1, 5)], 1))   # (b, 4 층, 192)
            L.append(np.stack([라벨(Xnp[이.index(n)]) for n in ns[s:s + 32]]).reshape(-1))
        return np.concatenate(F), np.concatenate(L), np.concatenate(주)
    Ft, Lt, At = 조각(시, net); Fl, Ll, _ = 조각(학, net)
    지 = {}; 몫 = np.bincount(Lt, minlength=5) / len(Lt); Lb = Lt.reshape(len(시), 192)
    for 층 in range(4):
        a = At[:, 층]; 받 = np.array([(a * (Lb == c)).sum(1).mean() for c in range(5)]); 지[f"쏠림{층 + 1}"] = {라벨이름[c]: round(float(받[c] / max(몫[c], 1e-9)), 3) for c in range(5)}
    지["조각 비율"] = {라벨이름[c]: round(float(몫[c]), 3) for c in range(5)}
    def 균형(X, y, Xt, yt):   # 릿지 원핫 → 균형 정확도 · 라벨마다 재현율
        mu, sd = X.mean(0), X.std(0) + 1e-6; Z = np.c_[(X - mu) / sd, np.ones(len(X))]; Zt = np.c_[(Xt - mu) / sd, np.ones(len(Xt))]
        W = np.linalg.solve(Z.T @ Z + 10 * np.eye(Z.shape[1]), Z.T @ np.eye(5)[y]); p = (Zt @ W - (Z @ W).mean(0)).argmax(1)   # 평균 빼서 많은 라벨로 쏠림 줄임
        재 = [float((p[yt == c] == c).mean()) if (yt == c).any() else float("nan") for c in range(5)]; return round(float(np.nanmean(재)), 4), {라벨이름[c]: round(재[c], 3) for c in range(5)}
    import copy, 모델127 as M7
    무 = M7.망() if net.cnn[0][0].in_channels == 1 else __import__("모델129").망("c"); 무.eval(); Fr, _, _ = 조각(시, 무); Frl, _, _ = 조각(학, 무)
    화 = lambda ns: Xnp[[이.index(n) for n in ns]].reshape(len(ns), 3, 8, 16, 8, 16).transpose(0, 1, 2, 4, 3, 5).reshape(-1, 256).astype(np.float32) / 255.
    지["탐침_학습CNN"] = 균형(Fl, Ll, Ft, Lt); 지["탐침_무작위CNN"] = 균형(Frl, Ll, Fr, Lt); 지["탐침_화소"] = 균형(화(학), Ll, 화(시), Lt)
    그림(net, Xnp, 이, 지, 폴더); return 지
def 그림(net, Xnp, 이, 지, 폴더, n="12003"):
    import torch, 층보기127 as V, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib.colors import ListedColormap
    plt.rcParams["font.family"] = "Malgun Gothic"; X3 = Xnp[이.index(n)]; Lb = 라벨(X3)
    with torch.no_grad(): d = V.펼침(net.cpu().eval(), torch.tensor(X3[None]))
    w = d["주의4"][0].mean(0).numpy().reshape(3, 8, 8); fig = plt.figure(figsize=(24, 12)); fig.suptitle("특징 점검 — 실제 3면도에서 어텐션 · CNN 이 곡선 · 접합 · 겹친 곳을 찾나", fontsize=18, weight="bold")
    for v in range(3):
        a = fig.add_axes([.02 + v * .16, .52, .15, .38]); a.imshow(X3[v], cmap="gray"); a.imshow(np.kron(Lb[v], np.ones((16, 16))), cmap=ListedColormap(["#00000000"] + 라벨색[1:]), vmin=0, vmax=4, alpha=.45, interpolation="nearest"); a.axis("off"); a.set_title(f"{n} {B.뷰[v]} · 조각 라벨", fontsize=12)
        a = fig.add_axes([.02 + v * .16, .08, .15, .38]); a.imshow(X3[v], cmap="gray"); a.imshow(np.kron(w[v] / w.max(), np.ones((16, 16))), cmap="viridis", alpha=.6, vmin=0, vmax=1); a.axis("off"); a.set_title(f"4 층 칸 평균 주의 · 몫 {w[v].sum():.2f}", fontsize=12)
    a = fig.add_axes([.52, .57, .2, .3]); a.axis("off")
    for c in range(1, 5): a.add_patch(plt.Rectangle((0, .85 - c * .2), .08, .12, fc=라벨색[c])); a.text(.12, .9 - c * .2, f"{라벨이름[c]} (조각 {지['조각 비율'][라벨이름[c]]:.0%})", fontsize=13, va="center")
    a = fig.add_axes([.52, .1, .2, .35]); x = np.arange(5)
    for 층, c in ((1, "#bbbbbb"), (4, "#4a7bd1")): a.bar(x + (층 == 4) * .38 - .19, [지[f"쏠림{층}"][k] for k in 라벨이름], .38, color=c, label=f"{층} 층")
    a.axhline(1, color="k", ls="--"); a.set_xticks(x); a.set_xticklabels(라벨이름, fontsize=11); a.set_title("주의 쏠림 배수 (1 = 고르게 · > 1 = 그 조각을 더 봄)", fontsize=13); a.legend()
    a = fig.add_axes([.77, .1, .21, .78]); 줄 = [("학습 CNN", "탐침_학습CNN", "#28a050"), ("무작위 CNN", "탐침_무작위CNN", "#999"), ("화소 그대로", "탐침_화소", "#d8262b")]
    for k, (이름, 키, c) in enumerate(줄): a.barh(np.arange(5) + k * .27 - .27, [지[키][1][r] for r in 라벨이름], .27, color=c, label=f"{이름} (균형 {지[키][0]:.2f})")
    a.set_yticks(np.arange(5)); a.set_yticklabels(라벨이름, fontsize=12); a.invert_yaxis(); a.set_xlim(0, 1); a.legend(fontsize=11, loc="lower right"); a.set_title("CNN 마지막 조각 특징으로 라벨 맞힘(라벨마다 재현율)", fontsize=13)
    fig.savefig(폴더 + "특징.png", dpi=60); plt.close(fig)
if __name__ == "__main__":
    import torch, 하네스 as H
    from omegaconf import OmegaConf
    판 = sys.argv[1]; cfg = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); 폴더 = f"{뿌리}/out/하네스/{판}/"
    net = H.망(cfg); net.load_state_dict(torch.load(폴더 + "점검/마지막.pt")["모델"]); z = np.load(H.M7.D + "그림.npz")
    지 = 재기(net, z["X"], list(z["이름"]), 폴더); json.dump(지, open(f"{뿌리}/하네스/판/{판}/특징.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil; shutil.copy(폴더 + "특징.png", f"{뿌리}/하네스/판/{판}/특징.png"); print(json.dumps(지, ensure_ascii=False))
