import bpy, json, os, math, mathutils
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/p52/"; cells={c["n"]:c for c in json.load(open(S+"/cut/cells52_z.json",encoding="utf-8"))}
bpy.ops.wm.open_mainfile(filepath=S+"/cut/parts52.blend"); sc=bpy.context.scene; cam=bpy.data.objects["cam"]; parts=[o for o in bpy.data.objects if o.name.startswith("p")]
for o in parts: o.hide_render=False
def ext(n): p=cells[n]["poly"]; return max(max(x for x,y in p)-min(x for x,y in p), max(y for x,y in p)-min(y for x,y in p))
big=sorted([o for o in parts if ext(o["n"])>24],key=lambda o:o["n"]); small=sorted([o for o in parts if ext(o["n"])<=24],key=lambda o:({"투구":0,"속머리(눈)":1,"마스크":2}[o["layer"]],o["n"]))
# 탐욕 줄 채우기: 큰 것부터 · 줄 너비 200 · 줄 높이 = 그 줄 최대 세로
def bb(n):
    p=cells[n]["poly"]; xs=[x for x,y in p]; ys=[y for x,y in p]; return min(xs),max(xs),min(ys),max(ys)
items=sorted(parts,key=lambda o:-ext(o["n"])); rows=[]; cur=[]; w=0
for o in items:
    x0,x1,y0,y1=bb(o["n"]); ew=x1-x0+6
    if cur and w+ew>200: rows.append(cur); cur=[]; w=0
    cur.append(o); w+=ew
rows.append(cur); z=62
for row in rows:
    h=max(bb(o["n"])[3]-bb(o["n"])[2] for o in row); tw=sum(bb(o["n"])[1]-bb(o["n"])[0]+6 for o in row); x=-tw/2
    for o in row:
        x0,x1,y0,y1=bb(o["n"]); o.location=(x-x0,0,z-h/2+(y0+y1)/2); x+=x1-x0+6
    z-=h+6
def look(center,yaw=0,pitch=0,dist=400,ortho=130):
    y,p=math.radians(yaw),math.radians(pitch); d=mathutils.Vector((math.sin(y)*math.cos(p),-math.cos(y)*math.cos(p),math.sin(p)))
    cam.location=mathutils.Vector(center)+d*dist; cam.rotation_euler=d.to_track_quat("Z","Y").to_euler(); cam.data.ortho_scale=ortho
def shot(name): sc.render.filepath=O+name; bpy.ops.render.render(write_still=True)
for i in range(16): look((0,0,-5),-14+i*1.75,-6+i*0.75,ortho=225); shot("grid_%02d.png"%i)
look((0,0,-5),0,0,ortho=225); shot("grid.png"); print("grid ok")
