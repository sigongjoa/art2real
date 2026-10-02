import sys, os, math, bpy, mathutils; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/toon/"
def toon_mat():
    m=bpy.data.materials.new("툰"); m.use_nodes=True; nt=m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    d=nt.nodes.new("ShaderNodeBsdfDiffuse"); d.inputs[0].default_value=(1,1,1,1); s2r=nt.nodes.new("ShaderNodeShaderToRGB"); cr=nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation="CONSTANT"
    cr.color_ramp.elements[0].position=0.0; cr.color_ramp.elements[0].color=(0.42,0.44,0.55,1); cr.color_ramp.elements[1].position=0.35; cr.color_ramp.elements[1].color=(0.86,0.88,0.95,1)
    e=nt.nodes.new("ShaderNodeEmission"); out=nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(d.outputs[0],s2r.inputs[0]); nt.links.new(s2r.outputs[0],cr.inputs[0]); nt.links.new(cr.outputs[0],e.inputs[0]); nt.links.new(e.outputs[0],out.inputs[0]); return m
def white_mat():
    m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0]); return m
for n in sys.argv[sys.argv.index("--")+1:]:
    sc=H.scene(res=(768,768),transparent=False)
    try: sc.render.engine="BLENDER_EEVEE"
    except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
    sc.world.use_nodes=False; sc.world.color=(1,1,1); sc.view_settings.view_transform="Standard"
    bpy.ops.wm.obj_import(filepath=O+f"{n}.obj",forward_axis="NEGATIVE_Z",up_axis="Y"); o=bpy.context.selected_objects[0]
    for p in o.data.polygons: p.use_smooth=True
    sun=bpy.data.objects.new("해",bpy.data.lights.new("해","SUN")); sc.collection.objects.link(sun); sun.rotation_euler=(math.radians(50),0,math.radians(30)); sun.data.energy=3
    tm,wm=toon_mat(),white_mat()
    sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings; fs.crease_angle=math.radians(140)
    for ang_name,(yaw,pitch) in {"a":(25,8),"b":(70,5)}.items():
        H.look((0,0,0),yaw,pitch,2.3,dist=8)
        # 1) 입력: 툰 + 검은 선 하나
        for ls in list(fs.linesets): fs.linesets.remove(ls)
        ls=fs.linesets.new("선"); ls.select_silhouette=ls.select_border=ls.select_crease=ls.select_contour=True; ls.select_external_contour=True; ls.linestyle.color=(0.05,0.05,0.08); ls.linestyle.thickness=2.0
        o.data.materials.clear(); o.data.materials.append(tm); H.shot(O+f"{n}_{ang_name}_입력.png")
        # 2) 정답: 흰 바탕 · 꺾임(파랑) 먼저 · 외곽/윤곽/가림(빨강) 위에
        for ls in list(fs.linesets): fs.linesets.remove(ls)
        l1=fs.linesets.new("꺾임"); l1.select_silhouette=l1.select_border=l1.select_contour=l1.select_external_contour=False; l1.select_crease=True; l1.linestyle.color=(0.1,0.4,1.0); l1.linestyle.thickness=2.4
        l2=fs.linesets.new("외곽가림"); l2.select_crease=False; l2.select_silhouette=l2.select_border=l2.select_contour=l2.select_external_contour=True; l2.linestyle.color=(0.95,0.15,0.15); l2.linestyle.thickness=2.4
        o.data.materials.clear(); o.data.materials.append(wm); H.shot(O+f"{n}_{ang_name}_정답.png")
    print("ok",n)
