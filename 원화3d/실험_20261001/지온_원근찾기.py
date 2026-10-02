import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\샘플\메크머리_CC0\지온"; G_=os.path.join(O,"원근"); os.makedirs(G_,exist_ok=True)
sc = H.scene(res=(160, 160), transparent=True); sc.display.shading.light = "FLAT"
obs=[]
for k in ("투구_가운데", "핀_왼", "핀_오른", "총_왼", "총_오른"):
    bpy.ops.wm.obj_import(filepath=os.path.join(O, f"자세_{k}.obj"), forward_axis="Y", up_axis="Z"); obs.append(bpy.context.selected_objects[0])
bb = [o.matrix_world @ Vector(v) for o in obs for v in o.bound_box]; c = sum(bb, Vector()) / len(bb)
H.look(tuple(c),180,0,150,dist=500); cam=sc.camera; cam.data.type="PERSP"; cam.data.lens=50; cam.data.sensor_width=36
for yaw in range(140, 231, 10):
  for pitch in (5,15,25,35):
    for dist in (110,160,240,400):
      y=math.radians(yaw); p=math.radians(pitch); d=Vector((math.sin(y)*math.cos(p), -math.cos(y)*math.cos(p), math.sin(p)))
      cam.location=c+d*dist; cam.rotation_euler=(-d).to_track_quat("-Z","Y").to_euler(); bpy.context.view_layer.update()
      sc.render.filepath=os.path.join(G_,f"y{yaw}_p{pitch}_d{dist}.png"); bpy.ops.render.render(write_still=True)
print("ok")
