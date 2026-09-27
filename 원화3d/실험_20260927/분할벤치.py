"""분할 예측 벤치 채점 — 완성 사진만 보고 부위별 분할을 맞혔나 (계획: claudedocs/plan_분할벤치_20260927.md).

    python 분할벤치.py dev|test [예측이름=R]   ->  out/분할벤치/점수_<세트>_<예측>.json + 표 출력
    python 분할벤치.py 자가검사                ->  집계 · 대조군 · 문턱이 질 수 있는지 assert

정답  out/분할벤치/정답/<키트>.json   예측  out/분할벤치/예측/<예측이름>/<키트>.json   (같은 스키마 · 부위 → 칸)
세트 점수 = 키트 평균의 평균(키트 가중 같음). 정답에 있는 부위만 채점 · 예측에 빠진 부위는 틀림."""
import json, os, sys
from collections import Counter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "분할벤치")
세트 = {"dev": ["EG_RX78", "MG_프리덤", "MG_자쿠", "MG_유니콘", "MG_밴시"],
        "test": ["FRA_오메가몬", "PG_RX78", "RG_RX78", "FA_輝鎚甲", "ZOIDS_실드라이거", "MODEROID_브레이번", "30MS"]}


def 읽기(p):
    return json.load(open(p, encoding="utf-8"))["부위"]


def B0(정):
    return {k: {"조각수": 1, "분할형": "통짜", "이음위치": "없음"} for k in 정}


def B1(정):
    return {k: {"조각수": max(1, v.get("색수", 1)), "분할형": "통짜" if v.get("색수", 1) <= 1 else "복합",
                "이음위치": "없음" if v.get("색수", 1) <= 1 else "앞모서리"} for k, v in 정.items()}


def B2_만들기(dev정답들):
    """개발 세트 정답에서 부위마다 최빈값 — 시험 세트에만 쓴다(개발에서는 표본 안 값)."""
    모음 = {}
    for 정 in dev정답들:
        for k, v in 정.items(): 모음.setdefault(k, []).append(v)
    최빈 = {k: {c: Counter(x[c] for x in vs).most_common(1)[0][0] for c in ("조각수", "분할형", "이음위치")} for k, vs in 모음.items()}
    return lambda 정: {k: 최빈.get(k, {"조각수": 1, "분할형": "통짜", "이음위치": "없음"}) for k in 정}


def 키트점수(정, 예):
    행 = []
    for k, g in 정.items():
        p = 예.get(k)
        if p is None: 행.append((0, 0, g["조각수"], 0)); continue
        행.append((int(p["분할형"] == g["분할형"]), int(int(p["조각수"]) == g["조각수"]),
                  abs(int(p["조각수"]) - g["조각수"]), int(p["이음위치"] == g["이음위치"])))
    n = len(행)
    return {"분할형": sum(r[0] for r in 행) / n, "조각수맞음": sum(r[1] for r in 행) / n,
            "조각수MAE": sum(r[2] for r in 행) / n, "이음위치": sum(r[3] for r in 행) / n, "부위수": n}


def 세트점수(키트별):
    ks = list(키트별.values())
    return {c: sum(k[c] for k in ks) / len(ks) for c in ("분할형", "조각수맞음", "조각수MAE", "이음위치")}


def 판정(R, 대조):
    최고형 = max(b["분할형"] for b in 대조.values()); 최저MAE = min(b["조각수MAE"] for b in 대조.values())
    q1 = R["분할형"] >= 최고형 + 0.15 and R["분할형"] >= 0.60
    q2 = R["조각수MAE"] < 최저MAE and R["조각수MAE"] <= 1.0
    q3 = R["이음위치"] >= 0.50
    return {"Q1 분할형": q1, "Q2 조각수": q2, "Q3 이음위치": q3, "Q4 오메가몬으로 옮김": q1 and q2,
            "대조 최고 분할형": 최고형, "대조 최저 MAE": 최저MAE}


def 채점(세트이름, 예측이름="R"):
    정답들 = {k: 읽기(os.path.join(D, "정답", k + ".json")) for k in 세트[세트이름] if os.path.exists(os.path.join(D, "정답", k + ".json"))}
    assert 정답들, "정답 없음: " + 세트이름
    b2 = B2_만들기([읽기(os.path.join(D, "정답", k + ".json")) for k in 세트["dev"] if os.path.exists(os.path.join(D, "정답", k + ".json"))])
    예측기 = {"B0 전부통짜": B0, "B1 색=부품": B1, "B2 부위다수결": b2}
    결과 = {}
    for 이름, f in 예측기.items():
        결과[이름] = 세트점수({k: 키트점수(정, f(정)) for k, 정 in 정답들.items()})
    예경로 = os.path.join(D, "예측", 예측이름)
    R키트 = {k: 키트점수(정, 읽기(os.path.join(예경로, k + ".json"))) for k, 정 in 정답들.items() if os.path.exists(os.path.join(예경로, k + ".json"))}
    if R키트:
        결과[예측이름] = 세트점수(R키트); 결과["키트별_" + 예측이름] = R키트
        대조 = {k: v for k, v in 결과.items() if k.startswith("B") and not (세트이름 == "dev" and k.startswith("B2"))}
        결과["판정"] = 판정(결과[예측이름], 대조)
        if 세트이름 == "dev": 결과["주의"] = "개발 세트: B2 는 표본 안 값이라 판정 대조에서 뺐다 · 규칙을 고쳐도 되는 세트"
    for 이름 in [k for k in 결과 if not k.startswith(("키트별", "판정", "주의"))]:
        v = 결과[이름]; print("  %-14s 분할형 %.3f  조각수맞음 %.3f  MAE %.2f  이음 %.3f" % (이름, v["분할형"], v["조각수맞음"], v["조각수MAE"], v["이음위치"]))
    if "판정" in 결과: print("  판정", 결과["판정"])
    json.dump(결과, open(os.path.join(D, "점수_%s_%s.json" % (세트이름, 예측이름)), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 결과


def 자가검사():
    정 = {"정강이": {"조각수": 2, "분할형": "앞뒤", "이음위치": "옆가운데", "색수": 1},
          "방패": {"조각수": 3, "분할형": "복합", "이음위치": "앞모서리", "색수": 3}}
    assert 키트점수(정, 정)["분할형"] == 1 and 키트점수(정, 정)["조각수MAE"] == 0
    assert 키트점수(정, {})["분할형"] == 0                       # 빠진 부위 = 틀림
    b0 = 키트점수(정, B0(정)); assert b0["분할형"] == 0 and b0["조각수MAE"] == 1.5
    b1 = 키트점수(정, B1(정)); assert b1["분할형"] == 0.5 and b1["조각수MAE"] == 0.5
    완벽 = 판정({"분할형": 1.0, "조각수MAE": 0.0, "이음위치": 1.0}, {"b": b1})
    assert 완벽["Q4 오메가몬으로 옮김"]
    대조수준 = 판정({"분할형": b1["분할형"], "조각수MAE": b1["조각수MAE"], "이음위치": 0.4}, {"b": b1})
    assert not 대조수준["Q1 분할형"] and not 대조수준["Q2 조각수"] and not 대조수준["Q3 이음위치"]   # 대조와 같으면 진다
    print("자가검사 통과")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "자가검사"
    자가검사() if a == "자가검사" else 채점(a, sys.argv[2] if len(sys.argv) > 2 else "R")
