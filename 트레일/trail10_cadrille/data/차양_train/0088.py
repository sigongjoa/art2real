import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-74,14),(-12,-39)).segment((12,-39)).segment((74,14)).segment((65,33)).segment((0,-20)).segment((-65,33)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(4,200,8).translate((35,0,13)))