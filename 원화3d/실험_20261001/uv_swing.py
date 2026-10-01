# 머리 중심(턱 위 점만)으로 카메라를 잡고 -40..+40도 흔들기 · A(앞만) B(앞옆)
import bpy, os, numpy as np, mathutils, math
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; tri=bpy.data.objects["트리포"]; me=tri.data
V=np.array([tri.matrix_world@v.co for v in me.vertices]); camF=bpy.data.objects["카메라_02_정면"]; Mi=camF.matrix_world.inverted()
ys=np.array([(Mi@mathutils.Vector(p)).y for p in V]); head=V[ys>np.percentile(ys,35)]; ctr=mathutils.Vector(head.mean(0))
cam=bpy.data.objects["카메라_02_3-4"]; cam.data.ortho_scale=170; d=cam.matrix_world.to_3x3()@mathutils.Vector((0,0,1)); cam.location=ctr+d*400; bpy.context.view_layer.update(); base=cam.matrix_world.copy()
sc.render.film_transparent=False; sc.world.use_nodes=False; sc.world.color=(0.02,0.02,0.03); sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=1000,860
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
for mat,pre in ((재질("앞만2",False),"A"),(재질("앞옆2",True),"B")):
    me.materials.clear(); me.materials.append(mat)
    for i in range(25):
        Rz=mathutils.Matrix.Rotation(math.radians(-40+i*(80/24)),4,"Z"); T=mathutils.Matrix.Translation(ctr); cam.matrix_world=T@Rz@T.inverted()@base; sc.render.filepath=S+"/cut/uvanim/%s%02d.png"%(pre,i); bpy.ops.render.render(write_still=True)
print("swing")
