import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-98,-4),(-11,-58)).segment((11,-58)).segment((98,-4)).segment((85,23)).segment((0,-31)).segment((-85,23)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(10,200,16).translate((0,0,12)))