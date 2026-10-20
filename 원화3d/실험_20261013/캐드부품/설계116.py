# 판정기준116 — 부품 낱말 코드 → CadQuery 3D → 설계도(3면도 실선 + 숨은선 · 중심선 · 앞 단면) → 비교기 · 생성기 실행 · 결정성 · 변별 시험 · 10-20
# 사용(venv · ART_MEM_GB=10): 설계116.py 시험 [수=200] → out/설명/캐드부품/설계116/결과.json · 예시.png
import sys, os, json, copy, tempfile, numpy as np, cv2
O = "G:/art2real/out/설명/캐드부품/"; D = O + "설계116/"; N = 128; K = 6

# ── 1. 코드 낱말: JSON 사양 → CadQuery ──
def 무작위(rng):
    kind = rng.choice(["상자", "원기둥", "원뿔", "돔", "컵", "계단축", "그릇"], p=[.22, .14, .12, .12, .16, .12, .12])
    s = {"바탕": {"종류": str(kind)}, "특징": [], "기울임": float(rng.choice([0, 0, 0, rng.uniform(15, 35)]))}
    b = s["바탕"]; R = float(rng.uniform(15, 30)); H = float(rng.uniform(12, 40))
    if kind == "상자": b.update(w=float(rng.uniform(30, 60)), d=float(rng.uniform(20, 50)), h=float(rng.uniform(8, 30)))
    elif kind in ("원기둥", "원뿔", "돔"): b.update(r=R, h=H)
    elif kind == "컵": b.update(r=R, h=H, 안r=R * float(rng.uniform(.6, .85)), 바닥=H * float(rng.uniform(.15, .5)))
    elif kind == "계단축": b.update(r=R, h=H, r2=R * float(rng.uniform(.4, .75)), h1=H * float(rng.uniform(.3, .6)))
    elif kind == "그릇": b.update(r=R, h=H * .7, 두께=float(rng.uniform(2, 5)))
    평 = kind in ("상자", "원기둥", "컵", "계단축")   # 윗면이 평평해 구멍 · 홈을 낼 수 있음
    if 평:
        for _ in range(int(rng.integers(0, 3))):
            f = str(rng.choice(["관통", "막힌", "홈"]))
            s["특징"].append({"종류": f, "x": float(rng.uniform(-.35, .35)), "y": float(rng.uniform(-.35, .35)), "크기": float(rng.uniform(.08, .18)), "깊이": float(rng.uniform(.3, .7))})
    if kind == "상자" and rng.random() < .4: s["특징"].append({"종류": "필렛", "크기": float(rng.uniform(1.5, 5))})
    return s
def 짓기(s):   # → cq.Workplane(솔리드 하나)
    import cadquery as cq
    b = s["바탕"]; k = b["종류"]
    if k == "상자": w = cq.Workplane("XY").box(b["w"], b["d"], b["h"], centered=(True, True, False)); 폭 = (b["w"], b["d"]); 위 = b["h"]
    else:
        R, H = b["r"], b["h"]; 폭 = (2 * R, 2 * R); 위 = H
        if k == "원기둥": pts = [(0, 0), (R, 0), (R, H), (0, H)]
        elif k == "원뿔": pts = [(0, 0), (R, 0), (0, H)]
        elif k == "돔": t = np.linspace(0, np.pi / 2, 24); pts = [(0, 0)] + [(R * np.cos(a), H * np.sin(a)) for a in t[:-1]] + [(0, H)]
        elif k == "컵": pts = [(0, 0), (R, 0), (R, H), (b["안r"], H), (b["안r"], b["바닥"]), (0, b["바닥"])]
        elif k == "계단축": pts = [(0, 0), (R, 0), (R, b["h1"]), (b["r2"], b["h1"]), (b["r2"], H), (0, H)]
        elif k == "그릇":
            t = np.linspace(0, np.pi / 2, 20); T = b["두께"]; 바 = [(R * np.sin(a), H * (1 - np.cos(a))) for a in t]; 안 = [((R - T) * np.sin(a), T + (H - T) * (1 - np.cos(a))) for a in t[::-1]]
            pts = [(0, 0)] + 바[1:] + 안[:-1] + [(0, T)]
        w = cq.Workplane("XZ").polyline([(float(x), float(y)) for x, y in pts]).close().revolve(360, (0, 0, 0), (0, 1, 0))
    for f in s["특징"]:
        if f["종류"] == "필렛":
            try: w = w.edges("|Z").fillet(f["크기"])
            except Exception: pass
            continue
        cx, cy, r = f["x"] * 폭[0], f["y"] * 폭[1], f["크기"] * min(폭)
        try:
            top = w.faces(">Z").workplane(origin=(0, 0, 위)).center(cx, cy)
            w = top.hole(2 * r) if f["종류"] == "관통" else top.hole(2 * r, f["깊이"] * 위) if f["종류"] == "막힌" else top.rect(2 * r, 1.4 * r).cutBlind(-f["깊이"] * 위)
        except Exception: pass
    if s["기울임"]: w = w.rotate((0, 0, 0), (1, 0, 0), s["기울임"])
    return w

