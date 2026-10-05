import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-75,10),(-4,-40)).segment((4,-40)).segment((75,10)).segment((68,25)).segment((0,-25)).segment((-68,25)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(5,200,16).translate((0,0,10)))