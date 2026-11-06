# 판 167 「함수18」 출력 서식 — CadQuery 정답 글 ↔ 함수 18 개 낱말 + 숫자 · 괄호 · 쉼표 · 따옴표 · result 줄은 변환기가 씀(모델은 안 씀)
# 11-06 사용자 「100000 개 중에서 예측하는 것보다는 100 개 예측하는 게 더 쉽잖아」 · 「아예 처음부터 지정된 18 개로 시작」 · 「토크나이저가 잘 동작한다는 거는 어떻게 확인하지?」
# 한 줄 = 몸 하나:  <b1><Workplane><XY><circle> 6.1<extrude> 44.7<z> 0.0 0.0 16.5
#   = b1 = place(cq.Workplane("XY").circle(6.1).extrude(44.7), "z", (0.0, 0.0, 16.5))
# 낱말은 꺾쇠로 감쌈(입력 선 글의 x · y · h 같은 글자와 안 겹치게) · 숫자는 원래 글자 그대로(왕복이 글자까지 같게) · 함수 뒤 숫자 개수는 다음 낱말까지
# 사용: python 하네스/서식18.py → 자체 시험 + 감사(정답 3,298 개 왕복 · 구조 · 어휘 밖 · 길이 · 망가진 줄) · python 하네스/서식18.py 기하 → 실행 부피 비교(표본)
import sys, os, re, glob, json
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
함수 = ["Workplane", "box", "circle", "extrude", "polyline", "close", "revolve", "add", "makeCone", "faces", "workplane", "center", "hole", "rect", "cutBlind", "edges", "fillet"]   # union 은 result 줄(변환기 몫)
값 = ["XY", "XZ", "top", "vert", "x", "y", "z"]   # top = ">Z" · vert = "|Z" · x y z = place 축
몸이름 = [f"b{i}" for i in range(6)]
낱말 = [f"<{w}>" for w in 함수 + 값 + 몸이름]   # 30 개 · 토크나이저에 이 순서로 더함(좌표 토큰 <0>~<127> 다음)
수 = r"-?\d+(?:\.\d+)?"
개수 = {"Workplane": (0, 0), "box": (3, 3), "circle": (1, 1), "extrude": (1, 1), "polyline": (2, 99), "close": (0, 0), "revolve": (0, 0), "add": (0, 0), "makeCone": (2, 2),
        "faces": (0, 0), "workplane": (1, 1), "center": (2, 2), "hole": (1, 2), "rect": (2, 2), "cutBlind": (1, 1), "edges": (0, 0), "fillet": (1, 1)}   # 함수 뒤 숫자 개수(최소, 최대)
_조각 = [   # (CadQuery 조각 정규식, 낱말 만들기) · 앞에서부터 맞는 것
    (r'cq\.Workplane\("(XY|XZ)"\)', lambda m: f"<Workplane><{m[1]}>"),
    (r"\.box\((" + 수 + "), (" + 수 + "), (" + 수 + r"), centered=\(True, True, False\)\)", lambda m: f"<box> {m[1]} {m[2]} {m[3]}"),
    (r"\.circle\((" + 수 + r")\)", lambda m: f"<circle> {m[1]}"),
    (r"\.extrude\((" + 수 + r")\)", lambda m: f"<extrude> {m[1]}"),
    (r"\.add\(cq\.Solid\.makeCone\((" + 수 + "), 0, (" + 수 + r")\)\)", lambda m: f"<add><makeCone> {m[1]} {m[2]}"),
    (r"\.polyline\(\[((?:\(" + 수 + ", " + 수 + r"\)(?:, )?)+)\]\)", lambda m: "<polyline> " + " ".join(re.findall(수, m[1]))),
    (r"\.close\(\)", lambda m: "<close>"),
    (r"\.revolve\(360, \(0, 0, 0\), \(0, 1, 0\)\)", lambda m: "<revolve>"),
    (r'\.faces\(">Z"\)', lambda m: "<faces><top>"),
    (r"\.workplane\(origin=\(0, 0, (" + 수 + r")\)\)", lambda m: f"<workplane> {m[1]}"),
    (r"\.center\((" + 수 + "), (" + 수 + r")\)", lambda m: f"<center> {m[1]} {m[2]}"),
    (r"\.hole\((" + 수 + r")(?:, (" + 수 + r"))?\)", lambda m: f"<hole> {m[1]}" + (f" {m[2]}" if m[2] else "")),
    (r"\.rect\((" + 수 + "), (" + 수 + r")\)", lambda m: f"<rect> {m[1]} {m[2]}"),
    (r"\.cutBlind\((" + 수 + r")\)", lambda m: f"<cutBlind> {m[1]}"),
    (r'\.edges\("\|Z"\)', lambda m: "<edges><vert>"),
    (r"\.fillet\((" + 수 + r")\)", lambda m: f"<fillet> {m[1]}")]
