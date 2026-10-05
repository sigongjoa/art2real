import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-91,-2),(-13,-43)).segment((13,-43)).segment((91,-2)).segment((84,12)).segment((0,-29)).segment((-84,12)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(3,200,26).translate((24,0,13)))