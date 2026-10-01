# 옆 윤곽3 프리즘(옆 카메라 축)으로 파츠 깊이 다듬기. 2D 맞춤(art = s*model + t)의 역으로 셀 px → 모델 px
import bpy, bmesh, json, os, numpy as np, mathutils
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene; h=json.load(open(S+"/cut/side_hull.json"))
cam=bpy.data.objects["카메라_02_옆"]; M=cam.matrix_world; W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale
bm=bmesh.new(); top=[]; bot=[]
for u,v in h["다각형"]:
    u=(u-h["tx"])/h["s"]; v=(v-h["ty"])/h["s"]; x=(u/W-0.5)*osc; y=(0.5-v/H)*osc*H/W
    top.append(bm.verts.new(M@mathutils.Vector((x,y,600)))); bot.append(bm.verts.new(M@mathutils.Vector((x,y,-600))))
bm.faces.new(top); bm.faces.new(bot[::-1]); n=len(top)
for i in range(n): bm.faces.new((top[i],bot[i],bot[(i+1)%n],top[(i+1)%n]))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); me=bpy.data.meshes.new("옆껍질"); bm.to_mesh(me); bm.free(); hull=bpy.data.objects.new("옆껍질",me); sc.collection.objects.link(hull)
parts=[o for o in bpy.data.objects if o.name.startswith("파츠")]; kept=0
for p in parts:
    md=p.modifiers.new("옆다듬기","BOOLEAN"); md.operation="INTERSECT"; md.object=hull; md.solver="EXACT"; bpy.context.view_layer.objects.active=p; bpy.ops.object.modifier_apply(modifier="옆다듬기")
    if len(p.data.polygons)==0: bpy.data.objects.remove(p)
    else: kept+=1
bpy.data.objects.remove(hull); print("남은 파츠",kept)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.film_transparent=True; sc.render.use_freestyle=True
for n in ("02_정면","02_옆","02_3-4"):
    c=bpy.data.objects["카메라_"+n]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/trim_%s.png"%n.split("_")[1]; bpy.ops.render.render(write_still=True)
sc.render.engine="BLENDER_WORKBENCH"; sc.render.use_freestyle=False; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="OBJECT"
for n in ("02_정면","02_옆","02_3-4"):
    c=bpy.data.objects["카메라_"+n]; sc.camera=c; sc.render.resolution_x,sc.render.resolution_y=c["W"],c["H"]; sc.render.filepath=S+"/cut/trimshade_%s.png"%n.split("_")[1]; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/tri_cut_trim.blend"); print("saved")
