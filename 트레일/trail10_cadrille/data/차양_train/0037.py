import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-75,-2),(-12,-34)).segment((12,-34)).segment((75,-2)).segment((63,23)).segment((0,-9)).segment((-63,23)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(5,200,18).translate((-34,0,10)))