# ── 2. 3D → 정규 메시 · 설계도 ──
def 메시(w):
    import cadquery as cq, trimesh
    p = tempfile.mktemp(suffix=".stl"); cq.exporters.export(w, p, tolerance=0.05, angularTolerance=0.1); m = trimesh.load(p, force="mesh"); os.remove(p)
    c = m.bounds.mean(0); e = float(m.extents.max()); return m, (m.vertices - c) / e, c, e
def 화소(a, b): return (a + .55) / 1.1 * N - .5, (.55 - b) / 1.1 * N - .5   # 숨은선88.그리기 의 광선 격자와 같은 좌표(가로 a · 세로 b)
def 중심선(s, c, e):   # 회전축(바탕이 회전체 · 원기둥)을 세 뷰에 · 축이 시선과 나란하면 + 표 — 사양에서 계산
    out = np.zeros((3, N, N), np.uint8)
    if s["바탕"]["종류"] == "상자": return out > 0
    t = np.radians(s["기울임"]); Rx = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    h = s["바탕"]["h"]; p0, p1 = ((Rx @ np.array([0, 0, -.1 * h]) - c) / e), ((Rx @ np.array([0, 0, 1.1 * h]) - c) / e)
    for j, (가, 세) in enumerate(((0, 1), (0, 2), (1, 2))):   # 위: x · y / 앞: x · z / 옆: y · z (숨은선88 과 같음)
        a0, b0 = 화소(p0[가], p0[세]); a1, b1 = 화소(p1[가], p1[세])
        if np.hypot(a1 - a0, b1 - b0) < 3: m = ((a0 + a1) / 2, (b0 + b1) / 2); cv2.line(out[j], (int(m[0] - 4), int(m[1])), (int(m[0] + 4), int(m[1])), 1); cv2.line(out[j], (int(m[0]), int(m[1] - 4)), (int(m[0]), int(m[1] + 4)), 1)
        else: cv2.line(out[j], (int(round(a0)), int(round(b0))), (int(round(a1)), int(round(b1))), 1)
    return out > 0
def 단면(v, f):   # 가운데 y = 0 평면에서 앞(x · z) 격자 점유 — open3d 점유(가벼움 · trimesh.contains 금지)
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    u = (np.arange(N) + .5) / N * 1.1 - .55; A, B = np.meshgrid(u, -u); q = np.stack([A, np.zeros_like(A), B], -1).reshape(-1, 3).astype(np.float32)
    return sc.compute_occupancy(o3d.core.Tensor(q)).numpy().reshape(N, N) > 0
def 점유(m, n=48):   # 3D 가 실제로 바뀌었나 재는 자(원 좌표 · 원본과 변형이 같은 격자를 쓰도록 고정 상자 ±80 mm)
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(m.vertices, np.float32)), o3d.core.Tensor(np.asarray(m.faces, np.uint32)))
    g = (np.arange(n) + .5) / n * 160 - 80; X, Y, Z = np.meshgrid(g, g, g, indexing="ij"); q = np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32)
    return sc.compute_occupancy(o3d.core.Tensor(q)).numpy().reshape(n, n, n) > 0
def 설계도(s):   # → dict 채널(bool N×N)
    import 숨은선88 as H88
    w = 짓기(s); m, v, c, e = 메시(w)
    if not w.val().isValid(): raise ValueError("솔리드 깨짐")   # 116b: 메시 watertight 말고 CAD 유효성(축 위 꼭짓점 회전체가 거짓 실패)
    선 = H88.그리기(v, m.faces); cl = 중심선(s, c, e); d = {}
    for j, nm in enumerate(("위", "앞", "옆")): d[nm + "실"], d[nm + "숨"], d[nm + "중심"] = 선[j][0], 선[j][1], cl[j]
    d["단면"] = 단면(v, m.faces); d["_점유"] = 점유(m); return d

# ── 3. 비교기 ──
def _F(a, b):
    if not a.any() and not b.any(): return 1.0
    k = np.ones((3, 3), np.uint8); ad, bd = cv2.dilate(a.astype(np.uint8), k) > 0, cv2.dilate(b.astype(np.uint8), k) > 0
    p = (a & bd).sum() / max(a.sum(), 1); r = (b & ad).sum() / max(b.sum(), 1); return 2 * p * r / max(p + r, 1e-9)
def 어긋남(d1, d2, 전체=True):
    ch = [nm + t for nm in ("위", "앞", "옆") for t in ("실", "숨")] + ([nm + "중심" for nm in ("위", "앞", "옆")] if 전체 else [])
    v = [1 - _F(d1[c], d2[c]) for c in ch]
    if 전체: i = (d1["단면"] & d2["단면"]).sum(); u = (d1["단면"] | d2["단면"]).sum(); v.append(1 - (i / u if u else 1))
    return float(np.max(v)), float(np.mean(v))   # 116b: 최댓값(판정) · 평균(116 과 맞대기)
