# 모드 b: 정면 셀 다각형을 카메라 축으로 밀어 프리즘 → 트리포 ∩ 프리즘 = 파츠. 검은면(눈구멍)은 뺀다(구멍).
import bpy, bmesh, json, os, sys, numpy as np, mathutils
S=os.path.dirname(os.path.abspath(__file__)); cells=json.load(open(S+"/cut/cells_front.json")); sc=bpy.context.scene
cam=bpy.data.objects["카메라_02_정면"]; M=cam.matrix_world; W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale
tri=bpy.data.objects["트리포"]
# 깃 제거: 카메라 공간에서 셀 맨 아래(턱)보다 낮은 점 삭제 · 프리즘 깊이는 코끝 +60 ~ 코끝 -130 (머리 깊이만 · 뒤 깃 제외)
Mi=M.inverted(); me=tri.data; bm=bmesh.new(); bm.from_mesh(me); bm.transform(tri.matrix_world)
ymax=max(v for c in cells for u,v in c["다각형"]); ychin=(0.5-(ymax+8)/H)*osc*H/W
zmax=max((Mi@v.co).z for v in bm.verts)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (Mi@v.co).y<ychin], context="VERTS"); bm.transform(tri.matrix_world.inverted()); bm.to_mesh(me); bm.free()
ZF, ZB = zmax+60, zmax-95; print("턱 y",round(ychin,1),"코끝 z",round(zmax,1))
def 프리즘(poly, name):
    bm=bmesh.new(); top=[]; bot=[]
    for u,v in poly:
        x=(u/W-0.5)*osc; y=(0.5-v/H)*osc*H/W
        top.append(bm.verts.new(M@mathutils.Vector((x,y,ZF)))); bot.append(bm.verts.new(M@mathutils.Vector((x,y,ZB))))
    bm.faces.new(top); bm.faces.new(bot[::-1]); n=len(top)
    for i in range(n): bm.faces.new((top[i],bot[i],bot[(i+1)%n],top[(i+1)%n]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); return o
parts=[]; 
for c in cells:
    if c["검은면"]: continue
    p=프리즘(c["다각형"],"프리즘%02d"%c["번호"]); part=tri.copy(); part.data=tri.data.copy(); part.name="파츠%02d"%c["번호"]; sc.collection.objects.link(part)
    md=part.modifiers.new("자르기","BOOLEAN"); md.operation="INTERSECT"; md.object=p; md.solver="EXACT"
    bpy.context.view_layer.objects.active=part; bpy.ops.object.modifier_apply(modifier="자르기")
    bpy.data.objects.remove(p)
    if len(part.data.polygons)==0: bpy.data.objects.remove(part); print("빈 파츠",c["번호"]); continue
    rng=np.random.RandomState(c["번호"]); part.color=(*rng.uniform(0.35,0.95,3),1); parts.append(part)
tri.hide_render=True; tri.hide_viewport=True
# 흰 발광 재질 (선 렌더용)
m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0])
for p in parts: p.data.materials.clear(); p.data.materials.append(m)
print("파츠", len(parts))
# 선 렌더 (EEVEE + Freestyle)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.film_transparent=True; sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings; fs.crease_angle=np.radians(110)
for ls in list(fs.linesets): fs.linesets.remove(ls)
ls=fs.linesets.new("선"); ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True; ls.linestyle.color=(0,0,0); ls.linestyle.thickness=2.0
sc.render.image_settings.color_mode="RGBA"
for n in ("02_정면","02_옆","02_3-4"):
    c=bpy.data.objects["카메라_"+n]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/cut_%s.png"%n.split("_")[1]; bpy.ops.render.render(write_still=True)
# 색 음영 렌더 (Workbench · 오브젝트 색)
sc.render.engine="BLENDER_WORKBENCH"; sc.render.use_freestyle=False; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="OBJECT"
for n in ("02_정면","02_옆","02_3-4"):
    c=bpy.data.objects["카메라_"+n]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/cutshade_%s.png"%n.split("_")[1]; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/tri_cut_parts.blend"); print("saved")
