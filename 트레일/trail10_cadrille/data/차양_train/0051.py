import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-64,1),(-8,-42)).segment((8,-42)).segment((64,1)).segment((55,19)).segment((0,-24)).segment((-55,19)).close().assemble().finalize().extrude(28).cut(cq.Workplane('XY').box(7,200,16).translate((-11,0,14))).cut(cq.Workplane('XY').box(6,200,8).translate((30,0,14)))