import bpy,sys,os,bmesh
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bm=bmesh.new(); bm.from_mesh(o.data)
nq=sum(1 for f in bm.faces if len(f.verts)==4); nt=sum(1 for f in bm.faces if len(f.verts)==3)
bm.free()
print(f"면 {len(o.data.polygons):,}  쿼드 {nq:,} 삼각 {nt:,}  쿼드율 {nq/max(len(o.data.polygons),1)*100:.0f}%")
