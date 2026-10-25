# 코드생성 판의 원인 쪼개기 — 실행된 생성 코드의 IoU 를 무엇이 깎나(학습 없음 · 판마다 점검 끝에서 자동)
# 몸 개수(모자람 · 같음 · 넘침) + 개수가 같은 것만 몸을 순서로 짝지어 바꿔 끼우기 사다리: 생성 그대로 → 위치(축 · 자리)만 정답 → 모양식만 정답 → 둘 다 정답(= 채점기 확인 · ≈ 1)
# 10-25 사용자 「스크립트로 잰 것도 하네스에 포함」 · 처음 잰 값(147): 몸 개수 맞음 39 % · 개수 같은 99 개 0.54 → 위치만 0.70 · 모양식만 0.55 · 둘 다 1.00
import os, sys, re, ast, json, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
정답폴더 = 뿌리 + "/out/하네스/코드자료/글/"   # 정답 글은 늘 기존 서식(place)으로 읽음
P = re.compile(r'^(b\d+) = place\((.*), "(\w)", \(([^()]*)\)\)$')
def 기존화(글):   # 배치먼저(layout + at(i, 식)) → place 서식 · 못 풀면 그대로(파싱에서 빠짐)
    if not 글.startswith("layout = "): return 글
    첫, _, 나머지 = 글.partition("\n")
    try: 배 = ast.literal_eval(첫[len("layout = "):])
    except Exception: return 글
    def 바꿈(m):
        i = int(m.group(2))
        if i >= len(배) or len(배[i]) < 3: return m.group(0)
        return f'{m.group(1)} = place({m.group(3)}, "{배[i][1]}", ({", ".join(f"{float(v):.1f}" for v in 배[i][2])}))'
    return "\n".join(re.sub(r"^(b\d+) = at\((\d+), (.*)\)$", 바꿈, l) for l in 나머지.splitlines())
def 몸들(글):   # → [(종류, 모양식, 축, 자리)] · 한 줄이라도 안 맞으면 None
    out = []
    for l in 기존화(글).splitlines():
        if l.startswith("result"): continue
        m = P.match(l)
        if not m: return None
        s = m.group(2); out.append(("cone" if "makeCone" in s else "rev" if "revolve" in s else "box" if ".box(" in s else "cyl" if ".circle(" in s else "?", s, m.group(3), m.group(4)))
    return out
def 글(몸):   # [(모양식, 축, 자리)] → place 서식 코드
    return "\n".join(f'b{i} = place({s}, "{a}", ({p}))' for i, (s, a, p) in enumerate(몸)) + "\nresult = " + ("b0" if len(몸) == 1 else "".join(f"b{i}.union(" for i in range(len(몸) - 1)) + f"b{len(몸) - 1}" + ")" * (len(몸) - 1))
