import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-95,6),(-16,-62)).segment((16,-62)).segment((95,6)).segment((75,46)).segment((0,-22)).segment((-75,46)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(7,200,14).translate((39,0,21))).cut(cq.Workplane('XY').box(7,200,18).translate((-39,0,21)))