_줄 = re.compile(r'(b[0-5]) = place\((.*), "([xyz])", \((' + 수 + "), (" + 수 + "), (" + 수 + r")\)\)")
def 바꿈(글):   # CadQuery 정답 글 → 함수18 글 · 모르는 조각이 있으면 ValueError(정답은 전부 바뀌어야 함 · 감사가 셈)
    줄들 = []
    for l in 글.splitlines():
        if l.startswith("result = "): continue
        m = _줄.fullmatch(l)
        if not m: raise ValueError(f"몸 줄 아님: {l[:80]}")
        식, 쪽 = m[2], [f"<{m[1]}>"]
        while 식:
            for 꼴, 만 in _조각:
                k = re.match(꼴, 식)
                if k: 쪽.append(만(k)); 식 = 식[k.end():]; break
            else: raise ValueError(f"모르는 조각: {식[:60]}")
        줄들.append("".join(쪽) + f"<{m[3]}> {m[4]} {m[5]} {m[6]}")
    return "\n".join(줄들)
숫 = r" -?\d+\.\d"   # 정답 숫자는 늘 코드글.수 = 소수 한 자리 · 앞에 빈칸 하나(11-06 맥락 없는 검토: 「116.503.5」 → center(116.503, 5) 로 조용히 읽었음)
_줄토 = re.compile(r"(?:<\w+>|" + 숫 + ")+")
_토 = re.compile(r"<(\w+)>|(" + 숫 + ")")
_문법 = re.compile(r"Workplane0 (?:XY0 (?:box3|circle1 extrude1|add0 makeCone2)|XZ0 polyline(\d+) close0 revolve0)(?: faces0 top0 workplane1 center2 (?:hole1|hole2|rect2 cutBlind1)| edges0 vert0 fillet1)* [xyz]3")   # 코드글.바탕글 · 특징글 그대로
def 되돌림(글):   # 함수18 글 → CadQuery 글(result 줄 붙임) · 정답 문법(바탕 → 특징 사슬 → 축) · 몸 이름 b0 b1 … 차례 · 숫자 꼴이 아니면 ValueError
    out = []
    for k, l in enumerate([x for x in 글.splitlines() if x.strip()]):
        if not _줄토.fullmatch(l): raise ValueError(f"낱말 · 숫자 꼴이 아닌 글자: {l[:60]}")
        조 = [(m[1], m[2].strip() if m[2] else None) for m in _토.finditer(l)]
        if 조[0] != (f"b{k}", None): raise ValueError(f"{k} 번째 줄은 <b{k}> 로 시작해야 함: {l[:40]}")
        묶 = []   # [(낱말, [숫자 글])]
        for w, n in 조[1:]:
            if w: 묶.append((w, []))
            elif not 묶: raise ValueError("숫자가 낱말보다 먼저")
            else: 묶[-1][1].append(n)
        서명 = " ".join(f"{w}{len(a)}" for w, a in 묶); m = _문법.fullmatch(서명)
        if not m: raise ValueError(f"정답 문법이 아님: {서명[:80]}")
        if m[1] and (int(m[1]) < 2 or int(m[1]) % 2): raise ValueError("polyline 숫자는 짝수 · 2 개 이상")
        (축, 자) = 묶.pop(); 식 = ""; i = 0
        while i < len(묶):
            w, a = 묶[i]
            if w == "Workplane": 식 += f'cq.Workplane("{묶[i + 1][0]}")'; i += 2; continue
            if w == "add": 식 += f".add(cq.Solid.makeCone({묶[i + 1][1][0]}, 0, {묶[i + 1][1][1]}))"; i += 2; continue
            if w == "faces": 식 += '.faces(">Z")'; i += 2; continue
            if w == "edges": 식 += '.edges("|Z")'; i += 2; continue
            if w == "box": 식 += f".box({a[0]}, {a[1]}, {a[2]}, centered=(True, True, False))"
            elif w == "polyline": 식 += ".polyline([" + ", ".join(f"({a[j]}, {a[j + 1]})" for j in range(0, len(a), 2)) + "])"
            elif w == "close": 식 += ".close()"
            elif w == "revolve": 식 += ".revolve(360, (0, 0, 0), (0, 1, 0))"
            elif w == "workplane": 식 += f".workplane(origin=(0, 0, {a[0]}))"
            else: 식 += f".{w}({', '.join(a)})"
            i += 1
        out.append(f'b{k} = place({식}, "{축}", ({자[0]}, {자[1]}, {자[2]}))')
    if not out: raise ValueError("몸이 없음")
    if len(out) > 6: raise ValueError("몸은 6 개까지(b0~b5)")
    return "\n".join(out) + "\nresult = " + ".union(".join(f"b{k}" for k in range(len(out))) + ")" * (len(out) - 1)
