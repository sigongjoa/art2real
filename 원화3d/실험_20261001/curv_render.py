import sys, os, colorsys, mathutils; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포곡률"
heat=[(0.15,0.35,0.95,1),(0.45,0.7,1,1),(0.85,0.85,0.88,1),(1,0.65,0.4,1),(0.95,0.2,0.15,1)]
for name in ("곡률지도","B법선_굵게","B법선_보통","B법선_잘게"):
    sc=H.scene(transparent=False); d=os.path.join(O,name); files=sorted(os.listdir(d),key=lambda s:int(s[1:-4])); objs=[]
    for k,fn in enumerate(files):
        i=int(fn[1:-4]); col=heat[i] if name=="곡률지도" else (lambda h:colorsys.hsv_to_rgb(h,0.55,0.95)+(1,))((i*0.618)%1); objs.append(H.load_obj(os.path.join(d,fn),fn,col))
    ctr=(5,-20,-58)
    for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-35,10),"뒤34":(-145,10)}.items(): H.look(ctr,yaw,pitch,105); H.shot(os.path.join(O,f"r_{name}_{nm}.png"))
print("done")
