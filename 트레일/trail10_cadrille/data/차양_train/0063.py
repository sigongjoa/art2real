import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-65,15),(-12,-34)).segment((12,-34)).segment((65,15)).segment((53,40)).segment((0,-9)).segment((-53,40)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(6,200,8).translate((0,0,9)))