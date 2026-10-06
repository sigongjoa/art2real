import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-89,17),(-12,-53)).segment((12,-53)).segment((89,17)).segment((74,48)).segment((0,-22)).segment((-74,48)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(5,200,22).translate((26,0,14))).cut(cq.Workplane('XY').box(7,200,18).translate((32,0,14)))