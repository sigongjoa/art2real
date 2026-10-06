import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-92,2),(-9,-62)).segment((9,-62)).segment((92,2)).segment((75,37)).segment((0,-27)).segment((-75,37)).close().assemble().finalize().extrude(31).cut(cq.Workplane('XY').box(6,200,10).translate((7,0,16)))