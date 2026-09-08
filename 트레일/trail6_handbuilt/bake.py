# -*- coding: utf-8 -*-
"""손으로 지은 부품에 원화를 굽고, 텍스처까지 붙인 A/B 를 뽑는다.

    python bake.py

굽는 알맹이는 trail4 의 `bake_art.py` 를 그대로 부른다 (면마다 판 고르기 · 광선 가려짐 검사 ·
클래스 대체색 · 시임 팽창이 전부 들어 있다). 여기서 하는 건 두 가지뿐이다.

    1) 부품 5개를 하나로 합친다 (UV 배치는 build.py 의 layout() 이 이미 끝냈다)
    2) 구운 뒤 A/B 를 텍스처 셰이딩으로 렌더하고 원화와 붙여 잰다

66번 경고 그대로 — 이 그림의 loss 는 **판정이 아니라 구경**이다. 아틀라스는 그 원화를
투영해 만든 것이라 같은 원화와 비교하면 투영을 재는 것이다.
"""
import json
import os
import subprocess
import sys

try:
    import bpy
except ImportError:
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
BASE = os.path.join(T4, "out", "nd_baked.blend")
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
VIEWS = (("front", 0), ("q", 40), ("side", 90))
DROP_FRAC = 0.50


def pack(src, dst):
    """부품 5개를 **합치기만** 한다. UV 배치는 build.py 가 이미 했다."""
    import bmesh  # noqa
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(src) as (s, d):
        d.objects = s.objects
    for o in d.objects:
        bpy.context.scene.collection.objects.link(o)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    # 팩은 안 한다. build.py 의 layout() 이 이미 축척 하나로 한 판에 배치했다
    # (섬 7개 · 밀도차 1.3배 · 겹침 없음). 여기서 pack 을 또 돌리면 그걸 흐트러뜨린다.
    import numpy as np
    me = o.data
    nf = len(me.polygons)
    uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
    names = [m.name if m else "" for m in me.materials]
    np.savez(os.path.splitext(dst)[0] + "_uv.npz", uv=uv.reshape(-1, 2), ls=ls, lt=lt,
             mat=mi, matnames=np.array(names))
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print(f"PACK OK faces={nf} -> {dst}")


def render_ab(part_blend, prefix):
    import math
    import bmesh
    import numpy as np

    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    x0, x1 = spec["front"]["u"]
    z0, z1 = spec["front"]["z"]
    y0, y1 = spec["side"]["y"]
    p = 0.012
    lo, hi = np.array([x0 - p, y0 - p, z0 - p]), np.array([x1 + p, y1 + p, z1 + p])

    def setup():
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'
        sc.display.shading.light = 'FLAT'
        sc.display.shading.color_type = 'TEXTURE'
        sc.render.film_transparent = True
        sc.render.resolution_x = sc.render.resolution_y = RES
        sc.view_settings.view_transform = 'Standard'
        cd = bpy.data.cameras.new("c")
        cd.type = 'ORTHO'
        cd.ortho_scale = U1 - U0
        cam = bpy.data.objects.new("c", cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
        return sc, cam

    def shoot(sc, cam, tag):
        for name, az in VIEWS:
            a = math.radians(az)
            cam.location = (math.sin(a) * 6, -math.cos(a) * 6, (Z0 + Z1) / 2)
            cam.rotation_euler = (math.radians(90), 0, a)
            sc.render.filepath = f"{prefix}_{tag}_{name}.png"
            bpy.ops.render.render(write_still=True)

    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc, cam = setup()
    shoot(sc, cam, "A")

    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc, cam = setup()
    names = json.load(open(os.path.join(T4, "named_parts.json"), encoding="utf-8"))
    for o in [x for x in sc.objects if x.type == 'MESH']:
        if "part_id" not in o.data.attributes:
            continue
        pid = np.empty(len(o.data.polygons), np.int32)
        o.data.attributes["part_id"].data.foreach_get("value", pid)
        cen = np.empty(len(o.data.polygons) * 3, np.float32)
        o.data.polygons.foreach_get("center", cen)
        cen = cen.reshape(-1, 3)
        inside = np.all((cen >= lo) & (cen <= hi), axis=1)
        kill = {int(i) for i in np.unique(pid)
                if (pid == i).sum() and inside[pid == i].mean() > DROP_FRAC}
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if pid[f.index] in kill], context='FACES')
        bm.to_mesh(o.data)
        bm.free()
    with bpy.data.libraries.load(part_blend) as (s, d):
        d.objects = s.objects
    for o in d.objects:
        sc.collection.objects.link(o)
    shoot(sc, cam, "B")
    print("TEXRENDER OK")


