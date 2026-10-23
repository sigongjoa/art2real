# CNN 계산 과정 디버깅 그림 — 화소 하나가 판정되기까지(입력 · 수용장 · 블록 1~4 특징 · 층별 몫) · 잘 되는 곳 대 곡선 옆 직선을 틀린 곳 · 10-23 사용자 「내가 디버깅할게」
# 머리가 1×1 이라 화소의 (곡선 − 직선) 점수 = Σ 층마다 W[층] · 특징[층] + 치우침 → 층별 몫으로 정확히 나뉨(합침 전부 판만)
# 사용(cadrille): python 하네스/계산과정그림.py [판 137전부합침] → out/하네스/<판>/계산과정.png
import os, sys, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
수용 = {1: 7, 2: 19, 3: 43, 4: 91}   # 3×3 보폭 2 + 3×3 보폭 1 블록을 쌓을 때 화소 하나가 보는 입력 폭(화소)
층이름 = {1: "블록 1 · 64칸 · 32채널", 2: "블록 2 · 32칸 · 64채널", 3: "블록 3 · 16칸 · 128채널", 4: "블록 4 · 8칸 · 256채널"}
def 펼침(n, x):   # (1, 3, 128, 128) → 뷰마다 블록 특징 [1..4]
    import torch
    b = len(x); f = x.reshape(b * 3, 1, 128, 128).float() / 255.; fs = []
    for 블록 in n.cnn: f = 블록(f); fs.append(f)
    return fs
