import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-64,13),(-9,-46)).segment((9,-46)).segment((64,13)).segment((57,27)).segment((0,-32)).segment((-57,27)).close().assemble().finalize().extrude(12).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(5,200,6).translate((0,0,6)))