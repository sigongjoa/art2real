import math, os, sys
import bpy
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(1,1,1); sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("W2 OK")
