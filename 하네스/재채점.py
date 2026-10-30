# 새 자(부피 IoU)로 지난 코드생성 판 다시 재기 — 학습 · 생성 없이 생성/ 의 글만 · 10-30 사용자 「수치는 볼 것도 없고 그냥 개판」
# 옛 자(한 각도 실루엣 · 각자 정규화)는 같은 모양 하나만 내도 0.34~0.41 → 145~155 의 0.48~0.53 이 바닥 위 0.1 이었음
# 자 검사: 바닥(모든 부품에 같은 모양 하나) · 사다리(위치만 정답 · 모양식만 정답 · 둘 다 정답 → 둘 다 ≈ 1 · 중간은 중간이어야)
# 사용: python 재채점.py 145선글코드 … 155도면좌표 → out/하네스/<판>/[시드n/]부피.json · out/하네스/재채점.json
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
바닥 = {"정육면체": 'b0 = place(cq.Workplane("XY").box(60.0, 60.0, 60.0, centered=(True, True, False)), "z", (0.0, 0.0, 0.0))\nresult = b0',
       "원기둥": 'b0 = place(cq.Workplane("XY").circle(30.0).extrude(60.0), "z", (0.0, 0.0, 0.0))\nresult = b0',
       "납작판": 'b0 = place(cq.Workplane("XY").box(100.0, 60.0, 4.0, centered=(True, True, False)), "z", (0.0, 0.0, 0.0))\nresult = b0'}
def 중(v): return round(float(np.median(v)), 4) if len(v) else None
if __name__ == "__main__":
    import 모델124 as B, 데이터117 as Q, 코드원인 as R
    from omegaconf import OmegaConf
    판들 = sys.argv[1:]; D = 뿌리 + "/out/하네스/"; 색 = {f"{r['i']:05d}": r for r in B.색인()}
    폴더들 = [(판, s, D + 판 + "/" + s) for 판 in 판들 for s in ("", "시드1/", "시드2/") if os.path.exists(D + 판 + "/" + s + "평가.json")]
    이름 = [r["부품"] for r in json.load(open(폴더들[0][2] + "평가.json", encoding="utf-8"))]
    잡 = [("조립", 색[n]["코드"], 1) for n in 이름] + [("글", g, 1) for g in 바닥.values()]; 자리 = {}
    for 판, s, f in 폴더들:
        설 = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml") if os.path.exists(f"{뿌리}/하네스/판/{판}/설정.yaml") else None
        정폴 = D + "코드자료/" + ("글도면/" if 설 is not None and str(설.get("코드", {}).get("좌표계", "mm")) == "도면" else "글/")
        for n in 이름:
            g = open(f + f"생성/{n}.py", encoding="utf-8").read(); 자리[(판, s, n, "생성")] = len(잡); 잡.append(("글", g, 1))
            a, b = R.몸들(g), R.몸들(open(정폴 + f"{n}.py", encoding="utf-8").read())
            if a and b and len(a) == len(b):   # 사다리(원인 쪼개기와 같은 바꿔 끼우기) — 자가 중간을 중간으로 재나
                for k, 몸 in (("위치만정답", [(x[1], y[2], y[3]) for x, y in zip(a, b)]), ("모양만정답", [(y[1], x[2], x[3]) for x, y in zip(a, b)]), ("둘다정답", [(y[1], y[2], y[3]) for y in b])):
                    자리[(판, s, n, k)] = len(잡); 잡.append(("글", R.글(몸), 1))
    print("잡", len(잡), flush=True); 렌 = B.병렬렌더(잡); 부 = [None if r is None else r[2] for r in 렌]
    정 = {n: 부[i] for i, n in enumerate(이름)}; 쓸 = [n for n in 이름 if 정[n] is not None]
    assert len(쓸) == len(이름), f"정답 부피 실패 {len(이름) - len(쓸)}"
    바 = {k: 중([Q.부피겹(부[len(이름) + j], 정[n]) for n in 쓸]) for j, k in enumerate(바닥)}
    표 = {"바닥": 바, "판": {}}; print("바닥(모든 부품에 같은 모양 하나):", 바, flush=True)
    for 판, s, f in 폴더들:
        평 = {r["부품"]: r for r in json.load(open(f + "평가.json", encoding="utf-8"))}
        줄 = {n: {"부피IoU": Q.부피겹(부[자리[(판, s, n, "생성")]], 정[n]), "옛IoU": 평[n]["IoU"]} for n in 쓸}
        같 = [n for n in 쓸 if (판, s, n, "둘다정답") in 자리 and 부[자리[(판, s, n, "생성")]] is not None]
        사 = {k: 중([Q.부피겹(부[자리[(판, s, n, k)]], 정[n]) for n in 같]) for k in ("위치만정답", "모양만정답", "둘다정답")} | {"생성그대로": 중([줄[n]["부피IoU"] for n in 같]), "개수같은수": len(같)}
        요 = {"부피IoU": 중([z["부피IoU"] for z in 줄.values()]), "옛IoU": 중([z["옛IoU"] for z in 줄.values()]), "사다리": 사}
        json.dump({"요약": 요, "부품": 줄}, open(f + "부피.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        표["판"][판 + ("·" + s.strip("/") if s else "")] = 요; print(판, s or "시드0", 요, flush=True)
    json.dump(표, open(D + "재채점.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
