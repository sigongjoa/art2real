# 겹침 유형별 디버깅 — 직선-직선 · 직선-곡선 · 곡선-곡선이 2 화소 안으로 붙어 지나는 곳(꼭짓점 빼고) · 판 모델의 오류율 · 층별 몫(정답 종류 쪽으로 민 몫) · 10-23 사용자 「비교용으로 직직 · 직곡 · 곡곡」
# 1 단계(모서리 지도): CAD 를 다시 투영해 모서리마다 따로 그림(정답 지도는 화소당 라벨 하나라 누가 겹쳤는지 모름) → out/하네스/겹침/<부품>.npz
# 2 단계(그림): python 하네스/겹침그림.py 그림 [판 137전부합침]
import os, sys, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
저장 = f"{뿌리}/out/하네스/겹침/"; 유형 = ["홀로 직선", "홀로 곡선", "직선-직선", "직선-곡선", "곡선-곡선"]
def _모서리(i):   # 부품 하나 → 뷰마다 모서리별 1 화소 마스크(packbits) · 종류(직선 1 / 곡선 2) · 꼭짓점
    p = 저장 + f"{i:05d}.npz"
    if os.path.exists(p): return
    try:
        import cv2, 선정답 as S
        뷰들 = S.계산(i); 짐 = {}
        for v, d in enumerate(뷰들):
            ms, ks = [], []
            for l in d["선"]:
                m = np.zeros((128, 128), np.uint8); q = np.array(l["꺾은선"] + [l["끝"][1]], np.float32)
                cv2.polylines(m, [q.round().astype(np.int32)], False, 1, 1); ms.append(np.packbits(m.astype(bool))); ks.append(1 if l["종류"] == "직선" else 2)
            짐[f"m{v}"] = np.array(ms) if ms else np.zeros((0, 2048), np.uint8); 짐[f"k{v}"] = np.array(ks, np.int8); 짐[f"p{v}"] = np.array(d["점"], np.float32).reshape(-1, 2)
        np.savez_compressed(p, **짐)
    except Exception as ex: open(p + ".err", "w", encoding="utf-8").write(str(ex)[:300])
def 모서리들(수=80, 일꾼=6, 초=120):
    import time, multiprocessing as mp, 모델124 as B
    os.makedirs(저장, exist_ok=True); 일 = [r["i"] for r in B.색인() if r["i"] >= B.NT][:수]; 일 = [i for i in 일 if not os.path.exists(저장 + f"{i:05d}.npz")]; 도는 = {}
    while 일 or 도는:
        while 일 and len(도는) < 일꾼: i = 일.pop(0); pr = mp.Process(target=_모서리, args=(i,)); pr.start(); 도는[i] = (pr, time.time())
        for i, (pr, t) in list(도는.items()):
            if not pr.is_alive(): pr.join(); del 도는[i]
            elif time.time() - t > 초: pr.kill(); pr.join(); open(저장 + f"{i:05d}.npz.err", "w").write("시간 초과"); del 도는[i]
        time.sleep(.2)
def 유형지도(z, v):   # 뷰 하나 → 화소마다 유형 번호(-1 없음) · 2 화소 안에 다른 모서리가 지나면 겹침 · 꼭짓점 3 화소 안은 뺌
    import cv2
    ms = np.unpackbits(z[f"m{v}"], axis=1)[:, :128 * 128].reshape(-1, 128, 128).astype(bool) if len(z[f"m{v}"]) else np.zeros((0, 128, 128), bool); ks = z[f"k{v}"]
    out = np.full((128, 128), -1, np.int8)
    if not len(ms): return out
    넓 = np.stack([cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0 for m in ms])   # 2 화소
    yy, xx = np.mgrid[:128, :128]; 점곁 = np.zeros((128, 128), bool)
    for (px, py) in z[f"p{v}"]: 점곁 |= (xx - px) ** 2 + (yy - py) ** 2 <= 9
    for e, (m, k) in enumerate(zip(ms, ks)):
        남 = 넓[np.arange(len(ms)) != e]; 남k = ks[np.arange(len(ms)) != e]
        for y, x in np.argwhere(m & ~점곁):
            옆 = 남k[남[:, y, x]] if len(남) else []
            if len(옆) == 0: t = 0 if k == 1 else 1
            else: s = {k, *옆}; t = 2 if s == {1} else 4 if s == {2} else 3
            out[y, x] = max(out[y, x], t)
    return out
