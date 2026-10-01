import bpy, bmesh, json, os, math, mathutils
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/p52/"; cells=json.load(open(S+"/cut/cells52_z.json",encoding="utf-8"))
bpy.ops.wm.read_homefile(use_empty=True); sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="OBJECT"; sh.show_cavity=True; sh.cavity_type="BOTH"
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.02,0.02,0.03); sc.render.resolution_x,sc.render.resolution_y=1000,860; sc.render.film_transparent=True; sc.render.image_settings.color_mode="RGBA"
def col(c):
    n=c["name"]
    if "홍채" in n: return (0.18,0.43,0.85,1)
    if "동공" in n: return (0.06,0.07,0.1,1)
    if "흰자" in n or "반짝" in n: return (0.84,0.9,1,1)
    if "눈구멍" in n or "그늘" in n: return (0.14,0.15,0.17,1)
    if "번개" in n: return (0.23,0.36,0.82,1)
    return (0.91,0.91,0.93,1)
# 좌표: x 오른 · z 위(= -y머리) · y 깊이(앞 = -y). 앞면 y = -z값 · 두께는 뒤(+y)로
parts=[]
for c in cells:
    bm=bmesh.new(); vs=[bm.verts.new((x,0,-y)) for x,y in c["poly"]]
    try: f=bm.faces.new(vs)
    except Exception: bm.free(); continue
    if f.normal.y>0: bmesh.ops.reverse_faces(bm,faces=[f])
    bmesh.ops.triangulate(bm,faces=bm.faces[:]); me=bpy.data.meshes.new("p%d"%c["n"]); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new("p%d"%c["n"],me); sc.collection.objects.link(o)
    sd=o.modifiers.new("두께","SOLIDIFY"); sd.thickness=c["d"]; sd.offset=-1; sd.use_even_offset=False; o.color=col(c); o["z"]=c["z"]; o["n"]=c["n"]; o["cx"]=c["cx"]; o["cy"]=c["cy"]; o["layer"]=c["layer"]; parts.append(o)
print("parts",len(parts))
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); cam.data.type="ORTHO"; cam.data.clip_end=5000; sc.camera=cam
def look(center,yaw=0,pitch=0,dist=400,ortho=130):
    y,p=math.radians(yaw),math.radians(pitch); d=mathutils.Vector((math.sin(y)*math.cos(p),-math.cos(y)*math.cos(p),math.sin(p)))
    cam.location=mathutils.Vector(center)+d*dist; cam.rotation_euler=d.to_track_quat("Z","Y").to_euler(); cam.data.ortho_scale=ortho
def shot(name): sc.render.filepath=O+name; bpy.ops.render.render(write_still=True)
# 1) 펼침 격자(겹 순서)
cellw=22; cols=8; rows=math.ceil(len(parts)/cols); order=sorted(parts,key=lambda o:({"투구":0,"속머리(눈)":1,"마스크":2}[o["layer"]],o["n"]))
for i,o in enumerate(order):
    r,q=divmod(i,cols); o.location=((q-(cols-1)/2)*cellw-o["cx"], 0, -(r)*cellw+(rows-1)*cellw/2+o["cy"])
look((0,0,0),0,0,ortho=cellw*cols*1.05); shot("grid.png")
for i in range(16): look((0,0,0),-14+i*1.75,-6+i*0.75,ortho=cellw*cols*1.05); shot("grid_%02d.png"%i)
# 2) 부품 하나씩 회전
for o in parts: o.hide_render=True
for n in (1,4,28,52):
    o=[p for p in parts if p["n"]==n][0]; o.hide_render=False; o.location=(-o["cx"],0,o["cy"]); poly=[c["poly"] for c in cells if c["n"]==n][0]; sz=max(max(abs(x-o["cx"]) for x,y in poly),max(abs(y-o["cy"]) for x,y in poly),8)
    for i in range(16): look((0,0,0),-55+i*7.3,18,ortho=max(sz*2.6,30)); shot("solo%02d_%02d.png"%(n,i))
    o.hide_render=True
# 3) 조립: 원래 자리 + z
for o in parts: o.hide_render=False; o.location=(0,-o["z"],0)
ctr=(0,0,-50); look(ctr,0,0,ortho=130); shot("asm_front.png"); look(ctr,90,0,ortho=130); shot("asm_side.png"); look(ctr,40,12,ortho=130); shot("asm_34.png")
for i in range(25): look(ctr,i*3.75,i*0.5,ortho=130); shot("asm_swing_%02d.png"%i)
bpy.ops.wm.save_as_mainfile(filepath=S+"/cut/parts52.blend"); print("done")
