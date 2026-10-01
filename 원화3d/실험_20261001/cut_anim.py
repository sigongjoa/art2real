# 과정 클립: 3/4 카메라에서 (1) 트리포 원본 → (2) 파츠가 번호순으로 하나씩 나타남 (3) 완성 뒤 한 바퀴. Workbench 오브젝트 색.
import bpy, os, math, mathutils
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; O=S+"/cut/anim/"
sc.render.engine="BLENDER_WORKBENCH"; sc.render.use_freestyle=False; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="OBJECT"; sc.render.film_transparent=False
sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03)
cam=bpy.data.objects["카메라_02_3-4"]; sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860; sc.render.resolution_percentage=100
parts=sorted([o for o in bpy.data.objects if o.name.startswith("파츠")],key=lambda o:o.name)
# 머리 중심으로 카메라 줌: 파츠 전체 bbox 중심
import numpy as np
pts=np.array([o.matrix_world@mathutils.Vector(c) for o in parts for c in o.bound_box]); ctr=mathutils.Vector(pts.mean(0)); 
cam.data.ortho_scale=180
# 카메라를 중심 쪽으로 평행이동(시선 방향 유지)
d=cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); cam.location=ctr+d*400
tri=bpy.data.objects["트리포"]; tri.hide_render=False; tri.color=(0.75,0.75,0.75,1)
for p in parts: p.hide_render=True
f=0
def shot():
    global f; sc.render.filepath=O+"f%04d.png"%f; bpy.ops.render.render(write_still=True); f+=1
for _ in range(6): shot()                 # 원본 트리포
tri.hide_render=True
for _ in range(3): shot()                 # 빈 화면
for p in parts:
    p.hide_render=False; shot()           # 파츠 하나씩
for _ in range(4): shot()
# 한 바퀴: 카메라를 중심 둘레로 회전 (z축)
base=cam.matrix_world.copy()
for i in range(36):
    R=mathutils.Matrix.Rotation(math.radians(i*10),4,"Z"); T=mathutils.Matrix.Translation(ctr); cam.matrix_world=T@R@T.inverted()@base; shot()
print("frames",f)
