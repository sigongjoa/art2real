import sys, os, json; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/merge/"; idx=json.load(open(O+"index.json",encoding="utf-8"))["parts"]; sc=H.scene()
def rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(1,)
objs={"P2":[],"P3":[]}
for e in idx:
    for v in ("P2","P3"):
        if e[v]: objs[v].append(H.load_obj(O+f"obj/{v}_{e['i']}.obj",f"{v}_{e['i']}",rgb(e["color"])))
ctr=(0,-45,-52)
for v in ("P2","P3"):
    for w in ("P2","P3"):
        for o in objs[w]: o.hide_render=(w!=v)
    for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-40,10)}.items(): H.look(ctr,yaw,pitch,150); H.shot(O+f"{v}_{nm}.png")
H.swing(O+"P3_swing",ctr,0,-90,25,10,150); print("done")