def 되돌림_안전(글):   # 생성 글용 — 틀린 꼴이면 몸 줄 없이 주석만(실행 실패 · 구조 채점 몸 0 개 · 검토: 「bN = 망가짐」이 몸 개수 점수를 받았음)
    try: return 되돌림(글)
    except ValueError as e: return f"# 함수18 되돌림 실패: {e}"
def 감사():   # 기준 1 · 3 · 4 · 5 · 6
    import 과제코드 as K, 코드구조 as S
    fs = sorted(glob.glob(K.자료폴더 + "글도면/*.py")); 같음 = 구 = 0; 길 = []; 밖 = set(); 틀 = []
    for f in fs:
        g = open(f, encoding="utf-8").read().strip(); d = 바꿈(g); h = 되돌림(d)
        같음 += h == g; 틀 += [] if h == g else [os.path.basename(f)]
        r = S.비교(g, h); 구 += r["몸수맞음"] and r["종류순서맞음"] == 1 and r["붙임맞음"] == 1 and r["몸겹침"] > .9999
        밖 |= {w for w in re.findall(r"<(\w+)>", d) if f"<{w}>" not in 낱말}; 길.append(d)
    return {"정답": len(fs), "왕복 글자 같음": 같음, "왕복 틀린 예": 틀[:3], "구조 같음": 구, "어휘 밖 낱말": sorted(밖), "글": 길}
