# -*- coding: utf-8 -*-
"""가린 시트 · 여러 방법 — 같은 메시는 한 쌍으로 묶어 한 번만 채점 · 대조 10 + 10 · 판정기준16 · 10-12
python 가린시트3.py <세트> <출력 폴더> <대응표.json> 이름:폴더 …   예) 검증2 out 표.json D:B_D C:B_C 교차:B_교차
python 가린시트3.py 집계 <대응표.json> <판정자A.json> <판정자B.json>   → 방법별 통과(둘 다 통과) · 윌슨 구간 · 판사 검사"""
import os, sys, json, random, hashlib, trimesh
H = os.path.dirname(os.path.abspath(__file__))
from 가린시트 import 쌍그림, 정, RR
from 집계 import 윌슨
if __name__ == "__main__" and sys.argv[1] != "집계":
    세트, O, 표 = sys.argv[1:4]; 방법 = [a.split(":") for a in sys.argv[4:]]; os.makedirs(O, exist_ok=True)
    L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]; 키 = sorted(k for k in L if k.split("/")[0] == 세트); rng = random.Random(int(os.environ.get("SEED", 20261016))); 항 = []
    for k in 키:
        i = k.split("/")[1]; 묶 = {}
        for 이름, 폴더 in 방법:
            p = os.path.join(H, 폴더 + "_" + 세트, "%s.stl" % i); h = hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "없음:" + 이름
            묶.setdefault(h, (p, []))[1].append(이름)
        for h, (p, 이름들) in 묶.items(): 항.append((k, "+".join(이름들), p if not h.startswith("없음") else None))
    for k in rng.sample(키, 10): 항.append((k, "양성", None))
    for k in rng.sample(키, 10):
        q = rng.choice([x for x in 키 if x != k]); 항.append((k, "음성", os.path.join(H, 방법[-1][1] + "_" + 세트, "%s.stl" % q.split("/")[1])))
    rng.shuffle(항); 대 = {}
    for n, (k, 후, p) in enumerate(항):
        사람 = 정(trimesh.load(RR + L[k]["부품"], force="mesh")); 후보 = 사람 if 후 == "양성" else (정(trimesh.load(p)) if p else None)
        쌍그림(사람, 후보).save(os.path.join(O, "쌍%03d.png" % n)); 대["쌍%03d" % n] = {"부품": k, "후보": 후}; print(n, flush=True)
    json.dump(대, open(표, "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("ok", len(대))
elif __name__ == "__main__":
    대, A, B = (json.load(open(p, encoding="utf-8")) for p in sys.argv[2:5]); ok = lambda q: A[q] == "통과" and B[q] == "통과"
    양 = [q for q, v in 대.items() if v["후보"] == "양성"]; 음 = [q for q, v in 대.items() if v["후보"] == "음성"]; 본 = [q for q, v in 대.items() if v["후보"] not in ("양성", "음성")]
    검 = {"양성 통과": sum(ok(q) for q in 양), "음성 실패": sum(A[q] != "통과" and B[q] != "통과" for q in 음), "일치": round(sum((A[q] == "통과") == (B[q] == "통과") for q in 본) / len(본), 3)}
    방법들 = sorted({m for q in 본 for m in 대[q]["후보"].split("+")}); 표 = {}
    for m in 방법들:
        qs = [q for q in 본 if m in 대[q]["후보"].split("+")]; k_ = sum(ok(q) for q in qs); 표[m] = {"n": len(qs), "통과": k_, "비율": round(k_ / len(qs), 3), "구간": 윌슨(k_, len(qs))}
    print(json.dumps({"판사 검사": 검, "표": 표}, ensure_ascii=False, indent=1))
