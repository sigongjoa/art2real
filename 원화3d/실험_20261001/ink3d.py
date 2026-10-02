import sys, os, math, bpy; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/ink3d/"; os.makedirs(O,exist_ok=True)
sc=H.scene(res=(900,900),transparent=False); sc.world.color=(1,1,1)
o=H.load_obj(S+"/cut/h_remesh.obj","h",(1,1,1,1),smooth=True)
m=bpy.data.materials.new("흰"); m.use_nodes=True; nt=m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(1,1,1,1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0]); o.data.materials.append(m)
try: sc.render.engine="BLENDER_EEVEE"
except TypeError: sc.render.engine="BLENDER_EEVEE_NEXT"
sc.render.film_transparent=False; sc.world.use_nodes=False; sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True; fs=vl.freestyle_settings
for ls in list(fs.linesets): fs.linesets.remove(ls)
ctr=(5,-20,-58); views={"정면":(0,0),"옆":(-90,0),"34":(-35,10)}
for ca in (150,140):
    fs.crease_angle=math.radians(ca)
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    ls=fs.linesets.new("선"); ls.select_by_visibility=True; ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True; ls.select_contour=True; ls.linestyle.color=(0,0,0); ls.linestyle.thickness=2.2
    for nm,(yaw,pitch) in views.items(): H.look(ctr,yaw,pitch,105); H.shot(O+f"ink_{ca}_{nm}.png")
print("done")