def 그림(판="137전부합침"):
    import torch, cv2, 과제선지도 as G, 분석그림 as A, 계산과정그림 as K, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from omegaconf import OmegaConf
    plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
    c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); X, Y, _, idx, vx, 이, Xnp = G.자료("cuda", c); y = G.자르기(Y, vx)
    n = A.불러(판).cuda(); o = G.예측(n, X[vx])[:, :, :6].float(); pr = o[:, :, :4].softmax(2)
    종 = (pr[:, :, 1:3].argmax(2) + 1).cpu().numpy(); 있 = (1 - pr[:, :, 0] > .5).cpu().numpy(); 지 = y["지도"].cpu().numpy()   # 직선 · 곡선 둘 중 무엇으로 읽었나
    시험 = {이[int(j)]: k for k, j in enumerate(vx.tolist())}; 셈 = {t: [0, 0] for t in range(5)}; 예시 = {t: None for t in range(5)}
    for f in sorted(os.listdir(저장)):
        if not f.endswith(".npz") or f[:5] not in 시험: continue
        z = np.load(저장 + f); k = 시험[f[:5]]
        for v in range(3):
            u = 유형지도(z, v)
            for t in range(5):
                m = (u == t) & 있[k, v] & np.isin(지[k, v], (1, 2))   # 모델이 선이라 읽고 정답이 직선 · 곡선인 화소
                if not m.any(): continue
                틀 = m & (종[k, v] != 지[k, v]); 셈[t][0] += int(m.sum()); 셈[t][1] += int(틀.sum())
                if 예시[t] is None and t >= 2 and 틀.sum() >= 3: yy, xx = np.argwhere(틀)[len(np.argwhere(틀)) // 2]; 예시[t] = (k, v, yy, xx)
                if 예시[t] is None and t < 2 and m.sum() >= 20: yy, xx = np.argwhere(m)[len(np.argwhere(m)) // 2]; 예시[t] = (k, v, yy, xx)
    for t in range(5): print(유형[t], "화소", 셈[t][0], "틀림", round(셈[t][1] / max(셈[t][0], 1), 3))
    색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8)
    줄 = [t for t in (0, 2, 3, 4) if 예시[t]]
    fig = plt.figure(figsize=(26, 7.2 * len(줄) + 6)); H_ = 1 / (len(줄) + .9)
    fig.suptitle(f"겹침 유형별 — 화소 하나가 직선 / 곡선으로 판정되기까지 (판 {판})", fontsize=22, weight="bold")
    for r, t in enumerate(줄):
        k, v, yy, xx = 예시[t]; x1 = X[vx][k:k + 1]
        with torch.no_grad(): fs = K.펼침(n, x1)
        y0 = int(np.clip(yy - 48, 0, 32)); x0 = int(np.clip(xx - 48, 0, 32)); 창 = (slice(y0, y0 + 96), slice(x0, x0 + 96)); 바닥 = 1 - H_ * (r + 1) - .02
        ax = fig.add_axes([.01, 바닥, .14, H_ * .78]); ax.imshow(255 - Xnp[int(vx[k]), v][창], cmap="gray", interpolation="nearest")
        for kk, ck in ((1, "#e33"), (2, "#e90"), (3, "#3a3"), (4, "#36c")): h = K.수용[kk]; ax.add_patch(plt.Rectangle((xx - x0 - h / 2, yy - y0 - h / 2), h, h, fill=False, ec=ck, lw=2))
        정 = int(지[k, v, yy, xx]); 읽 = int(종[k, v, yy, xx])
        ax.plot(xx - x0, yy - y0, "o", ms=9, mec="k", mfc="#ff0"); ax.set_title(f"【{유형[t]}】 부품 {이[int(vx[k])]}\n정답 {('', '직선', '곡선')[정]} · 모델 {('', '직선', '곡선')[읽]} {'(맞음)' if 정 == 읽 else '(틀림)'}", fontsize=14); ax.axis("off")
        for j, (im, tt) in enumerate(((색[지[k, v]][창], "정답"), (색[np.where(있[k, v], 종[k, v], 0)][창], "모델(직선 · 곡선만)"))):
            ax = fig.add_axes([.155 + j * .105, 바닥, .1, H_ * .78]); ax.imshow(im, interpolation="nearest"); ax.plot(xx - x0, yy - y0, "o", ms=8, mec="k", mfc="#ff0"); ax.set_title(tt, fontsize=13); ax.axis("off")
        for j, kk in enumerate((1, 2, 3, 4)):
            f = fs[kk - 1][v].detach().cpu().numpy(); s = 128 // f.shape[1]; 작 = (slice(y0 // s, (y0 + 96) // s), slice(x0 // s, (x0 + 96) // s))
            ax = fig.add_axes([.37 + j * .105, 바닥, .1, H_ * .78]); ax.imshow(np.kron(K.주성분(f[:, 작[0], 작[1]], None), np.ones((s, s, 1))), interpolation="nearest")
            ax.plot(xx - x0, yy - y0, "o", ms=8, mec="k", mfc="#ff0"); ax.set_title(K.층이름[kk], fontsize=11); ax.axis("off")
        m = K.몫(n, fs, v, yy, xx); 바른 = ("", "직선", "곡선")[정]; 다른 = ("", "곡선", "직선")[정]
        값 = [m[바른][kk] - m[다른][kk] for kk in (1, 2, 3, 4)]
        ax = fig.add_axes([.81, 바닥 + H_ * .08, .17, H_ * .62]); ax.barh(["블록 1", "블록 2", "블록 3", "블록 4"], 값, color=["#3a3" if q > 0 else "#e33" for q in 값]); ax.axvline(0, color="k", lw=1); ax.invert_yaxis()
        ax.set_title(f"정답({바른}) 쪽으로 민 몫 · 합 {sum(값):+.1f}\n오른쪽(초록) = 맞는 쪽 · 왼쪽(빨강) = 틀린 쪽", fontsize=11)
    ax = fig.add_axes([.06, .02, .5, H_ * .6]); 이름 = [유형[t] for t in range(5)]; 율 = [셈[t][1] / max(셈[t][0], 1) for t in range(5)]
    ax.bar(이름, 율, color=["#9ab", "#9ab", "#36c", "#e33", "#3a3"]); [ax.text(i_, 율[i_] + .01, f"{율[i_]:.2f}\n({셈[i_][0]:,} 화소)", ha="center", fontsize=12) for i_ in range(5)]
    ax.set_ylim(0, max(율) * 1.35 + .02); ax.set_title("겹침 유형별 — 선 화소를 다른 종류로 읽은 비율(시험 부품 · 꼭짓점 3 화소 안 뺌)", fontsize=15); ax.tick_params(labelsize=13)
    p = f"{뿌리}/out/하네스/{판}/겹침유형.png"; fig.savefig(p, dpi=55, bbox_inches="tight"); plt.close(fig); print(p); return 셈
if __name__ == "__main__":
    if sys.argv[1] == "모서리": 모서리들(int(sys.argv[2]) if len(sys.argv) > 2 else 80)
    else: 그림(*(sys.argv[2:3]))
