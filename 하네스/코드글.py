# 사양(JSON · 조립124) → CadQuery 파이썬 글 · 판 145~ 언어 모델의 정답 · 10-24 사용자 「cadquery 를 output 으로 하는 LLM」
# 정답 「코드」 는 JSON 사양(몸 · 바탕 · 특징 · 축 · 자리)이고 조립124.짓기 가 CadQuery 로 지었다 → 같은 형상을 내는 CadQuery 글로 옮김
# 글 = 몸마다 한 줄(바탕 + 특징 사슬) · place(w, 축, 자리) 로 눕히고 가운데 맞춰 놓기 · result = 합집합 · 머리말(import · place)은 실행할 때 붙임(모델은 몸 줄만 씀)
# 원래 짓기가 try 로 건너뛴 특징(필렛 · 구멍 실패)은 글에서도 뺌 — 줄마다 실제로 지어 보고 남김
import numpy as np
머리말 = '''import cadquery as cq
def place(w, axis, pos):
    if axis == "x": w = w.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "y": w = w.rotate((0, 0, 0), (1, 0, 0), -90)
    bb = w.val().BoundingBox()
    return w.translate((pos[0] - (bb.xmin + bb.xmax) / 2, pos[1] - (bb.ymin + bb.ymax) / 2, pos[2] - (bb.zmin + bb.zmax) / 2))
'''
def 수(v): return f"{float(v):.1f}"
def 점들(pts): return "[" + ", ".join(f"({수(x)}, {수(y)})" for x, y in pts) + "]"
def 바탕글(b):   # → (CadQuery 식, 폭, 위)
    k = b["종류"]
    if k == "상자": return f'cq.Workplane("XY").box({수(b["w"])}, {수(b["d"])}, {수(b["h"])}, centered=(True, True, False))', (b["w"], b["d"]), b["h"]
    R, H = b["r"], b["h"]
    if k == "원기둥": return f'cq.Workplane("XY").circle({수(R)}).extrude({수(H)})', (2 * R, 2 * R), H
    if k == "원뿔": return f'cq.Workplane("XY").add(cq.Solid.makeCone({수(R)}, 0, {수(H)}))', (2 * R, 2 * R), H
    if k == "돔": t = np.linspace(0, np.pi / 2, 7); pts = [(0, 0)] + [(R * np.cos(a), H * np.sin(a)) for a in t[:-1]] + [(0, H)]   # 원래 24 점 → 7 점(글 짧게 · 왕복 IoU 로 확인)
    elif k == "컵": pts = [(0, 0), (R, 0), (R, H), (b["안r"], H), (b["안r"], b["바닥"]), (0, b["바닥"])]
    elif k == "계단축": pts = [(0, 0), (R, 0), (R, b["h1"]), (b["r2"], b["h1"]), (b["r2"], H), (0, H)]
    elif k == "그릇":
        t = np.linspace(0, np.pi / 2, 6); T = b["두께"]; 바 = [(R * np.sin(a), H * (1 - np.cos(a))) for a in t]; 안 = [((R - T) * np.sin(a), T + (H - T) * (1 - np.cos(a))) for a in t[::-1]]
        pts = [(0, 0)] + 바[1:] + 안[:-1] + [(0, T)]
    else: raise KeyError(k)
    return f'cq.Workplane("XZ").polyline({점들(pts)}).close().revolve(360, (0, 0, 0), (0, 1, 0))', (2 * R, 2 * R), H
def 특징글(f, 폭, 위):
    if f["종류"] == "필렛": return f'.edges("|Z").fillet({수(f["크기"])})'
    cx, cy, r = f["x"] * 폭[0], f["y"] * 폭[1], f["크기"] * min(폭); 판 = f'.faces(">Z").workplane(origin=(0, 0, {수(위)})).center({수(cx)}, {수(cy)})'
    if f["종류"] == "관통": return 판 + f".hole({수(2 * r)})"
    if f["종류"] == "막힌": return 판 + f".hole({수(2 * r)}, {수(f['깊이'] * 위)})"
    return 판 + f".rect({수(2 * r)}, {수(1.4 * r)}).cutBlind({수(-f['깊이'] * 위)})"
def 실행(글):   # 머리말 + 글 → cq.Workplane(result)
    ns = {}; exec(머리말 + 글, ns); return ns["result"]
def 글로(c):   # 사양 → 글(머리말 빼고) · 몸마다 특징을 하나씩 붙여 지어 보고 실패하면 뺌(원래 짓기의 try 와 같게)
    import cadquery as cq
    줄 = []
    for i, s in enumerate(c["몸"]):
        식, 폭, 위 = 바탕글(s["바탕"]); ns = {"cq": cq}
        for f in s["특징"]:
            후보 = 식 + 특징글(f, 폭, 위)
            try: w = eval(후보, ns); w.val(); 식 = 후보
            except Exception: pass
        if s.get("기울임"): 식 += f".rotate((0, 0, 0), (1, 0, 0), {수(s['기울임'])})"
        줄.append(f'b{i} = place({식}, "{s["축"]}", ({", ".join(수(v) for v in s["자리"])}))')
    줄.append("result = " + ".union(".join(f"b{i}" for i in range(len(c["몸"]))) + ")" * (len(c["몸"]) - 1))
    return "\n".join(줄)
if __name__ == "__main__":   # 자체 시험: 부품 몇 개 왕복(사양 짓기 vs 글 실행) 부피 IoU
    import sys, json; sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품")
    import 모델124 as B, 조립124 as C, 설계116 as S
    부품 = sys.argv[1:] or ["12050", "12000", "12010", "12020", "12030"]; 겹들 = []
    for p in 부품:
        s = json.load(open(B.D + f"사양/{p}.json", encoding="utf-8")); 글 = 글로(s["코드"]); 가 = C.메시(C.짓기(json.loads(json.dumps(s["코드"]))))[0]; 나 = C.메시(실행(글))[0]
        v = S.점유(가); u = S.점유(나); 겹 = float((v & u).sum() / max((v | u).sum(), 1)); 겹들.append(겹)
        print(p, "글자", len(글), "부피 IoU", round(겹, 3))
    print("첫 부품 글:\n" + 글로(json.load(open(B.D + f"사양/{부품[0]}.json", encoding="utf-8"))["코드"]))
    assert min(겹들) > .9, 겹들; print("코드글 시험 통과")
