import bpy, sys, os
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\B1"
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "head60k.blend"))
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = 500
sh = sc.display.shading; sh.color_type = "SINGLE"; sh.single_color = (0.85,0.85,0.88)
o = [x for x in sc.objects if x.type=="MESH"][0]
for lam in (0.5, 1.0, 1.5):
    o.scale = (1, lam, 1)
    for L, tag in (("FLAT","sil"), ("STUDIO","shade")):
        sh.light = L; sh.show_cavity = (L == "STUDIO")
        H.look((0,0,0), 0, 0, ortho=120); H.shot(os.path.join(OUT, "front_%s_%.1f.png" % (tag, lam)))
    sh.light = "STUDIO"; sh.show_cavity = True
    H.look((0,0,0), 90, 0, ortho=180); H.shot(os.path.join(OUT, "side_%.1f.png" % lam))
