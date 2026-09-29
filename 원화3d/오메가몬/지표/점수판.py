# -*- coding: utf-8 -*-
"""점수판 — 네 지표를 한 표에 · 대조군 순서 시험(집합.순서기대) 통과 여부.
    python 점수판.py  (랜드마크.py · 선F1.py · 드림심.py 를 먼저 돌려 json 이 있어야 · VLM 은 VLM짝/답.json)
"""
import os, json, itertools
from 집합 import 집합, OUT, 순서기대
J = lambda f: json.load(open(os.path.join(OUT, f), encoding="utf-8"))
후보 = [n for n in 집합 if n != "02"]
랜 = J("랜드마크.json"); 선 = J("선F1.json"); 드 = J("드림심.json")
답 = json.load(open(os.path.join(OUT, "VLM짝", "답.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "VLM짝", "답.json")) else {}
def vlm(n):
    승 = 경 = 0
    for m in 후보:
        if m == n: continue
        x, y = 답.get("%s_vs_%s" % (n, m)), 답.get("%s_vs_%s" % (m, n))
        픽 = [p for p in ((n if x == "A" else m) if x else None, (m if y == "A" else n) if y else None) if p]
        if not 픽 or (len(픽) == 2 and 픽[0] != 픽[1]): continue
        경 += 1; 승 += 픽[0] == n
    return (승, 경)
def 순서(점, 낮을수록):
    return [n for n in sorted(후보, key=lambda n: (점[n] if 낮을수록 else -점[n])) if n in 순서기대]
def 통과(순):
    """기대: FRA 맨 앞 · RX78 맨 뒤 · 4 판이 5 · 6 보다 앞. (5 ≈ 6 은 안 따짐)"""
    i = {n: k for k, n in enumerate(순)}; return i["FRA"] == 0 and i["RX78"] == len(순) - 1 and i["4판"] < min(i["5판"], i["6판"])
print("%-5s | %7s %-8s | %6s %6s | %7s | %s" % ("이름", "랜드마크", "최악", "선F1", "선R", "DreamSim", "VLM 승/경기"))
for n in 후보:
    v = vlm(n); print("%-5s | %7.1f %-8s | %6.3f %6.3f | %7.3f | %d/%d" % (n, 랜[n]["평균"], 랜[n]["최악"], 선[n]["정면"]["전체"]["F1"], 선[n]["정면"]["전체"]["R"], 드[n]["정면"], v[0], v[1]))
print("\n대조군 순서 시험 (기대 %s · 5≈6 무시)" % " > ".join(순서기대))
for 이름, 점, 낮 in (("랜드마크 잔차", {n: 랜[n]["평균"] for n in 후보}, True), ("선 F1", {n: 선[n]["정면"]["전체"]["F1"] for n in 후보}, False), ("DreamSim", {n: 드[n]["정면"] for n in 후보}, True)):
    s = 순서(점, 낮); print("%-10s %s  → %s" % (이름, " > ".join(s), "통과" if 통과(s) else "실패"))
짝 = [(a, b) for a, b in itertools.permutations(후보, 2) if "%s_vs_%s" % (a, b) in 답]; print("VLM 짝     답 %d 개 / %d 짝 · 순서 일치 확인된 짝: %s" % (len(답), len(후보) * (len(후보) - 1) // 2, ", ".join(sorted({"%s>%s" % ((a if 답["%s_vs_%s" % (a, b)] == "A" else b), (b if 답["%s_vs_%s" % (a, b)] == "A" else a)) for a, b in 짝 if "%s_vs_%s" % (b, a) in 답 and (답["%s_vs_%s" % (a, b)] == "A") == (답["%s_vs_%s" % (b, a)] == "B")}))))
