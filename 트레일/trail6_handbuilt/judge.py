# -*- coding: utf-8 -*-
"""손으로 지은 부품이 나아졌는지 잰다. A = 생성 메시 그대로, B = 그 자리에 내 부품.

    python judge.py                      # 렌더까지 알아서 부른다

지표는 두 개다. 하나만 보면 "지표에는 안 잡히는데 눈에는 보이는" 결함이 남는다 (LESSONS 57).
    실루엣 IoU    바깥 윤곽이 맞나
    내부 선 밀도  안쪽에 형태가 있나   (Canny, 실루엣 경계 5px 제외)
그리고 면 수 — 얼마를 주고 샀는지 같이 적는다 (LESSONS 52: 지표 하나만 보고 좋아하지 마라).
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
RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1
VIEWS = (("front", 0), ("q", 40), ("side", 90))
DROP_FRAC = 0.50    # 이 비율 넘게 상자에 든 파츠는 통째로 뺀다.
                    # 0.30 도 0.25 도 더 나빴다 — a_shoulder(0.32) 는 매끈한 공이 아니라
                    # 팔 이음매고, 지우면 구멍이 나서 IoU 가 0.851 -> 0.763 으로 떨어진다.


# ----------------------------------------------------------------- 블렌더 쪽
def render_ab(part_blend, prefix):
    import math
    import bmesh
    from mathutils import Vector

    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    x0, x1 = spec["front"]["u"]
    z0, z1 = spec["front"]["z"]
    y0, y1 = spec["side"]["y"]
    pad = 0.012
    lo = Vector((x0 - pad, y0 - pad, z0 - pad))
    hi = Vector((x1 + pad, y1 + pad, z1 + pad))

    def setup():
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'
        sc.display.shading.light = 'MATCAP'
        sc.display.shading.studio_light = 'basic_1.exr'
        sc.display.shading.color_type = 'SINGLE'
        sc.display.shading.single_color = (0.86, 0.86, 0.88)
        sc.display.shading.show_cavity = True
        sc.display.shading.cavity_type = 'BOTH'
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

    def faces_now():
        return sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type == 'MESH')

    stats = {}

    # A — 생성 메시 그대로
    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc, cam = setup()
    stats["A_faces_total"] = faces_now()
    stats["A_faces_region"] = count_in_box(lo, hi)
    shoot(sc, cam, "A")

    # B — 상자 안 면을 지우고 그 자리에 손으로 지은 부품
    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc, cam = setup()
    # 상자로 면을 자르면 팔이 톱니로 잘려 **그 톱니가 Canny 에 잡힌다** — 지표가 거짓말을 한다.
    # 파츠(part_id) 단위로, 상자 안에 절반 넘게 들어간 파츠만 통째로 뺀다.
    import numpy as np
    names = json.load(open(os.path.join(T4, "named_parts.json"), encoding="utf-8"))
    dropped = []
    for o in [x for x in sc.objects if x.type == 'MESH']:
        if "part_id" not in o.data.attributes:
            continue
        pid = np.empty(len(o.data.polygons), np.int32)
        o.data.attributes["part_id"].data.foreach_get("value", pid)
        cen = np.empty(len(o.data.polygons) * 3, np.float32)
        o.data.polygons.foreach_get("center", cen)
        cen = cen.reshape(-1, 3)
        inside = np.all((cen >= np.array(lo)) & (cen <= np.array(hi)), axis=1)
        kill_ids = set()
        for i in np.unique(pid):
            m = pid == i
            if m.sum() and inside[m].mean() > DROP_FRAC:
                kill_ids.add(int(i))
                dropped.append((names[i - 1] if 0 < i <= len(names) else f"#{i}",
                                int(m.sum()), round(float(inside[m].mean()), 2)))
            elif m.sum() and inside[m].sum() > 40:
                stats.setdefault("kept_in_box", []).append(
                    (names[i - 1] if 0 < i <= len(names) else f"#{i}",
                     int(inside[m].sum()), round(float(inside[m].mean()), 2)))
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if pid[f.index] in kill_ids], context='FACES')
        bm.to_mesh(o.data)
        bm.free()
    stats["dropped"] = dropped
    with bpy.data.libraries.load(part_blend) as (src, dst):
        dst.objects = src.objects
    for o in dst.objects:
        sc.collection.objects.link(o)
    stats["B_faces_total"] = faces_now()
    stats["B_faces_region"] = count_in_box(lo, hi)
    shoot(sc, cam, "B")

    # 격리 렌더 — 주변 기하 없이 그 자리의 형태만 본다.
    # 합성 렌더는 남은 원래 기하가 섞여 지표를 흐린다.
    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc, cam = setup()
    for o in [x for x in sc.objects if x.type == 'MESH']:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces
                                   if not all(lo[i] <= f.calc_center_median()[i] <= hi[i]
                                              for i in range(3))], context='FACES')
        bm.to_mesh(o.data); bm.free()
    shoot(sc, cam, "Aiso")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = setup()
    with bpy.data.libraries.load(part_blend) as (src, dst2):
        dst2.objects = src.objects
    for o in dst2.objects:
        sc.collection.objects.link(o)
    shoot(sc, cam, "Biso")

    stats["box"] = [list(lo), list(hi)]
    json.dump(stats, open(prefix + "_stats.json", "w"), indent=1)
    print("RENDER OK", json.dumps(stats))


def count_in_box(lo, hi):
    n = 0
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        for f in o.data.polygons:
            c = o.matrix_world @ f.center
            if all(lo[i] <= c[i] <= hi[i] for i in range(3)):
                n += 1
    return n


# ----------------------------------------------------------------- 판정 쪽
def line_density(alpha, gray, skin=5):
    """내부 선 밀도 — 실루엣 경계에서 skin 화소 안쪽만 센다. 바깥 윤곽은 형태가 아니다."""
    import cv2
    import numpy as np
    a = alpha.astype(np.uint8)
    inner = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (skin * 2 + 1,) * 2)).astype(bool)
    if inner.sum() == 0:
        return 0.0, 0
    e = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 60, 140) > 0
    return float((e & inner).sum() / inner.sum()), int(inner.sum())


def crop_box(spec, view, pad=0.02):
    """부품 상자를 그 뷰의 화소 범위로. 측면은 화면 가로가 월드 y 다."""
    import numpy as np
    x0, x1 = spec["front"]["u"]
    z0, z1 = spec["front"]["z"]
    y0, y1 = spec["side"]["y"]
    h0, h1 = (x0, x1) if view == "front" else (y0, y1)
    c = lambda u: int(round((u - U0) / (U1 - U0) * (RES - 1)))
    r = lambda z: int(round((Z1 - z) / (Z1 - Z0) * (RES - 1)))
    return (slice(max(r(z1 + pad), 0), r(z0 - pad)), slice(max(c(h0 - pad), 0), c(h1 + pad)))


def main_measure(prefix):
    import cv2
    import numpy as np
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    rows = []
    for view in ("front", "side"):
        sl = crop_box(spec, view)
        art = np.load(os.path.join(T4, f"rgb_{view}.npy"))
        a_alpha = (art[..., 3] > 0)[sl]
        a_gray = cv2.cvtColor(art[..., :3], cv2.COLOR_RGB2GRAY)[sl]
        d, n = line_density(a_alpha, a_gray)
        rows.append(("원화", view, d, n, a_alpha.mean(), None))
        for tag in ("A", "B", "Aiso", "Biso"):
            im = cv2.imread(f"{prefix}_{tag}_{view}.png", cv2.IMREAD_UNCHANGED)
            al = (im[..., 3] > 0)[sl]
            gr = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)[sl]
            d, n = line_density(al, gr)
            iou = float((al & a_alpha).sum() / max((al | a_alpha).sum(), 1))
            rows.append((tag, view, d, n, al.mean(), iou))
    return rows


def sheet(prefix, rows_data):
    """원화 | A | B | Aiso | Biso 를 한 장으로. 지표가 좋아졌다고 형태가 좋아진 게 아니다 (LESSONS 20)."""
    import cv2
    import numpy as np
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    rows = []
    for view in ("front", "side"):
        sl = crop_box(spec, view, pad=0.05)
        tiles = []
        art = np.load(os.path.join(T4, f"rgb_{view}.npy"))
        a = cv2.cvtColor(art[..., :3], cv2.COLOR_RGB2BGR).copy()
        a[art[..., 3] == 0] = 255
        num = {(t, v): (d, iou) for t, v, d, _, _, iou in rows_data}
        def cap(tag):
            d, iou = num.get((tag, view), (None, None))
            s_ = f"  line {d * 100:.2f}%" if d is not None else ""
            return s_ + (f"  IoU {iou:.3f}" if iou is not None else "")
        tiles.append(("art " + view + cap("원화"), a[sl]))
        for tag in ("A", "B", "Aiso", "Biso"):
            im = cv2.imread(f"{prefix}_{tag}_{view}.png", cv2.IMREAD_UNCHANGED)
            b = im[..., :3].copy()
            b[im[..., 3] == 0] = 255
            tiles.append((f"{tag} {view}" + cap(tag), b[sl]))
        out = []
        for name, t in tiles:
            t = cv2.resize(t, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
            t = cv2.copyMakeBorder(t, 28, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            cv2.putText(t, name.encode("ascii", "replace").decode(), (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
            out.append(t)
        h = max(t.shape[0] for t in out)
        out = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
               for t in out]
        rows.append(np.hstack(out))
    w = max(r.shape[1] for r in rows)
    rows = [cv2.copyMakeBorder(r, 0, 0, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))
            for r in rows]
    dst = os.path.join(HERE, "out", "proof_ab.png")
    cv2.imwrite(dst, np.vstack(rows))
    return dst


def main():
    prefix = os.path.join(HERE, "out", "j")
    part = os.path.join(HERE, "out", "pauldron.blend")
    if "--skip-render" not in sys.argv:
        subprocess.run([BLENDER, "-b", "--python", __file__, "--", "render", part, prefix], check=True)
    rows = main_measure(prefix)
    stats = json.load(open(prefix + "_stats.json"))
    print()
    print(f"{'':6}{'뷰':<7}{'내부 선 밀도':>13}{'면적(px)':>10}{'채움':>8}{'실루엣 IoU':>12}")
    for tag, view, d, n, fill, iou in rows:
        print(f"{tag:<6}{view:<7}{d * 100:>12.2f}%{n:>10}{fill:>8.3f}"
              + (f"{iou:>12.3f}" if iou is not None else f"{'-':>12}"))
    print()
    print(f"상자 안 면 수   A {stats['A_faces_region']:,}  ->  B {stats['B_faces_region']:,}")
    print(f"전체 면 수      A {stats['A_faces_total']:,}  ->  B {stats['B_faces_total']:,}")
    print("증명 그림", sheet(prefix, rows))


if __name__ == "__main__":
    if bpy is not None:
        argv = sys.argv[sys.argv.index("--") + 1:]
        render_ab(argv[1], argv[2])
    else:
        main()
