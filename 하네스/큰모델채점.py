# 큰 모델 시험 채점 — 같은 시험 부품 20 개 · 새 자(부피 IoU) · 한 번에 쓰기 / 도구 사용 / 우리 154 · 152 LoRA / 바닥(원기둥)
# 10-30 사용자 「성능 좋은 거면 성능 좋은 거 쓰면 끝나는 거 아니야?」 — BenchCAD(렌더 → CAD 코드 · 복셀 IoU)에서 큰 모델 한 번 60~73 · 도구 92~96
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
if __name__ == "__main__":
    import 모델124 as B, 데이터117 as Q, 재채점
    D = 뿌리 + "/out/하네스/"; T = D + "큰모델시험/"; 부품 = json.load(open(T + "부품.json")); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    팔 = {"큰 모델 · 한 번": T + "한번/{}.py", "큰 모델 · 도구": T + "도구/{}.py", "154 LoRA": D + "154MLP포함/생성/{}.py", "152 LoRA": D + "152오래학습/생성/{}.py"}
    글 = lambda p: open(p, encoding="utf-8").read() if os.path.exists(p) else "result = None"
    잡 = [("조립", 색[n]["코드"], 1) for n in 부품] + [("글", 재채점.바닥["원기둥"], 1)] + [("글", 글(p.format(n)), 1) for p in 팔.values() for n in 부품]
    렌 = B.병렬렌더(잡); 부 = lambda r: None if r is None else r[2]; k = len(부품)
    assert all(r is not None for r in 렌[:k]), "정답 렌더 실패"
    표 = {"원기둥 하나(바닥)": [Q.부피겹(부(렌[k]), 부(렌[t])) for t in range(k)]}
    for j, 이름 in enumerate(팔): 표[이름] = [Q.부피겹(부(렌[k + 1 + j * k + t]), 부(렌[t])) for t in range(k)]
    결 = {이름: {"중앙": round(float(np.median(v)), 3), "평균": round(float(np.mean(v)), 3), "실행": sum(x > 0 for x in v), "부품": dict(zip(부품, [round(x, 3) for x in v]))} for 이름, v in 표.items()}
    json.dump(결, open(T + "채점.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for 이름, r in 결.items(): print(f"{이름:12s} 중앙 {r['중앙']:.3f} · 평균 {r['평균']:.3f} · 실행 {r['실행']}/{k}")
    print("부품별:", " ".join(부품)); [print(f"{이름:12s}", " ".join(f"{x:.2f}" for x in r["부품"].values())) for 이름, r in 결.items()]
