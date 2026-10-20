# 118b 결과를 실제 렌더로 — 부품마다: 입력(155°) · 시점 맞춰 1 등으로 고른 후보 · 정답 · (동점이면) 정답과 동점 변형의 반 자른 단면 렌더 · 10-20
# 사용(cadrille venv · ART_MEM_GB=10): 렌더118.py → out/설명/캐드부품/임베딩117/렌더118_맞힘.png · 렌더118_동점.png
import json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
import 설계116 as S, 데이터117 as Q, 회전118 as R
D = Q.D; 색 = json.load(open(D + "색인.json", encoding="utf-8")); 점 = json.load(open(D + "회전118b_재채점.json", encoding="utf-8"))["점수들"]["T2"]
사양 = lambda c: json.loads(c["코드"])
def 반단면(spec, a, e):   # CAD 에서 보는 쪽 반(y < 가운데)을 잘라 냄 — 자른 면이 솔리드로 닫혀 속이 보임(trimesh 뚜껑은 shapely 가 없어 못 씀)
    import cadquery as cq
    w = S.짓기(spec); bb = w.val().BoundingBox(); cy = (bb.ymin + bb.ymax) / 2
    칼 = cq.Workplane("XY").box(400, 200, 400).translate((0, cy - 100, (bb.zmin + bb.zmax) / 2)); m, *_ = S.메시(w.cut(칼)); return Q.렌더(m, a, e)[0]
def 줄(r, s):
    입 = cv2.imdecode(np.fromfile(D + "렌더/" + r["정답"]["이름"] + "_155.png", np.uint8), 1)[..., ::-1].copy()
    후 = [r["정답"]] + r["T2"]; s = np.array(s); k = int(np.argmax(s)); 동 = [j for j in range(1, 6) if np.isclose(s[j], s[0], atol=1e-6)]
    m0, *_ = S.메시(S.짓기(사양(후[0]))); _, a, e, _ = R.맞추기(m0, 입)
    mk, *_ = S.메시(S.짓기(사양(후[k]))); _, ak, ek, _ = R.맞추기(mk, 입)
    out = [(입, "입력(155°)"), (Q.렌더(mk, ak, ek)[0], f"고른 후보 · {ak}° · {'정답' if k == 0 else 후[k]['변형']}"), (Q.렌더(m0, a, e)[0], f"정답 · {a}°")]
    if 동:
        v = 후[동[0]]; mv, *_ = S.메시(S.짓기(사양(v)))
        out += [(반단면(사양(후[0]), 35, 25), "정답 반 자름"), (반단면(사양(v), 35, 25), f"동점 변형 반 자름 · {v['변형']}")]
    return out, bool(동), k == 0 and not 동
if __name__ == "__main__":
    맞, 동점 = [], []
    for r, s in zip(색, 점):
        if len(맞) >= 6 and len(동점) >= 6: break
        try: 칸, 동, 엄 = 줄(r, s)
        except Exception as ex: print("건너뜀", ex); continue
        if 동 and len(동점) < 6: 동점.append((r["정답"]["종류"], 칸))
        elif 엄 and len(맞) < 6: 맞.append((r["정답"]["종류"], 칸))
    for 이름, 목록, 제목 in (("맞힘", 맞, "118b 맞힌 부품 — 입력 그림 한 장에서 시점을 찾고(가운데) 정답과 같은 후보를 고름"), ("동점", 동점, "118b 동점 부품 — 겉(입력 · 고른 후보 · 정답)은 같아 보이지만, 반을 잘라 보면 속 깊이가 다르다")):
        n = max(len(x[1]) for x in 목록); fig, ax = plt.subplots(len(목록), n, figsize=(3.2 * n, 3.2 * len(목록)))
        for i, (종, 칸) in enumerate(목록):
            for j in range(n):
                a_ = ax[i, j]; a_.axis("off")
                if j < len(칸): a_.imshow(칸[j][0]); a_.set_title(f"{종} · {칸[j][1]}" if j == 0 else 칸[j][1], fontsize=9)
        fig.suptitle(제목, fontsize=14); plt.tight_layout(); plt.savefig(D + f"렌더118_{이름}.png", dpi=70); plt.close(fig); print("저장", 이름, len(목록))
