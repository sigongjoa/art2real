import sys, os, colorsys; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포먹선분할"
for name in ("t20_k1","t20_k3","t26_k3"):
    sc=H.scene(transparent=False); d=os.path.join(O,name)
    for fn in sorted(os.listdir(d),key=lambda s:int(s[1:-4])):
        i=int(fn[1:-4]); col=colorsys.hsv_to_rgb((i*0.618)%1,0.6,0.95)+(1,); H.load_obj(os.path.join(d,fn),fn,col,smooth=True)
    ctr=(5,-20,-58)
    for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-35,10),"뒤34":(-145,10)}.items(): H.look(ctr,yaw,pitch,105); H.shot(os.path.join(O,f"r_{name}_{nm}.png"))
print("done")
