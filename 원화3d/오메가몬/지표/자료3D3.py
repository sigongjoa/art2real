# -*- coding: utf-8 -*-
"""자료 3D 3 — 두 방식 섞기 (09-29 「그 방식이랑 지금 방식이랑 섞어야지」).
  새 방식: 02 캡처 → 실루엣 → 선 → 면(자료영역)  →  **단면표**(부품마다 높이별 안 x · 밖 x · 앞 z · 뒤 z)
  옛 방식: 단면표 → 켜(볼록 단면) → 마디(이웃 켜의 볼록 껍질 합) · 소체 먼저, 갑주는 그 위 껍질 · 파고듦 검사   (머리_단계.py 의 켜 · 쌓기를 머리 단위로)
    python 자료3D3.py -> out/오메가몬2/자료/3D3/<부품>.stl · 자료3D3.png · 자료3D3.json(단면표)
단면표 읽기: 정면 면(자료3D2_이름.json) 을 높이 y 로 잘라 [xl, xr] · 옆 면(자료3D3_옆이름.json) 을 같은 y 로 잘라 [z앞, z뒤](옆 캡처는 코가 왼쪽 → z = (가운데 − x)).
"""
import os, sys, json
import numpy as np, cv2, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); D3 = J(D, "3D3"); os.makedirs(D3, exist_ok=True); S = 3
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 틀(sil): ys, xs = np.nonzero(sil); return ys.min(), ys.max(), (xs.min() + xs.max()) / 2
class 장:
    def __init__(s, 태그, 위ids, 아래ids, 뒤집=False, 눈ids=None, 눈단위=None):
        """눈금 0~100 = 뿔 끝(위ids 의 위) ~ 턱 끝(아래ids 의 아래). 옆처럼 뿔이 잘린 장은 눈ids 의 중심을 정면의 눈 높이(눈단위)에, 턱 끝을 100 에 맞춘다(09-29)."""
        s.라벨 = np.load(J(D, 태그 + "_영역.npz"))["라벨"]; s.뒤집 = 뒤집
        ys, _ = np.nonzero(np.isin(s.라벨, 아래ids)); 턱 = ys.max() / S
        if 눈ids is not None and 눈단위 is not None:
            ys, _ = np.nonzero(np.isin(s.라벨, 눈ids)); 눈 = ys.mean() / S; s.h = (턱 - 눈) / (100 - 눈단위) * 100; s.y0 = 턱 - s.h; s.y1 = 턱
        else:
            ys, _ = np.nonzero(np.isin(s.라벨, 위ids)); s.y0 = ys.min() / S; s.y1 = 턱; s.h = s.y1 - s.y0
        m = (s.라벨 > 0) & (np.arange(s.라벨.shape[0])[:, None] < s.y1 * S); ys, xs = np.nonzero(m); s.cx = (xs.min() + xs.max()) / 2 / S
    def 자르기(s, ids, y):
        """면(들)을 높이 y(단위)로 잘라 [최소, 최대] (단위 · 정면 x 는 오른쪽 + · 옆은 z 앞 +)"""
        r = int((s.y0 + y / 100 * s.h) * S); r = min(max(r, 0), s.라벨.shape[0] - 1); xs = np.nonzero(np.isin(s.라벨[r], ids))[0]
        if len(xs) == 0: return None
        a, b = (xs.min() / S - s.cx) / s.h * 100, (xs.max() / S - s.cx) / s.h * 100
        return (-b, -a) if s.뒤집 else (a, b)
    def 범위(s, ids):
        ys = np.nonzero(np.isin(s.라벨, ids).any(1))[0]; return ((ys.min() / S - s.y0) / s.h * 100, (ys.max() / S - s.y0) / s.h * 100) if len(ys) else None
정이름 = json.load(open(J(D, "자료3D2_이름.json"), encoding="utf-8")); 정이름["투구"] = 정이름.get("투구", [3, 4, 5, 7, 8])
옆이름 = json.load(open(J(D, "자료3D3_옆이름.json"), encoding="utf-8")) if os.path.exists(J(D, "자료3D3_옆이름.json")) else {}
정 = 장("02_정면", 정이름["뿔"], 정이름["부리"][-1:]); 정눈 = float(np.mean(정.범위(정이름["눈L"] + 정이름["눈R"])))
옆 = 장("02_옆", 옆이름["투구"], 옆이름["부리3"], 뒤집=True, 눈ids=옆이름["눈"], 눈단위=정눈)
print("정면 눈 높이 %.0f · 옆 면 높이 범위(단위):" % 정눈, {int(i): tuple(int(v) for v in 옆.범위([int(i)])) for i in np.unique(옆.라벨) if i > 0})
# ── 단면표 ──
def 단면표(정ids, 옆ids, n=7, 기본z=(4.0, -30.0)):
    r = 정.범위(정ids)
    if not r: return []
    표 = []
    for y in np.linspace(r[0] + 0.5, r[1] - 0.5, n):
        x = 정.자르기(정ids, y); z = 옆.자르기(옆ids, y) if 옆ids else None
        if x is None: continue
        표.append((float(y), float(x[0]), float(x[1]), float(z[0]) if z else 기본z[1], float(z[1]) if z else 기본z[0]))    # y · xl · xr · z뒤 · z앞
    return 표
