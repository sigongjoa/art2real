import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-94,16),(-12,-50)).segment((12,-50)).segment((94,16)).segment((80,44)).segment((0,-22)).segment((-80,44)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,8).translate((0,0,8)))