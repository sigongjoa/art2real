import sys, os, json, colorsys; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
S=os.path.dirname(os.path.abspath(__file__)); O=S+"/cut/named/"; names=json.load(open(O+"names.json",encoding="utf-8"))
sc=H.scene(res=(900,900),transparent=False); sh=sc.display.shading; sh.light="FLAT"; sh.show_cavity=False; sc.world.color=(0,0,0); sc.view_settings.view_transform="Standard"
for gi in range(len(names)):
    p=O+f"g{gi}.obj"
    if os.path.exists(p): H.load_obj(p,f"g{gi}",(((gi+1)*16)/255.0,0.5,0.5,1),smooth=False)
ctr=(5,-20,-58)
for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-35,10)}.items(): H.look(ctr,yaw,pitch,105); H.shot(O+f"map_{nm}.png")
print("done")
