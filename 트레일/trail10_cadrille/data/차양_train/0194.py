import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-84,6),(-10,-36)).segment((10,-36)).segment((84,6)).segment((75,25)).segment((0,-17)).segment((-75,25)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(5,200,24).translate((0,0,13)))