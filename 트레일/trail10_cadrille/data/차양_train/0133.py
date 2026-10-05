import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-82,7),(-5,-39)).segment((5,-39)).segment((82,7)).segment((71,29)).segment((0,-17)).segment((-71,29)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(6,200,18).translate((0,0,14)))