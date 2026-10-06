import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-85,7),(-14,-59)).segment((14,-59)).segment((85,7)).segment((70,38)).segment((0,-28)).segment((-70,38)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(7,200,26).translate((-23,0,18)))