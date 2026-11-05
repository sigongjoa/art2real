# 학습 중 스텝별 생성 모양 한 장 — 행 = 입력 · 정답 · 스텝들, 열 = 고정 시험 부품(검증/<스텝>_<부품>.py)
# 11-05 사용자 「수치적으로는 확인하기 어려우니깐 실제로 생성된 이미지를 원한다」 · 학습 중에도 따로 돌려 볼 수 있음(렌더는 CPU)
# 사용: python 하네스/단계모양.py <판> [스텝 …]   (스텝을 안 주면 있는 것 중 고르게 6 개) → out/하네스/<판>/단계모양.png
import sys, os, glob, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
def 고르기(있는, k=6):   # 스텝 목록에서 처음 · 끝 포함 고르게 k 개
    if len(있는) <= k: return 있는
    return sorted({있는[round(i * (len(있는) - 1) / (k - 1))] for i in range(k)})
def 그리기(판, 스텝들=None):
    import 과제코드 as K, 모델124 as B, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; 폴 = f"{뿌리}/out/하네스/{판}/"; 파 = glob.glob(폴 + "검증/*.py")
    부품 = sorted({os.path.basename(f)[6:-3] for f in 파}, key=lambda n: (n != "12050", n)); 있는 = sorted({int(os.path.basename(f)[:5]) for f in 파})
    스텝들 = 스텝들 or 고르기(있는); 색 = {f"{r['i']:05d}": r for r in B.색인()}; k = len(부품)
    잡 = [("조립", 색[n]["코드"], 1) for n in 부품] + [("글", open(폴 + f"검증/{s:05d}_{n}.py", encoding="utf-8").read() if os.path.exists(폴 + f"검증/{s:05d}_{n}.py") else "", 1) for s in 스텝들 for n in 부품]
    렌 = B.병렬렌더(잡, n=2); 줄 = 2 + len(스텝들)
    fig, ax = plt.subplots(줄, k, figsize=(k * 3 + 1.5, 줄 * 2.8), squeeze=False)
    for j, n in enumerate(부품):
        ax[0, j].imshow(np.asarray(K.도면그림(n)), cmap="gray"); ax[0, j].set_title(n, fontsize=12)
        ax[1, j].imshow(np.asarray(렌[j][0])) if 렌[j] else None
        for i, s in enumerate(스텝들):
            r = 렌[k * (i + 1) + j]; a = ax[2 + i, j]
            if r is None: a.text(.5, .5, "X 실행 안 됨", ha="center", va="center", fontsize=14, color="#c0392b", transform=a.transAxes)
            else: a.imshow(np.asarray(r[0]))
    for a in ax.flat: a.axis("off")
    for i, t in enumerate(["입력", "정답"] + [f"{s:,} 스텝" for s in 스텝들]): ax[i, 0].text(-.08, .5, t, ha="right", va="center", fontsize=14, weight="bold", color="#1e8449" if i == 1 else "#222", transform=ax[i, 0].transAxes)
    fig.suptitle(f"판 {판} — 학습하면서 생성 모양이 어떻게 바뀌나 (처음 보는 부품 {k} 개)", fontsize=16, weight="bold")
    fig.tight_layout(rect=(.1, 0, 1, .96)); p = 폴 + "단계모양.png"; fig.savefig(p, dpi=65); plt.close(fig); return p
if __name__ == "__main__":
    assert 고르기([0, 250, 500, 750, 1000, 1250, 1500], 4) == [0, 500, 1000, 1500] and 고르기([0, 250], 6) == [0, 250]
    print(그리기(sys.argv[1], [int(x) for x in sys.argv[2:]] or None))
