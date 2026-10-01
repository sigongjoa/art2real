import bpy, numpy as np, json
o=bpy.data.objects["TripoSG참고"]; me=o.data; M=np.array(o.matrix_world)
V=np.array([v.co[:] for v in me.vertices]); V=(M[:3,:3]@V.T).T+M[:3,3]
F=[list(p.vertices) for p in me.polygons]; tri=[f for f in F if len(f)==3]; print("verts",len(V),"faces",len(F),"tris",len(tri), "bbox", V.min(0).round(1), V.max(0).round(1))
np.savez("cut/tri_world.npz", V=V, F=np.array(tri) if len(tri)==len(F) else np.array([f[:3] for f in F]))
cams={}
for c in bpy.data.objects:
    if c.type=="CAMERA": cams[c.name]={"M":np.array(c.matrix_world).tolist(),"ortho":c.data.ortho_scale,"W":c["W"],"H":c["H"]}
json.dump(cams,open("cut/cams.json","w"))
