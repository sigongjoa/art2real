import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-63,14),(-5,-26)).segment((5,-26)).segment((63,14)).segment((52,36)).segment((0,-4)).segment((-52,36)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,10).translate((0,0,8)))