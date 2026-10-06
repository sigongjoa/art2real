import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-96,1),(-12,-50)).segment((12,-50)).segment((96,1)).segment((79,36)).segment((0,-15)).segment((-79,36)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(6,200,8).translate((0,0,20)))