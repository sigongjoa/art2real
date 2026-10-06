import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-89,20),(-12,-71)).segment((12,-71)).segment((89,20)).segment((72,54)).segment((0,-37)).segment((-72,54)).close().assemble().finalize().extrude(33).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(5,200,22).translate((21,0,17)))