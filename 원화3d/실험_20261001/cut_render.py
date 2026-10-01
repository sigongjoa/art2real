# 모드 a: TripoSG 머리를 원점에 옮겨 세 카메라로 (1) 흰 음영+검은 Freestyle 선 (2) 알파 렌더
import bpy, json, sys, os, numpy as np
S=os.path.dirname(os.path.abspath(__file__)); fit=json.load(open(S+"/cut/fit.json"))
mode=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "a"
sc=bpy.context.scene
for o in list(bpy.data.objects):
    if o.type=="MESH" and o.name!="TripoSG참고": bpy.data.objects.remove(o)
src=bpy.data.objects["TripoSG참고"]; me=src.data.copy(); ob=bpy.data.objects.new("트리포",me); sc.collection.objects.link(ob)
# 세계 좌표 → (x-140)*s + d  : 원본 matrix_world 를 적용한 뒤 변환
import mathutils
M=src.matrix_world.copy(); T=mathutils.Matrix.Translation((fit["dx"],fit["dy"],fit["dz"])) @ mathutils.Matrix.Scale(fit["s"],4) @ mathutils.Matrix.Translation((-140,0,0))
ob.matrix_world=T@M; src.hide_render=True; src.hide_viewport=True
# 머리만: z < zcut 면 삭제
import bmesh; bm=bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world); zc=fit["zcut"]*fit["s"]+fit["dz"]
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z<zc], context="VERTS"); bm.transform(ob.matrix_world.inverted()); bm.to_mesh(me); bm.free()
# 깃 제거(정면 카메라 공간에서 셀 맨 아래보다 낮은 점) — 비교를 머리끼리 하려고
cam=bpy.data.objects["카메라_02_정면"]; Mc=cam.matrix_world; Mi=Mc.inverted(); W,H,osc=cam["W"],cam["H"],cam.data.ortho_scale
cells=json.load(open(S+"/cut/cells_front.json")); ymax=max(v for c in cells for u,v in c["다각형"]); ychin=(0.5-(ymax+8)/H)*osc*H/W
bm=bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world); bmesh.ops.delete(bm, geom=[v for v in bm.verts if (Mi@v.co).y<ychin], context="VERTS"); bm.transform(ob.matrix_world.inverted()); bm.to_mesh(me); bm.free(); print("깃 제거 턱 y",round(ychin,1),"남은 점",len(me.vertices))
def 흰재질(o):
    m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0]); o.data.materials.clear(); o.data.materials.append(m)
def 선렌더(이름들, 접두):
    try: sc.render.engine="BLENDER_EEVEE"
    except TypeError as e: print(e); sc.render.engine="BLENDER_EEVEE_NEXT"
    sc.render.film_transparent=True; sc.render.use_freestyle=True; sc.render.line_thickness=2.0
    vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings; fs.crease_angle=np.radians(110)
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    ls=fs.linesets.new("선"); ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True; ls.select_edge_mark=False; ls.linestyle.color=(0,0,0); ls.linestyle.thickness=2.0
    sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGBA"
    for n in 이름들:
        cam=bpy.data.objects["카메라_"+n]; sc.camera=cam; sc.render.resolution_x, sc.render.resolution_y=cam["W"],cam["H"]; sc.render.resolution_percentage=100
        sc.render.filepath=S+"/cut/%s_%s.png"%(접두,n.split("_")[1]); bpy.ops.render.render(write_still=True); print("rendered",sc.render.filepath)
if mode=="a":
    for o in bpy.data.objects:
        if o.type=="MESH" and not o.hide_render: 흰재질(o)
    선렌더(("02_정면","02_옆","02_3-4"),"tri")
    bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/tri_cut.blend")