def sweep_fill(atlas_npy, spec_colors, out_png):
    """**기각됨 (LESSONS 73).** `SWEEP=1` 일 때만 돈다.

    단색으로 때운 텍셀을 **UV 축을 따라** 원화색으로 쓸어 채운다.

    UV 를 지을 때 내가 정했으니 모든 텍셀이 무슨 뜻인지 안다 — 캡 띠는 가로가 고리 둘레,
    세로가 앞->뒤다. 3판이 본 건 앞쪽 40% 뿐이고 나머지는 클래스 단색이었다(65% 텍셀).
    그 단색을 **같은 둘레 위치의 실제 원화색**으로 세로로 끌고 간다.
    갑주 패널선은 형태를 따라 도니까 이게 사람이 손으로 할 일과 같다.
    """
    import cv2
    import numpy as np
    img = np.load(atlas_npy).astype(np.int16)
    fb = np.array(list(spec_colors), np.int16)              # 대체색들 (합성값이라 정확히 일치한다)
    solid = np.zeros(img.shape[:2], bool)
    for c in fb:
        solid |= np.all(img == c, 2)
    # CLSCOL[0] 은 (150,150,**155**) 다. |c-150|<4 로 걸렀더니 파랑 채널이 안 걸려
    # 배경이 "유효한 색"으로 취급됐고, 쓸어 채우기가 그 회색을 캡 띠로 끌어왔다.
    bg = np.all(img == np.array([150, 150, 155], np.int16), 2)
    valid = ~solid & ~bg
    # 잘못 읽은 덩어리를 먼저 버린다. 가려짐 검사는 통과했는데 그 자리 원화가 팔(검정)이라
    # 캡 한복판이 새까맣게 찍혔다. **원화의 먹선은 가늘고 오독은 덩어리다** —
    # 침식으로 5px 를 견디면 선이 아니라 덩어리다.
    dark = valid & (img.max(2) < 70)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    blob = cv2.dilate(cv2.erode(dark.astype(np.uint8), ker), ker).astype(bool) & dark
    valid &= ~blob
    before = (solid | blob).sum()
    print(f"오독 덩어리 버림 {int(blob.sum()):,} 텍셀")
    out = img.copy()
    # 1) 세로(앞->뒤) 로 끌고 간다. 2) 남은 건 가로로.
    for axis in (0, 1):
        v = valid.copy()
        a = out.copy()
        idx = np.where(v, np.arange(v.shape[axis]).reshape(-1, 1) if axis == 0
                       else np.arange(v.shape[axis]).reshape(1, -1), -1)
        fwd = np.maximum.accumulate(idx, axis=axis)
        bwd = np.flip(np.maximum.accumulate(np.flip(np.where(v, idx, -1), axis), axis=axis), axis)
        for tgt in (fwd, bwd):
            take = (~v) & ~bg & (tgt >= 0)
            if not take.any():
                continue
            r, c = np.nonzero(take)
            src = (tgt[r, c], c) if axis == 0 else (r, tgt[r, c])
            out[r, c] = a[src]
            valid |= take
    after = ((~valid) & ~bg).sum()
    print(f"쓸어 채우기  단색 {before:,} -> 남은 {after:,}  "
          f"(부품 텍셀의 {before / max((~bg).sum(), 1) * 100:.1f}% -> "
          f"{after / max((~bg).sum(), 1) * 100:.1f}%)")
    buf = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(out_png.replace("_atlas.png", "_atlas_raw.png"),
                cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    np.save(atlas_npy, buf)
    cv2.imwrite(out_png, cv2.cvtColor(buf, cv2.COLOR_RGB2BGR))
    return buf


def flatten_faces(atlas_npy, uvnpz, colors, out_png, min_px=40):
    """**면 하나 = 색 하나.** 텍셀마다 원화를 찍어 읽으면 면 경계를 넘나든다.

    셀 원화는 평면색이고 내가 지은 면은 곧 갑판이다. 그러니 면 안에서 읽은 색들의
    **중앙값 하나**로 그 면을 통째로 칠한다. 검은 덩어리(오독)도 중앙값이면 살아남지 못한다.
    유효 텍셀이 min_px 미만인 면은 그 재질의 실측색으로.
    """
    import cv2
    import numpy as np
    img = np.load(atlas_npy).astype(np.int16)
    S = img.shape[0]
    d = np.load(uvnpz, allow_pickle=True)
    uv, ls, lt, mat = d["uv"], d["ls"], d["lt"], d["mat"]
    names = [str(x) for x in d["matnames"]]
    fb = np.array(list(colors), np.int16)
    solid = np.zeros(img.shape[:2], bool)
    for c in fb:
        solid |= np.all(img == c, 2)
    bg = np.all(img == np.array([150, 150, 155], np.int16), 2)
    valid = ~solid & ~bg
    out = img.copy()
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    read, rejected = 0, []
    for f in range(len(ls)):
        p = uv[ls[f]:ls[f] + lt[f]].copy()
        p[:, 1] = 1 - p[:, 1]
        q = np.round(np.clip(p, 0, 1) * (S - 1)).astype(np.int32)
        m = np.zeros((S, S), np.uint8)
        cv2.fillPoly(m, [q], 1)
        # 굽기가 시임을 6회 팽창시켜 놨다. 안쪽으로 깎고 읽어야 옆 면 색이 안 섞인다
        inner = cv2.erode(m, ker).astype(bool)
        sel = img[inner & valid]
        gold = "gold" in names[mat[f]]
        col = None
        if len(sel) >= min_px:
            med = np.median(sel, 0)
            # 읽은 색이 그 면의 **재질과 색상이 맞을 때만** 받는다.
            # 안 걸러면 뿔이 왼쪽 어깨의 빨간 방패나 흰 투구를 읽어 온다.
            # 절대거리로 재면 셀의 밝은 톤까지 버리니 **색상(파랑 우세 / 빨강 우세)** 으로 판정한다.
            r_, g_, b_ = med
            # 금은 **노랑**이라 g 가 r 에 붙어 있고(158,138,76 -> r-g=20),
            # 빨간 방패는 g 가 뚝 떨어진다(180,60,50 -> r-g=120). 빨강 우세만 보면 방패가 통과한다.
            ok = (r_ - b_ > 20 and r_ - g_ < 60) if gold else (b_ - r_ > 5)
            if ok:
                col = med
                read += 1
            else:
                rejected.append((f, tuple(int(x) for x in med), gold))
        if col is None:
            col = colors[1] if gold else colors[0]
        out[m.astype(bool)] = col
    print(f"면 단위 평면색  원화에서 읽은 면 {read}/{len(ls)} ({read / len(ls) * 100:.0f}%)  "
          f"재질 불일치로 버린 면 {len(rejected)}")
    for f, c, g in rejected[:6]:
        print(f"    면{f:3d} {'gold' if g else 'shell'} 이 읽은 색 {c}")
    buf = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(out_png.replace("_atlas.png", "_atlas_raw.png"),
                cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    np.save(atlas_npy, buf)
    cv2.imwrite(out_png, cv2.cvtColor(buf, cv2.COLOR_RGB2BGR))


def repoint(blend, png):
    """구운 blend 가 쓸어 채운 PNG 를 다시 읽게 한다."""
    bpy.ops.wm.open_mainfile(filepath=blend)
    for im in bpy.data.images:
        if im.source == 'FILE':
            im.filepath = png
            im.reload()
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("REPOINT OK")


def measure(prefix):
    import cv2
    import numpy as np
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    x0, x1 = spec["front"]["u"]
    z0, z1 = spec["front"]["z"]
    y0, y1 = spec["side"]["y"]
    pad = 0.02
    c = lambda u: int(round((u - U0) / (U1 - U0) * (RES - 1)))
    r = lambda z: int(round((Z1 - z) / (Z1 - Z0) * (RES - 1)))
    print(f"\n{'':4}{'뷰':<7}{'형태 불일치':>13}{'색 L1(겹친 곳)':>18}")
    for view in ("front", "side"):
        h0, h1 = (x0, x1) if view == "front" else (y0, y1)
        sl = (slice(max(r(z1 + pad), 0), r(z0 - pad)), slice(max(c(h0 - pad), 0), c(h1 + pad)))
        art = np.load(os.path.join(T4, f"rgb_{view}.npy"))
        am = (art[..., 3] > 0)[sl]
        a = art[..., :3].astype(np.float32)[sl]
        for tag in ("A", "B"):
            im = cv2.imread(f"{prefix}_{tag}_{view}.png", cv2.IMREAD_UNCHANGED)
            bm_ = (im[..., 3] > 0)[sl]
            b = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB).astype(np.float32)[sl]
            both, uni = am & bm_, am | bm_
            print(f"{tag:<4}{view:<7}{1 - both.sum() / max(uni.sum(), 1):>12.1%}"
                  f"{np.abs(a - b)[both].mean() / 255:>17.1%}")


def main():
    out = os.path.join(HERE, "out")
    packed = os.path.join(out, "pauldron_packed.blend")
    baked = os.path.join(out, "pb")
    subprocess.run([BLENDER, "-b", "--python", __file__, "--", "pack",
                    os.path.join(out, "pauldron.blend"), packed], check=True)
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    env = dict(os.environ)
    if "color" in spec:
        env["BAKE_CLSCOL"] = json.dumps({"1": spec["color"]["shell"], "3": spec["color"]["gold"]})
    subprocess.run([BLENDER, "-b", "--python", os.path.join(T4, "bake_art.py"), "--",
                    packed, baked], check=True, env=env)
    cols = [spec["color"]["shell"], spec["color"]["gold"], [26, 26, 32], [238, 238, 242]]
    if os.environ.get("FLAT", "1") == "1":
        flatten_faces(baked + "_atlas.npy", os.path.splitext(packed)[0] + "_uv.npz",
                      cols, baked + "_atlas.png")
        subprocess.run([BLENDER, "-b", "--python", __file__, "--", "repoint",
                        baked + ".blend", baked + "_atlas.png"], check=True)
    if os.environ.get("SWEEP") == "1":
        # 기각됨 (LESSONS 73). 스위치로만 남긴다
        sweep_fill(baked + "_atlas.npy", cols, baked + "_atlas.png")
        subprocess.run([BLENDER, "-b", "--python", __file__, "--", "repoint",
                        baked + ".blend", baked + "_atlas.png"], check=True)
    subprocess.run([BLENDER, "-b", "--python", __file__, "--", "render",
                    baked + ".blend", os.path.join(out, "t")], check=True)
    measure(os.path.join(out, "t"))


if __name__ == "__main__":
    if bpy is not None:
        argv = sys.argv[sys.argv.index("--") + 1:]
        if argv[0] == "pack":
            pack(os.path.abspath(argv[1]), os.path.abspath(argv[2]))
        elif argv[0] == "repoint":
            repoint(os.path.abspath(argv[1]), os.path.abspath(argv[2]))
        else:
            render_ab(os.path.abspath(argv[1]), os.path.abspath(argv[2]))
    else:
        main()
