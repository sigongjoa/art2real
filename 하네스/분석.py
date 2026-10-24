# 하네스 분석 단계 — 판 보고서 맨 앞 「분석」(블로그 글) 초안 · 근거 claudedocs/research_읽히는블로그_20261022.md · 본보기 하네스/판/136합침 · 10-23
# 비교 그림 → claude -p 초안(틀 · 규칙 · 본보기) → 검사(소제목 · 숫자 출처) → 맥락 없는 독자 → 고침 → 분석 칸이 비었을 때만 넣음(사람 글은 안 덮음)
# 사용: python 하네스/분석.py <판> [--덮어쓰기]
import os, re, sys, json
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
from 쇼츠 import 클로드, 훅줄빼기
소제목 = ["한 줄로", "왜 이 판을 했나", "바꾼 것 하나", "결과", "왜 이렇게 나왔나", "한계", "배운 것과 다음"]
규칙 = """- 틀: 아래 일곱 소제목(### )을 이 순서로 다 쓴다: """ + " · ".join(소제목) + """
- 「한 줄로」 는 **물음**: 한 문장, 빈 줄, **답**: 한두 문장(판정 포함).
- 「결과」 는 그림 하나 `![결론 문장](비교.png)`(없으면 시트.png) — 그림 설명은 「무엇을 보라」는 결론 문장. 그다음 작은 표: | | 이 판 | 대조 | 목표 | 넘었나 | — 목표는 판정 기준 값, 넘었나는 ✓ · ✗.
- 「왜 이렇게 나왔나」 는 **확인한 것** 과 **짐작 (아직 확인 안 함)** 둘로 나눈다. 확인한 것에는 판 기록에 있는 숫자로 뒷받침되는 것만.
- 숫자는 아래 판 기록 · 대조 판 기록에 있는 것만 쓴다(지어내지 않음). 소수는 둘째 자리까지.
- 처음 보는 사람이 읽는 글: 평소 말 · 1 인칭(우리) · 문장은 짧게 · 낯선 낱말(CNN · F1 · 에폭 등)은 처음 한 번 풀거나 안 쓴다 · 지표 이름(선_자리 같은 것)은 쓰지 말고 말로(「선이 있는 자리를 찾음」).
- 실패면 실패라고 쓴다. 한계에는 시험 크기 · 한 번만 돌림 · 설명 안 된 어긋남을 적는다.
- 길이: 공백 빼고 1,000~1,600 글자(본보기 1,254). 넘치면 줄인다. 고쳐 쓸 때는 설명을 덧붙이지 말고 바꿔 쓴다.
- 「판」 = 실험 한 번 · 「대조」 = 비교 대상 판 · 「목표」 = 미리 정한 기준 — 이 셋은 보고서 머리에서 풀어 주니 글에서 다시 설명하지 않는다.
- 다른 논문 방법(L-CNN · PPGNet · PICASSO · GAT-CADNet)을 말하면 그 개념 그림을 한 줄 링크로 붙인다: `[개념 그림 — L-CNN](../../개념그림/lcnn/lcnn.gif)` 처럼(경로는 하네스/개념그림/<이름>/<이름>.gif).
- 본문만 출력(코드펜스 · 머리말 · 「적용 규칙」 줄 없이)."""
상한 = 1800
공용어 = "(이 글은 실험 보고서 시리즈의 한 쪽이다. 「판」 = 실험 한 번, 「대조」 = 비교 대상 판, 「목표」 = 미리 정한 기준이라는 건 쪽 머리에 따로 적혀 있으니 막힌 곳으로 적지 마라.)"
def 숫자들(t): return set(re.findall(r"\d+\.\d+|\d+", t.replace(",", "")))
def 재료(판):
    d = f"{뿌리}/하네스/판/{판}/"; from omegaconf import OmegaConf
    c = OmegaConf.load(d + "설정.yaml"); j = json.load(open(d + "판정.json", encoding="utf-8")); 대판 = str(c.대조.get("판", "")) if c.대조 else ""
    대 = json.load(open(f"{뿌리}/하네스/판/{대판}/판정.json", encoding="utf-8"))["지표"] if os.path.exists(f"{뿌리}/하네스/판/{대판}/판정.json") else dict(c.대조.get("값", {})) if c.대조 else {}
    곡 = json.load(open(d + "학습.json", encoding="utf-8")) if os.path.exists(d + "학습.json") else []
    바 = OmegaConf.to_container(OmegaConf.load(f"{뿌리}/하네스/conf/바탕.yaml"))
    def 바값(k):   # 옛 판 설정에 없던 항목(None)은 바탕 기본값 — 131 초안이 「130 기본 무게가 기록에 없다」고 씀(10-23)
        v = 바
        for p in k.split("."): v = v.get(p) if isinstance(v, dict) else None
        return v
    바뀐 = {k: [바값(k) if a is None else a, b] for k, (a, b) in j["바뀐 손잡이"].items()}
    줄곡 = 곡 if len(곡) <= 12 else [r for r in 곡 if r["에폭"] % 5 == 0 or r is 곡[-1] or r is 곡[0]]
    기록 = {"판": 판, "가지": str(c.판.가지), "시도": str(c.판.get("시도")), "명제(사전등록)": str(c.판.get("명제")), "바뀐 손잡이(앞 값 → 이 판 값)": 바뀐, "판정": j["판정"], "기준": j["기준"], "지표": j["지표"],
            "대조 판": 대판, "대조 지표": 대, "학습 곡선": 줄곡, "에폭": int(c.학습.에폭),
            "데이터": {"학습 부품": 3000 if c.get("목표") == "선지도" else int(c.데이터.학습수), "시험 부품": 299, "도면": "부품마다 위 · 앞 · 옆 세 장 · 128×128"}, "한 번만 돌림(시드 하나)": True}
    앞 = ""
    if 대판 and os.path.exists(f"{뿌리}/하네스/판/{대판}/보고.md"):
        m = re.search(r"## 분석[^\n]*\n(.*?)(?=\n## |\n명제: |\Z)", open(f"{뿌리}/하네스/판/{대판}/보고.md", encoding="utf-8").read(), re.S); 앞 = re.sub(r"<!--.*?-->", "", m.group(1)).strip() if m else ""
    return d, c, 기록, ("" if 앞 == "(비어 있음)" else 앞)
