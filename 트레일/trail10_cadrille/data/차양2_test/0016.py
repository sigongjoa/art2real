import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-97,0),(-12,-58)).segment((12,-58)).segment((97,0)).segment((85,25)).segment((0,-33)).segment((-85,25)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(6,200,10).translate((30,0,21))).cut(cq.Workplane('XY').box(7,200,30).translate((40,0,21)))