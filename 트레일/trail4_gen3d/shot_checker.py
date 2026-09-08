import math, os, sys
import bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
obs=[o for o in bpy.context.scene.objects if o.type=='MESH']

# 섬 개수 세기
tot=0; rows=[]
for o in obs:
    bm=bmesh.new(); bm.from_mesh(o.data)
    uvl=bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    seen=set(); isl=0
    for f in bm.faces:
        if f.index in seen: continue
        isl+=1; st=[f]; seen.add(f.index)
        while st:
            c=st.pop()
            for l in c.loops:
                for lr in (l.link_loop_radial_next,):
                    g=lr.face
                    if g.index in seen: continue
                    # 같은 섬이면 공유 에지의 UV 가 붙어 있다
                    if (l[uvl].uv-lr.link_loop_next[uvl].uv).length<1e-5 and \
                       (l.link_loop_next[uvl].uv-lr[uvl].uv).length<1e-5:
                        seen.add(g.index); st.append(g)
    bm.free(); tot+=isl
    rows.append((o.name,len(o.data.polygons),isl))
rows.sort(key=lambda r:-r[2])
print(f"ISLANDS 합계 {tot:,}")
for n,f,i in rows[:10]: print(f"  {n:24s} 면 {f:6,}  섬 {i:5,}  면/섬 {f/max(i,1):5.1f}")

# 체커 재질
img=bpy.data.images.new("chk",1024,1024)
img.generated_type='COLOR_GRID'
for o in obs:
    m=bpy.data.materials.new("chk_"+o.name); m.use_nodes=True
    nt=m.node_tree; tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    o.data.materials.clear(); o.data.materials.append(m)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.film_transparent=True; sc.render.resolution_x=sc.render.resolution_y=800
sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new("w"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[1].default_value=1.6
sc.world=w
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag,osc,z in ((0,"front",1.2,0.5),(90,"side",1.2,0.5),(0,"foot",0.40,0.10),(0,"torso",0.55,0.62)):
    cd.ortho_scale=osc; a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,z); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("CHECKER OK")
