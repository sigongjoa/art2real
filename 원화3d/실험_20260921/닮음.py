# -*- coding: utf-8 -*-
"""**왜 안 닮았나** — 겉은 맞고 속이 비었다는 것을 잰다 (2026-09-21).

    python 닮음.py [케이스=오메가몬]   -> out/닮음_<케이스>.png · out/기록/닮음_*.json

사용자(09-21): 「너 내가 왜 이상하다고 하는지 이미지로 보이지. **원화랑 전혀 안 닮은 거** 말이야」

맞다. 그리고 그 까닭은 손잡이(p · σ)가 아니라 **증거 채널**이다. 그것을 둘로 갈라 잰다:

    겉  실루엣 IoU        원화 테두리를 얼마나 맞히나      <- 실루엣이 증거다 -> 높다
    속  **먹선 재현**      원화 **안쪽 선**을 얼마나 맞히나  <- 증거가 없다 -> 0 에 가깝다

우리 메시의 「선」은 **이웃 면 사이 각이 큰 모서리**(크리스)를 앞에서 본 것이다. 원화의 선은
`hull.ink_map`. 둘을 같은 1024 판에 그려 겹친다 — **빨강만 있고 파랑이 없으면 그게 「안 닮음」이다.**

⚠ 가림(앞의 면이 뒤의 선을 가리는 것)은 안 본다. 그래서 **우리 쪽 선 개수는 후하게** 잡힌다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
W = H.W
OUT = H.OUT
각문턱 = 30.0                   # 이보다 크게 꺾이면 「선」으로 친다 (도)
허용 = 3                        # 화소. 이 안에 있으면 맞힌 것으로 친다


렌더소스 = r'''
import bpy, math, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out, u0, u1, z0, z1 = a[0], a[1], float(a[2]), float(a[3]), float(a[4]), float(a[5])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=src)
o = bpy.context.selected_objects[0]
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("m"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.72, 0.73, 0.76, 1); b.inputs["Roughness"].default_value = 0.45
o.data.materials.append(mat)
sc = bpy.context.scene
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = max(u1 - u0, z1 - z0)
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = Vector(((u0 + u1) / 2, -6.0, (z0 + z1) / 2))      # **원화 창과 같은 틀** (화소가 1:1 로 맞는다)
cam.rotation_euler = (math.radians(90), 0, 0)
for nm, rot, e in (("key", (55, 0, -40), 2.0), ("fill", (70, 0, 120), 0.5), ("rim", (120, 0, 200), 0.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e
    l = bpy.data.objects.new(nm, ld); sc.collection.objects.link(l)
    l.rotation_euler = tuple(math.radians(x) for x in rot)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.22
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("렌더 끝")
'''


def 창렌더(m, out):
    """**원화 창과 같은 정사영**으로 1024² 렌더 — 화소가 마스크와 1:1 이다."""
    import subprocess
    sc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_닮음렌더.py")
    ply = os.path.join(OUT, "_닮음.ply")
    open(ply, "wb").write(trimesh.exchange.ply.export_ply(m, encoding="ascii"))
    open(sc, "w", encoding="utf-8").write(렌더소스)
    subprocess.run([r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe", "-b", "--python", sc, "--",
                    ply, out, str(W.U0), str(W.U1), str(W.Z0), str(W.Z1)], capture_output=True, timeout=1800)
    return out


def 메시선(m, bs=1, view="front"):
    """크리스 모서리를 판에 그린다 -> bool 1024²."""
    from PIL import Image, ImageDraw
    V = np.asarray(m.vertices)
    ang = m.face_adjacency_angles
    쌍 = m.face_adjacency_edges[ang > np.radians(각문턱)]
    fn = m.face_normals[m.face_adjacency[ang > np.radians(각문턱)]]
    보임 = fn[:, :, 1].min(1) < -0.2 if view == "front" else fn[:, :, 1].max(1) > 0.2
    쌍 = 쌍[보임]
    sign = 1 if view == "front" else bs
    py, px = W.topix(sign * V[:, 0], V[:, 2])
    im = Image.new("1", (W.RES, W.RES), 0)
    dr = ImageDraw.Draw(im)
    for a, b in 쌍:
        dr.line([px[a], py[a], px[b], py[b]], fill=1)
    return np.array(im, bool), len(쌍)


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    m = trimesh.load(os.path.join(OUT, "hull.glb"), force="mesh", process=False)

    # 겉 — 실루엣
    s = np.asarray(W.silhouette(np.asarray(m.vertices), np.asarray(m.faces), "front")).astype(bool)
    a = masks["front"].astype(bool)
    겉 = float(W.iou(masks["front"], s))

    # 속 — 원화 먹선 대 우리 크리스선 (둘 다 실루엣 **안쪽**만)
    선원 = H.ink_map(os.path.join(base, src["front"]))
    _, w2 = H.to_win(H.declutter(raw["front"]), 선원.astype(np.float32))
    원선 = H._warp_one(w2, "front", p) > 0.5
    안 = ndimage.binary_erosion(a, iterations=4)
    원선 &= 안
    우리선, 모서리수 = 메시선(m, bs, "front")
    우리선 &= 안
    # **보이는 선** — 원화 창과 같은 틀로 렌더해서 눈에 실제로 잡히는 경계만 (Canny)
    import cv2
    rp = 창렌더(m, os.path.join(OUT, "닮음_렌더_%s.png" % case))
    rim = cv2.imdecode(np.fromfile(rp, np.uint8), cv2.IMREAD_UNCHANGED)
    회 = cv2.cvtColor(rim[:, :, :3], cv2.COLOR_BGR2GRAY)
    보임 = (cv2.Canny(cv2.GaussianBlur(회, (3, 3), 0), 20, 60) > 0) & 안

    def 점수(우리, 허용):
        맞 = ndimage.binary_dilation(우리, iterations=허용)
        재 = float((원선 & 맞).sum()) / max(원선.sum(), 1)
        역 = ndimage.binary_dilation(원선, iterations=허용)
        정 = float((우리 & 역).sum()) / max(우리.sum(), 1)
        return 재, 정

    # **대조군** — 같은 선을 좌우 반전. 우리 선이 노이즈면 점수가 거의 안 떨어진다.
    표 = []
    for 이름, 우리 in (("기하에 새겨진 선", 우리선), ("렌더에 보이는 선", 보임)):
        재, 정 = 점수(우리, 허용)
        재c, 정c = 점수(우리[:, ::-1] & 안, 허용)
        표.append({"무엇": 이름, "화소": int(우리.sum()), "재현": round(재, 3), "정밀": round(정, 3),
                   "대조 재현": round(재c, 3), "이득": round(재 - 재c, 3)})
    재현, 정밀 = 표[1]["재현"], 표[1]["정밀"]
    맞 = ndimage.binary_dilation(보임, iterations=허용)

    # **판 안이 평평한가** — 선으로 갈린 칸마다 밝기의 표준편차.
    # 원화는 셀 채색이라 칸 안이 거의 한 톤이다. 우리 것은 단면이 타원이라 **부풀어서 그러데이션**이 생긴다.
    원im = cv2.imdecode(np.fromfile(os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png"), np.uint8),
                        cv2.IMREAD_COLOR)
    원회 = cv2.cvtColor(cv2.resize(원im, (W.RES, W.RES)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    칸, n칸 = ndimage.label(안 & ~ndimage.binary_dilation(원선, iterations=1))
    크기 = np.bincount(칸.ravel())
    쓸 = [i for i in range(1, n칸 + 1) if 크기[i] >= 400]
    def 흔들림(im):
        v = [float(im[칸 == i].std()) for i in 쓸]
        w = [크기[i] for i in 쓸]
        return float(np.average(v, weights=w)) if v else 0.0
    평면 = {"원화": round(흔들림(원회), 1), "우리": round(흔들림(회.astype(np.float32)), 1), "칸": len(쓸)}

    print("  겉  실루엣 IoU %.3f" % 겉)
    print("  속  원화 안쪽 선 %d 화소 (허용 %d 화소 · 대조군 = 좌우 반전)" % (원선.sum(), 허용))
    for r in 표:
        print("      %-10s %6d 화소 · 재현 %.3f (대조 %.3f · **이득 %+.3f**) · 정밀 %.3f"
              % (r["무엇"], r["화소"], r["재현"], r["대조 재현"], r["이득"], r["정밀"]))

    print("  면  선으로 갈린 칸 %d 개 · 칸 안 밝기 흔들림  원화 %.1f  ->  우리 %.1f  (**%.1f 배**)"
          % (평면["칸"], 평면["원화"], 평면["우리"], 평면["우리"] / max(평면["원화"], 0.1)))

    # ---- 그림
    S = 620
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    렌더 = Image.open(rp).convert("RGB").resize((S, S))
    겹 = np.array(Image.open(rp).convert("RGB"))                              # **렌더 위에** 원화 선을 얹는다
    겹[ndimage.binary_dilation(원선 & ~맞, iterations=1)] = (215, 45, 45)     # 원화에 있는데 렌더에 안 보이는 선
    겹[ndimage.binary_dilation(원선 & 맞, iterations=1)] = (30, 150, 70)      # 둘 다 있는 선
    겹im = Image.fromarray(겹).resize((S, S), Image.LANCZOS)
    실 = np.full((W.RES, W.RES, 3), 255, np.uint8)
    실[a & s] = (40, 160, 90)
    실[a & ~s] = (215, 45, 45)
    실[~a & s] = (40, 90, 220)
    실im = Image.fromarray(실).resize((S, S), Image.LANCZOS)

    sheet = Image.new("RGB", (4 * (S + 8), S + 186), "white")
    for i, im in enumerate((원, 렌더, 실im, 겹im)):
        sheet.paste(im, (i * (S + 8), 176))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 21)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "왜 안 닮았나 — 원화와 **같은 틀**로 나란히 놓고 쟀다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), "겉 — 실루엣 IoU %.3f. 테두리는 맞는다." % 겉, (28, 110, 60), f본)
    dr.text((14, 80), "선 — 렌더에 보이는 선의 원화 선 재현 %.3f (좌우 반전 대조 %.3f). **먹선은 실제로 들어가 있다.**"
            % (표[1]["재현"], 표[1]["대조 재현"]), (40, 90, 200), f본)
    dr.text((14, 108), "그런데도 안 닮았다. 남는 차이는 **면과 색**이다 — 단면이 전부 타원이라 판이 다 부풀었고, "
                       "갑주의 깊이 단차도 색도 없다.", (200, 40, 40), f본)
    dr.text((14, 140), "⚠ 이번 평면성 측정은 **실패했다** — 칸 안 밝기 흔들림이 원화 %.1f · 우리 %.1f 로 뒤집혔다. "
            "원화의 검정 · 금색이 한 칸에 섞여서다. 색을 빼고 다시 재야 한다."
            % (평면["원화"], 평면["우리"]), (90, 92, 100), f작)
    for i, t in enumerate(("원화", "우리 결과 (원화 창과 같은 틀로 렌더)",
                           "겉 — 초록 겹침 · 빨강 못 덮음 · 파랑 원화 밖",
                           "속 — 렌더 위의 원화 선. 빨강 = 렌더에 안 보임 · 초록 = 보임")):
        dr.text((i * (S + 8) + 6, 176 - 26), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "닮음_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "겉 IoU": round(겉, 4), "원화 안쪽 선 화소": int(원선.sum()),
               "우리 선 화소": int(우리선.sum()), "모서리 수": int(모서리수),
               "속 점수": 표, "판 평면성": 평면,
               "손잡이": {"각문턱": 각문턱, "허용": 허용, "출처": "guessed(눈으로)"},
               "안 본 것": "가림(앞 면이 뒤 선을 가리는 것) — 우리 쪽 선을 후하게 잡는다"},
              open(os.path.join(OUT, "기록", "닮음_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")