def 검사(글, 기록):
    문 = [f"소제목 「{s}」 없음" for s in 소제목 if f"### {s}" not in 글]
    if "**확인한 것**" not in 글 or "짐작" not in 글: 문.append("「왜 이렇게 나왔나」 에 **확인한 것** / **짐작** 둘로 안 나눔")
    if not re.search(r"!\[[^\]]{8,}\]\((비교|시트)\.png\)", 글): 문.append("결론 캡션이 붙은 그림 없음")
    if "| 목표 |" not in 글.replace(" ", " "): 문.append("결과 표에 목표 칸 없음")
    if re.search(r"(선|점)_[가-힣]+", 글): 문.append("지표 이름(선_자리 같은 것)이 그대로 나옴: " + ", ".join(sorted(set(re.findall(r"(?:선|점)_[가-힣]+", 글)))[:4]))
    import glob   # 숫자 출처 = 이 판 기록 + 하네스 판 기록 전체(앞 판 숫자 인용 허용) · 반올림 · 백분율(×100) 허용
    값 = [float(x) for p in [json.dumps(기록, ensure_ascii=False)] + [open(f, encoding="utf-8").read() for f in glob.glob(f"{뿌리}/하네스/판/*/판정.json")] for x in re.findall(r"-?\d+\.\d+", p)]
    def 나옴(n):
        k = len(n.split(".")[1]); v = float(n)
        return any(abs(round(x, k) - v) < 1e-9 or abs(round(x * 100, k) - v) < 1e-9 for x in 값)
    없 = sorted({n for n in 숫자들(re.sub(r"!\[.*?\]\(.*?\)", "", 글)) if "." in n and not 나옴(n)})
    n = len(re.sub(r"\s|!\[.*?\]\(.*?\)", "", 글))
    if n > 상한: 문.append(f"너무 김: {n} 글자(공백 뺌) — {상한} 아래로 줄임 · 덧붙이지 말고 겹치는 설명 · 배경을 덜어냄")
    if 없: 문.append("판 기록에 없는 숫자: " + ", ".join(없[:8]) + " — 지어낸 숫자는 빼거나 기록의 숫자로")
    return 문
