import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-90,5),(-18,-74)).segment((18,-74)).segment((90,5)).segment((70,45)).segment((0,-34)).segment((-70,45)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(7,200,34).translate((-32,0,18))).cut(cq.Workplane('XY').box(5,200,24).translate((22,0,18)))