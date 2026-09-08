# -*- coding: utf-8 -*-
"""생성 메시(TripoSG)에 `look.py` 와 **똑같은 재질 4종**을 물린다.

    blender -b --python tri_look.py

손으로 지은 것과 같은 조명·같은 카메라·같은 셰이더로 찍어야 비교가 된다.
색은 전부 라벤더다 — 생성 메시는 뿔이 별개 오브젝트가 아니라서 금색을 나눌 데가 없다.
그것 자체가 이 메시의 한계다 (부품으로 안 갈라진다).
"""
import bpy, os, sys, math
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GLB = os.path.join(HERE, "out", "tri_pauldron.glb")
# 원화 견갑+뿔 마스크(panels.json lav+gold, 10,163px)에서 잰 상자
X0, X1, Z0, Z1 = 0.1179, 0.2504, 0.7856, 0.9850
CY = 0.027
AZ = 0            # tri_fit.py 가 IoU 로 고른 값. 눈으로 -90 이라 찍었던 게 틀렸다
FITBY = "width"   # 폭 기준 배율 (IoU 0.677 vs 높이 기준 0.607)


def bring():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = "TRI"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if AZ:
        o.data.transform(Matrix.Rotation(math.radians(AZ), 4, 'Z'))
    co = [v.co for v in o.data.vertices]
    mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    s = ((X1 - X0) / max(mx.x - mn.x, 1e-9) if FITBY == "width"
         else (Z1 - Z0) / max(mx.z - mn.z, 1e-9))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-(mn + mx) / 2))
    o.data.transform(Matrix.Translation(Vector(((X0 + X1) / 2, CY, (Z0 + Z1) / 2))))
    print("TRI 배치 az=%d %s 배율 %.4f  면 %d" % (AZ, FITBY, s, len(o.data.polygons)))
    return o


def main():
    bring()
    import look                       # stage()/변형들을 그대로 쓴다
    sc = look.stage()
    for k in ("1flat", "2cel", "3metal", "4worn"):
        for x in [y for y in sc.objects if y.name.endswith("_OL")]:
            bpy.data.objects.remove(x, do_unlink=True)
        look.VARIANTS[k]()
        sc.view_settings.view_transform = 'Standard' if k == "2cel" else 'Filmic'
        sc.render.filepath = os.path.join(HERE, "out", "trilook_%s.png" % k)
        bpy.ops.render.render(write_still=True)
        print("TRILOOK", k)


if __name__ == "__main__":       # tri_paint.py 가 bring() 만 가져다 쓴다
    main()