def 켜(y, xl, xr, zb, zf, 각=0.75, n=24):
    cx, rx, cz, rz = (xl + xr) / 2, max(0.6, (xr - xl) / 2), (zf + zb) / 2, max(0.6, (zf - zb) / 2)
    return [(cx + rx * np.sign(np.cos(t)) * abs(np.cos(t)) ** 각, y, cz + rz * np.sign(np.sin(t)) * abs(np.sin(t)) ** 각) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
def 마디(표, 각=0.75):
    K = [켜(*row, 각=각) for row in 표]; return M.Manifold.batch_boolean([M.Manifold.hull_points(a + b) for a, b in zip(K[:-1], K[1:])], M.OpType.Add)
표들 = {}; 부품 = {}
# 소체: 투구 면 폭(정면) · 옆 투구 면 앞뒤 → 그 안쪽(−3)
표들["소체"] = [(y, xl + 3, xr - 3, zb + 3, zf - 3) for y, xl, xr, zb, zf in 단면표(정이름["투구"], 옆이름.get("투구"), n=9)]
부품["소체"] = 마디(표들["소체"], 각=0.9)
표들["돔"] = 단면표(정이름["투구"], 옆이름.get("투구"), n=9); 부품["돔"] = 마디(표들["돔"], 각=0.9)
표들["뿔"] = 단면표(정이름["뿔"], 옆이름.get("뿔"), n=8, 기본z=(15.0, 5.0))   # 옆 캡처에 뿔이 잘려 없다 → 이마 앞(옆 면 1 의 z) 기본값; 부품["뿔"] = 마디(표들["뿔"], 각=0.6) if len(표들["뿔"]) > 1 else None
for k, ids in (("부리1", 정이름["부리"][:1]), ("부리2", 정이름["부리"][1:2]), ("부리3", 정이름["부리"][2:3])):
    표들[k] = 단면표(ids, 옆이름.get(k), n=5); 부품[k] = 마디(표들[k], 각=0.5) if len(표들[k]) > 1 else None
for k in ("볼L", "볼R"):
    표들[k] = 단면표(정이름[k], 옆이름.get("볼"), n=6); 부품[k] = 마디(표들[k], 각=0.5) if len(표들[k]) > 1 else None
for k in ("눈L", "눈R"):
    표들[k] = 단면표(정이름[k], 옆이름.get("눈"), n=4)
    if len(표들[k]) > 1: 부품["돔"] = 부품["돔"] - 마디([(y, xl, xr, zb - 40, zf + 10) for y, xl, xr, zb, zf in 표들[k]], 각=0.6); 부품["눈구멍" + k[-1]] = 마디([(y, xl + 0.5, xr - 0.5, zb - 2, zb + 0.5) for y, xl, xr, zb, zf in 표들[k]], 각=0.6)
부품 = {k: v for k, v in 부품.items() if v is not None}
for k in list(부품):                                                                                 # 갑주 ∩ 소체 = 0 (옛 규칙)
    if k != "소체": 부품[k] = 부품[k] - 부품["소체"]
out = {}
for k, m in 부품.items():
    mm_ = m.to_mesh(); t = trimesh.Trimesh(np.array(mm_.vert_properties)[:, :3], np.array(mm_.tri_verts), process=False)
    if t.is_empty: continue
    if t.volume < 0: t.invert()
    t.export(J(D3, k + ".stl")); out[k] = t
print("부품", list(out), "· 닫힘", all(t.is_watertight for t in out.values())); json.dump({k: [[round(v, 1) for v in r] for r in 표] for k, 표 in 표들.items()}, open(J(D, "자료3D3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, 표 in 표들.items(): print("  %-5s" % k, " ".join("y%.0f[%.0f,%.0f|%.0f,%.0f]" % r for r in 표[:3]), "…" if len(표) > 3 else "")
# 렌더
ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); 판들 = []; rng = np.random.RandomState(7); 색 = {k: tuple(int(x) for x in rng.randint(70, 230, 3)) for k in out}; 색["소체"] = (40, 40, 45)
for 이름_, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
    th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); W, H, s = 700, 700, 5.0; 삼 = []
    for k, t in out.items():
        V = np.asarray(t.vertices) @ R.T; uv = np.stack([V[:, 0] * s + W / 2, V[:, 1] * s + 60], 1); z = V[:, 2]
        for tri in t.faces: 삼.append((z[tri].mean(), k, uv[tri]))
    삼.sort(key=lambda a: a[0]); im_ = np.full((H, W, 3), 245, np.uint8); ID = np.zeros((H, W), np.int32); idx = {k: i + 1 for i, k in enumerate(out)}
    for _, k, q in 삼: q = np.round(q).astype(np.int32); cv2.fillPoly(im_, [q], 색[k][::-1]); cv2.fillPoly(ID, [q], idx[k])
    im_[cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0] = (0, 0, 0)
    p_ = Image.fromarray(im_[:, :, ::-1]); ImageDraw.Draw(p_).text((8, 6), "단면표 → 마디 · %s (yaw %d°)" % (이름_, yaw), font=ft, fill=(0, 0, 0)); 판들.append(p_)
캡 = Image.open(J(D, "자료영역_셋.png")).convert("RGB"); 캡 = 캡.crop((캡.width // 4, 0, 캡.width // 2, 캡.height // 3)); 캡 = 캡.resize((int(캡.width * 700 / 캡.height), 700))
시트 = Image.new("RGB", (캡.width + sum(p_.width for p_ in 판들) + 40, 700), (250, 250, 248)); 시트.paste(캡, (0, 0)); x = 캡.width + 10
for p_ in 판들: 시트.paste(p_, (x, 0)); x += p_.width + 10
시트.save(J(D, "자료3D3.png")); print(J(D, "자료3D3.png"))
