import sys, os, json; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/tilt/"; idx=json.load(open(O+"index.json",encoding="utf-8")); sc=H.scene()
def rgb(h): h=h.lstrip("#"); return tuple(min(1,int(h[i:i+2],16)/255*1.25) for i in (0,2,4))+(1,)
for e in idx["판"]: H.load_obj(O+f"obj/T_{e['i']}.obj","T_%d"%e["i"],rgb(e["color"]),smooth=False)
ctr=(0,-50,-55)
for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-40,10),"위":(0,80)}.items(): H.look(ctr,yaw,pitch,140); H.shot(O+f"T_{nm}.png")
H.swing(O+"T_swing",ctr,0,-90,25,10,140); print("done")
