import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-89,12),(-12,-36)).segment((12,-36)).segment((89,12)).segment((78,34)).segment((0,-14)).segment((-78,34)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(4,200,10).translate((42,0,14))).cut(cq.Workplane('XY').box(7,200,10).translate((-36,0,14)))