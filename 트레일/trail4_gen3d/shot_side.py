import math, os, sys
import bpy
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.render.film_transparent=True
sc.render.resolution_x=520; sc.render.resolution_y=900
sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new("w"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[1].default_value=1.5; sc.world=w
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.15
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((90,"R"),(270,"L")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("SIDESHOT OK")
