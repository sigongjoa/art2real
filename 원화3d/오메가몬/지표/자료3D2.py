# -*- coding: utf-8 -*-
"""자료 3D 2 단계 — 기본 도형 바탕 · 치수는 자료에서 (09-29 「면을 그대로가 아니라 기본 도형 바탕으로」).
    python 자료3D2.py -> out/오메가몬2/자료/3D2/<이름>.stl · 자료3D2.png(캡처 정면 | 정면 · 3/4 · 옆 렌더) · 자료3D2.json(읽은 치수)
도형(머리 높이 100 단위 · x 오른쪽 · y 아래 · z 앞):
  돔 = 타원체(정면 실루엣 폭 · 옆 앞뒤 윤곽) · 뿔 = 쐐기(정면 뿔 면 밑동 폭 · 끝 · 옆 기울기) · 차양 = 눈 위 판 쐐기 · 눈구멍 = 돔 앞면에 판 오목
  부리 = 계단 쐐기 셋(정면 가운데 면 폭 · 옆 앞 윤곽 돌출) · 볼 = 얇은 삼각 판(정면 바깥 면). 치수는 정면 면 라벨(자료영역)과 옆 실루엣에서 읽는다.
면 이름은 자리로 정한다(위 가운데 가늘고 긴 것 = 뿔 · 어두운 것 = 눈구멍 · …) — 표를 찍어 확인.
"""
import os, sys, json, math
import numpy as np, cv2, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); D3 = J(D, "3D2"); os.makedirs(D3, exist_ok=True); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); S = 3
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 틀(sil): ys, xs = np.nonzero(sil); return ys.min(), ys.max(), (xs.min() + xs.max()) / 2
# ── 자료 읽기 ──
sil = 읽기(J(D, "02_정면_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; y0, y1, cx = 틀(sil); h = y1 - y0; 라벨 = np.load(J(D, "02_정면_영역.npz"))["라벨"]
im = 읽기(기록["02_정면"]["파일"]); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); g3 = cv2.resize(g, (라벨.shape[1], 라벨.shape[0]))
U = lambda px, py: ((px / S - cx) / h * 100, (py / S - y0) / h * 100)                                  # 3 배 px → 단위
def 반폭(y):                                                                                            # 정면 실루엣 반폭(단위) at y
    r = int(y0 + y / 100 * h); xs = np.nonzero(sil[min(max(r, 0), sil.shape[0] - 1)])[0]; return (xs.max() - xs.min()) / 2 / h * 100 if len(xs) else 0
옆 = 읽기(J(D, "02_옆_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; sy0, sy1, scx = 틀(옆); sh = sy1 - sy0
def 옆z(y, 앞=True):                                                                                    # 옆 실루엣 앞/뒤 윤곽(단위 · 앞 +)
    r = int(sy0 + y / 100 * sh); xs = np.nonzero(옆[min(max(r, 0), 옆.shape[0] - 1)])[0]
    if not len(xs): return 0.0
    return (scx - (xs.min() if 앞 else xs.max())) / sh * 100
면 = {}
for i in [v for v in np.unique(라벨) if v > 0]:
    ys, xs = np.nonzero(라벨 == i); x, y = U(xs.astype(float), ys.astype(float)); 면[int(i)] = dict(cx=float(x.mean()), cy=float(y.mean()), x0=float(x.min()), x1=float(x.max()), y0=float(y.min()), y1=float(y.max()), n=len(xs), 밝기=float(np.median(g3[ys, xs])))
# ── 면 이름 자리로 ──
def 고르기(조건, 키=lambda f: -f["n"]): c = [i for i, f in 면.items() if 조건(f)]; return sorted(c, key=lambda i: 키(면[i]))
뿔 = 고르기(lambda f: f["y0"] < 5 and abs(f["cx"]) < 8 and (f["y1"] - f["y0"]) > 40)[:1]
눈 = 고르기(lambda f: f["밝기"] < 95 and 35 < f["cy"] < 70 and 5 < abs(f["cx"]) < 32 and f["n"] > 400)
눈L = [i for i in 눈 if 면[i]["cx"] < 0][:1]; 눈R = [i for i in 눈 if 면[i]["cx"] > 0][:1]
가운데아래 = sorted(고르기(lambda f: abs(f["cx"]) < 10 and 62 < f["cy"] < 96 and f["밝기"] >= 70)[:3], key=lambda i: 면[i]["cy"])     # 가운데 큰 면 셋 → 위에서 아래로 = 부리 계단
볼L = 고르기(lambda f: -40 < f["cx"] < -18 and 40 < f["cy"] < 80 and f["밝기"] >= 70 and f["y1"] < 92)[:1]; 볼R = 고르기(lambda f: 18 < f["cx"] < 40 and 40 < f["cy"] < 80 and f["밝기"] >= 70 and f["y1"] < 92)[:1]   # 깃(y1 > 92)은 뺀다
이름 = {"뿔": 뿔, "눈L": 눈L, "눈R": 눈R, "부리": 가운데아래[:3], "볼L": 볼L, "볼R": 볼R}
if os.path.exists(J(D, "자료3D2_이름.json")):                                                          # 사람이(없으면 Claude 가) 번호 그림을 보고 붙인 이름이 규칙보다 우선
    손 = json.load(open(J(D, "자료3D2_이름.json"), encoding="utf-8")); 이름 = {k: 손[k] for k in 이름}; 이름["투구"] = 손.get("투구", []); 뿔, 눈L, 눈R, 볼L, 볼R = 이름["뿔"], 이름["눈L"], 이름["눈R"], 이름["볼L"], 이름["볼R"]; 가운데아래 = 이름["부리"]
print("면 이름(자리로):", {k: v for k, v in 이름.items()})
# ── 치수 ──
치 = {}
투 = [면[i] for i in 이름.get("투구", []) if i in 면]; 돔위 = min(f["y0"] for f in 투) if 투 else 33.0; 돔중 = (돔위 + 88) / 2      # 머리 높이 100 에 뿔이 들어 있어 돔은 투구 면의 위(≈33)부터
치["돔"] = dict(위=돔위, 중심y=돔중, 반폭=반폭(돔중), 앞=옆z(돔중), 뒤=옆z(돔중, False), 앞_위=옆z(돔위 + 3), 뒤_위=옆z(돔위 + 3, False))
f = 면[뿔[0]] if 뿔 else None; 치["뿔"] = dict(밑폭=(f["x1"] - f["x0"]) if f else 12, 끝y=f["y0"] if f else 0, 밑y=f["y1"] if f else 40, 앞_끝=옆z(max(0.0, f["y0"] if f else 0)), 앞_밑=옆z(f["y1"] if f else 40))
치["눈"] = {k: (dict(cx=면[v[0]]["cx"], cy=면[v[0]]["cy"], w=면[v[0]]["x1"] - 면[v[0]]["x0"], hgt=면[v[0]]["y1"] - 면[v[0]]["y0"]) if v else None) for k, v in (("L", 눈L), ("R", 눈R))}
치["부리"] = [dict(cy=면[i]["cy"], y0=면[i]["y0"], y1=면[i]["y1"], 반폭=(면[i]["x1"] - 면[i]["x0"]) / 2, 앞=옆z(면[i]["cy"])) for i in 가운데아래[:3]]
치["볼"] = {k: (dict(x0=면[v[0]]["x0"], x1=면[v[0]]["x1"], y0=면[v[0]]["y0"], y1=면[v[0]]["y1"]) if v else None) for k, v in (("L", 볼L), ("R", 볼R))}
치["옆윤곽"] = {int(y): (round(옆z(y), 1), round(옆z(y, False), 1)) for y in range(0, 101, 10)}
json.dump(dict(이름=이름, 치수=치), open(J(D, "자료3D2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
# ── 도형 ──
합 = lambda L: M.Manifold.batch_boolean(list(L), M.OpType.Add)
def 타원체(cx, cy, cz, rx, ry, rz): return M.Manifold.sphere(1.0, 48).scale([rx, ry, rz]).translate([cx, cy, cz])
def 쐐(점): return M.Manifold.hull_points([list(map(float, p)) for p in 점])
부품 = {}
d = 치["돔"]; rx = d["반폭"]; zc = (d["앞"] + d["뒤"]) / 2; rz = (d["앞"] - d["뒤"]) / 2; ry = 88 - d["중심y"]
부품["돔"] = 타원체(0, d["중심y"], zc, rx, ry, rz) - M.Manifold.cube([200, 200, 200], True).translate([0, 88 + 100, 0])   # 투구 위(y≈33)에서 얼굴 y 88 까지
p = 치["뿔"]; bw = p["밑폭"] / 2; 부품["뿔"] = 쐐([(-bw, p["밑y"], p["앞_밑"] - 6), (bw, p["밑y"], p["앞_밑"] - 6), (-bw * 0.9, p["밑y"], p["앞_밑"] + 2), (bw * 0.9, p["밑y"], p["앞_밑"] + 2), (0, p["끝y"], p["앞_끝"] - 2), (0, p["끝y"] + 1, p["앞_끝"] + 1)])
for k, s in (("L", -1), ("R", 1)):
    e = 치["눈"][k]
    if e:
        zf = 옆z(e["cy"]); 차 = 쐐([(s * (abs(e["cx"]) - e["w"] / 2 - 2), e["cy"] - e["hgt"] / 2 - 6, zf - 8), (s * (abs(e["cx"]) + e["w"] / 2 + 4), e["cy"] - e["hgt"] / 2 - 4, zf - 8), (s * (abs(e["cx"]) - e["w"] / 2 - 2), e["cy"] - e["hgt"] / 2 - 1, zf + 3), (s * (abs(e["cx"]) + e["w"] / 2 + 4), e["cy"] - e["hgt"] / 2 + 1, zf + 3), (s * (abs(e["cx"]) - e["w"] / 2 - 2), e["cy"] - e["hgt"] / 2 - 6, zf + 2), (s * (abs(e["cx"]) + e["w"] / 2 + 4), e["cy"] - e["hgt"] / 2 - 4, zf + 2)])
        부품["차양" + k] = 차
        구멍 = M.Manifold.cube([e["w"], e["hgt"], 30], True).translate([e["cx"], e["cy"], zf + 15 - 4]); 부품["돔"] = 부품["돔"] - 구멍; 부품["눈구멍" + k] = M.Manifold.cube([e["w"] - 1, e["hgt"] - 1, 1.5], True).translate([e["cx"], e["cy"], zf - 4])
for j, b in enumerate(치["부리"]):
    zb = b["앞"]; zt = 옆z(b["y0"]); 부품["부리%d" % (j + 1)] = 쐐([(-b["반폭"], b["y0"], zt - 10), (b["반폭"], b["y0"], zt - 10), (-b["반폭"], b["y0"], zt), (b["반폭"], b["y0"], zt), (-b["반폭"] * 0.7, b["y1"], zb - 10), (b["반폭"] * 0.7, b["y1"], zb - 10), (0, b["y1"], zb)])
for k, s, ids_ in (("L", -1, 볼L), ("R", 1, 볼R)):
    if not ids_: continue
    m_ = (라벨 == ids_[0]).astype(np.uint8); cs__, _ = cv2.findContours(m_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); poly = cv2.approxPolyDP(max(cs__, key=cv2.contourArea), 2.0, True).reshape(-1, 2).astype(float)
    P = [U(px, py) for px, py in poly]; 안 = min(P, key=lambda q: abs(q[0]))[0]; 밖 = max(P, key=lambda q: abs(q[0]))[0]
    zof = lambda x, y: 옆z(y) - 6 - 12 * (abs(x) - abs(안)) / max(1e-3, abs(밖) - abs(안))                  # 볼 판: 안쪽은 얼굴 앞면 가까이 · 바깥으로 갈수록 뒤로(날개)
    부품["볼" + k] = 쐐([(x, y, zof(x, y)) for x, y in P] + [(x, y, zof(x, y) - 2.5) for x, y in P])
for n_, m in 부품.items():
    mm_ = m.to_mesh(); t = trimesh.Trimesh(np.array(mm_.vert_properties)[:, :3], np.array(mm_.tri_verts), process=False)
    if t.volume < 0: t.invert()
    t.export(J(D3, n_ + ".stl")); 부품[n_] = t
print("부품", list(부품), "· 닫힘", all(t.is_watertight for t in 부품.values()))
# ── 렌더 ──
ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); 판들 = []; rng = np.random.RandomState(7); 색 = {n_: tuple(int(x) for x in rng.randint(70, 230, 3)) for n_ in 부품}
for 이름_, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
    th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); W, H, s = 700, 700, 5.0; 삼 = []
    for n_, t in 부품.items():
        V = np.asarray(t.vertices) @ R.T; uv = np.stack([V[:, 0] * s + W / 2, V[:, 1] * s + 60], 1); z = V[:, 2]
        for tri in t.faces: 삼.append((z[tri].mean(), n_, uv[tri]))
    삼.sort(key=lambda a: a[0]); im_ = np.full((H, W, 3), 245, np.uint8); ID = np.zeros((H, W), np.int32); idx = {n_: k + 1 for k, n_ in enumerate(부품)}
    for _, n_, q in 삼: q = np.round(q).astype(np.int32); cv2.fillPoly(im_, [q], 색[n_][::-1]); cv2.fillPoly(ID, [q], idx[n_])
    im_[cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0] = (0, 0, 0)
    p_ = Image.fromarray(im_[:, :, ::-1]); ImageDraw.Draw(p_).text((8, 6), "기본 도형 · %s (yaw %d°)" % (이름_, yaw), font=ft, fill=(0, 0, 0)); 판들.append(p_)
캡 = Image.open(J(D, "자료영역_셋.png")).convert("RGB"); 캡 = 캡.crop((캡.width // 4, 0, 캡.width // 2, 캡.height // 3)); 캡 = 캡.resize((int(캡.width * 700 / 캡.height), 700))
시트 = Image.new("RGB", (캡.width + sum(p_.width for p_ in 판들) + 40, 700), (250, 250, 248)); 시트.paste(캡, (0, 0)); x = 캡.width + 10
for p_ in 판들: 시트.paste(p_, (x, 0)); x += p_.width + 10
시트.save(J(D, "자료3D2.png")); print(J(D, "자료3D2.png"))
