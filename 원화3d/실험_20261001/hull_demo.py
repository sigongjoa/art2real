import bpy, bmesh, json, os, math, mathutils
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/hull/"; D=json.load(open(S+"/cut/parts_hull.json",encoding="utf-8")); P={p["name"]:p for p in D["parts"]}
bpy.ops.wm.read_homefile(use_empty=True); sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="OBJECT"; sh.show_cavity=True; sh.show_xray=True; sh.xray_alpha=0.45
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.02,0.02,0.03); sc.render.resolution_x,sc.render.resolution_y=1000,860; sc.render.film_transparent=False
def prism(polys, axis, name, span=60, color=(0.9,0.9,0.9,1)):
    bm=bmesh.new()
    for poly in polys:
        vs=[bm.verts.new((x,-span,-y)) if axis=="y" else bm.verts.new((-span,-za,-y)) for (x,za,y) in [(q[0],q[0],q[1]) for q in poly]] if False else None
        if axis=="y": vs=[bm.verts.new((x,-span,-y)) for x,y in poly]
        else: vs=[bm.verts.new((-span,-za,-y)) for za,y in poly]
        try: f=bm.faces.new(vs)
        except Exception: continue
        tr=bmesh.ops.triangulate(bm,faces=[f]); r=bmesh.ops.extrude_face_region(bm,geom=tr["faces"]); vv=[g for g in r["geom"] if isinstance(g,bmesh.types.BMVert)]
        bmesh.ops.translate(bm,verts=vv,vec=(0,2*span,0) if axis=="y" else (2*span,0,0))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); o.color=color; return o
name="미늘1"; p=P[name]; fp=prism(p["front"],"y","F",color=(0.95,0.8,0.3,1)); sp=prism(p["side"],"x","S",color=(0.3,0.7,0.95,1))
M=mathutils.Matrix(((1,0,0,0),(0,0,-1,0),(0,-1,0,0),(0,0,0,1)))
bpy.ops.wm.obj_import(filepath=S+f"/cut/hullobj/A_{name}.obj", forward_axis="Y", up_axis="Z"); a=bpy.context.selected_objects[0]; a.matrix_world=M; a.color=(0.92,0.92,0.95,1)
for pg in a.data.polygons: pg.use_smooth=True
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); cam.data.type="ORTHO"; cam.data.clip_end=5000; sc.camera=cam
def look(center,yaw=0,pitch=0,dist=400,ortho=130):
    y,pp=math.radians(yaw),math.radians(pitch); d=mathutils.Vector((math.sin(y)*math.cos(pp),-math.cos(y)*math.cos(pp),math.sin(pp)))
    cam.location=mathutils.Vector(center)+d*dist; cam.rotation_euler=d.to_track_quat("Z","Y").to_euler(); cam.data.ortho_scale=ortho
def shot(n): sc.render.filepath=O+n; bpy.ops.render.render(write_still=True)
ctr=(0,-30,-83)
for i in range(24):
    t=i/23; fp.hide_render=False; sp.hide_render=(i<8); a.hide_render=(i<16); sh.xray_alpha=0.45 if i<16 else 0.15
    look(ctr,-30+i*2.5,18,ortho=110); shot("demo_%02d.png"%i)
print("demo ok")
