# 코드생성 판의 바퀴별 곡선 — 학습 중 정해진 스텝마다: 학습 · 시험 토큰 맞음 · 시험 부품 일부 부피 IoU · 도면 몫(남의 선 글 CE − 제 선 글 CE)
# 11-05 사용자 「그거를 안본게 문제인거지 epoch마다 어떻게 바뀌는건지?」 · 147~164 는 학습 끝 점 하나만 비교 → 「손잡이 나쁨」과 「덜 배움」을 못 갈랐다
# 과제코드.점검 이 부름(학습.곡선 = 간격 스텝 · 0 이면 끔) → 곡선.json · 곡선.png(보고서 칸)
import os, sys, json
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
def 합(칸):   # 코드배움.재기 결과 {칸: {수, 맞음, CE}} → 전체 맞음 · CE(토큰 수 가중)
    n = sum(v["수"] for v in 칸.values()) or 1
    return sum(v["수"] * v["맞음"] for v in 칸.values()) / n, sum(v["수"] * v["CE"] for v in 칸.values()) / n
def 재기(model, proc, 학, 시, 입력, 제약=False, N=40, M=20):   # 학 · 시 = [(부품, 선 글, 정답 글)]
    import numpy as np, 코드배움, 과제코드 as K
    학맞, _ = 합(코드배움.재기(model, proc, 학[:N], 입력)); 시맞, 시CE = 합(코드배움.재기(model, proc, 시[:N], 입력))
    남 = [(n, 시[(i + 1) % N][1], g) for i, (n, _, g) in enumerate(시[:N])]   # 바로 다음 부품의 선 글을 넣음(정답 글은 그대로)
    _, 남CE = 합(코드배움.재기(model, proc, 남, 입력))
    글들 = K.생성(model, proc, [K.항목(n, l, g, 입력, 정답=False) for n, l, g in 시[:M]], 제약=제약)
    줄, _, _ = K.평가([n for n, _, _ in 시[:M]], 글들, 일꾼=2); 쓸 = [r for r in 줄 if not r["OOM"] and not r["정답실패"]]
    model.train()
    return {"학습맞음": round(학맞, 4), "시험맞음": round(시맞, 4), "도면몫": round(남CE - 시CE, 4), "부피IoU": round(float(np.median([r["부피IoU"] for r in 쓸])), 4) if 쓸 else None,
            "실행률": round(float(np.mean([r["실행"] for r in 쓸])), 4) if 쓸 else None, "부품수": {"맞음": N, "IoU": M}}
def 그림(폴더, 곡, 바퀴스텝):   # 곡 = [{"스텝", ...}] → 곡선.png · 가로축 = 바퀴(스텝 / 학습 부품 수)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; x = [r["스텝"] / 바퀴스텝 for r in 곡]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    ax[0].plot(x, [r["학습맞음"] for r in 곡], "o-", label="학습 부품"); ax[0].plot(x, [r["시험맞음"] for r in 곡], "o-", label="처음 보는 부품"); ax[0].set_title("토큰 맞음 — 벌어지면 외우기 시작", fontsize=13); ax[0].legend()
    ax[1].plot(x, [r["부피IoU"] for r in 곡], "o-", color="#27ae60"); ax[1].axhline(.15, ls=":", color="#999"); ax[1].axhline(.35, ls="--", color="#e67e22"); ax[1].set_title(f"처음 보는 부품 {곡[0]['부품수']['IoU']} 개 부피 IoU · 점선 바닥 0.15 · 다음 계단 0.35", fontsize=12)
    ax[2].plot(x, [r["도면몫"] for r in 곡], "o-", color="#8e44ad"); ax[2].set_title("도면 몫 — 남의 도면이면 loss 가 얼마나 나빠지나", fontsize=12)
    for a in ax: a.set_xlabel("바퀴 (학습 부품을 본 횟수)"); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(폴더 + "곡선.png", dpi=70); plt.close(fig)
if __name__ == "__main__":   # 자체 시험: 합 · 그림
    a, c = 합({"나머지": {"수": 3, "맞음": 1.0, "CE": 0.0}, "x": {"수": 1, "맞음": 0.0, "CE": 4.0}}); assert (a, c) == (0.75, 1.0), (a, c)
    import tempfile; d = tempfile.mkdtemp() + "/"
    그림(d, [{"스텝": s, "학습맞음": .8 + s / 1e4, "시험맞음": .8, "도면몫": .05, "부피IoU": .2, "부품수": {"IoU": 20}} for s in (750, 1500)], 3000); assert os.path.exists(d + "곡선.png")
    print("코드곡선 시험 통과")
