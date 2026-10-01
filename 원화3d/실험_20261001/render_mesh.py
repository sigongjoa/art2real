import bpy, os, sys, json, math, numpy as np, mathutils
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; pre=sys.argv[sys.argv.index("--")+1]
for o in list(bpy.data.objects):
    if o.type=="MESH": bpy.data.objects.remove(o)
bpy.ops.wm.obj_import(filepath=S+"/cut/%s_groove.obj"%pre, forward_axis="Y", up_axis="Z"); ob=[o for o in bpy.data.objects if o.type=="MESH"][0]; ob.name="hull"
cams=json.load(open(S+"/cut/cams.json")); ob.matrix_world=mathutils.Matrix(cams["카메라_02_정면"]["M"])      # 정면 카메라 좌표로 지은 메시
for p in ob.data.polygons: p.use_smooth=True
# 옆 카메라(수식): 정면 카메라 좌표에서 +x 쪽에서 -x 로 본다 · 얼굴(+z)이 왼쪽 · hull_groove.py 의 side_px 와 같은 자리
import numpy as _np
cF=cams["카메라_02_정면"]; W,H,sF=cF["W"],cF["H"],cF["ortho"]; MF=mathutils.Matrix(cF["M"]); fit=_np.load(S+"/cut/hull_fit.npy"); s_side,ty=float(fit[0]),float(fit[1])
ucen=float(fit[2]); k=W/sF; off=float(fit[3]) if len(fit)>3 else 0.0
yc=ty*sF/W/s_side*(-1)*(-1); yc=ty*sF/W; zc=off+(ucen-W/2)/(k*s_side)
R=mathutils.Matrix(((0,0,1),(0,1,0),(-1,0,0))).transposed()   # 열 = right(0,0,-1) · up(0,1,0) · back(1,0,0)
R=mathutils.Matrix(((0,0,1),(0,1,0),(-1,0,0)))                 # 행렬 열벡터: col0=right=(0,0,-1)? 아래에서 직접 조립
Rm=mathutils.Matrix.Identity(3); Rm.col[0]=(0,0,-1); Rm.col[1]=(0,1,0); Rm.col[2]=(1,0,0)
loc_c=mathutils.Vector((400.0, yc, zc)); camS=bpy.data.objects.new("카메라_옆수식",bpy.data.cameras.new("옆수식")); sc.collection.objects.link(camS)
camS.data.type="ORTHO"; camS.data.ortho_scale=sF/s_side; camS.data.clip_end=5000; camS["W"]=W; camS["H"]=H
Mc=mathutils.Matrix.Translation(loc_c)@Rm.to_4x4(); camS.matrix_world=MF@Mc
sc.render.engine="BLENDER_WORKBENCH"; sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="SINGLE"; sh.single_color=(0.8,0.8,0.8); sh.show_cavity=True; sh.cavity_type="BOTH"; sh.cavity_valley_factor=1.3; sh.cavity_ridge_factor=0.6
sc.render.film_transparent=True; sc.render.image_settings.color_mode="RGBA"
for nm in ("02_정면","옆수식","02_3-4"):
    c=bpy.data.objects["카메라_"+nm]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/%sshade_%s.png"%(pre,nm.split("_")[1] if "_" in nm else "옆"); bpy.ops.render.render(write_still=True)
# 흔들기 · 3/4 — 정면 카메라 좌표에서 머리 중심을 y 축으로 돌려 본다(블록아웃 3/4 카메라는 이 틀과 안 맞는다)
Vc=np.array([v.co for v in ob.data.vertices]); ctr_c=mathutils.Vector(Vc.mean(0)); cam=bpy.data.objects.new("카메라_돌림",bpy.data.cameras.new("돌림")); sc.collection.objects.link(cam); cam.data.type="ORTHO"; cam.data.ortho_scale=170; cam.data.clip_end=5000
def 보기(deg):
    Ry=mathutils.Matrix.Rotation(math.radians(deg),4,"Y"); loc=ctr_c+Ry.to_3x3()@mathutils.Vector((0,0,400)); cam.matrix_world=MF@(mathutils.Matrix.Translation(loc)@Ry)
sc.render.film_transparent=True; 보기(35); sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860; sc.render.filepath=S+"/cut/%sshade_3-4.png"%pre; bpy.ops.render.render(write_still=True)
sc.render.film_transparent=False; sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03)
for i in range(25):
    보기(-40+i*(80/24)); sc.render.filepath=S+"/cut/hanim/%s%02d.png"%(pre,i); bpy.ops.render.render(write_still=True)
# 선 렌더(정면 · 옆) — 선 대조용
m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
for x in list(nt.nodes): nt.nodes.remove(x)
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0]); ob.data.materials.append(m)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.film_transparent=True; sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings; fs.crease_angle=math.radians(150)
for ls in list(fs.linesets): fs.linesets.remove(ls)
ls=fs.linesets.new("선"); ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True; ls.linestyle.color=(0,0,0); ls.linestyle.thickness=2.0
for nm in ("02_정면","옆수식"):
    c=bpy.data.objects["카메라_"+nm]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/%s_%s.png"%(pre,nm.split("_")[1] if "_" in nm else "옆"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/%s.blend"%pre); print("rendered")
