# 88 편 위쪽 카드 재료 — 124 실제 렌더: 뭉침 짝 · 에폭 과정 · 본/처음 점수 · 몸 수별 점수 · 학습 부품 8 짝 · 10-22
# 사용(cadrille venv): python 재료.py
import sys, os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품"); os.chdir("G:/art2real/원화3d/실험_20261013/캐드부품")
import 모델124 as B, 모델120 as M
A = "G:/art2real/out/영상05/대화/88_자리/자료/"; os.makedirs(A, exist_ok=True)
진, 빨, 초 = "#6b7078", "#d8262b", "#28a050"
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
def 글판(fig): ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); return ax
def 짝판(짝들, nm, 왼="정답", 오="모델 답", 열=2, 아래=None):
    fig = 판(); 행 = (len(짝들) + 열 - 1) // 열; h = .86 / 행
    for i, (a, b) in enumerate(짝들):
        x0 = .01 + (i % 열) * (.97 / 열); y0 = .88 - (i // 열 + 1) * h
        for j, im in enumerate((a, b)):
            if im is not None: ax = fig.add_axes([x0 + j * (.485 / 열), y0, .485 / 열 - .01, h - .02]); ax.imshow(im); ax.axis("off")
    ax = 글판(fig)
    for c in range(열): ax.text(.01 + c / 열 + .25 / 열, .93, 왼, fontsize=24, color=진, ha="center"); ax.text(.01 + c / 열 + .75 / 열, .93, 오, fontsize=24, color=빨, ha="center")
    if 아래: ax.text(.5, .02, 아래, fontsize=26, color=빨, ha="center")
    저장(fig, nm)
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"
    확 = json.load(open(B.D + "확인124.json", encoding="utf-8")); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    net = B.망(); net.load_state_dict(torch.load(B.D + "머리.pt")); net.eval(); z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"])
    def 짝들(ns):
        with torch.no_grad(): o = net(torch.tensor(z["E"][[이.index(n) for n in ns]]).reshape(len(ns), -1)).reshape(-1, 6, B.W).numpy()
        g = B.병렬렌더([("조립", 색[n]["코드"]) for n in ns]); p = B.병렬렌더([("자리", B.사양(a)) for a in o])
        return [(a and a[0], b and b[0]) for a, b in zip(g, p)]
    # 뭉침 — 시험 부품(처음 보는 것) 덩어리 5 · 6 개 둘(12032 0.46 · 12047 0.37)
    뭉 = 짝들(["12032", "12047"]); 짝판(뭉, "뭉침.png", 열=1)
    # 에폭 과정 — 고정 시험 3 개 × (1 · 11 · 60 에폭 · 정답)
    j = json.load(open(B.D + "학습.json", encoding="utf-8")); 고 = [0, 2, 4]; 열들 = [("1 에폭", "과정_01_{t}"), ("11 에폭", "과정_11_{t}"), ("60 에폭", "과정_60_{t}"), ("정답", None)]
    fig = 판()
    for r, t in enumerate(고):
        for c, (_, f) in enumerate(열들):
            p = B.D + "렌더/" + (f.format(t=t) if f else f"{j['고정'][t]}_정답") + ".png"
            if os.path.exists(p): ax = fig.add_axes([.01 + c * .25, .6 - r * .29, .23, .27]); ax.imshow(M.읽(p)); ax.axis("off")
    ax = 글판(fig)
    for c, (이름, _) in enumerate(열들): ax.text(.125 + c * .25, .91, 이름, fontsize=26, color=초 if c == 2 else 진, ha="center")
    저장(fig, "과정.png")
    # 본 것 / 처음 본 것
    fig = 판(); ax = 글판(fig); 학, 시 = 확["학습"]["IoU 중앙"], 확["시험"]["IoU 중앙"]
    ax.text(.27, .55, f"{학:.2f}", fontsize=110, color=빨, ha="center", va="center"); ax.text(.27, .22, "학습 때 본 부품", fontsize=32, color=진, ha="center")
    ax.text(.73, .55, f"{시:.2f}", fontsize=110, color=빨, ha="center", va="center"); ax.text(.73, .22, "처음 보는 부품", fontsize=32, color=진, ha="center"); 저장(fig, "본것.png")
    # 몸 수별(학습 부품)
    fig = 판(); ax = 글판(fig); 하, 여 = 확["학습"]["몸 1 IoU 중앙"], 확["학습"]["몸 2+ IoU 중앙"]
    ax.text(.27, .55, f"{하:.2f}", fontsize=110, color=초, ha="center", va="center"); ax.text(.27, .22, "덩어리 하나", fontsize=34, color=진, ha="center")
    ax.text(.73, .55, f"{여:.2f}", fontsize=110, color=빨, ha="center", va="center"); ax.text(.73, .22, "둘 이상", fontsize=34, color=진, ha="center"); 저장(fig, "몸수.png")
    # 단순한 부품 — 전 모델(123b) 대 이번(124) · 결과.json
    요 = json.load(open(B.D + "결과.json", encoding="utf-8"))["요약"]; fig = 판(); ax = 글판(fig); ax.text(.5, .86, "단순한 부품 200", fontsize=34, color=진, ha="center")
    ax.text(.27, .5, f"{요['단순 시험 123b']:.2f}", fontsize=110, color=초, ha="center", va="center"); ax.text(.27, .18, "전 모델", fontsize=34, color=진, ha="center")
    ax.text(.73, .5, f"{요['단순 시험 124']:.2f}", fontsize=110, color=빨, ha="center", va="center"); ax.text(.73, .18, "이번 모델", fontsize=34, color=진, ha="center")
    ax.annotate("", xy=(.56, .5), xytext=(.44, .5), arrowprops=dict(arrowstyle="-|>", color="#333", lw=5)); 저장(fig, "잊음.png")
    # 학습 부품 4 짝 — IoU 고루
    후 = sorted([(i, n) for n, i in zip(확["학습"]["이름"], 확["학습"]["IoU"]) if len(색[n]["코드"]["몸"]) > 1 and i > 0])
    고른 = [후[int(k)][1] for k in np.linspace(0, len(후) - 1, 4)]; 짝판(짝들(고른), "본부품.png", 열=2)
    print("저장", 학, 시, 하, 여, 고른)
