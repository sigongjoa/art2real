import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-56,1),(-12,-55)).segment((12,-55)).segment((56,1)).segment((44,25)).segment((0,-31)).segment((-44,25)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,14).translate((-18,0,8))).cut(cq.Workplane('XY').box(7,200,12).translate((28,0,8)))