# -*- coding: utf-8 -*-
"""검증 집계 — 판정기준12 그대로: 판정자 검사 → 세트 · 방법별 통과율(윌슨 95 %) → 라벨 칸(n < 8 은 모름) → 판정 · 10-12
python runs/기능0/집계.py <대응표.json> <판정자1.json> <판정자2.json>  →  결과판정12.json + 표 출력
판정자 json = {"쌍NNN": "통과" | "애매" | "실패", ...}"""
import os, sys, json, math
H = os.path.dirname(os.path.abspath(__file__))
def 윌슨(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return (round(max(0, c - h), 3), round(min(1, c + h), 3))
def 칸(xs):   # xs = [통과 bool] → n · 비율 · 구간
    n = len(xs); k = sum(xs); return {"n": n, "통과": k, "비율": round(k / n, 3) if n else None, "구간": 윌슨(k, n)}
def 집계(대응, J1, J2, 규칙, 의미):
    ok = lambda q: J1.get(q) == "통과" and J2.get(q) == "통과"   # 둘 다 통과여야 통과
    양 = [q for q, v in 대응.items() if v["후보"] == "양성"]; 음 = [q for q, v in 대응.items() if v["후보"].startswith("음성")]
    본 = [q for q, v in 대응.items() if v["후보"] in ("우리", "교차")]
    일치 = sum((J1.get(q) == "통과") == (J2.get(q) == "통과") for q in 본) / len(본)
    검사 = {"양성 대조 통과": sum(ok(q) for q in 양), "음성 대조 실패": sum(J1.get(q) != "통과" and J2.get(q) != "통과" for q in 음), "두 판정자 일치": round(일치, 3)}
    검사["통과"] = 검사["양성 대조 통과"] >= 9 and 검사["음성 대조 실패"] >= 9 and 일치 >= 0.75
    표 = {}
    for 세트 in ("시험", "검증"):
        for 방 in ("우리", "교차"):
            qs = [q for q in 본 if 대응[q]["후보"] == 방 and 대응[q]["부품"].startswith(세트)]; 표[세트 + "/" + 방] = 칸([ok(q) for q in qs])
    라벨표 = {}
    for 이름, 사전 in (("규칙", 규칙), ("의미", 의미)):
        모든 = sorted({l for v in 사전.values() for l in v})
        for l in 모든:
            for 세트 in ("시험", "검증"):
                for 방 in ("우리", "교차"):
                    qs = [q for q in 본 if 대응[q]["후보"] == 방 and 대응[q]["부품"].startswith(세트) and l in 사전.get(대응[q]["부품"], [])]
                    c = 칸([ok(q) for q in qs]); c["말"] = "모름" if c["n"] < 8 else "잘함" if c["구간"][0] >= .5 else "못함" if c["구간"][1] < .5 else "모름"
                    라벨표["%s:%s/%s/%s" % (이름, l, 세트, 방)] = c
    v우, v교 = 표["검증/우리"]["비율"], 표["검증/교차"]["비율"]
    외움칸 = [l for l in {k.rsplit("/", 2)[0] for k in 라벨표} if 라벨표[l + "/시험/우리"]["n"] >= 8 and 라벨표[l + "/검증/우리"]["n"] >= 8]
    외움 = sum(라벨표[l + "/시험/우리"]["비율"] - 라벨표[l + "/검증/우리"]["비율"] > .2 for l in 외움칸)
    판 = "판정자 검사 실패 — 무효" if not 검사["통과"] else ("쓸 만함" if v우 >= .5 and v우 - v교 >= .15 else "못 씀")
    return {"판정자 검사": 검사, "표": 표, "라벨표": 라벨표, "외움": {"비교 칸": len(외움칸), "차이 > 0.2": 외움, "외움": len(외움칸) > 0 and 외움 > len(외움칸) / 2}, "판정": 판}
if __name__ == "__main__" and len(sys.argv) == 1:   # 자체 검사: 구간 · 판정자 검사 · 판정이 질 수 있는지
    assert 윌슨(0, 10)[0] == 0 and 윌슨(10, 10)[1] == 1 and 0.18 < 윌슨(5, 10)[0] < 0.25, 윌슨(5, 10)
    대 = {"쌍%03d" % i: {"부품": "검증/%02d" % (i % 10), "후보": "우리" if i < 10 else "교차" if i < 20 else "양성" if i < 30 else "음성:검증/00"} for i in range(40)}
    모두 = {q: "통과" for q in 대}; r = 집계(대, 모두, 모두, {}, {}); assert not r["판정자 검사"]["통과"] and r["판정"].startswith("판정자"), r["판정자 검사"]   # 음성도 통과 주는 판정자는 무효
    좋 = {q: ("실패" if v["후보"].startswith("음성") or v["후보"] == "교차" else "통과") for q, v in 대.items()}; r = 집계(대, 좋, 좋, {}, {}); assert r["판정"] == "쓸 만함", r["판정"]
    print("ok 자체 검사")
elif __name__ == "__main__":
    대응, J1, J2 = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:4])
    규칙 = {k: v["라벨"] for k, v in json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"].items()}
    의미 = {k.replace("_", "/"): v["라벨"] for k, v in json.load(open(os.path.join(H, "의미라벨.json"), encoding="utf-8")).items()}
    r = 집계(대응, J1, J2, 규칙, 의미); json.dump(r, open(os.path.join(H, "결과판정12.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: r[k] for k in ("판정자 검사", "표", "외움", "판정")}, ensure_ascii=False, indent=1))
