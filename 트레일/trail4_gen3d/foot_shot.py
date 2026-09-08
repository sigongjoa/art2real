import math, os, sys
import bpy, mathutils
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1]); OUT=os.path.abspath(sys.argv[sys.argv.index("--")+2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in obs: o.select_set(True)
bpy.context.view_layer.objects.active=obs[0]
if len(obs)>1: bpy.ops.object.join()
ob=bpy.context.view_layer.objects.active
co=[ob.matrix_world@v.co for v in ob.data.vertices]
lo=mathutils.Vector([min(c[i] for c in co) for i in range(3)]); hi=mathutils.Vector([max(c[i] for c in co) for i in range(3)])
s=1.0/(hi.z-lo.z); ob.scale=(s,)*3; bpy.ops.object.transform_apply(scale=True)
lo,hi=lo*s,hi*s; ob.location=(-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z); bpy.ops.object.transform_apply(location=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='MATCAP'; sc.display.shading.studio_light='basic_1.exr'
sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.85,0.85,0.87)
sc.display.shading.show_cavity=True; sc.display.shading.cavity_type='BOTH'
sc.render.film_transparent=True; sc.render.resolution_x=900; sc.render.resolution_y=420
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=0.62
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6, -math.cos(a)*6, 0.105)
    cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=OUT.replace(".png",f"_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("OK")
