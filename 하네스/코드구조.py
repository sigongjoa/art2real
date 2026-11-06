# 코드생성 판의 구조 채점 — 생성 글 · 정답 글을 몸 목록(종류 · 상자 크기 · 자리)으로 읽고 몸 개수 · 종류 · 붙임(어느 몸의 어느 면) · 몸별 겹침을 비교
# 11-06 사용자 「원형에서 부품의 수와 연결관계를 표현할 수 있지? 생성된 부품의 수와 연결관계 또는 iou 를 비교해야」 · 「니가 틀렸다 맞았다 판단을 제대로 못하잖아」
# 글을 읽기만 함(실행 안 함) → 실행 안 되는 생성 글도 채점 · place(w, 축, 자리) 는 몸 상자 가운데를 자리에 둠(코드글.머리말)
# 붙임은 정답 사양에만 있음 → 정답 · 생성 모두 같은 규칙(붙임추정)으로 상자에서 셈 · 규칙이 맞는지는 감사()가 정답 사양 붙임과 대조
# 사용: python 하네스/코드구조.py <판 …> → out/하네스/<판>/구조.json · 자체 시험은 인자 없이
import sys, os, re, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
면이름 = ["+x", "-x", "+y", "-y", "+z", "-z"]   # 조립124: 붙임 = [몸, 면] · 면 = 축 * 2 + (0 이면 +, 1 이면 -)
수 = r"-?\d+(?:\.\d+)?"
줄꼴 = re.compile(r'(b\d+) = place\((.*), "([xyz])", \((' + 수 + r'), (' + 수 + r'), (' + 수 + r')\)\)\s*$')
def 몸(식):   # 몸 식 → (종류, (가로, 세로, 높이)) · 축 돌리기 전 · 못 읽으면 None
    if m := re.search(r"makeCone\((" + 수 + r"), " + 수 + r", (" + 수 + r")\)", 식): r, h = map(float, m.groups()); return "원뿔", (2 * r, 2 * r, h)
    if m := re.search(r"(?:^|[^.\w])cone\((" + 수 + r"), (" + 수 + r")\)", 식): r, h = map(float, m.groups()); return "원뿔", (2 * r, 2 * r, h)   # 158 원뿔이름 서식
    if m := re.search(r"\.box\((" + 수 + r"), (" + 수 + r"), (" + 수 + r")", 식): return "상자", tuple(map(float, m.groups()))
    if ".revolve(" in 식 and (m := re.search(r"polyline\(\[(.*?)\]\)", 식)):
        p = [tuple(map(float, x)) for x in re.findall(r"\((" + 수 + r"), (" + 수 + r")\)", m.group(1))]
        if p: R, H = max(abs(x) for x, _ in p), max(y for _, y in p) - min(y for _, y in p); return "회전체", (2 * R, 2 * R, H)
        return None
    if m := re.search(r"\.circle\((" + 수 + r")\)\.extrude\((" + 수 + r")\)", 식): r, h = map(float, m.groups()); return "원기둥", (2 * r, 2 * r, h)
    return None
def 읽기(글):   # 글 → [{"이름", "종류", "크기"(x, y, z 축 돌린 뒤), "자리"}] · 몸 줄을 못 읽으면 그 몸은 종류 "?"(개수에는 셈)
    out = []
    for l in 글.splitlines():
        m = 줄꼴.match(l.strip())
        if not m:
            if re.match(r"b\d+ = ", l.strip()): out.append({"이름": l.split(" = ")[0].strip(), "종류": "?", "크기": None, "자리": None})
            continue
        b = 몸(m.group(2)); 축 = m.group(3); 자 = tuple(map(float, m.group(4, 5, 6)))
        if b is None: out.append({"이름": m.group(1), "종류": "?", "크기": None, "자리": 자}); continue
        a, c, h = b[1]; 크 = {"z": (a, c, h), "x": (h, c, a), "y": (a, h, c)}[축]   # place: x = Y 축 90° (z→x) · y = X 축 −90° (z→y)
        out.append({"이름": m.group(1), "종류": b[0], "크기": 크, "자리": 자})
    return out
