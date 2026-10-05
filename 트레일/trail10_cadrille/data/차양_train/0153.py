import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-63,12),(-11,-30)).segment((11,-30)).segment((63,12)).segment((56,26)).segment((0,-16)).segment((-56,26)).close().assemble().finalize().extrude(11).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,10).translate((-20,0,6)))