import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-93,19),(-13,-56)).segment((13,-56)).segment((93,19)).segment((75,56)).segment((0,-19)).segment((-75,56)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(9,200,20).translate((0,0,13)))