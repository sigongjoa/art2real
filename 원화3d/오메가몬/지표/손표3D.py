# -*- coding: utf-8 -*-
"""손 단면표 → 옛 낱말 → 오버레이 (2026-09-29 밤 · 패널 권고 3~4 · 「알아서 고쳐서 제대로 되게」).
    python 손표3D.py -> out/오메가몬2/자료/손표/<부품>.stl · 손표3D_오버레이.png(정면 · 옆 캡처 위 · 첫 줄) · 손표3D.png(정면 · 3/4 · 옆 렌더)
단위 = 머리 높이 100(뿔 끝 0 · 턱 끝 100) · x 오른쪽 + · y 아래 + · z 앞 +. 표는 02_정면_격자.png · 02_옆_격자.png 를 **눈으로 읽어** 적었다(자동 자르기 아님 · 기본값 없음).
옛 낱말: 켜(볼록 단면) → 쌓기(마디) · 껍질(소체 앞면에서 띄운 판) · 기둥(정면 다각형 밀기) · 정리(앞 부품 합을 한 번에 뺌). 소체 = 머리 통만(날개 · 눈 제외) · 좌우 대칭.
"""
import os, sys, json
import numpy as np, cv2, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); DO = J(D, "손표"); os.makedirs(DO, exist_ok=True); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); S = 3
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
합 = lambda L: M.Manifold.batch_boolean(list(L), M.OpType.Add)
# ── 손 단면표 (격자에서 읽음) ── y · 반폭(x 대칭) · z앞 · z뒤 · 읽은 것
# 정면 실루엣: y35 ±9 · y40 ±15 · y45 ±20 · y50 ±22 · y55 ±23 · y60 ±25 · y65 ±26(볼 시작) — 옆: y40 z 10/−6 · y50 10/−18 · y60 22/−30 · y70 23/−29 · y85 35/−35 · y100 11/−31 (앞/뒤)
소체표 = [(36, 7, 6, -5, "투구 시작"), (42, 14, 8, -10, "관자놀이 위"), (50, 19, 8, -16, "차양 높이"), (58, 21, 6, -22, "눈 위"), (66, 20, 4, -24, "눈 높이"), (74, 17, 6, -24, "코 옆"), (82, 13, 10, -22, "미늘 · 볼 아래"), (90, 9, 12, -18, "턱 위"), (100, 4, 8, -12, "턱 끝")]
돔표 = [(35, 9, 10, -6, "투구 꼭대기 · 뿔 밑"), (40, 15, 10, -12, "관자놀이 위"), (46, 20, 10, -17, "투구 가장 넓음"), (52, 22, 9, -20, "차양 윗변"), (58, 23, 6, -26, "차양 밑 · 얼굴로"), (66, 22, 4, -30, "눈 옆 투구 옆판"), (76, 18, 4, -33, "투구 옆판 아래"), (90, 12, 4, -34, "뒤통수 아래")]
# 뿔: 정면 면 1 — 가운데 x 2~10 · 밑 폭 ±5(y 50) → 끝 y 0 · 옆 자료 없음 → 이마 앞 z(돔 앞 8~13)에서 위로 갈수록 살짝 앞 · 얇은 날(두께 3)
뿔표 = [(52, 6, 14, 9), (40, 5.5, 13, 8.5), (30, 5, 12, 8), (20, 4, 11, 7.5), (10, 3, 10, 7), (0, 1, 9, 7)]                                    # y · 반폭 · z앞 · z뒤 (정면 면 1: y 0~59 · x −4~13 → 가운데 4.5 치우침은 yaw 5° 탓 · 대칭으로)
# 차양(눈썹): 정면 면 5(왼) · 8+7(오른) — 안쪽 y 52~60 · 바깥 y 56~62 · x 2~22 · 옆 면 2: z 앞 +2 ~ 뒤 −10, 아랫변이 앞
차양반 = [(2, 50), (14, 47), (22, 52), (21, 60), (10, 60), (3, 58)]                                                                       # (dx, y) 반쪽 — 정면 면 5 · 8 · 7: y 49~64 · x 0~22 · 옆 면 2: z 6/−8
# 눈구멍: 정면 면 10(왼 · x −20~−7 · y 60~72) · 12+13+16(오른) — 옆 면 3~9: z 앞 −4 ~ 뒤 −13(눈이 차양 밑 안쪽)
눈구멍반 = [(8, 60), (20, 57), (23, 64), (19, 73), (9, 72)]                                                                                  # 위 y 57~60 · 아래 72~73 = 높이 13~15                                                                               # 정면 면 10: y 58~72 · x −20~−11 (오른쪽 13 은 조각)
홍채 = (15, 66, 4.5)
# 코 쐐기 + 미늘 + 턱: 정면 면 17(코 · x −13~−1 · y 70~87) · 18(오른 코 x 0~10) · 24+25(둘째 · y 82~92) · 30+31(턱 · y 90~100) — 옆 면 5(코 y 55~72 z 25→33) · 13(미늘 y 70~85 z 24→31) · 15(턱 y 85~100 z 17→28)
부리표 = [  # y · 반폭 · z앞 · z뒤  — 옆 면 5 코(y 55~73 z 7→24) · 13 미늘(y 70~86 z 1→22) · 15 턱(y 86~100 z 5→36) · 옆 실루엣 앞: y60 22 · y70 23 · y80 29 · y85 35 · y90 33 · y100 11
    (58, 3, 10, 4, "코 뿌리(눈 사이)"), (66, 8, 18, 3, "코 옆 벌어짐"), (73, 11, 22, 5, "코 끝"), (75, 10, 20, 5, "미늘 윗변(코 밑)"),
    (86, 8, 27, 9, "미늘 끝"), (88, 7, 29, 10, "턱 판 윗변"), (95, 5, 30, 8, "턱 앞 = 가장 앞"), (100, 3, 22, 6, "턱 끝")]
