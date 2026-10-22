# 분석 칸 그림 — 부품 하나를 크게: 입력 · 정답 · 이 판 · 대조 판(선지도 판) · 폰에서 보이게 · 10-22 (research_읽히는블로그: 그림 하나 = 메시지 하나)
# 사용(cadrille): python 하네스/분석그림.py <판> [대조판] [부품 12050] → 하네스/판/<판>/비교.png
import os, sys, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
def 불러(판):
    import torch, 과제선지도 as G
    from omegaconf import OmegaConf
    c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); s = c.get("선지도", {})
    n = G.망(c.인코더, 탐침=bool(s.get("탐침층", False)), 합침=str(s.get("합침", "없음")))
    n.load_state_dict(torch.load(f"{뿌리}/out/하네스/{판}/점검/{c.학습.에폭:02d}.pt", weights_only=False)); return n.eval()
def 칠(o):   # (6, 128, 128) → RGB · 「선이냐 먼저 · 종류는 다음」 읽기
    import torch
    색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8)
    pr = o[:4].float().softmax(0); 지 = torch.where(1 - pr[0] > .5, pr[1:].argmax(0) + 1, 0).numpy(); rgb = 색[지].astype(float)
    a = torch.sigmoid(o[5].float()).numpy().clip(0, 1)[..., None] * .8; return (rgb * (1 - a) + np.array([216, 38, 43]) * a).astype(np.uint8)
def 비교(판, 대조판=None, 부품="12050", 뷰=1):
    import torch, 과제선지도 as G, 하네스 as H, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; z = np.load(H.M7.D + "그림.npz"); 이 = list(z["이름"]); x = z["X"][이.index(부품)]
    d = np.load(f"{뿌리}/out/하네스/선정답/{부품}.npz"); 정 = G.맞춤(x, d["지도"])[뷰]; 열 = G.열지도(d["점"][None])[0, 뷰].astype(float)
    색 = np.array([[255, 255, 255], [74, 123, 209], [40, 160, 80], [217, 160, 32]], np.uint8); 정rgb = (색[정] * (1 - 열[..., None] * .8) + np.array([216, 38, 43]) * 열[..., None] * .8).astype(np.uint8)
    칸 = [(255 - x[뷰], "입력 도면"), (정rgb, "정답")]
    with torch.no_grad():
        for p, 말 in ((판, f"이 판 ({판})"), (대조판, f"대조 ({대조판})")):
            if p: 칸.append((칠(불러(p)(torch.tensor(x[None]))[0, 뷰, :6]), 말))
    fig, ax = plt.subplots(1, len(칸), figsize=(4.2 * len(칸), 4.9))
    for a, (im, t) in zip(ax, 칸): a.imshow(im, cmap="gray" if im.ndim == 2 else None, interpolation="nearest"); a.set_title(t, fontsize=19, weight="bold"); a.axis("off")
    fig.text(.5, .02, "파랑 직선 · 초록 곡선 · 노랑 곡면 테두리 · 빨강 꼭짓점", ha="center", fontsize=15)
    p = f"{뿌리}/하네스/판/{판}/비교.png"; fig.savefig(p, dpi=70, bbox_inches="tight"); plt.close(fig); return p
if __name__ == "__main__": print(비교(sys.argv[1], *(sys.argv[2:4])))
