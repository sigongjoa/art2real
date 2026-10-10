# 셸 판 그림 흐름도 — 부품마다 줄 · 단계마다 실제 그림 (선 → 열린 면 → 벽 두께 → 셸만 → 포켓까지 → 사람) · python runs/선고리/셸그림.py 4 21 35
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "깊이학습"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
import 선고리 as G
from render import render
from 윤곽 import 메시로
from s0 import unit
from PIL import Image, ImageDraw, ImageFont
import cadquery as cq
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 260; 꼬 = os.environ.get("OUTS", "_셸시험")
ids = [int(a) for a in sys.argv[1:]]; T = np.load(os.path.join(R, "깊이학습", "시험.npz")); X = T["X"].astype(np.float32); 부 = T["부품"]
쪽이름 = {0: "앞", 1: "뒤", 2: "옆(왼)", 3: "옆(오른)", 4: "위", 5: "아래"}
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, 노랑=False, v=(1, .6, .8)):
    m = 정(m); return render(np.asarray(m.vertices), np.asarray(m.faces), list(v), img_size=C, cols=None if 노랑 else np.tile([.45, .68, .98], (len(m.faces), 1)))
def 칸(a): return Image.fromarray(a).resize((C, C), Image.NEAREST)
열 = ["① 선 (앞 · 옆 · 위)", "② 열린 면 찾기", "③ 벽 두께", "④ 셸만 (속 비움)", "⑤ 포켓까지", "사람 부품"]
im = Image.new("RGB", (30 + 6 * (C + 12), 110 + len(ids) * (C + 70)), "white"); d = ImageDraw.Draw(im)
d.text((20, 20), "셸 판 — 속이 빈 껍질을 CAD 「속 비우기」로 · 부품마다 실제로 돌린 그림 (A = 정답 깊이)", font=F(28), fill="black")
for j, t in enumerate(열): d.text((30 + j * (C + 12) + C // 2, 85), t, font=F(22), fill=(31, 95, 173) if j < 5 else (120, 120, 120), anchor="mm")
for r_, i in enumerate(ids):
    y = 110 + r_ * (C + 70); S, L, Dh, D = X[i]; mu = unit(trimesh.load(G.RR if hasattr(G, "RR") else "G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh")) if False else unit(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"))
    선 = [G.모서리선(mu, D[k], S[k], k) for k in (0, 2, 4)]
    a = np.full((128, 3 * 128, 3), 255, np.uint8)
    for q, (k, l) in enumerate(zip((0, 2, 4), 선)): b = a[:, q * 128:(q + 1) * 128]; b[S[k] > .5] = (236, 240, 248); b[l > .5] = (200, 30, 30)
    im.paste(Image.fromarray(a).resize((C, C // 3), Image.NEAREST), (30, y + C // 3))
    열림 = G.열린면(S, Dh, D); j_ = json.load(open(os.path.join(H, "결과_A" + 꼬, "%02d.json" % i), encoding="utf-8"))
    if 열림 is None:
        for c_ in (1, 2, 3): d.text((30 + c_ * (C + 12) + C // 2, y + C // 2), "열린 면 없음" if c_ == 1 else "—", font=F(24), fill=(200, 40, 40), anchor="mm")
    else:
        k, m, tpx, frac = 열림
        b = np.full((128, 128, 3), 255, np.uint8); b[S[k] > .5] = (220, 225, 235); b[m] = (240, 120, 60); im.paste(칸(b), (30 + (C + 12), y))
        d.text((30 + (C + 12) + C // 2, y + C + 14), "%s 쪽 · 넓이 %d%%" % (쪽이름[k], 100 * frac), font=F(20), fill=(60, 60, 60), anchor="mm")
        dist = cv2.distanceTransform((S[k] > .5).astype(np.uint8), cv2.DIST_L2, 3); b = np.full((128, 128, 3), 255, np.uint8); b[S[k] > .5] = (220, 225, 235)
        b[(S[k] > .5) & (dist <= tpx + .5)] = (40, 160, 70); im.paste(칸(b), (30 + 2 * (C + 12), y))
        d.text((30 + 2 * (C + 12) + C // 2, y + C + 14), "벽 %.1f (긴 변 100)" % (tpx / 128 * 110), font=F(20), fill=(60, 60, 60), anchor="mm")
        바 = cq.importers.importStep(os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)); rs, t = G.셸(바, 열림, S)
        if rs is not None:
            vv = {0: (-1, .3, .3), 1: (1, .3, .3), 2: (.3, -1, .3), 3: (.3, 1, .3), 4: (.3, .3, -1), 5: (.3, .3, 1)}[k]   # 열린 쪽에서 보기
            im.paste(그(메시로(rs), v=vv), (30 + 3 * (C + 12), y))
        else: d.text((30 + 3 * (C + 12) + C // 2, y + C // 2), "셸 실패", font=F(24), fill=(200, 40, 40), anchor="mm")
    im.paste(그(trimesh.load(os.path.join(H, "결과_A" + 꼬, "%02d_선고리.stl" % i))), (30 + 4 * (C + 12), y))
    e = j_["edge_f1"]; d.text((30 + 4 * (C + 12) + C // 2, y + C + 14), "점수 %.2f · 조각 %d" % (e, j_["조각"]), font=F(20), fill=(40, 150, 60) if e >= .42 else (200, 40, 40), anchor="mm")
    im.paste(그(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"), 노랑=True), (30 + 5 * (C + 12), y))
    d.text((34, y + 4), "#%d" % i, font=F(22), fill=(90, 90, 90))
im.save(os.path.join(H, "셸흐름그림.png")); print("ok")
