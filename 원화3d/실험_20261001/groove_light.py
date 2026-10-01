# 가벼운 판: 세분 1 · foreach 변위 · Workbench 캐비티 · 과정 프레임(원본 → 먹선 자리 색 → 홈 깊어짐 → 한 바퀴)
import bpy, os, numpy as np, mathutils, math
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; tri=bpy.data.objects["트리포"]; O=S+"/cut/ganim/"
d, w_px = 0.8, 3.0
md=tri.modifiers.new("세분","SUBSURF"); md.levels=1; md.subdivision_type="SIMPLE"; bpy.context.view_layer.objects.active=tri; bpy.ops.object.modifier_apply(modifier="세분")
me=tri.data; n=len(me.vertices); print("점",n,"면",len(me.polygons))
co=np.zeros(n*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3); nr=np.zeros(n*3); me.vertices.foreach_get("normal",nr); nr=nr.reshape(-1,3)
M=np.array(tri.matrix_world); V=(M[:3,:3]@co.T).T+M[:3,3]; R=M[:3,:3]; N=(R@nr.T).T; N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-9
disp=np.zeros(n)
for 키,camname,fit in (("정면","카메라_02_정면",(1.0,0,0)),("옆","카메라_02_옆",(0.9,36,45))):
    cam=bpy.data.objects[camname]; Mi=np.array(cam.matrix_world.inverted()); W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale
    vc=(Mi[:3,:3]@V.T).T+Mi[:3,3]; px=(vc[:,0]/osc+0.5)*W; py=(0.5-vc[:,1]/(osc*H/W))*H; s,tx,ty=fit; px=s*px+tx; py=s*py+ty
    dist=np.load(S+f"/cut/벽거리_{키}.npy"); ix=np.clip(px.round().astype(int),0,W-1); iy=np.clip(py.round().astype(int),0,H-1); dv=dist[iy,ix]
    camdir=np.array(cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1))); facing=(N@camdir)>0.25
    g=np.clip(1-dv/w_px,0,1)*facing; disp=np.maximum(disp,g); print(키,"홈 점",int((g>0).sum()))
# 정점 색: 홈 자리 빨강
ca=me.color_attributes.new("홈","FLOAT_COLOR","POINT"); col=np.tile([0.8,0.8,0.8,1.0],(n,1)); col[disp>0]=[0.9,0.1,0.1,1.0]; ca.data.foreach_set("color",col.ravel())
nl=np.linalg.norm(nr,axis=1,keepdims=True)+1e-9; nrn=nr/nl; sw=float(np.cbrt(abs(np.linalg.det(R)))); print('세계 배율',sw)   # 로컬 법선 · 세계 배율로 나눠 로컬 단위 변위
def 변위(k): me.vertices.foreach_set("co",(co-nrn*(d*k*disp/sw)[:,None]).ravel()); me.update()
sc.render.engine="BLENDER_WORKBENCH"; sc.render.use_freestyle=False; sc.render.film_transparent=False; sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03)
sh=sc.display.shading; sh.light="STUDIO"; sh.show_cavity=True; sh.cavity_type="BOTH"; sh.cavity_ridge_factor=1.5; sh.cavity_valley_factor=2.0
cam=bpy.data.objects["카메라_02_3-4"]; sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860
pts=V; ctr=mathutils.Vector(pts.mean(0)); cam.data.ortho_scale=190; dv_=cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); cam.location=ctr+dv_*400; base=cam.matrix_world.copy()
f=0
def shot():
    global f; sc.render.filepath=O+"f%04d.png"%f; bpy.ops.render.render(write_still=True); f+=1
sh.color_type="SINGLE"; sh.single_color=(0.8,0.8,0.8)
for _ in range(6): shot()                                   # 원본
sh.color_type="VERTEX"
for _ in range(8): shot()                                   # 먹선 자리 색
for k in np.linspace(0,1,10): 변위(k); shot()                # 홈 파임
for _ in range(4): shot()
for i in range(36):
    Rz=mathutils.Matrix.Rotation(math.radians(i*10),4,"Z"); T=mathutils.Matrix.Translation(ctr); cam.matrix_world=T@Rz@T.inverted()@base; shot()
cam.matrix_world=base; print("frames",f)
# 세 카메라 정지 렌더(캐비티 · 회색)
sh.color_type="SINGLE"; sc.render.film_transparent=True
for nm in ("02_정면","02_옆","02_3-4"):
    c=bpy.data.objects["카메라_"+nm]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]
    if nm=="02_3-4": c.data.ortho_scale=190
    sc.render.filepath=S+"/cut/grooveshade_%s.png"%nm.split("_")[1]; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/tri_groove.blend"); print("saved")
# 선 렌더(정면 · 옆) — 선 대조용
m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
for x in list(nt.nodes): nt.nodes.remove(x)
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0]); me.materials.clear(); me.materials.append(m)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings; fs.crease_angle=np.radians(150)
for ls in list(fs.linesets): fs.linesets.remove(ls)
ls=fs.linesets.new("선"); ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True; ls.linestyle.color=(0,0,0); ls.linestyle.thickness=2.0; sc.render.image_settings.color_mode="RGBA"
for nm in ("02_정면","02_옆"):
    c=bpy.data.objects["카메라_"+nm]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/groove_%s.png"%nm.split("_")[1]; bpy.ops.render.render(write_still=True)
print("lines")
