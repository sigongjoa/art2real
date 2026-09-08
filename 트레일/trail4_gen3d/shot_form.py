import math, os, sys
import bpy
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='MATCAP'; sc.display.shading.studio_light='basic_1.exr'
sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.85,0.85,0.87)
sc.display.shading.show_cavity=True; sc.display.shading.cavity_type='BOTH'
sc.display.shading.curvature_ridge_factor=1.0
sc.display.shading.curvature_valley_factor=1.0
sc.render.film_transparent=True
sc.render.resolution_x=640; sc.render.resolution_y=1100
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag,osc,z in ((90,"side",1.15,0.5),(0,"front",1.15,0.5),
                     (90,"leg",0.45,0.28),(90,"torso",0.5,0.68)):
    cd.ortho_scale=osc; a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,z); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("FORM OK")
