# 확인124 — 124 머리가 학습 부품(본 것)도 못 맞히는가 · 시험과 같은 자(3/4 실루엣 IoU) · 학습 없음 · 10-22
# 미리 적은 읽기: 학습 300 IoU 중앙 < 0.75 → 학습 부품도 못 맞춤(입력 표현 · 머리 쪽) · ≥ 0.85 → 외움은 됨(일반화 쪽) · 그 사이 = 둘 다
# 같이: 몸 칸별 자리 오차(L1 · 크기 비) · 몸 수 맞음 — 학습 300 대 시험 300 · 렌더 없이
# 사용: (cadrille) 확인124.py → out/설명/캐드부품/모델124/확인124.json
import json, numpy as np
import 모델124 as B, 조립124 as C
if __name__ == "__main__":   # torch 는 여기서만 — 맨 위에 두면 일꾼 6 개가 다 불러 10 GB 상한을 넘김(10-22 MemoryError 0 점 359 개)
    import torch
    net = B.망(); net.load_state_dict(torch.load(B.D + "머리.pt")); net.eval()
    z = np.load(B.D + "임베딩.npz"); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 이 = list(z["이름"])
    학 = [n for n in 이 if int(n) < B.NT][::40][:300]; 시 = [n for n in 이 if int(n) >= B.NT]
    결 = {}
    for 이름, ns in (("학습", 학), ("시험", 시)):
        with torch.no_grad(): o = net(torch.tensor(z["E"][[이.index(n) for n in ns]]).reshape(len(ns), -1)).reshape(-1, C.K, B.W).numpy()
        Y = np.stack([B.과녁(색[n])[0] for n in ns]); 있 = Y[..., 0] > 0
        자리 = np.abs(o[..., 20:23] - Y[..., 20:23]).sum(-1)[있]; 종 = (o[..., 1:8].argmax(-1) == Y[..., 1:8].argmax(-1))[있]
        몸1 = 있.sum(1) == 1; 줄 = []
        for n, r in zip(ns, B.병렬렌더([("조립", 색[n]["코드"]) for n in ns])): 줄.append(r)
        예 = B.병렬렌더([("자리", B.사양(a)) for a in o])
        assert sum(g is None for g in 줄) <= 5, f"정답 렌더 실패 {sum(g is None for g in 줄)} — 일꾼 문제부터"
        iou = [0. if g is None or p is None else float((g[1] & p[1]).sum() / max((g[1] | p[1]).sum(), 1)) for g, p in zip(줄, 예)]
        결[이름] = {"IoU 중앙": round(float(np.median(iou)), 4), "몸 1 IoU 중앙": round(float(np.median(np.array(iou)[몸1])), 4),
                   "몸 2+ IoU 중앙": round(float(np.median(np.array(iou)[~몸1])), 4), "몸 수 맞음": float(np.mean((o[..., 0] > 0).sum(1) == 있.sum(1))),
                   "자리 오차 중앙(크기 비)": round(float(np.median(자리)), 4), "몸 종류 맞음": round(float(종.mean()), 4), "IoU": [round(x, 4) for x in iou], "이름": ns}
        print(이름, {k: v for k, v in 결[이름].items() if k not in ("IoU", "이름")}, flush=True)
    json.dump(결, open(B.D + "확인124.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
