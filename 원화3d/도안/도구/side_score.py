"""**측면도 숫자로 잰다.** 정면만 재면 납작한 팬케이크도 만점이 나온다.

    blender -b <모델.blend> --python side_score.py -- <buildspec.json> <side_envelope.json> <출력폴더>
    py -3.11 side_score.py <side_envelope.json> <측면그림.png> <출력폴더>      (채점만)

측면 참조의 px -> 월드는 측면 외형 추출이 이미 정해놨다 (`px` 블록):
    y = (px_x - center_x) * world_per_px          # -y 가 앞
    z = z_top - (px_y - y_top) * world_per_px

**어느 쪽이 앞인지는 그림이 정한다.** 좌우를 뒤집어 둘 다 재고 맞는 쪽을 쓴다 —
한 번만 정하고 설계도에 적는다. 매번 고르면 그건 손실을 고르는 것이다.
"""
import json
import math
import os
import sys

try:
    import bpy
except ImportError:
    bpy = None


def render(spec_p, out, res=512):
    spec = json.load(open(spec_p, encoding="utf-8"))
    vf = spec["view_front"]
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("c")
    cam.type, cam.ortho_scale = 'ORTHO', vf["span"]
    cam.clip_start, cam.clip_end = 0.001, 40
    ob = bpy.data.objects.new("c", cam)
    sc.collection.objects.link(ob)
    sc.camera = ob
    ob.location = (8, 0, vf["cz"])
    ob.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light, sh.color_type = 'STUDIO', 'SINGLE'
    sh.single_color = (0.74, 0.74, 0.78)
    sh.show_cavity, sh.show_object_outline = True, False
    sc.render.image_settings.color_mode = 'RGBA'
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.abspath(os.path.join(out, "side_render.png"))
    bpy.ops.render.render(write_still=True)
    json.dump({"ortho_scale": vf["span"], "z_center": vf["cz"], "res": res},
              open(os.path.join(out, "side_frame.json"), "w"), indent=1)
    print("SIDE RENDER", sc.render.filepath)


def score(envp, imgp, out):
    import numpy as np
    from PIL import Image, ImageFilter
    env = json.load(open(envp, encoding="utf-8"))
    px = env["px"]
    fr = json.load(open(os.path.join(out, "side_frame.json")))
    s, zc, R = fr["ortho_scale"], fr["z_center"], fr["res"]
    k, cx, ytop = px["world_per_px"], px["center_x"], px["y_top"]
    ztop = max(r[0] for r in env["rows"])

    # **GT 는 외형 추출이 추적한 그 마스크다.** 배경 임계값으로 다시 만들면
    # 어깨·망토까지 들어와 같은 그림에서 GT 가 둘이 된다(실측: 위쪽 과함, 아래쪽 빠짐).
    mp = os.path.splitext(envp)[0] + ".mask.npy"
    if os.path.exists(mp):
        sil = np.load(mp)
    else:
        im = Image.open(imgp).convert("RGB")
        if max(im.size) != px["scale"]:
            t = px["scale"] / max(im.size)
            im = im.resize((round(im.width * t), round(im.height * t)), Image.LANCZOS)
        a = np.asarray(im).astype(int)
        sil = ~((a[..., 0] > 240) & (a[..., 1] > 240) & (a[..., 2] > 240))
    sil = np.asarray(Image.fromarray((sil * 255).astype(np.uint8), "L")
                     .filter(ImageFilter.MaxFilter(5))
                     .filter(ImageFilter.MinFilter(5))) > 127
    box = (round(cx - (s / 2) / k), round(ytop + (ztop - (zc + s / 2)) / k),
           round(cx + (s / 2) / k), round(ytop + (ztop - (zc - s / 2)) / k))
    ref = np.asarray(Image.fromarray((sil * 255).astype(np.uint8), "L")
                     .crop(box).resize((R, R), Image.NEAREST)) > 127
    mod = np.asarray(Image.open(os.path.join(out, "side_render.png")))[..., 3] > 40
    best = None
    for flip, m in (("as-is", mod), ("flipped", mod[:, ::-1])):
        i, u = (ref & m).sum(), (ref | m).sum()
        v = i / u if u else 0.0
        print(f"  측면 {flip:8s} IoU {v:.3f} · 빠짐 {(ref&~m).sum()/max(1,ref.sum()):5.1%} "
              f"· 과함 {(m&~ref).sum()/max(1,m.sum()):5.1%}")
        if best is None or v > best[0]:
            best = (v, flip, m)
    v, flip, m = best
    print(f"측면 IoU {v:.3f}  (앞 방향: {flip})")
    ov = np.zeros((R, R, 3), np.uint8)
    ov[ref & m] = (60, 190, 90); ov[ref & ~m] = (70, 110, 220); ov[m & ~ref] = (220, 70, 70)
    Image.fromarray(ov).save(os.path.join(out, "side_overlay.png"))
    return v


if __name__ == "__main__":
    if bpy is not None and "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
        render(argv[0], argv[2] if len(argv) > 2 else "side_out")
    else:
        score(sys.argv[1], sys.argv[2], sys.argv[3])
