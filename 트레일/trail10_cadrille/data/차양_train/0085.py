import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-72,18),(-12,-35)).segment((12,-35)).segment((72,18)).segment((60,43)).segment((0,-10)).segment((-60,43)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(8,200,16).translate((0,0,13)))