# 원화를 카메라 투영 UV 로 TripoSG 에 입힌다. (a) 정면만 투영 → 옆·3/4 에서 먹선이 어디로 가는지 (b) 정면+옆 섞음(법선 가중) → 보기용
import bpy, bmesh, os, numpy as np, mathutils, math
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; tri=bpy.data.objects["트리포"]; me=tri.data
def uv_from_cam(camname, fit, name):
    cam=bpy.data.objects[camname]; Mi=cam.matrix_world.inverted(); W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale; s,tx,ty=fit
    uv=me.uv_layers.new(name=name); Mw=tri.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v=Mw@me.vertices[me.loops[li].vertex_index].co; vc=Mi@v; px=(vc.x/osc+0.5)*W; py=(0.5-vc.y/(osc*H/W))*H; px=s*px+tx; py=s*py+ty
            uv.data[li].uv=(px/W, 1-py/H)
    return cam
camF=uv_from_cam("카메라_02_정면",(1.0,0,0),"앞"); camS=uv_from_cam("카메라_02_옆",(0.9,36,45),"옆")
# 법선 가중(앞을 보는 정도) → 색 속성
n=len(me.vertices); R=tri.matrix_world.to_3x3(); dF=camF.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); dS=camS.matrix_world.to_3x3()@mathutils.Vector((0,0,1))
ca=me.color_attributes.new("w","FLOAT_COLOR","POINT")
for i,v in enumerate(me.vertices):
    N=(R@v.normal).normalized(); f=max(0,N.dot(dF)); s_=max(0,N.dot(dS)); w=f/(f+s_+1e-6); ca.data[i].color=(w,w,w,1)
def 재질(name, blend):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    out=nt.nodes.new("ShaderNodeOutputMaterial"); em=nt.nodes.new("ShaderNodeEmission"); nt.links.new(em.outputs[0],out.inputs[0])
    def tex(img,uvname):
        t=nt.nodes.new("ShaderNodeTexImage"); t.image=bpy.data.images.load(S+"/cut/"+img); t.extension="CLIP"; u=nt.nodes.new("ShaderNodeUVMap"); u.uv_map=uvname; nt.links.new(u.outputs[0],t.inputs[0]); return t
    tf=tex("art_front.jpg","앞")
    if blend:
        ts=tex("art_side.jpg","옆"); mix=nt.nodes.new("ShaderNodeMixRGB"); va=nt.nodes.new("ShaderNodeVertexColor"); va.layer_name="w"
        nt.links.new(va.outputs[0],mix.inputs[0]); nt.links.new(ts.outputs[0],mix.inputs[1]); nt.links.new(tf.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],em.inputs[0])
    else: nt.links.new(tf.outputs[0],em.inputs[0])
    return m
mA=재질("앞만",False); mB=재질("앞옆",True)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.use_freestyle=False; sc.render.film_transparent=True; sc.render.image_settings.color_mode="RGBA"; sc.view_settings.view_transform="Standard"
def 렌더(mat, pre, views=("02_정면","02_옆","02_3-4")):
    me.materials.clear(); me.materials.append(mat)
    for nm in views:
        c=bpy.data.objects["카메라_"+nm]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/%s_%s.png"%(pre,nm.split("_")[1]); bpy.ops.render.render(write_still=True)
렌더(mA,"uvA"); 렌더(mB,"uvB")
# 3/4 가까이(쇼츠용) · 한 바퀴 12장
cam=bpy.data.objects["카메라_02_3-4"]; base=cam.matrix_world.copy(); V=np.array([tri.matrix_world@v.co for v in me.vertices]); ctr=mathutils.Vector(V.mean(0)); cam.data.ortho_scale=190; d=cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); cam.location=ctr+d*400; base2=cam.matrix_world.copy()
sc.render.film_transparent=False; sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03); os.makedirs(S+"/cut/uvanim",exist_ok=True)
for k,(mat,pre) in enumerate(((mA,"A"),(mB,"B"))):
    me.materials.clear(); me.materials.append(mat); sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860
    for i in range(24):
        Rz=mathutils.Matrix.Rotation(math.radians(-60+i*5),4,"Z"); T=mathutils.Matrix.Translation(ctr); cam.matrix_world=T@Rz@T.inverted()@base2; sc.render.filepath=S+"/cut/uvanim/%s%02d.png"%(pre,i); bpy.ops.render.render(write_still=True)
cam.matrix_world=base; bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/tri_uv.blend"); print("done")
