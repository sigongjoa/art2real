import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-57,-5),(-8,-25)).segment((8,-25)).segment((57,-5)).segment((44,21)).segment((0,1)).segment((-44,21)).close().assemble().finalize().extrude(20).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(3,200,16).translate((-25,0,10))).cut(cq.Workplane('XY').box(6,200,8).translate((9,0,10)))