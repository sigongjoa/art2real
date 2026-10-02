import sys, os, colorsys, mathutils; sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포분할"
for n in (6,12,20):
    sc=H.scene(transparent=False); objs=[]
    for i in range(n):
        h=(i*0.618)%1; r,g,b=colorsys.hsv_to_rgb(h,0.55,0.95); objs.append(H.load_obj(os.path.join(O,f"부품{n}",f"p{i}.obj"),f"p{i}",(r,g,b,1)))
    ctr=(5,-20,-58)
    for nm,(yaw,pitch) in {"정면":(0,0),"옆":(-90,0),"34":(-35,10),"뒤34":(-145,10)}.items(): H.look(ctr,yaw,pitch,105); H.shot(os.path.join(O,f"r{n}_{nm}.png"))
    # 펼침: 부품을 중심에서 바깥으로 1.6 배 밀기
    for o in objs:
        bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]; c0=sum(bb,mathutils.Vector())/8; cen=mathutils.Vector((ctr[0],ctr[1],ctr[2])); o.location=o.location+(c0-cen)*0.6
    H.look(ctr,-35,10,140); H.shot(os.path.join(O,f"r{n}_펼침.png"))
print("done")