def 붙임추정(몸들):   # 몸 i(≥1) 마다 앞선 몸 j · 면 f 중 조립124 놓기 규칙에 가장 맞는 것 — 자식 가운데 = 부모 가운데 + 축 a 로 부호 · (부모 반폭 + 자식 반폭 × 0.6)
    r = [None]                       # 11-06 감사: 「틈이 가장 작은 몸」은 반쯤 박혀 여럿과 닿아 0.754 → 이 규칙
    for i, s in enumerate(몸들[1:], 1):
        if s["크기"] is None: r.append(None); continue
        c, h = np.array(s["자리"]), np.array(s["크기"]) / 2; 후 = []
        for j, t in enumerate(몸들[:i]):
            if t["크기"] is None or t["자리"] is None: continue
            pc, ph = np.array(t["자리"]), np.array(t["크기"]) / 2
            for f in range(6):
                a, sg = f // 2, (1 if f % 2 == 0 else -1); q = pc.copy(); q[a] += sg * (ph[a] + .6 * h[a])
                후.append((float(np.abs(q - c).sum() / max(h.sum(), 1e-6)), j, f))
        r.append(min(후)[1:] if 후 else None)
    return r
def 상자겹(s, t):
    if s["크기"] is None or t["크기"] is None: return 0.
    lo = np.maximum(np.array(s["자리"]) - np.array(s["크기"]) / 2, np.array(t["자리"]) - np.array(t["크기"]) / 2)
    hi = np.minimum(np.array(s["자리"]) + np.array(s["크기"]) / 2, np.array(t["자리"]) + np.array(t["크기"]) / 2)
    교 = np.prod(np.maximum(hi - lo, 0)); 합 = np.prod(s["크기"]) + np.prod(t["크기"]) - 교; return float(교 / 합) if 합 > 0 else 0.
def 비교(정글, 생글):   # 부품 하나 → 칸들 · 몸은 번호(b0, b1 …) 순서로 짝(정답도 생성도 b0 = 바탕 · 붙임은 앞선 몸에만)
    import collections
    정, 생 = 읽기(정글), 읽기(생글); n, m = len(정), len(생); k = min(n, m)
    a, b = collections.Counter(x["종류"] for x in 정), collections.Counter(x["종류"] for x in 생); 공 = sum((a & b).values())
    정붙, 생붙 = 붙임추정(정), 붙임추정(생)
    return {"정답몸": n, "생성몸": m, "몸수맞음": n == m, "종류F1": 2 * 공 / (n + m) if n + m else 1.,
            "종류순서맞음": sum(정[i]["종류"] == 생[i]["종류"] for i in range(k)) / max(n, 1),   # 자리마다 같은 종류 / 정답 몸 수
            "붙임맞음": sum(정붙[i] is not None and 정붙[i] == 생붙[i] for i in range(1, k)) / max(n - 1, 1) if n > 1 else 1.,   # 몸 i 가 같은 몸의 같은 면에 붙음 / 정답 붙임 수
            "몸겹침": sum(상자겹(정[i], 생[i]) for i in range(k)) / max(n, m, 1)}   # 짝 몸 상자 IoU · 빠지거나 넘친 몸은 0
def 집계(줄):
    return {"구조_몸수맞음": round(float(np.mean([r["몸수맞음"] for r in 줄])), 4), "구조_몸수차": round(float(np.mean([abs(r["생성몸"] - r["정답몸"]) for r in 줄])), 4),
            "구조_종류F1": round(float(np.mean([r["종류F1"] for r in 줄])), 4), "구조_종류순서": round(float(np.mean([r["종류순서맞음"] for r in 줄])), 4),
            "구조_붙임맞음": round(float(np.mean([r["붙임맞음"] for r in 줄])), 4), "구조_몸겹침": round(float(np.mean([r["몸겹침"] for r in 줄])), 4)}
