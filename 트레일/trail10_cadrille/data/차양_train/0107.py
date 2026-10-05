import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-77,17),(-4,-54)).segment((4,-54)).segment((77,17)).segment((68,35)).segment((0,-36)).segment((-68,35)).close().assemble().finalize().extrude(27).cut(cq.Workplane('XY').box(4,200,22).translate((-27,0,14)))