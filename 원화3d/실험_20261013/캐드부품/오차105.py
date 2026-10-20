# 판0 틀림은 몇 층 틀림인가 — 시험 300 · 영역별 |예측 − 정답| 분포 · 손실 중 1 층 이내 틀림 몫 · 학습 300 도 · 10-20
# 사용(venv · ART_MEM_GB=10): 오차105.py → out/설명/캐드부품/손실103/오차.json
import json, numpy as np, 손실103 as L
K = 32; 칸 = [(0, 0), (1, 1), (2, 2), (3, 5), (6, 33)]
결 = {}
for 꼴, 부품 in (("시험", L.부[L.시][:300]), ("학습", L.tr[:300])):
    s = {}
    for i in 부품:
        l, p = L.손실(i); g = np.array(L.층[i]).astype(int); sh = np.array(L.껍32[i]).astype(int); 안 = np.array(L.입[i][:, 1]) > 0; e = np.abs(p.astype(int) - g)
        for 이름, m in (("안 전체(깊이 있음)", 안 & (g < K)), ("껍질 그대로", 안 & (g < K) & (g <= sh)), ("깎인 속", 안 & (g < K) & (g >= sh + 2))):
            a = s.setdefault(이름, np.zeros((len(칸), 2)))
            for j, (lo, hi) in enumerate(칸): mm = m & (e >= lo) & (e <= hi); a[j] += [mm.sum(), l[mm].sum()]
    결[꼴] = {k: {f"{lo}~{hi} 층 틀림": {"화소 몫": round(v[j, 0] / v[:, 0].sum(), 3), "손실 몫": round(v[j, 1] / v[:, 1].sum(), 3)} for j, (lo, hi) in enumerate(칸)} for k, v in s.items()}
print(json.dumps(결, ensure_ascii=False, indent=1)); json.dump(결, open(L.D + "오차.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