# 볼 날개: 정면 면 11(왼 · x −41~−26 · y 58~78) · 14(오른 x 20~36 · y 50~82) — 옆 면 14 뒤쪽 z −5 ~ −25 (뒤로 뻗음)
볼반 = [(22, 58), (30, 62), (40, 70), (41, 74), (34, 78), (23, 76)]                                                                       # 정면 면 11: y 58~73 x −41~−22 (14 오른쪽은 y 49~83 x 14~38 · yaw 탓 큼) · z 는 dx 로: 안 −2 → 밖 −22
번개반 = [(17, 46), (21, 44), (19, 49), (23, 47), (20, 52)]

def 켜(y, hw, zf, zb, 각=0.75, n=32):
    cz, rz = (zf + zb) / 2, max(0.3, (zf - zb) / 2); hw = max(0.3, hw)
    return [(hw * np.sign(np.cos(t)) * abs(np.cos(t)) ** 각, y, cz + rz * np.sign(np.sin(t)) * abs(np.sin(t)) ** 각) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
def 쌓기(표, 각=0.75, 불=0.0): K = [켜(r[0], r[1] + 불, r[2] + 불, r[3] - 불, 각) for r in 표]; return 합(M.Manifold.hull_points(a + b) for a, b in zip(K[:-1], K[1:]))
def 앞z(y, 표=소체표): return float(np.interp(y, [r[0] for r in 표], [r[2] for r in 표]))
def 껍질반(반, z앞, 두께=3.0, 휨=0.25):
    """반쪽 정면 다각형 [(dx,y)] 을 소체 앞면 z앞(y) 에서 띄우고, 바깥(dx 큼)으로 갈수록 뒤로 휘는 판. 좌우 합."""
    out = []
    for s in (-1, 1):
        pts = [(s * dx, y, z앞(y) + 1.5 - 휨 * dx) for dx, y in 반] + [(s * dx, y, z앞(y) + 1.5 - 휨 * dx - 두께) for dx, y in 반]; out.append(M.Manifold.hull_points(pts))
    return 합(out)
def 기둥반(반, z0, z1): return 합(M.Manifold.hull_points([(s * dx, y, z) for dx, y in 반 for z in (z0, z1)]) for s in (-1, 1))
부품 = {}
부품["소체"] = 쌓기(소체표, 각=0.85)
속 = 쌓기(소체표, 각=0.85, 불=0.4)
부품["돔"] = 쌓기(돔표, 각=0.9) - 속
부품["뿔"] = 쌓기([(y, hw, zf, zb) for y, hw, zf, zb in 뿔표][::-1], 각=0.6)
부품["차양"] = 껍질반(차양반, lambda y: 앞z(y) + 4, 두께=5.0, 휨=0.3)                                                                   # 소체 앞 +4 에 두께 5 눈썹 바
눈깎 = 기둥반(눈구멍반, -40, 40); 눈z = 앞z(66)                                                                                            # 소체 앞면 z(눈 높이)
부품["소체"] = 부품["소체"] - 기둥반(눈구멍반, 눈z - 5, 40); 속 = 속 - 기둥반(눈구멍반, 눈z - 5.4, 40)                                    # 소체를 5 단위 파낸 눈구멍
부품["돔"] = 부품["돔"] - 눈깎; 부품["차양"] = 부품["차양"] - 눈깎
부품["눈구멍"] = 기둥반(눈구멍반, 눈z - 5, 눈z - 3.5)                                                                                     # 파인 바닥의 검은 판
for s in (-1, 1): 부품["홍채" + ("L" if s < 0 else "R")] = M.Manifold.sphere(홍채[2], 32).scale([1, 1, 0.35]).translate([s * 홍채[0], 홍채[1], 눈z - 3.5 + 0.8])      # 눈구멍 바닥 앞의 납작 구(원통은 축이 y 로 가 막대가 됐다)
부품["부리"] = 쌓기(부리표, 각=0.45) - 속
부품["볼"] = 합(M.Manifold.hull_points([(s * dx, y, -4 - 14 * (dx - 22) / 19) for dx, y in 볼반] + [(s * dx, y, -4 - 14 * (dx - 22) / 19 - 2.0) for dx, y in 볼반]) for s in (-1, 1)) - 속
부품["번개"] = 합(M.Manifold.hull_points([(s * dx, y, z) for dx, y in 번개반 for z in (-1, 1)]) for s in (-1, 1)).translate([0, 0, 0]) ^ (쌓기(돔표, 각=0.9, 불=0.6) - 쌓기(돔표, 각=0.9, 불=-0.6))
out = {}
for k, m in 부품.items():
    if m.is_empty(): print("빈:", k); continue
    mm_ = m.to_mesh(); t = trimesh.Trimesh(np.array(mm_.vert_properties)[:, :3], np.array(mm_.tri_verts), process=False)
    if t.volume < 0: t.invert()
    t.export(J(DO, k + ".stl")); out[k] = t
print("부품", list(out))
# ── 오버레이(첫 줄) ──
정이름 = json.load(open(J(D, "자료3D2_이름.json"), encoding="utf-8")); 옆이름 = json.load(open(J(D, "자료3D3_옆이름.json"), encoding="utf-8"))
def 틀(태그, 위, 아래, 눈=None, 눈단위=None):
    라벨 = np.load(J(D, 태그 + "_영역.npz"))["라벨"]; ys, _ = np.nonzero(np.isin(라벨, 아래)); 턱 = ys.max() / S
    if 눈 is not None: ys, _ = np.nonzero(np.isin(라벨, 눈)); e = ys.mean() / S; h = (턱 - e) / (100 - 눈단위) * 100; y0 = 턱 - h
    else: ys, _ = np.nonzero(np.isin(라벨, 위)); y0 = ys.min() / S; h = 턱 - y0
    m = (라벨 > 0) & (np.arange(라벨.shape[0])[:, None] < 턱 * S); ys, xs = np.nonzero(m); return y0, h, (xs.min() + xs.max()) / 2 / S
L = np.load(J(D, "02_정면_영역.npz"))["라벨"]; fy0, fh, fcx = 틀("02_정면", 정이름["뿔"], 정이름["부리"][-1:]); ys, _ = np.nonzero(np.isin(L, 정이름["눈L"] + 정이름["눈R"])); 정눈 = (ys.mean() / S - fy0) / fh * 100
sy0, sh, scx = 틀("02_옆", 옆이름["투구"], 옆이름["부리3"], 옆이름["눈"], 정눈)
rng = np.random.RandomState(11); 색 = {k: tuple(int(x) for x in rng.randint(70, 230, 3)) for k in out}; 색["소체"] = (40, 40, 45); 색["눈구멍"] = (20, 20, 20); 색["홍채L"] = 색["홍채R"] = (230, 150, 60)
def 그리기(im, yaw, y0, h, cx, 뒤집, alpha):
    H, W = im.shape[:2]; th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); s = h / 100; 삼 = []
    for k, t in out.items():
        V = np.asarray(t.vertices) @ R.T; x = V[:, 0] * (-1 if 뒤집 else 1); uv = np.stack([x * s + cx, V[:, 1] * s + y0], 1)
        for tri in t.faces: 삼.append((V[tri, 2].mean(), k, uv[tri]))
    삼.sort(key=lambda a: a[0]); ov = im.copy(); ID = np.zeros((H, W), np.int32); idx = {k: i + 1 for i, k in enumerate(out)}
    for _, k, q in 삼: q = np.round(q).astype(np.int32); cv2.fillPoly(ov, [q], 색[k][::-1]); cv2.fillPoly(ID, [q], idx[k])
    vis = cv2.addWeighted(im, 1 - alpha, ov, alpha, 0); vis[cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0] = (0, 0, 0); return vis, ID
ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); 판들 = []
for 태그, yaw, (y0, h, cx), 뒤집 in (("02_정면", 0, (fy0, fh, fcx), False), ("02_옆", -90, (sy0, sh, scx), True)):
    im = 읽기(기록[태그]["파일"]); vis, ID = 그리기(im, yaw, y0, h, cx, 뒤집, 0.5); ys, xs = np.nonzero(ID > 0); a, b, c, d = max(0, ys.min() - 30), ys.max() + 30, max(0, xs.min() - 30), xs.max() + 30
    crop = vis[a:b, c:d]; crop = cv2.resize(crop, (int(crop.shape[1] * 600 / crop.shape[0]), 600)); p = Image.fromarray(crop[:, :, ::-1]); ImageDraw.Draw(p).text((8, 6), "손표 · " + 태그 + " 오버레이", font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0)); 판들.append(p)
for 이름_, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
    bg = np.full((600, 600, 3), 245, np.uint8); vis, ID = 그리기(bg, yaw, 40, 480.0, 300, False, 1.0); p = Image.fromarray(vis[:, :, ::-1]); ImageDraw.Draw(p).text((8, 6), "손표 · " + 이름_, font=ft, fill=(0, 0, 0)); 판들.append(p)
시트 = Image.new("RGB", (sum(p.width for p in 판들) + 10 * len(판들), 600), (250, 250, 248)); x = 0
for p in 판들: 시트.paste(p, (x, 0)); x += p.width + 10
시트.save(J(D, "손표3D.png")); print(J(D, "손표3D.png"))
