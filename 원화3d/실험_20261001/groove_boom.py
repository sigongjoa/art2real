# 둘째 판 재현: 세계 배율(428)로 안 나눈 변위 → 폭발. 3/4 한 장만.
import bpy, os, numpy as np, mathutils
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; tri=bpy.data.objects["트리포"]
md=tri.modifiers.new("세분","SUBSURF"); md.levels=1; md.subdivision_type="SIMPLE"; bpy.context.view_layer.objects.active=tri; bpy.ops.object.modifier_apply(modifier="세분")
me=tri.data; n=len(me.vertices); co=np.zeros(n*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3); nr=np.zeros(n*3); me.vertices.foreach_get("normal",nr); nr=nr.reshape(-1,3)
M=np.array(tri.matrix_world); V=(M[:3,:3]@co.T).T+M[:3,3]; R=M[:3,:3]; N=(R@nr.T).T; N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-9; disp=np.zeros(n)
for 키,camname,fit in (("정면","카메라_02_정면",(1.0,0,0)),("옆","카메라_02_옆",(0.9,36,45))):
    cam=bpy.data.objects[camname]; Mi=np.array(cam.matrix_world.inverted()); W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale
    vc=(Mi[:3,:3]@V.T).T+Mi[:3,3]; px=(vc[:,0]/osc+0.5)*W; py=(0.5-vc[:,1]/(osc*H/W))*H; s,tx,ty=fit; px=s*px+tx; py=s*py+ty
    dist=np.load(S+f"/cut/벽거리_{키}.npy"); ix=np.clip(px.round().astype(int),0,W-1); iy=np.clip(py.round().astype(int),0,H-1); dv=dist[iy,ix]
    camdir=np.array(cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1))); facing=(N@camdir)>0.25; disp=np.maximum(disp,np.clip(1-dv/3.0,0,1)*facing)
nrn=nr/(np.linalg.norm(nr,axis=1,keepdims=True)+1e-9); me.vertices.foreach_set("co",(co-nrn*(0.8*disp)[:,None]).ravel()); me.update()
sc.render.engine="BLENDER_WORKBENCH"; sc.render.film_transparent=False; sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03); sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="SINGLE"; sh.single_color=(0.8,0.8,0.8); sh.show_cavity=True
cam=bpy.data.objects["카메라_02_3-4"]; sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860; ctr=mathutils.Vector(V.mean(0)); cam.data.ortho_scale=190; dv_=cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); cam.location=ctr+dv_*400
sc.render.filepath=S+"/ep9_media/groove_boom.png"; bpy.ops.render.render(write_still=True); print("boom")