def 몫(n, fs, v, y, x):   # 화소 (y, x) 의 클래스별 점수를 층별로 나눔 · 이어 붙인 순서 = [블록4 · 블록3 · 블록2 · 블록1](과제선지도.망 합침 전부)
    W = n.머리.weight[:, :, 0, 0].detach().cpu().numpy(); b0 = n.머리.bias.detach().cpu().numpy()
    cy, cx = y // 2, x // 2; 칸 = (y % 2) * 2 + (x % 2)
    특 = [fs[3][v, :, cy // 8, cx // 8], fs[2][v, :, cy // 4, cx // 4], fs[1][v, :, cy // 2, cx // 2], fs[0][v, :, cy, cx]]
    특 = [t.detach().cpu().numpy() for t in 특]; 끝 = np.cumsum([0] + [len(t) for t in 특])
    out = {}
    for c, 이름 in ((1, "직선"), (2, "곡선")):
        ch = c * 4 + 칸; out[이름] = {k: float(W[ch, 끝[i]:끝[i + 1]] @ 특[i]) for i, k in enumerate((4, 3, 2, 1))}; out[이름]["치우침"] = float(b0[ch])
    return out
def 주성분(f, 창):   # (C, h, w) 특징 → 창 안에서 주성분 3 개를 RGB 로
    C, h, w = f.shape; a = f.reshape(C, -1).T; a = a - a.mean(0); u, s, vt = np.linalg.svd(a, full_matrices=False); p = (a @ vt[:3].T)
    p = (p - p.min(0)) / (np.ptp(p, 0) + 1e-9); return p.reshape(h, w, 3)
def 그림(판="137전부합침"):
    import torch, 과제선지도 as G, 분석그림 as A, 하네스 as H, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from omegaconf import OmegaConf
    plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False   # 맑은 고딕에 − 글리프가 없어 네모로 깨짐
    c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); X, Y, _, idx, vx, 이, Xnp = G.자료("cuda", c); y = G.자르기(Y, vx)
    n = A.불러(판).cuda(); o = G.예측(n, X[vx])[:, :, :6].float(); pr = o[:, :, :4].softmax(2)
    예 = torch.where(1 - pr[:, :, 0] > .5, pr[:, :, 1:].argmax(2) + 1, 0).cpu().numpy(); 지 = y["지도"].cpu().numpy()
    import cv2
    곡곁 = np.stack([[cv2.dilate((지[i, v] == 2).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0 for v in range(3)] for i in range(len(지))])
    먼곳 = np.stack([[cv2.dilate((지[i, v] >= 2).astype(np.uint8), np.ones((21, 21), np.uint8)) == 0 for v in range(3)] for i in range(len(지))])
    틀림 = (지 == 1) & (예 == 2) & 곡곁; 맞음 = (지 == 1) & (예 == 1) & 먼곳
    # 같은 부품 · 같은 뷰에 둘 다 있는 자리 하나(가장 틀림 많은 곳)
    점수 = 틀림.sum((2, 3)) * (맞음.sum((2, 3)) > 0); i, v = np.unravel_index(점수.argmax(), 점수.shape)
    ys, xs = np.argwhere(틀림[i, v]).T; k = len(ys) // 2; 나쁨 = (ys[k], xs[k])
    gy, gx = np.argwhere(맞음[i, v]).T; d = (gy - 나쁨[0]) ** 2 + (gx - 나쁨[1]) ** 2; 좋음 = (gy[d.argmin()], gx[d.argmin()])
    x1 = X[vx][i:i + 1]
    with torch.no_grad(): fs = 펼침(n, x1)
    부품 = 이[int(vx[i])]; 색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8)
    # 모든 틀림 · 맞음 화소의 층별 몫 평균(시험 299 · 앞에서 400 개씩)
    def 평균몫(마스크, 최대=400):
        acc = {k: [] for k in (4, 3, 2, 1, "치우침")}; 자리 = np.argwhere(마스크)[:: max(1, int(마스크.sum()) // 최대)][:최대]
        cache = {}
        for (ii, vv, yy, xx) in 자리:
            if ii not in cache:
                with torch.no_grad(): cache = {ii: 펼침(n, X[vx][ii:ii + 1])}
            m = 몫(n, cache[ii], vv, yy, xx)
            for kk in acc: acc[kk].append(m["곡선"][kk] - m["직선"][kk])
        return {kk: float(np.mean(vv_)) for kk, vv_ in acc.items()}
    평틀, 평맞 = 평균몫(틀림), 평균몫(맞음)
    fig = plt.figure(figsize=(26, 21)); fig.suptitle(f"CNN 계산 과정 — 화소 하나가 직선 / 곡선으로 판정되기까지 (판 {판} · 부품 {부품} · {('위', '앞', '옆')[v]} 뷰)", fontsize=22, weight="bold")
    for r, (자리, 제목) in enumerate(((좋음, "잘 되는 곳 — 곡선과 먼 직선 · 직선으로 맞힘"), (나쁨, "우리 문제 — 곡선 옆 직선 · 곡선으로 틀림"))):
        yy, xx = 자리; y0 = int(np.clip(yy - 48, 0, 32)); x0 = int(np.clip(xx - 48, 0, 32)); 창 = (slice(y0, y0 + 96), slice(x0, x0 + 96))
        ax = fig.add_axes([.01, .64 - r * .32, .14, .26]); ax.imshow(255 - Xnp[int(vx[i]), v][창], cmap="gray", interpolation="nearest")
        for k_, 색k in ((1, "#e33"), (2, "#e90"), (3, "#3a3"), (4, "#36c")):
            h = 수용[k_]; ax.add_patch(plt.Rectangle((xx - x0 - h / 2, yy - y0 - h / 2), h, h, fill=False, ec=색k, lw=2))
        ax.plot(xx - x0, yy - y0, "o", ms=9, mec="k", mfc="#ff0"); ax.set_title(f"{제목}\n입력 · 노란 점 = 판정할 화소 · 네모 = 블록 1(빨) 2(주) 3(초) 4(파)가 보는 범위", fontsize=11); ax.axis("off")
        for j, (im, t) in enumerate(((색[지[i, v]][창], "정답"), (색[예[i, v]][창], "모델 출력"))):
            ax = fig.add_axes([.155 + j * .105, .64 - r * .32, .1, .26]); ax.imshow(im, interpolation="nearest"); ax.plot(xx - x0, yy - y0, "o", ms=8, mec="k", mfc="#ff0"); ax.set_title(t, fontsize=13); ax.axis("off")
        for j, k_ in enumerate((1, 2, 3, 4)):
            f = fs[k_ - 1][v].detach().cpu().numpy(); s = 128 // f.shape[1]; 작 = (slice(y0 // s, (y0 + 96) // s), slice(x0 // s, (x0 + 96) // s))
            ax = fig.add_axes([.37 + j * .105, .64 - r * .32, .1, .26]); ax.imshow(np.kron(주성분(f[:, 작[0], 작[1]], None), np.ones((s, s, 1))), interpolation="nearest")
            ax.plot(xx - x0, yy - y0, "o", ms=8, mec="k", mfc="#ff0"); ax.set_title(f"{층이름[k_]}\n(주성분 3 개를 색으로)", fontsize=11); ax.axis("off")
        m = 몫(n, fs, v, yy, xx); 차 = {k_: m["곡선"][k_] - m["직선"][k_] for k_ in (1, 2, 3, 4, "치우침")}; 합 = sum(차.values())
        ax = fig.add_axes([.81, .66 - r * .32, .17, .22]); 이름들 = ["블록 1", "블록 2", "블록 3", "블록 4", "치우침"]; 값 = [차[1], 차[2], 차[3], 차[4], 차["치우침"]]
        ax.barh(이름들, 값, color=["#e33" if t > 0 else "#36c" for t in 값]); ax.axvline(0, color="k", lw=1); ax.invert_yaxis()
        ax.set_title(f"이 화소의 (곡선 - 직선) 점수 층별 몫 · 합 {합:+.1f}\n오른쪽(빨강) = 곡선 쪽으로 밂 · 왼쪽(파랑) = 직선 쪽", fontsize=11)
    ax = fig.add_axes([.06, .04, .55, .22]); 이름들 = ["블록 1\n보는 범위 7", "블록 2\n19", "블록 3\n43", "블록 4\n91"]; xk = np.arange(4)
    ax.bar(xk - .2, [평맞[k_] for k_ in (1, 2, 3, 4)], .4, color="#36c", label="곡선과 먼 직선 · 맞힘"); ax.bar(xk + .2, [평틀[k_] for k_ in (1, 2, 3, 4)], .4, color="#e33", label="곡선 옆 직선 · 곡선으로 틀림")
    ax.axhline(0, color="k", lw=1); ax.set_xticks(xk); ax.set_xticklabels(이름들, fontsize=13); ax.legend(fontsize=13)
    ax.set_title("시험 부품 전체 평균 — 층마다 (곡선 - 직선) 점수에 보탠 몫 · 0 위 = 곡선 쪽으로 밂 · 0 아래 = 직선 쪽", fontsize=15)
    ax = fig.add_axes([.65, .04, .33, .22]); ax.axis("off")
    ax.text(0, 1, "읽는 법\n\n· 마지막 머리는 네 층 특징의 가중합(1×1)이라\n  화소의 판정 점수 = 블록 1 + 2 + 3 + 4 몫 + 치우침\n· 보는 범위가 큰 블록 3 · 4 는 옆의 원까지 본다\n· 틀린 화소에서 그 층들이 곡선 쪽으로 밀면\n  「동네에 원이 있으니 곡선」 으로 판정한 것", fontsize=14, va="top")
    p = f"{뿌리}/out/하네스/{판}/계산과정.png"; fig.savefig(p, dpi=55, bbox_inches="tight"); plt.close(fig); print(p, 부품, ("위", "앞", "옆")[v], "좋음", 좋음, "나쁨", 나쁨, "평균 틀림", {k: round(v_, 2) for k, v_ in 평틀.items()}, "평균 맞음", {k: round(v_, 2) for k, v_ in 평맞.items()})
if __name__ == "__main__": 그림(*(sys.argv[1:2]))
