import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-96,23),(-12,-50)).segment((12,-50)).segment((96,23)).segment((80,55)).segment((0,-18)).segment((-80,55)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(9,200,20).translate((0,0,13)))