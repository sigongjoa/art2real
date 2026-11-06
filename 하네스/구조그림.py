# 부품 구조 그림 — 몸마다 색 · 정답 붙임 나무(몸 · 종류 · 어느 몸의 어느 면) · 생성 코드도 몸마다 색
# 11-06 사용자 「원형에서 부품의 수와 연결관계를 표현할 수 있지? 생성된 부품의 수와 연결관계 또는 iou 를 비교해야」 → 「시각적으로 보여줘」
# 사용: python 하네스/구조그림.py <부품> [판 …] → out/하네스/구조_<부품>.png
import sys, os, re, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
면이름 = ["+x", "-x", "+y", "-y", "+z", "-z"]
색들 = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]
def 몸들(글):   # 글 → [(이름, 식 줄)] · 몸 줄만
    return [(m.group(1), l) for l in 글.splitlines() if (m := re.match(r"(b\d+) = ", l))]
def 종류(줄):
    if "makeCone" in 줄 or "cone(" in 줄: return "원뿔"
    if ".box(" in 줄: return "상자"
    if ".revolve(" in 줄: return "회전체"
    if ".circle(" in 줄: return "원기둥"
    return "?"
def 망(줄):   # 몸 줄 하나를 지어 삼각형으로 · 실패면 None
    import 코드글, cadquery as cq
    try:
        ns = {}; exec(코드글.머리말 + 줄, ns); w = ns[줄.split(" = ")[0]]; v, t = w.val().tessellate(0.8)
        return np.array([(p.x, p.y, p.z) for p in v]), np.array(t)
    except Exception: return None
def 그리기(n, 판들=()):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import 모델124 as B, 과제코드 as K
    plt.rcParams["font.family"] = "Malgun Gothic"
    사양 = next(r for r in B.색인() if f"{r['i']:05d}" == n)["코드"]; 사양 = 사양 if isinstance(사양, dict) else json.loads(사양)
    글들 = [("정답", open(K.자료폴더 + f"글도면/{n}.py", encoding="utf-8").read())] + [(f"판 {p}", open(f"{뿌리}/out/하네스/{p}/생성/{n}.py", encoding="utf-8").read()) for p in 판들]
    fig = plt.figure(figsize=(6 * (len(글들) + 1), 7))
    for k, (제목, 글) in enumerate(글들):
        a = fig.add_subplot(1, len(글들) + 1, k + 2 if k else 1, projection="3d"); 다 = []
        for i, (이름, 줄) in enumerate(몸들(글)):
            m = 망(줄)
            if m is None: continue
            v, t = m; 다.append(v); a.add_collection3d(Poly3DCollection(v[t], facecolor=색들[i % 8], edgecolor="none", alpha=.9))
        if 다:
            v = np.concatenate(다); c = (v.max(0) + v.min(0)) / 2; r = (v.max(0) - v.min(0)).max() / 2
            for s, cc in zip("xyz", c): getattr(a, f"set_{s}lim")(cc - r, cc + r)
        a.view_init(25, -60); a.set_axis_off()
        목 = ", ".join(f"b{i} {종류(줄)}" for i, (_, 줄) in enumerate(몸들(글)))
        a.set_title(f"{제목} — 몸 {len(몸들(글))} 개\n{목}", fontsize=12, weight="bold" if k == 0 else None)
    a = fig.add_subplot(1, len(글들) + 1, 2); a.axis("off"); a.set_title("정답 붙임 나무 (몸 ← 어느 몸의 어느 면)", fontsize=12, weight="bold")
    몸 = 사양["몸"]; 깊 = [0] * len(몸)
    for i, s in enumerate(몸):
        if i: 깊[i] = 깊[s["붙임"][0]] + 1
    for i, s in enumerate(몸):
        x, y = 깊[i], -i
        if i:
            j, f = s["붙임"]; a.annotate("", (x - .32, y), (깊[j] + .32, -j), arrowprops=dict(arrowstyle="<-", color="#555", lw=1.5))
            a.text((x + 깊[j]) / 2 + .12, (y - j) / 2, f"b{j} 의 {면이름[f]} 면", fontsize=11, color="#333", ha="left", va="center")
        a.text(x, y, f"b{i} {s['바탕']['종류']}", ha="center", va="center", fontsize=13, color="white", weight="bold", bbox=dict(boxstyle="round,pad=.4", fc=색들[i % 8], ec="none"))
    a.set_xlim(-.6, max(깊) + 1.4); a.set_ylim(-len(몸) + .4, .6)
    fig.suptitle(f"부품 {n} — 몸마다 색 · 정답은 붙임 나무로 연결 관계가 정해져 있다", fontsize=16, weight="bold"); fig.tight_layout(rect=(0, 0, 1, .92)); p = f"{뿌리}/out/하네스/구조_{n}.png"; fig.savefig(p, dpi=70); plt.close(fig); return p
if __name__ == "__main__":
    assert 종류('b0 = place(cq.Workplane("XY").box(1, 2, 3), "z", (0, 0, 0))') == "상자" and 종류("x.add(cq.Solid.makeCone(1, 0, 2))") == "원뿔"
    print(그리기(sys.argv[1], sys.argv[2:]))
