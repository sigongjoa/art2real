import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-56,6),(-11,-43)).segment((11,-43)).segment((56,6)).segment((42,34)).segment((0,-15)).segment((-42,34)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(4,200,12).translate((27,0,10))).cut(cq.Workplane('XY').box(8,200,10).translate((0,0,10)))