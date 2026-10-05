import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-79,12),(-8,-50)).segment((8,-50)).segment((79,12)).segment((65,40)).segment((0,-22)).segment((-65,40)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,16).translate((0,0,14)))