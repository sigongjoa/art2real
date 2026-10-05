import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-89,5),(-4,-35)).segment((4,-35)).segment((89,5)).segment((76,31)).segment((0,-9)).segment((-76,31)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,10).translate((0,0,5)))