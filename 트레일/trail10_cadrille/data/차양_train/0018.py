import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-74,-3),(-8,-27)).segment((8,-27)).segment((74,-3)).segment((65,15)).segment((0,-9)).segment((-65,15)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(3,200,14).translate((0,0,8)))