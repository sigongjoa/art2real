import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-87,13),(-4,-37)).segment((4,-37)).segment((87,13)).segment((74,40)).segment((0,-10)).segment((-74,40)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(4,200,16).translate((41,0,13))).cut(cq.Workplane('XY').box(8,200,16).translate((26,0,13)))