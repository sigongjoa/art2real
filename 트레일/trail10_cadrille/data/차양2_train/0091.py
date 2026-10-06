import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-92,-2),(-11,-70)).segment((11,-70)).segment((92,-2)).segment((73,37)).segment((0,-31)).segment((-73,37)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,24).translate((1,0,14)))