import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-88,16),(-11,-56)).segment((11,-56)).segment((88,16)).segment((75,42)).segment((0,-30)).segment((-75,42)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(12,200,6).translate((-8,0,13)))