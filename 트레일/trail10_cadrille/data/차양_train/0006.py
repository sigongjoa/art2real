import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-60,16),(-5,-39)).segment((5,-39)).segment((60,16)).segment((49,38)).segment((0,-17)).segment((-49,38)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,8)))