def 바닥(정글들):   # 모든 부품에 같은 글 하나를 냈을 때 · 시험 정답 글 각각을 후보로 · 칸마다 가장 좋은 값(문턱은 이것을 넘어야 뜻이 있음)
    b = {}
    for 후 in 정글들:
        for k, v in 집계([비교(g, 후) for g in 정글들]).items(): b[k] = min(b.get(k, 9e9), v) if k == "구조_몸수차" else max(b.get(k, 0), v)
    return {k.replace("구조_", "구조바닥_"): v for k, v in b.items()}
def 재기(폴더, 이름들, 정글들, 생글들):   # 과제코드.점검 이 부름 → 구조.json · 지표 dict(+ 바닥)
    줄 = [{"부품": n, **비교(g, s)} for n, g, s in zip(이름들, 정글들, 생글들)]; 요 = {**집계(줄), **바닥(정글들)}
    json.dump({"요약": 요, "부품": 줄}, open(폴더 + "구조.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); return 요
def 감사():   # 붙임추정 이 정답 사양 붙임을 되살리나 · 정답 글 3,298 개(글도면) · 몸 종류 읽기도 사양과 대조
    import 모델124 as B, 과제코드 as K
    회 = {"돔", "컵", "계단축", "그릇"}; 붙맞 = 붙수 = 종맞 = 종수 = 0
    for r in B.색인():
        p = K.자료폴더 + f"글도면/{r['i']:05d}.py"
        if not os.path.exists(p): continue
        c = r["코드"] if isinstance(r["코드"], dict) else json.loads(r["코드"]); 몸들 = 읽기(open(p, encoding="utf-8").read())
        if len(몸들) != len(c["몸"]): continue   # 짓다 빠진 몸(글로 가 버린 것)은 감사에서 뺌
        for s, t in zip(c["몸"], 몸들): 종수 += 1; 종맞 += ("회전체" if s["바탕"]["종류"] in 회 else s["바탕"]["종류"]) == t["종류"]
        for i, e in enumerate(붙임추정(몸들)[1:], 1): 붙수 += 1; 붙맞 += e is not None and list(e) == list(c["몸"][i]["붙임"])
    return {"종류 읽기 맞음": round(종맞 / 종수, 4), "붙임 추정 맞음": round(붙맞 / 붙수, 4), "몸": 종수, "붙임": 붙수}
if __name__ == "__main__":
    g = 'b0 = place(cq.Workplane("XY").box(10.0, 10.0, 10.0, centered=(True, True, False)), "z", (0.0, 0.0, 0.0))\nb1 = place(cq.Workplane("XY").circle(2.0).extrude(6.0), "z", (0.0, 0.0, 8.0))\nresult = b0.union(b1)'
    r = 비교(g, g); assert r["몸수맞음"] and r["종류F1"] == 1 and r["붙임맞음"] == 1 and abs(r["몸겹침"] - 1) < 1e-9, r
    assert 붙임추정(읽기(g))[1] == (0, 4), 붙임추정(읽기(g))   # 위에 얹음 = b0 의 +z 면
    h = g.replace('"z", (0.0, 0.0, 8.0)', '"x", (8.0, 0.0, 0.0)'); assert 붙임추정(읽기(h))[1] == (0, 0), 붙임추정(읽기(h))   # 옆 = +x 면
    assert 비교(g, "b0 = place(망가진")["생성몸"] == 1 and 비교(g, "")["몸겹침"] == 0
    print("코드구조 자체 시험 통과")
    if len(sys.argv) > 1 and sys.argv[1] == "감사": print("감사", 감사()); sys.exit()
    import 과제코드 as K, glob
    for 판 in sys.argv[1:]:
        폴 = f"{뿌리}/out/하네스/{판}/"; ns = sorted(os.path.basename(f)[:-3] for f in glob.glob(폴 + "생성/*.py"))
        print(판, len(ns), 재기(폴, ns, [open(K.자료폴더 + f"글도면/{n}.py", encoding="utf-8").read() for n in ns], [open(폴 + f"생성/{n}.py", encoding="utf-8").read() for n in ns]))
