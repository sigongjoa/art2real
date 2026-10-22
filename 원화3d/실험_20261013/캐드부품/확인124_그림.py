# 확인124 그림 — 학습 부품(본 것) 중 몸 2+ 8 개: 정답 | 124 예측 · IoU 낮음→높음 고루 · 10-22
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델124 as B
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"
    d = json.load(open(B.D + "확인124.json", encoding="utf-8"))["학습"]; 색 = {f"{r['i']:05d}": r for r in B.색인()}
    후 = sorted([(i, n) for n, i in zip(d["이름"], d["IoU"]) if len(색[n]["코드"]["몸"]) > 1])
    고 = [후[int(k)] for k in np.linspace(0, len(후) - 1, 8)]
    net = B.망(); net.load_state_dict(torch.load(B.D + "머리.pt")); net.eval(); z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"])
    with torch.no_grad(): o = net(torch.tensor(z["E"][[이.index(n) for _, n in 고]]).reshape(len(고), -1)).reshape(-1, 6, B.W).numpy()
    정 = B.병렬렌더([("조립", 색[n]["코드"]) for _, n in 고]); 예 = B.병렬렌더([("자리", B.사양(a)) for a in o])
    fig, ax = plt.subplots(2, 8, figsize=(24, 7))
    for t, ((i, n), g, p) in enumerate(zip(고, 정, 예)):
        for r, x, 글 in ((0, g, f"{n} 정답 · 몸 {len(색[n]['코드']['몸'])}"), (1, p, f"124 예측 · IoU {i:.2f}")):
            if x is not None: ax[r, t].imshow(x[0])
            ax[r, t].set_title(글, fontsize=13); ax[r, t].axis("off")
    fig.suptitle("확인124 — 학습한 부품(본 것)인데도 몸 붙는 자리가 틀림 · 학습 0.669 / 시험 0.638 · 몸 1 개는 0.94", fontsize=17)
    fig.tight_layout(); fig.savefig(B.D + "그림_확인124.png", dpi=60); print("끝")