def 망가짐시험():   # 기준 6 · 모델이 낼 법한 망가진 줄 → ValueError(되돌림) · 되돌림_안전 은 멈추지 않음
    나쁜 = ["", "<b0>", "<b0><Workplane><XY><box> 1.0 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> 1.0<extrude> 2.0<z> 0.0 0.0", "1.0 <b0>",
           "<b0><Workplane><XY><polyline> 1.0 2.0 3.0<close><revolve><z> 0.0 0.0 0.0", "<b0><Workplane><XY><foo> 1.0<z> 0.0 0.0 0.0", "<b0><box> 1.0 2.0 3.0<z> 0.0 0.0 0.0",
           "<b0><Workplane><XY><add> 1.0 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> 1.0<extrude> 2.0<z> 0.0 0.0 0.0\n<b1><Workplane><XY><circle> 1.0<extrude>",
           # 11-06 맥락 없는 검토가 찾은 조용한 통과들
           "<b0><Workplane><XY><box> 1.0 2.0 3.0<faces><top><workplane> 3.0<center> 116.503.5<hole> 1.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> 1.0<extrude> 2.0<z> 0.0 0.016.5",
           "<b0><Workplane><XY><circle> .5<extrude> 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> - 4.0<extrude> 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> 1<extrude> 2.0<z> 0.0 0.0 0.0",
           "<b0><Workplane><XY><circle> 1.0<extrude> 2.0<z> 0.0 0.0 0.0\n<b0><Workplane><XY><box> 1.0 2.0 3.0<z> 0.0 0.0 0.0", "<b1><Workplane><XY><box> 1.0 2.0 3.0<z> 0.0 0.0 0.0",
           "<b0><Workplane><XY><circle> 6.1<z> 0.0 0.0 0.0", "<b0><Workplane><XY><box> 1.0 2.0 3.0<center> 1.0 1.0<hole> 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><box> 1.0 2.0 3.0<fillet> 0.5<z> 0.0 0.0 0.0",
           "<b0><Workplane><XY><box> 1.0 2.0 3.0<faces><top><workplane> 3.0<center> 1.0 1.0<rect> 2.0 2.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><box> 1.0 2.0 3.0<circle> 1.0<extrude> 2.0<z> 0.0 0.0 0.0",
           "<b0><Workplane><XZ><box> 1.0 2.0 3.0<z> 0.0 0.0 0.0", "<b0><Workplane><XY><polyline> 0.0 0.0 1.0 0.0 1.0 1.0<close><revolve><z> 0.0 0.0 0.0", "<b0><Workplane><XY><circle> 1.0<extrude> 2.0<z> 0.0 0.0 0.0 x"]
    for x in 나쁜:
        try: 되돌림(x); raise AssertionError(f"막지 못함: {x!r}")
        except ValueError: pass
        assert 되돌림_안전(x).startswith("# 함수18 되돌림 실패"), x
        assert not re.search(r"^b\d+ = ", 되돌림_안전(x), re.M), x   # 실패하면 몸 줄 0 개
    return len(나쁜)
if __name__ == "__main__":
    g = 'b0 = place(cq.Workplane("XY").box(34.1, 47.4, 9.0, centered=(True, True, False)).edges("|Z").fillet(2.0), "z", (0.0, 0.0, 0.0))\nb1 = place(cq.Workplane("XY").circle(6.1).extrude(44.7), "z", (0.0, 0.0, 16.5))\nresult = b0.union(b1)'
    d = 바꿈(g); assert d.splitlines()[1] == "<b1><Workplane><XY><circle> 6.1<extrude> 44.7<z> 0.0 0.0 16.5", d; assert 되돌림(d) == g, 되돌림(d)
    assert len(낱말) == 30 and len(set(낱말)) == 30 and len(함수) == 17   # union 은 변환기 몫 → 모델 낱말 함수 17 + 값 7 + 몸 6
    print("망가진 줄", 망가짐시험(), "개 모두 막힘")
    if len(sys.argv) > 1 and sys.argv[1] == "기하":   # 기준 2 · 표본 실행 부피(왕복 글자가 같으면 같아야 함 — 반올림 실수 잡기)
        import random, 과제코드 as K, 모델124 as B, 데이터117 as Q
        fs = sorted(glob.glob(K.자료폴더 + "글도면/*.py")); random.seed(0); 표 = random.sample(fs, int(sys.argv[2]) if len(sys.argv) > 2 else 60)
        원 = [open(f, encoding="utf-8").read().strip() for f in 표]; 렌 = B.병렬렌더([("글", g, 1) for g in 원] + [("글", 되돌림(바꿈(g)), 1) for g in 원], n=4); k = len(원)
        v = [Q.부피겹(렌[i][2], 렌[k + i][2]) for i in range(k) if 렌[i] is not None and 렌[k + i] is not None]
        print("기하 표본", k, "렌더 된 짝", len(v), "부피 IoU 최소", round(min(v), 4) if v else None); sys.exit()
    a = 감사(); 글 = a.pop("글"); print("감사", a)
    assert a["왕복 글자 같음"] == a["정답"] and a["구조 같음"] == a["정답"] and not a["어휘 밖 낱말"], a
    print("서식18 자체 시험 · 감사 통과")
