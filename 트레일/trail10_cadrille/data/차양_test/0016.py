import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-91,3),(-7,-42)).segment((7,-42)).segment((91,3)).segment((84,17)).segment((0,-28)).segment((-84,17)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(4,200,12).translate((10,0,7))).cut(cq.Workplane('XY').box(3,200,8).translate((-26,0,7)))