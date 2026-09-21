# -*- coding: utf-8 -*-
"""**색이 정말 닮게 만드나** — 안 쓴 판으로 시험한다 (2026-09-21).

    python 색검증.py [케이스=오메가몬]   -> out/색검증_<케이스>.png · out/기록/색검증_*.json

사용자(09-21): 「도색 하니깐 제대로 보인다고?」

**옳은 의심이다.** 09-21 의 「색몫 64.9%」는 **앞 판에서 색을 뜨고 앞에서 렌더해 앞 원화와 비교**했다.
색을 뜬 곳에서 다시 재면 당연히 가까워진다 — **순환**이다.

그래서 **가려 놓고**(held-out) 다시 잰다:

    색을 **앞 · 뒤 판에서만** 뜬다 (옆 판은 안 본다)
    **옆에서** 렌더해서 **옆 원화**와 견준다      <- 이 판은 색을 뜰 때 한 번도 안 봤다

    회색 거리 대비 색 거리가 줄면 **색이 실제로 닮게 만든다**.
    안 줄면 앞에서 본 64.9% 는 순환이었다는 뜻이다.
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 왜다른가 as WD
W = H.W
OUT = H.OUT

렌더소스 = WD.렌더소스.replace(
    'cam.location = Vector(((u0 + u1) / 2, -6.0, (z0 + z1) / 2))\ncam.rotation_euler = (math.radians(90), 0, 0)',
    'if a[7] == "side":\n'
    '    cam.location = Vector((-6.0, (u0 + u1) / 2, (z0 + z1) / 2))\n'
    '    cam.rotation_euler = (math.radians(90), 0, math.radians(-90))\n'
    'else:\n'
    '    cam.location = Vector(((u0 + u1) / 2, -6.0, (z0 + z1) / 2))\n'
    '    cam.rotation_euler = (math.radians(90), 0, 0)')


def 창색(png, raw_v, v, p):
    """원화 한 장을 **창 좌표 색 그림**으로."""
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
    알 = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
    d = H.declutter(raw_v)
    return np.clip(np.dstack([H._warp_one(H.to_win(d, rgb[:, :, k].astype(np.float32))[1], v, p)
                              for k in range(3)]), 0, 255).astype(np.uint8)


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    m = trimesh.load(os.path.join(OUT, "hull.glb"), force="mesh", process=False)
    V = np.asarray(m.vertices, float)
    Nn = np.asarray(m.vertex_normals)

    # **앞 · 뒤에서만** 색을 뜬다 (옆은 가린다)
    col = np.full((len(V), 4), 255, np.uint8)
    본 = np.zeros(len(V), bool)
    for v, sign, 방향 in (("front", +1, -1), ("back", bs, +1)):
        ch = 창색(os.path.join(base, src[v]), raw[v], v, p)
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        본다 = Nn[:, 1] * 방향 > 0.15
        for k in range(3):
            col[본다, k] = ch[:, :, k][py[본다], px[본다]]
        본 |= 본다
    from scipy.spatial import cKDTree
    t = cKDTree(V[본])
    _, i = t.query(V[~본], k=1)
    col[~본] = col[본][i]
    print("  앞 · 뒤에서 뜬 정점 몫 %.4f (옆은 안 봤다)" % 본.mean(), flush=True)

    색메시 = m.copy()
    색메시.visual = trimesh.visual.ColorVisuals(색메시, vertex_colors=col)
    d = os.path.join(OUT, "색검증", case)
    os.makedirs(d, exist_ok=True)
    plyC = os.path.join(d, "앞뒤색.ply")
    plyG = os.path.join(d, "회색.ply")
    open(plyC, "wb").write(trimesh.exchange.ply.export_ply(색메시, encoding="ascii"))
    open(plyG, "wb").write(trimesh.exchange.ply.export_ply(m, encoding="ascii"))
    sc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_색검증렌더.py")
    open(sc, "w", encoding="utf-8").write(렌더소스)

    낸 = {}
    for 이름, ply, mode in (("회색", plyG, "gray"), ("색", plyC, "color")):
        for 판 in ("front", "side"):
            o = os.path.join(d, "%s_%s.png" % (이름, 판))
            subprocess.run([r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe", "-b", "--python", sc,
                            "--", ply, o, str(W.U0), str(W.U1), str(W.Z0), str(W.Z1), mode, 판],
                           capture_output=True, timeout=1800)
            낸[(이름, 판)] = o

    def 읽기(png):
        im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 4:
            a = im[:, :, 3:4] / 255.0
            im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    결과 = {}
    for 판 in ("front", "side"):
        원 = 창색(os.path.join(base, src[판]), raw[판], 판, p)
        안 = ndimage.binary_erosion(masks[판].astype(bool), iterations=3)
        d회 = WD.거리(읽기(낸[("회색", 판)]), 원, 안)
        d색 = WD.거리(읽기(낸[("색", 판)]), 원, 안)
        결과[판] = {"회색": round(d회, 2), "색": round(d색, 2), "색몫": round(1 - d색 / max(d회, 1e-6), 4)}
        print("  %-6s 회색 %.1f -> 색 %.1f · 색몫 %.3f%s"
              % (판, d회, d색, 결과[판]["색몫"], "   <- **가려 둔 판**" if 판 == "side" else ""), flush=True)

    Q = {"held-out(옆)에서도 색이 이긴다": bool(결과["side"]["색"] < 결과["side"]["회색"]),
         "held-out 색몫 >= 앞의 절반": bool(결과["side"]["색몫"] >= 0.5 * 결과["front"]["색몫"])}
    for k, v in Q.items():
        print("   %-28s %s" % (k, "통과" if v else "**짐**"), flush=True)

    S = 420
    행 = [("원화", [창색(os.path.join(base, src[v]), raw[v], v, p) for v in ("front", "side")]),
          ("회색", [읽기(낸[("회색", v)]) for v in ("front", "side")]),
          ("앞·뒤에서만 뜬 색", [읽기(낸[("색", v)]) for v in ("front", "side")])]
    sheet = Image.new("RGB", (3 * (S + 8), 2 * (S + 8) + 150), "white")
    for c, (t, ims) in enumerate(행):
        for r, a in enumerate(ims):
            sheet.paste(Image.fromarray(a).resize((S, S)), (c * (S + 8), 150 + r * (S + 8)))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "색이 정말 닮게 만드나 — **안 쓴 판**으로 시험했다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "앞 판: 회색 %.1f -> 색 %.1f (색몫 %.1f%%)   ← 색을 여기서 떴다. **순환이 섞여 있다**"
            % (결과["front"]["회색"], 결과["front"]["색"], 100 * 결과["front"]["색몫"]), (90, 92, 100), f본)
    dr.text((14, 80), "옆 판: 회색 %.1f -> 색 %.1f (**색몫 %.1f%%**)   ← **한 번도 안 본 판**"
            % (결과["side"]["회색"], 결과["side"]["색"], 100 * 결과["side"]["색몫"]), (200, 40, 40), f본)
    dr.text((14, 112), "윗줄 앞에서 본 것 · 아랫줄 옆에서 본 것", (90, 92, 100), f작)
    for c, (t, _) in enumerate(행):
        dr.text((c * (S + 8) + 6, 130), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "색검증_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "결과": 결과, "판정": Q,
               "까닭": "앞 판 색몫은 색을 뜬 판에서 다시 잰 것이라 순환이 섞여 있다. 옆 판이 held-out 이다."},
              open(os.path.join(OUT, "기록", "색검증_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
