import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-61,-5),(-5,-50)).segment((5,-50)).segment((61,-5)).segment((49,19)).segment((0,-26)).segment((-49,19)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,6).translate((-22,0,8)))