import bpy, json, os, math, mathutils, glob
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/hull/"; idx=json.load(open(S+"/cut/hullobj/index.json",encoding="utf-8"))
bpy.ops.wm.read_homefile(use_empty=True); sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="OBJECT"; sh.show_cavity=True; sh.cavity_type="BOTH"
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.02,0.02,0.03); sc.render.resolution_x,sc.render.resolution_y=1000,860; sc.render.film_transparent=True; sc.render.image_settings.color_mode="RGBA"
def col(name):
    if "눈구멍" in name: return (0.14,0.15,0.17,1)
    if name.startswith("눈 "): return (0.18,0.43,0.85,1)
    if "번개" in name: return (0.23,0.36,0.82,1)
    return (0.91,0.91,0.93,1)
M=mathutils.Matrix(((1,0,0,0),(0,0,-1,0),(0,-1,0,0),(0,0,0,1)))   # (x, y아래, z앞) → 블렌더 (x, -z앞, -y)
objs={"A":[],"B":[]}
for e in idx:
    if not e.get("vox"): continue
    p=S+f"/cut/hullobj/{e['var']}_{e['name']}.obj"; bpy.ops.wm.obj_import(filepath=p, forward_axis="Y", up_axis="Z"); o=bpy.context.selected_objects[0]; o.name=e["var"]+"_"+e["name"]; o.matrix_world=M; o.color=col(e["name"]); o["pname"]=e["name"]
    for pg in o.data.polygons: pg.use_smooth=True
    objs[e["var"]].append(o)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); cam.data.type="ORTHO"; cam.data.clip_end=5000; sc.camera=cam
def look(center,yaw=0,pitch=0,dist=400,ortho=130):
    y,p=math.radians(yaw),math.radians(pitch); d=mathutils.Vector((math.sin(y)*math.cos(p),-math.cos(y)*math.cos(p),math.sin(p)))
    cam.location=mathutils.Vector(center)+d*dist; cam.rotation_euler=d.to_track_quat("Z","Y").to_euler(); cam.data.ortho_scale=ortho
def shot(name): sc.render.filepath=O+name; bpy.ops.render.render(write_still=True)
ctr=(0,-30,-50)
for var in ("A","B"):
    for v2 in ("A","B"):
        for o in objs[v2]: o.hide_render=(v2!=var)
    look(ctr,0,0,ortho=130); shot(f"{var}_front.png"); look(ctr,90,0,ortho=130); shot(f"{var}_side.png"); look(ctr,40,12,ortho=130); shot(f"{var}_34.png")
    for i in range(25): look(ctr,i*3.75,i*0.5,ortho=130); shot(f"{var}_swing_{i:02d}.png")
    homes={o.name:o.location.copy() for o in objs[var]}; cols=7; cw=34
    for i,o in enumerate(objs[var]):
        bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]; c0=sum(bb,mathutils.Vector())/8; r,q=divmod(i,cols); o.location=o.location-c0+mathutils.Vector(((q-(cols-1)/2)*cw,0,45-r*cw))
    look((0,0,0),0,0,ortho=cw*cols*1.08); shot(f"{var}_grid.png"); look((0,0,0),35,15,ortho=cw*cols*1.08); shot(f"{var}_grid34.png")
    for i in range(16): look((0,0,0),-14+i*1.75,-6+i*0.75,ortho=cw*cols*1.08); shot(f"{var}_gridswing_{i:02d}.png")
    for o in objs[var]: o.location=homes[o.name]
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/parts_hull.blend"); print("done")
