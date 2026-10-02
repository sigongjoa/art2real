import sys, os, json, mathutils; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/hullH/"; idx=json.load(open(S+"/cut/hullobjH/index.json",encoding="utf-8")); sc=H.scene()
def col(name):
    if "눈구멍" in name or "그늘" in name: return (0.14,0.15,0.17,1)
    if "홍채" in name or "동공" in name: return (0.18,0.43,0.85,1)
    if "흰자" in name or "반짝" in name: return (0.84,0.9,1,1)
    if "번개" in name: return (0.23,0.36,0.82,1)
    return (0.91,0.91,0.93,1)
objs=[H.load_obj(S+f"/cut/hullobjH/C_{e['n']}.obj","C_%d"%e["n"],col(e["name"])) for e in idx if e.get("vox")]
tri=H.load_obj(S+"/cut/h_units.obj","tripo",(0.8,0.8,0.84,1)); ctr=(0,-20,-55)
for o in objs: o.hide_render=True
for nm,(yaw,pitch) in H.VIEWS.items(): H.look(ctr,yaw,pitch,150); H.shot(O+"T_%s.png"%nm.replace("/",""))
tri.hide_render=True
for o in objs: o.hide_render=False
for nm,(yaw,pitch) in H.VIEWS.items(): H.look(ctr,yaw,pitch,150); H.shot(O+"C_%s.png"%nm.replace("/",""))
H.swing(O+"C_swing",ctr,0,90,25,12,150)
cols=8; cw=30
for i,o in enumerate(objs):
    bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]; c0=sum(bb,mathutils.Vector())/8; r,q=divmod(i,cols); o.location=o.location-c0+mathutils.Vector(((q-(cols-1)/2)*cw,0,90-r*cw))
H.look((0,0,0),0,0,cw*cols*1.08); H.shot(O+"C_grid.png"); H.look((0,0,0),35,15,cw*cols*1.08); H.shot(O+"C_grid34.png")
for i in range(16): H.look((0,0,0),-14+i*1.75,-6+i*0.75,cw*cols*1.08); H.shot(O+"C_gridswing_%02d.png"%i)
print("done")
