import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-95,-2),(-16,-74)).segment((16,-74)).segment((95,-2)).segment((77,35)).segment((0,-37)).segment((-77,35)).close().assemble().finalize().extrude(27).cut(cq.Workplane('XY').box(5,200,12).translate((0,0,14)))