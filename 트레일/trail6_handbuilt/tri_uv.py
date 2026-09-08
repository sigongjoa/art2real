# -*- coding: utf-8 -*-
"""생성 견갑을 **전개도로 펴서** 본다.

    blender -b --python tri_paint.py     # 먼저. out/tri_col.npy · tri_prov.npy 를 만든다
    blender -b --python tri_uv.py

화면에서 보면 어느 각도든 "칠해져 있다"고 보인다. 원화는 단면(투영)이고 표면은 전개도라
**화면 화소 수와 표면 면적은 다른 물건**이다 (128). 그 차이는 펴 봐야 보인다.

굽는 건 두 장이다.

    tri_uv_col.png    면 색 그대로 (판 라벨의 평면색)
    tri_uv_prov.png   **출처** — 초록 직접 / 노랑 전파 / 파랑 뿔계급 / 빨강 못받음

두 번째가 이 트레일의 질문에 답한다: 원화가 이 표면의 어디까지 닿았나.
UV 는 Smart UV Project 다 — 좋은 언랩을 만들려는 게 아니라 **면적을 정직하게 펴려는** 것이다.
"""
import bpy, os, sys, math, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
ATLAS = 1024
PROVCOL = np.array([[90, 200, 110],      # 0 직접  — 원화가 이 면을 실제로 봤다
                    [240, 205, 90],      # 1 전파  — 그래프가 부품 안에서 옮겼다
                    [90, 150, 240],      # 2 뿔계급 — 넷이 같은 물건이라 재질을 나눴다
                    [230, 80, 80]], float)   # 3 못받음 — 두께 대체


def rasterize(me, per_face, atlas):
    """면의 UV 삼각형을 아틀라스에 평면색으로 채운다. 면 하나 = 색 하나 (74)."""
    nf = len(me.polygons)
    uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    img = np.zeros((atlas, atlas, 3), np.float32)
    hit = np.zeros((atlas, atlas), bool)
    for i in range(nf):
        U = uv[ls[i]:ls[i] + lt[i]]
        for a, b, c in [(0, j, j + 1) for j in range(1, lt[i] - 1)]:
            t = U[[a, b, c]]
            sx = t[:, 0] * (atlas - 1)
            sy = (1.0 - t[:, 1]) * (atlas - 1)
            x0 = max(int(np.floor(sx.min())), 0); x1 = min(int(np.ceil(sx.max())) + 1, atlas)
            y0 = max(int(np.floor(sy.min())), 0); y1 = min(int(np.ceil(sy.max())) + 1, atlas)
            if x1 <= x0 or y1 <= y0:
                continue
            gy, gx = np.mgrid[y0:y1, x0:x1]
            px = gx + 0.5; py = gy + 0.5
            d = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
            if abs(d) < 1e-9:
                continue
            w0 = ((sy[1] - sy[2]) * (px - sx[2]) + (sx[2] - sx[1]) * (py - sy[2])) / d
            w1 = ((sy[2] - sy[0]) * (px - sx[2]) + (sx[0] - sx[2]) * (py - sy[2])) / d
            m = (w0 >= -0.002) & (w1 >= -0.002) & (w0 + w1 <= 1.002)
            if not m.any():
                continue
            img[gy[m], gx[m]] = per_face[i]
            hit[gy[m], gx[m]] = True
    return img, hit


def save(img, hit, name):
    """빈 텍셀은 회색 격자로 — 안 채워진 게 검정으로 보이면 색으로 오해한다."""
    a = img.copy()
    gy, gx = np.mgrid[0:ATLAS, 0:ATLAS]
    chk = (((gx // 16) + (gy // 16)) % 2).astype(float) * 12 + 30
    a[~hit] = chk[~hit][:, None]
    p = os.path.join(OUT, name)
    im = bpy.data.images.new(name, ATLAS, ATLAS)
    rgba = np.concatenate([np.clip(a / 255.0, 0, 1), np.ones((ATLAS, ATLAS, 1))], 2)
    im.pixels = rgba[::-1].ravel()
    im.filepath_raw = p; im.file_format = 'PNG'; im.save()
    print("  %s  채운 텍셀 %.1f%%" % (name, hit.mean() * 100))
    return p


def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "tri_paint.blend"))
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
    me = o.data
    MODE = os.environ.get("MODE", "v4")
    col = np.load(os.path.join(OUT, "tri_col.npy")).astype(float)
    pf = os.path.join(OUT, "tri_prov.npy")
    prov = np.load(pf) if os.path.exists(pf) else None   # v0~v3 은 출처를 안 남긴다
    assert len(col) == len(me.polygons), "면 수가 다르다 — tri_paint 를 다시 돌려라"

    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')

    ar = np.empty(len(me.polygons)); me.polygons.foreach_get("area", ar)
    print("[%s] 면 %d · smart_project" % (MODE, len(me.polygons)))
    if prov is not None:
        for k, tag in ((0, "직접"), (1, "전파"), (2, "뿔계급"), (3, "못받음")):
            m = prov == k
            print("  %-6s 면 %6d (%.1f%%)   **면적 %5.1f%%**"
                  % (tag, m.sum(), m.mean() * 100, ar[m].sum() / ar.sum() * 100))

    # 전개도에서 몇 색을 쓰나 — 셀이면 적어야 한다. v2 는 화소를 찍어 수백 색이었다
    u = np.unique(col.round().astype(int), axis=0)
    print("  이 전개도가 쓰는 색: %d개" % len(u))

    img, hit = rasterize(me, col, ATLAS)
    save(img, hit, "tri_uv_%s_col.png" % MODE)
    if prov is not None:
        img2, _ = rasterize(me, PROVCOL[prov], ATLAS)
        save(img2, hit, "tri_uv_%s_prov.png" % MODE)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "tri_uv.blend"))


if __name__ == "__main__":   # paint_uv.py 가 rasterize()/save() 를 가져다 쓴다
    main()
