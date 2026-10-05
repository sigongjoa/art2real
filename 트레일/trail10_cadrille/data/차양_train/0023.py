import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-60,0),(-12,-29)).segment((12,-29)).segment((60,0)).segment((52,16)).segment((0,-13)).segment((-52,16)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(5,200,6).translate((0,0,8)))