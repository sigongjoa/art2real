import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-73,16),(-4,-38)).segment((4,-38)).segment((73,16)).segment((62,38)).segment((0,-16)).segment((-62,38)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,22).translate((0,0,13)))