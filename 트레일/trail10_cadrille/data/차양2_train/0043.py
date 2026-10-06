import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-93,20),(-16,-47)).segment((16,-47)).segment((93,20)).segment((77,52)).segment((0,-15)).segment((-77,52)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(6,200,20).translate((31,0,14)))