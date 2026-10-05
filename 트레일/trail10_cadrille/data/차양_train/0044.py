import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-87,6),(-12,-45)).segment((12,-45)).segment((87,6)).segment((79,22)).segment((0,-29)).segment((-79,22)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(4,200,16).translate((3,0,8)))