칸 = ["생성 그대로", "위치만 정답", "모양식만 정답", "둘 다 정답"]; 키 = [None, "위치만정답", "모양만정답", "정답글"]
def 중(v): v = [x for x in v if x is not None]; return round(float(np.median(v)), 3) if v else None
def 재기(폴더):   # 폴더 = out/하네스/<판>/ (평가.json · 생성/) → 원인쪼개기.json · 원인쪼개기.png · 요약 dict
    import 모델124 as B
    d = json.load(open(폴더 + "평가.json", encoding="utf-8")); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 줄, 일 = [], []
    for r in d:
        if not r["실행"]: continue
        n = r["부품"]; a = 몸들(open(폴더 + f"생성/{n}.py", encoding="utf-8").read()); b = 몸들(open(정답폴더 + f"{n}.py", encoding="utf-8").read())
        if a is None or b is None: continue
        z = {"부품": n, "IoU": r["IoU"], "생성몸": len(a), "정답몸": len(b), "종류같음": [x[0] for x in a] == [x[0] for x in b]}
        if len(a) == len(b):
            for k, g in (("위치만정답", 글([(x[1], y[2], y[3]) for x, y in zip(a, b)])), ("모양만정답", 글([(y[1], x[2], x[3]) for x, y in zip(a, b)])), ("정답글", 글([(y[1], y[2], y[3]) for y in b]))): 일.append((len(줄), k, g))
        줄.append(z)
    렌 = B.병렬렌더([("글", g) for _, _, g in 일] + [("조립", 색[z["부품"]]["코드"]) for z in 줄]); 정 = 렌[len(일):]
    for (i, k, _), x in zip(일, 렌[:len(일)]):
        y = 정[i]; 줄[i].setdefault("바꿈", {})[k] = None if x is None or y is None else round(float((x[1] & y[1]).sum() / max((x[1] | y[1]).sum(), 1)), 4)
    같 = [z for z in 줄 if "바꿈" in z]; n = max(len(줄), 1)
    요 = {"실행된것": len(줄), "몸개수": {"모자람": round(sum(z["생성몸"] < z["정답몸"] for z in 줄) / n, 3), "같음": round(len(같) / n, 3), "넘침": round(sum(z["생성몸"] > z["정답몸"] for z in 줄) / n, 3)},
          "종류순서같음": round(sum(z["종류같음"] for z in 줄) / n, 3), "개수같은수": len(같), "사다리": {c: 중([z["IoU"] for z in 같] if k is None else [z["바꿈"][k] for z in 같]) for c, k in zip(칸, 키)}}
    json.dump({"요약": 요, "부품": 줄}, open(폴더 + "원인쪼개기.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    그림(폴더, 요, 같); return 요
def 그림(폴더, 요, 같):   # 위: 몸 개수 막대 · 사다리 / 아래: 위치만 정답으로 가장 많이 오른 셋(골라 낸 예시라 전형보다 큼)
    import 모델124 as B, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    후 = sorted([z for z in 같 if z["바꿈"].get("위치만정답") is not None], key=lambda z: z["IoU"] - z["바꿈"]["위치만정답"])[:3]; 글들 = []
    for z in 후:
        a = 몸들(open(폴더 + f"생성/{z['부품']}.py", encoding="utf-8").read()); b = 몸들(open(정답폴더 + f"{z['부품']}.py", encoding="utf-8").read())
        글들 += [글([(x[1], x[2], x[3]) for x in a]), 글([(x[1], y[2], y[3]) for x, y in zip(a, b)]), 글([(y[1], x[2], x[3]) for x, y in zip(a, b)]), 글([(y[1], y[2], y[3]) for y in b])]
    렌 = B.병렬렌더([("글", g) for g in 글들]) if 글들 else []
    fig = plt.figure(figsize=(16, 15)); fig.suptitle("실행된 코드의 모양은 어디서 틀리나 — 생성 코드의 몸을 정답 것으로 바꿔 끼우기", fontsize=19, weight="bold")
    a = fig.add_axes([.06, .7, .38, .14]); m = 요["몸개수"]; x0 = 0
    for k, c, tc in (("같음", "#3a9d5d", "white"), ("모자람", "#d9534f", "white"), ("넘침", "#f0ad4e", "black")):
        a.barh(0, m[k], left=x0, color=c); m[k] > .06 and a.text(x0 + m[k] / 2, 0, f"{'맞음' if k == '같음' else k} {m[k]:.0%}", ha="center", va="center", color=tc, fontsize=14, weight="bold"); x0 += m[k]
    a.set_xlim(0, 1); a.axis("off"); a.set_title(f"① 몸 개수 — 실행된 {요['실행된것']} 개 중 정답과 개수가 같은 것 · 종류 순서까지 같음 {요['종류순서같음']:.0%}", fontsize=14, loc="left")
    a = fig.add_axes([.52, .66, .44, .24]); v = [요["사다리"][c] for c in 칸]
    if all(x is not None for x in v):
        a.plot(칸, v, "o-", color="#e07b39", lw=3, ms=9)
        for i, y in enumerate(v): a.text(i, y + .03, f"{y:.2f}", ha="center", color="#e07b39", fontsize=13, weight="bold")
    a.axhline(.737, color="#999", ls="--"); a.text(3.1, .737, "목표선 0.737", va="center", fontsize=11, color="#666"); a.set_ylim(0, 1.1); a.set_title(f"② 개수가 같은 {요['개수같은수']} 개 — IoU 중앙값", fontsize=14, loc="left"); a.grid(alpha=.3)
    fig.text(.04, .615, "③ 예시: 위치만 정답으로 옮겼을 때 가장 많이 오른 셋(골라 낸 것)", fontsize=14)
    for i, z in enumerate(후):
        for j in range(4):
            a = fig.add_axes([.04 + j * .24, .41 - i * .2, .2, .17]); x = 렌[i * 4 + j]
            if x is not None: a.imshow(np.asarray(x[0]))
            v = z["IoU"] if j == 0 else z["바꿈"][키[j]]; a.set_title(f"{z['부품']} · {칸[j]} · IoU {v:.2f}" if v is not None else f"{z['부품']} · {칸[j]}", fontsize=12); a.axis("off")
    fig.savefig(폴더 + "원인쪼개기.png", dpi=72); plt.close(fig)
if __name__ == "__main__":   # 자체 시험: 배치먼저 → 기존화 왕복 · 몸들 파싱 · 인자로 판 이름을 주면 그 판을 잼
    sys.path.insert(0, 뿌리 + "/하네스"); import 코드글, glob
    for f in sorted(glob.glob(정답폴더 + "*.py"))[:300]:
        g = open(f, encoding="utf-8").read(); assert 기존화(코드글.배치먼저(g)) == g, f; assert 몸들(g) is not None, f
    print("코드원인 시험 통과 · 배치먼저 왕복 300")
    for 판 in sys.argv[1:]: print(판, json.dumps(재기(f"{뿌리}/out/하네스/{판}/"), ensure_ascii=False))
