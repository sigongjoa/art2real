import bpy,sys,os,numpy as np,bmesh
for p in sys.argv[sys.argv.index("--")+1:]:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p))
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
    a=np.empty(len(me.polygons)); me.polygons.foreach_get("area",a)
    bm=bmesh.new(); bm.from_mesh(me)
    vol=bm.calc_volume(signed=True)
    # 면 종횡비: 최장변/최단변. 큰 값 = 찌그러진 삼각형
    ar=[]
    for f in bm.faces:
        e=[ed.calc_length() for ed in f.edges]
        if min(e)>1e-9: ar.append(max(e)/min(e))
    ar=np.array(ar)
    bm.free()
    print(f"{os.path.basename(p):20s} 부피 {vol*1e6:9.1f}cm3  면적합 {a.sum():.4f}  "
          f"면적 p1 {np.percentile(a,1)*1e6:.4f}  종횡비 p50 {np.median(ar):.2f} "
          f"p95 {np.percentile(ar,95):.2f} p99.9 {np.percentile(ar,99.9):.1f}")