def 변형들(s, rng, n=5):
    out = []; 수 = [("바탕", k) for k, x in s["바탕"].items() if isinstance(x, float)] + [("특징", i, k) for i, f in enumerate(s["특징"]) for k in ("x", "y", "크기", "깊이") if k in f and not (k == "깊이" and f["종류"] == "관통")]
    for t in range(n):
        v = copy.deepcopy(s); 고 = rng.integers(0, 4) if (s["특징"] or s["기울임"]) else 0
        if 고 == 1 and s["특징"]: v["특징"].pop(int(rng.integers(len(v["특징"])))); 종 = "특징 빼기"
        elif 고 == 2 and s["기울임"]: v["기울임"] += float(rng.choice([-5, 5])); 종 = "기울기 ±5°"
        else:
            p = 수[int(rng.integers(len(수)))]; 배 = float(rng.choice([.85, .9, 1.1, 1.15]))
            if p[0] == "바탕": v["바탕"][p[1]] *= 배; 종 = f"바탕 {p[1]} ×{배}"
            else:
                f = v["특징"][p[1]]
                if p[2] in ("x", "y"): f[p[2]] += float(rng.choice([-.08, .08])); 종 = f"특징 {f['종류']} 자리"
                else: f[p[2]] *= 배; 종 = f"특징 {f['종류']} {p[2]} ×{배}"
        out.append((종, v))
    return out

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True); n = int(sys.argv[2]) if len(sys.argv) > 2 else 200; rng = np.random.default_rng(116)
    실행 = 0; 결정 = 0; 같음 = 0; 변 = {"전체": [], "3면도만": []}; 평균 = {"전체": [], "3면도만": []}; 종류별 = {}; 예 = []
    for t in range(n):
        s = 무작위(rng)
        try: d = 설계도(s)
        except Exception as ex: print(t, s["바탕"]["종류"], "실패", type(ex).__name__, str(ex)[:60], flush=True); continue
        실행 += 1; d2 = 설계도(s); 결정 += all((d[c] == d2[c]).all() for c in d if not c.startswith("_"))
        for 종, v in 변형들(s, rng):
            try: dv = 설계도(v)
            except Exception: continue
            바뀜 = (d["_점유"] ^ dv["_점유"]).sum() / max(d["_점유"].sum(), 1)
            if 바뀜 < .01: 같음 += 1; continue   # 116b: 3D 가 1 % 도 안 바뀐 변형은 변별에서 뺌
            for 판 in 변: a, a평 = 어긋남(d, dv, 판 == "전체"); 변[판].append(a); 평균[판].append(a평); 종류별.setdefault((s["바탕"]["종류"], 종.split(" ×")[0]), []).append((판, a))
        if len(예) < 6: 예.append((s, d))
    결 = {"코드 수": n, "실행": 실행 / n, "결정성": 결정 / max(실행, 1), "3D 거의 같은 변형(뺌)": 같음, "변별에 센 변형": len(변["전체"])}
    for 판, a in 변.items(): a = np.array(a); 결[f"구별 못 함({판})"] = float((a < .01).mean()); 결[f"어긋남 중앙({판})"] = float(np.median(a)); 결[f"구별 못 함·평균 집계({판})"] = float((np.array(평균[판]) < .01).mean())
    결["구별 못 함 종류(3면도만 · 많은 순)"] = sorted([(f"{k[0]} · {k[1]}", round(float(np.mean([x < .01 for 판, x in v if 판 == "3면도만"])), 2), round(float(np.mean([x < .01 for 판, x in v if 판 == "전체"])), 2), len(v) // 2) for k, v in 종류별.items()], key=lambda z: -z[1])[:12]
    print(json.dumps(결, ensure_ascii=False, indent=1)); json.dump(결, open(D + "결과b.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    fig, ax = plt.subplots(len(예), 4, figsize=(14, 3.4 * len(예)))
    for r, (s, d) in enumerate(예):
        for j, nm in enumerate(("위", "앞", "옆")):
            im = np.ones((N, N, 3)); im[d[nm + "숨"]] = (.45, .65, 1); im[d[nm + "실"]] = 0; im[d[nm + "중심"]] = (.9, .5, .1); ax[r, j].imshow(im); ax[r, j].set_title(f"{s['바탕']['종류']} · {nm} (주황 = 중심선)"); ax[r, j].axis("off")
        ax[r, 3].imshow(d["단면"], cmap="Greys"); ax[r, 3].set_title("앞 단면"); ax[r, 3].axis("off")
    plt.tight_layout(); plt.savefig(D + "예시b.png", dpi=60)
