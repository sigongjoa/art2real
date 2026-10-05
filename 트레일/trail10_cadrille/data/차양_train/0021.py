import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-75,7),(-8,-44)).segment((8,-44)).segment((75,7)).segment((61,35)).segment((0,-16)).segment((-61,35)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(4,200,8).translate((0,0,5)))