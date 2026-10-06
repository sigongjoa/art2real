import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-89,12),(-6,-58)).segment((6,-58)).segment((89,12)).segment((75,41)).segment((0,-29)).segment((-75,41)).close().assemble().finalize().extrude(31).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,22).translate((10,0,16))).cut(cq.Workplane('XY').box(12,200,6).translate((11,0,16)))