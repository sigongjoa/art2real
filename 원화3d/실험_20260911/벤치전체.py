# -*- coding: utf-8 -*-
"""**벤치 전체를 한 장으로** — 판정표 + 실물 29장의 모양(45도) -> out/벤치모양_전체.png

    python 벤치전체.py <벤치lam4.jsonl> [초 예산=480]

케이스마다 한 줄 그림을 out/벤치모양/<케이스>.png 로 먼저 적고, 이미 있으면 건너뛴다.
예산을 넘기면 새 케이스를 안 잡고 멈춘다 — 다시 돌리면 이어서 한다 (메모리 정리 대비).
다 모이면 맨 위에 판정표를 붙여 한 장으로 합친다. 렌더러는 `벤치그림.py` 것 그대로."""
import json
import os
import sys
import time

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 벤치그림 as RG                                  # HERE 로 cwd 를 옮기고 O · B 를 부른다
from 계획 import _font

O, B = RG.O, RG.B
S, G, LW = 150, 8, 210
RH = S + 22
W_ = LW + len(RG.COLS) * (S + G) + G
TILE = os.path.join(RG.HERE, "out", "벤치모양")
ALL = ["파이프0.20", "파이프0.50", "타원0.20", "타원0.50", "오라클0.20", "오라클0.50"]


def tile(case, r):
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    plain, p20, axes, _ = O.build(case, truth, 0.20, "파이프")
    vox = {"이진": plain, "파이프0.20": p20,
           "파이프0.50": O.build(case, truth, 0.50, "파이프")[1],
           "타원0.50": O.build(case, truth, 0.50, "타원")[1],
           "오라클0.50": O.build(case, truth, 0.50, "오라클")[1]}
    meshes = {"정답": truth, **{k: O.C.to_mesh(v, axes) for k, v in vox.items()}}
    sdf = (ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)).astype(np.float32)
    meshes["균일@파이프0.50"] = B.sdf_mesh(sdf, axes, r["t"]["파이프0.50"])
    R = RG.rot(np.asarray(meshes["이진"].vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.06
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    im = Image.new("RGB", (W_, RH), "white")
    d = ImageDraw.Draw(im)
    f2, f3 = _font(14), _font(12)
    d.text((16, S // 2 - 10), case[:26], fill=(20, 20, 20), font=f2)
    if case == "소체":
        d.text((16, S // 2 + 10), "(base_female 과 같은 메시)", fill=(150, 150, 150), font=f3)
    for j, (name, key) in enumerate(RG.COLS):
        x0 = LW + G + j * (S + G)
        src = meshes["정답"] if key is None else meshes[key]
        im.paste(Image.fromarray(RG.render(src, frame, S, RG.TINT[name])), (x0, 0))
        d.rectangle([x0, 0, x0 + S - 1, S - 1], outline=(222, 222, 222))
        if key is None:
            continue
        v = r["128"][key]
        if key in ("이진", "균일@파이프0.50"):
            d.text((x0, S + 3), "%.4f" % v, fill=(70, 70, 70), font=f3)
        else:
            dv = v - r["128"]["균일@" + key]
            d.text((x0, S + 3), "%.4f (%+.4f)" % (v, dv), font=f3,
                   fill=(30, 130, 70) if dv > 0 else (190, 60, 40))
    return im


def header(rows):
    n = len(rows)
    H = 360
    im = Image.new("RGB", (W_, H), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((24, 16), "실물 벤치 %d장 — 판정과 모양 (45도, 원화 세 장 중 어느 것도 안 그린 각도)" % n, fill=(20, 20, 20), font=f1)
    d.text((24, 54), "대조군 = hull 을 그 판본과 같은 부피까지 매끈하게 안으로 민 것 (정보 0). "
                     "통과 = 격자 128·192 둘 다 평균 > 0 이고 과반 승 (돌리기 전에 정한 기준)", fill=(90, 90, 90), font=f3)
    xs = [24, 190, 400, 610, 850]
    for x, t in zip(xs, ["판본", "새 대조 · 격자128", "새 대조 · 격자192", "옛 대조(저장소 규약) · 128", "판정"]):
        d.text((x, 88), t, fill=(20, 20, 20), font=f2)
    own = lambda r, g, k: r[g][k] - r[g]["균일@" + k]
    old = lambda r, g, k: r[g][k] - r[g]["균일층@파이프0.20"]
    for i, k in enumerate(ALL):
        a = [np.array([f(r, g, k) for r in rows]) for f, g in ((own, "128"), (own, "192"), (old, "128"))]
        ok = [v.mean() > 0 and (v > 0).sum() > n / 2 for v in a[:2]]
        verdict = "통과" if all(ok) else ("격자가 갈림 · 결론 없음" if any(ok) else "짐")
        col = (30, 130, 70) if all(ok) else (150, 110, 20) if any(ok) else (190, 60, 40)
        y = 116 + i * 28
        cells = [k] + ["%+.4f (%2d/%d)" % (v.mean(), (v > 0).sum(), n) for v in a] + [verdict]
        for x, t in zip(xs, cells):
            d.text((x, y), t, fill=col if x in (24, 850) else (40, 40, 40), font=f2)
    d.text((24, 300), "칸 아래 = 3D IoU (괄호는 제 부피 대조군 대비 · 초록 이김 / 빨강 짐). "
                      "옛 대조군은 한 겹에 부피가 20% 넘게 빠져 부피가 안 맞았다.", fill=(90, 90, 90), font=f3)
    for j, (name, _) in enumerate(RG.COLS):
        d.text((LW + G + j * (S + G), H - 26), name, fill=(40, 40, 40), font=f2)
    return im


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
    order = [c["name"] for c in json.load(open("벤치.json", encoding="utf-8"))["cases"]]
    rows.sort(key=lambda r: order.index(r["case"]))
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 480
    os.makedirs(TILE, exist_ok=True)
    O.H.register_sheets()
    t0 = time.time()
    for r in rows:
        p = os.path.join(TILE, r["case"] + ".png")
        if os.path.exists(p):
            continue
        if time.time() - t0 > budget:
            print("  예산 %.0f초를 넘겼다 — 다시 돌리면 이어서 한다" % budget, flush=True)
            break
        tile(r["case"], r).save(p)
        print("  %-26s 그림 (%.0f초)" % (r["case"][:26], time.time() - t0), flush=True)
    done = [r for r in rows if os.path.exists(os.path.join(TILE, r["case"] + ".png"))]
    print("  %d / %d 장" % (len(done), len(rows)), flush=True)
    if len(done) < len(rows):
        return
    hd = header(rows)
    im = Image.new("RGB", (W_, hd.height + len(rows) * RH + 10), "white")
    im.paste(hd, (0, 0))
    for i, r in enumerate(rows):
        im.paste(Image.open(os.path.join(TILE, r["case"] + ".png")), (0, hd.height + i * RH))
    im.save(os.path.join(RG.HERE, "out", "벤치모양_전체.png"))
    print("  -> out/벤치모양_전체.png")


if __name__ == "__main__":
    main()
