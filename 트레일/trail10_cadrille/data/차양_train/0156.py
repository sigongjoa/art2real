import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-57,11),(-13,-43)).segment((13,-43)).segment((57,11)).segment((50,26)).segment((0,-28)).segment((-50,26)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(5,200,20).translate((0,0,11)))