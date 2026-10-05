import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-90,11),(-11,-55)).segment((11,-55)).segment((90,11)).segment((77,38)).segment((0,-28)).segment((-77,38)).close().assemble().finalize().extrude(28).cut(cq.Workplane('XY').box(6,200,10).translate((32,0,14))).cut(cq.Workplane('XY').box(8,200,22).translate((-11,0,14)))