def 초안(판, 덮어쓰기=False):
    d, c, 기록, 앞 = 재료(판)
    if "## 분석\n" not in open(d + "보고.md", encoding="utf-8").read(): import 보고; 보고.만들기(판)   # 분석 칸 생기기 전 보고서(130~135) — 쓰기 전에 칸부터(10-23 초안 6 개를 쓰고 넣다가 버림)
    m = re.search(r"## 분석[^\n]*\n(.*?)(?=\n## |\n명제: |\Z)", open(d + "보고.md", encoding="utf-8").read(), re.S)
    if m and "(비어 있음)" not in m.group(1) and not 덮어쓰기: return {"건너뜀": "분석 칸에 이미 글이 있음(사람 글 보호)"}
    if c.get("목표", "CAD") == "선지도":
        import 분석그림; 분석그림.비교(판, 기록["대조 판"] if os.path.exists(f"{뿌리}/out/하네스/{기록['대조 판']}/점검") else None)
    if not os.path.exists(d + "비교.png") and os.path.exists(d + "시트.png"):   # 계산 판(140~)은 비교 그림을 안 만듦 → 글이 가리키는 비교.png 가 깨졌음(10-24 사용자 「이미지 첨부 안 되는 거 있어」) → 시트를 씀
        import shutil; shutil.copy(d + "시트.png", d + "비교.png")
    본보기 = re.search(r"## 분석[^\n]*\n(.*?)(?=\n명제: )", open(f"{뿌리}/하네스/판/136합침/보고.md", encoding="utf-8").read(), re.S).group(1)
    본보기 = re.sub(r"<!--.*?-->", "", 본보기).strip()
    글감 = f"[규칙]\n{규칙}\n\n[본보기 — 판 136 의 분석(틀 · 말투만 따르고 내용은 이 판 기록으로)]\n{본보기}\n\n[이 판 기록]\n{json.dumps(기록, ensure_ascii=False, indent=1)}\n\n[대조 판의 분석(맥락)]\n{앞 or '(없음)'}"
    쓰기 = lambda 덧="": 훅줄빼기(클로드("너는 ML 실험 블로그 필자다. 하네스 판 보고서 맨 앞 「분석」 칸을 한국어로 쓴다.\n\n" + 글감 + 덧, 900))
    글 = 쓰기(); 기록검사 = []
    for _ in range(2):
        문 = 검사(글, 기록); 기록검사.append(문)
        if not 문: break
        글 = 쓰기(f"\n\n[앞 초안]\n{글}\n\n[검사에 걸린 것 — 이것만 고치고 나머지는 그대로]\n" + "\n".join(문))
    읽기 = 훅줄빼기(클로드("너는 이 프로젝트를 처음 보는 독자다. 파일을 찾지 말고 아래 글만 읽고, 막히는 곳(모르는 낱말 · 끊긴 논리 · 근거 없는 말)을 짧게 적어라. 다섯 개까지 · 중요한 것부터. 막힌 곳이 없으면 「없음」. " + 공용어 + "\n\n" + 글, 600))
    if 읽기.strip(" 「」.\n") != "없음":
        글 = 쓰기(f"\n\n[앞 초안]\n{글}\n\n[맥락 없는 독자가 막힌 곳 — 바꿔 써서 풀되 길이는 늘리지 말 것 · 틀 · 숫자는 그대로]\n{읽기}")
        for _ in range(2):   # 고쳐 쓴 뒤에도 검사(길이 포함) — 10-23 130~135 초안이 독자 지적을 덧붙이다 2,900~4,500 자로 불어남
            문 = 검사(글, 기록); 기록검사.append(문)
            if not 문: break
            글 = 쓰기(f"\n\n[앞 초안]\n{글}\n\n[검사에 걸린 것 — 이것만 고치고 나머지는 그대로]\n" + "\n".join(문))
    t = open(d + "보고.md", encoding="utf-8").read(); a = t.index("## 분석\n") + len("## 분석\n"); b = t.index("\n명제: ")
    open(d + "보고.md", "w", encoding="utf-8").write(t[:a] + "<!-- 사람 칸: 하네스 분석 단계 초안(claude -p) · 고치면 다시 만들어도 남는다 -->\n" + 글.strip() + "\n" + t[b:])
    import 보고; 보고.만들기(판); json.dump({"검사": 기록검사, "맥락없는읽기": 읽기[:1500]}, open(d + "분석.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"글자": len(글), "검사_끝": 기록검사[-1], "맥락없는읽기": 읽기[:200]}
if __name__ == "__main__": print(json.dumps(초안(sys.argv[1], "--덮어쓰기" in sys.argv), ensure_ascii=False, indent=1))
